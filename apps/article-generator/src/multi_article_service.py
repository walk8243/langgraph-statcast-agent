"""Unified multi-material article service orchestrating Text-to-SQL, synthesis, and persistence."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from src.config import settings
from src.multi_article_synthesizer import (
    ArticleOutline,
    CollectedMaterial,
    DataRequirement,
    MultiDataArticleSynthesizer,
)
from src.postgres_client import Article, PostgresClient
from src.text_to_sql import TextToSqlEngine, TextToSqlResult

logger = logging.getLogger(__name__)


class MultiArticleServiceError(Exception):
    """Raised when multi-material article generation encounters an error."""

    pass


class MultiArticleService:
    """End-to-end service for collecting multiple data materials, synthesizing, and saving comprehensive articles."""

    def __init__(
        self,
        text_to_sql_engine: Optional[TextToSqlEngine] = None,
        synthesizer: Optional[MultiDataArticleSynthesizer] = None,
        postgres_client: Optional[PostgresClient] = None,
    ):
        self.sql_engine = text_to_sql_engine or TextToSqlEngine()
        self.synthesizer = synthesizer or MultiDataArticleSynthesizer()
        self.postgres = postgres_client or PostgresClient()

    def collect_material(self, requirement: DataRequirement) -> CollectedMaterial:
        """Collect a single material using TextToSqlEngine and ClickHouse."""
        logger.info(f"Collecting material [{requirement.label}]: '{requirement.prompt}'")
        try:
            sql_result: TextToSqlResult = self.sql_engine.process(requirement.prompt)

            if not sql_result.is_valid:
                logger.warning(
                    f"SQL validation error for [{requirement.label}]: {sql_result.validation_error}"
                )
                return CollectedMaterial(
                    label=requirement.label,
                    prompt=requirement.prompt,
                    sql=sql_result.generated_sql or "-- (Validation Failed)",
                    df=None,
                    row_count=0,
                    error=f"SQL Validation Error: {sql_result.validation_error}",
                    section_hint=requirement.section_hint,
                )

            if sql_result.execution_error:
                logger.warning(
                    f"ClickHouse execution error for [{requirement.label}]: {sql_result.execution_error}"
                )
                return CollectedMaterial(
                    label=requirement.label,
                    prompt=requirement.prompt,
                    sql=sql_result.generated_sql,
                    df=None,
                    row_count=0,
                    error=f"Execution Error: {sql_result.execution_error}",
                    section_hint=requirement.section_hint,
                )

            return CollectedMaterial(
                label=requirement.label,
                prompt=requirement.prompt,
                sql=sql_result.generated_sql,
                df=sql_result.dataframe,
                row_count=sql_result.row_count,
                error=None,
                section_hint=requirement.section_hint,
            )
        except Exception as e:
            logger.error(f"Unexpected error collecting [{requirement.label}]: {e}")
            return CollectedMaterial(
                label=requirement.label,
                prompt=requirement.prompt,
                sql="-- (Process Failed)",
                df=None,
                row_count=0,
                error=str(e),
                section_hint=requirement.section_hint,
            )

    def collect_materials(
        self, requirements: List[DataRequirement]
    ) -> List[CollectedMaterial]:
        """Collect all data materials for given requirements."""
        materials: List[CollectedMaterial] = []
        for req in requirements:
            material = self.collect_material(req)
            materials.append(material)
        return materials

    def format_combined_sql(self, materials: List[CollectedMaterial]) -> str:
        """Combine multiple SQL queries into a clean formatted string for storage and display."""
        sql_blocks: List[str] = []
        for idx, mat in enumerate(materials, start=1):
            header = f"-- [素材 {idx}: {mat.label}]\n-- 指示: {mat.prompt}"
            if mat.error:
                header += f"\n-- 状態: エラー ({mat.error})"
            block = f"{header}\n{mat.sql.strip()}"
            sql_blocks.append(block)
        return "\n\n".join(sql_blocks)

    def build_execution_summary(
        self, materials: List[CollectedMaterial]
    ) -> Dict[str, Any]:
        """Create structured JSON-serializable summary of multiple queries execution."""
        material_summaries = []
        successful_count = 0
        total_rows = 0

        for mat in materials:
            is_success = mat.df is not None and mat.error is None
            if is_success:
                successful_count += 1
                total_rows += mat.row_count

            material_summaries.append(
                {
                    "label": mat.label,
                    "prompt": mat.prompt,
                    "row_count": mat.row_count,
                    "columns": list(mat.df.columns) if mat.df is not None else [],
                    "success": is_success,
                    "error": mat.error,
                    "section_hint": mat.section_hint,
                }
            )

        return {
            "type": "multi_material",
            "total_materials": len(materials),
            "successful_materials": successful_count,
            "total_rows_collected": total_rows,
            "materials": material_summaries,
        }

    def generate_and_save_multi_article(
        self,
        outline: ArticleOutline,
        requirements: List[DataRequirement],
    ) -> Article:
        """Run complete multi-material pipeline:

        1. Collect all data materials via Text-to-SQL + ClickHouse.
        2. Synthesize structured article via Gemini.
        3. Persist article and combined SQL / summary into PostgreSQL.
        """
        logger.info(f"Starting multi-material article generation for: '{outline.title}'")

        if not requirements:
            raise MultiArticleServiceError("At least one DataRequirement must be provided.")

        # 1. Collect materials
        materials = self.collect_materials(requirements)

        # Check if all materials failed
        successful_materials = [m for m in materials if m.df is not None and not m.error]
        if not successful_materials:
            errors = [f"[{m.label}]: {m.error}" for m in materials if m.error]
            raise MultiArticleServiceError(
                f"All data material extractions failed: {'; '.join(errors)}"
            )

        # 2. Synthesize article
        title, markdown_content, model_used = self.synthesizer.generate_article(
            outline=outline,
            materials=materials,
        )

        # 3. Build persistence artifacts
        combined_sql = self.format_combined_sql(materials)
        summary_dict = self.build_execution_summary(materials)
        summary_json = json.dumps(summary_dict, ensure_ascii=False)

        article = Article(
            title=title,
            prompt=f"【企画】{outline.title} - {outline.theme}",
            generated_sql=combined_sql,
            execution_summary=summary_json,
            content_markdown=markdown_content,
            model_name=model_used,
        )

        # 4. Save to PostgreSQL
        article_id = self.postgres.save_article(article)
        article.id = article_id
        logger.info(
            f"Successfully generated and saved multi-material Article #{article_id}: '{title}'"
        )
        return article
