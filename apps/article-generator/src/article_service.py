"""Unified service orchestrating Text-to-SQL, article synthesis, and PostgreSQL persistence."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from src.article_synthesizer import ArticleSynthesizer
from src.clickhouse_client import ClickHouseClient
from src.config import settings
from src.postgres_client import Article, PostgresClient
from src.qdrant_memory import QdrantKnowledgeStore
from src.text_to_sql import TextToSqlEngine, TextToSqlResult

logger = logging.getLogger(__name__)


class ArticleServiceError(Exception):
    """Raised when article generation or persistence encounters an error."""

    pass


class ArticleService:
    """End-to-end service for generating and saving analytical articles."""

    def __init__(
        self,
        text_to_sql_engine: Optional[TextToSqlEngine] = None,
        article_synthesizer: Optional[ArticleSynthesizer] = None,
        postgres_client: Optional[PostgresClient] = None,
    ):
        self.sql_engine = text_to_sql_engine or TextToSqlEngine()
        self.synthesizer = article_synthesizer or ArticleSynthesizer()
        self.postgres = postgres_client or PostgresClient()

    def generate_and_save_article(self, prompt: str) -> Article:
        """Run complete pipeline: Text-to-SQL -> ClickHouse -> LLM Synthesis -> PostgreSQL save."""
        logger.info(f"Starting article generation for prompt: '{prompt}'")

        # 1. Text-to-SQL and ClickHouse execution
        sql_result: TextToSqlResult = self.sql_engine.process(prompt)

        if not sql_result.is_valid:
            raise ArticleServiceError(
                f"SQL validation failed for generated query: {sql_result.validation_error}"
            )

        if sql_result.execution_error:
            raise ArticleServiceError(
                f"ClickHouse execution failed: {sql_result.execution_error}"
            )

        df = sql_result.dataframe

        # 2. Article Synthesis via Gemini
        title, markdown_content, model_used = self.synthesizer.generate_article(
            user_prompt=prompt,
            sql=sql_result.generated_sql,
            df=df,
        )

        # 3. Create execution summary
        summary_dict = {
            "row_count": sql_result.row_count,
            "columns": list(df.columns) if df is not None else [],
        }

        article = Article(
            title=title,
            prompt=prompt,
            generated_sql=sql_result.generated_sql,
            execution_summary=json.dumps(summary_dict, ensure_ascii=False),
            content_markdown=markdown_content,
            model_name=model_used,
        )

        # 4. Save to PostgreSQL
        article_id = self.postgres.save_article(article)
        logger.info(f"Successfully generated and saved Article #{article_id}: '{title}'")
        return article

    def get_article(self, article_id: int) -> Optional[Article]:
        """Fetch an article by ID from PostgreSQL."""
        return self.postgres.get_article(article_id)

    def list_articles(self, limit: int = 20, offset: int = 0) -> List[Article]:
        """Fetch recent articles list from PostgreSQL."""
        return self.postgres.list_articles(limit=limit, offset=offset)
