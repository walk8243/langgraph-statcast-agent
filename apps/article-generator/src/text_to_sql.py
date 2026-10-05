"""Text-to-SQL engine integrating Qdrant context, Gemini LLM, and ClickHouse execution."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from google import genai
from google.genai import types
import pandas as pd

from src.clickhouse_client import ClickHouseClient, SqlValidationError
from src.config import settings
from src.qdrant_memory import QdrantKnowledgeStore

logger = logging.getLogger(__name__)


@dataclass
class TextToSqlResult:
    """Represents the output of a Text-to-SQL generation and execution cycle."""

    question: str
    generated_sql: str
    is_valid: bool = False
    validation_error: Optional[str] = None
    dataframe: Optional[pd.DataFrame] = None
    row_count: int = 0
    execution_error: Optional[str] = None
    retrieved_context: Dict[str, Any] = field(default_factory=dict)


class TextToSqlEngine:
    """Core engine for converting natural language queries into ClickHouse SQL and executing them."""

    def __init__(
        self,
        clickhouse: Optional[ClickHouseClient] = None,
        qdrant_store: Optional[QdrantKnowledgeStore] = None,
        gemini_api_key: Optional[str] = None,
        gemini_model: Optional[str] = None,
    ):
        self.clickhouse = clickhouse or ClickHouseClient()
        self.qdrant = qdrant_store or QdrantKnowledgeStore()
        self.gemini_api_key = gemini_api_key or settings.gemini_api_key
        self.gemini_model = gemini_model or settings.gemini_model

        self._gemini_client: Optional[genai.Client] = None
        if self.gemini_api_key:
            try:
                self._gemini_client = genai.Client(api_key=self.gemini_api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Gemini client: {e}")

    def retrieve_context(self, question: str) -> Dict[str, List[Dict[str, Any]]]:
        """Search Qdrant for relevant DDLs, docs, and SQL examples based on the question."""
        try:
            ddl_hits = self.qdrant.search(question, limit=3, item_type="ddl")
            doc_hits = self.qdrant.search(question, limit=2, item_type="doc")
            sql_hits = self.qdrant.search(question, limit=3, item_type="sql_example")

            # Fallback if no specific hits found in vector search (e.g. empty collection)
            if not ddl_hits:
                ddl_hits = [{"payload": p} for p in self.qdrant.get_all_ddls()[:3]]

            return {
                "ddls": [hit["payload"] for hit in ddl_hits if "payload" in hit],
                "docs": [hit["payload"] for hit in doc_hits if "payload" in hit],
                "sql_examples": [hit["payload"] for hit in sql_hits if "payload" in hit],
            }
        except Exception as e:
            logger.warning(f"Error retrieving context from Qdrant: {e}")
            return {"ddls": [], "docs": [], "sql_examples": []}

    def _build_prompt(self, question: str, context: Dict[str, List[Dict[str, Any]]]) -> str:
        """Construct the prompt sent to Gemini for SQL generation."""
        ddl_text = "\n\n".join(
            f"Table `{d.get('table_name', 'table')}`:\n{d.get('content', '')}"
            for d in context.get("ddls", [])
        )
        docs_text = "\n\n".join(
            f"Documentation [{d.get('title', '')}]:\n{d.get('content', '')}"
            for d in context.get("docs", [])
        )
        examples_text = "\n\n".join(
            f"-- Question: {ex.get('question', '')}\n{ex.get('sql', '')}"
            for ex in context.get("sql_examples", [])
        )

        prompt = f"""
You are an expert ClickHouse SQL engineer analyzing MLB Statcast data.
Your task is to generate a single, highly optimized ClickHouse SQL query (SELECT statement only) that answers the user's question.

### ClickHouse Table Schemas:
{ddl_text if ddl_text else "No DDL available in context. Assume tables statcast.statcast_raw, statcast.players, statcast.teams exist."}

### Statcast Domain Documentation & Rules:
{docs_text}
- Always generate standard ClickHouse SQL syntax.
- Only SELECT statements or WITH ... SELECT are permitted. Do NOT generate INSERT, UPDATE, DELETE, DROP, or ALTER statements.
- Use ClickHouse aggregate functions (e.g., count(), avg(), sum(), countIf(), avgIf(), round()).
- Filter NULLs where appropriate (e.g., launch_speed IS NOT NULL).
- When linking players, JOIN statcast.players ON s.batter = p.player_id (or s.pitcher = p.player_id).
- Return ONLY the executable SQL query. Do not wrap in markdown quotes (no ```sql) and do not provide explanatory text.

### Example Queries:
{examples_text}

### User Question:
{question}

SQL Query:
""".strip()
        return prompt

    def generate_sql(self, question: str) -> Tuple[str, Dict[str, Any]]:
        """Generate SQL query for a natural language question.

        Returns:
            Tuple of (generated_sql, retrieved_context)
        """
        context = self.retrieve_context(question)
        prompt = self._build_prompt(question, context)

        if not self._gemini_client:
            raise RuntimeError("Gemini API key is not configured or client failed to initialize.")

        candidate_models = [self.gemini_model]
        for fallback in ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.7-flash", "gemini-flash-latest"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        response = None
        last_error = None
        for model_name in candidate_models:
            try:
                response = self._gemini_client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                    ),
                )
                if response and response.text:
                    break
            except Exception as e:
                logger.warning(f"Failed to generate SQL with model {model_name} ({e}), trying fallback...")
                last_error = e

        if not response or not response.text:
            raise RuntimeError(f"All candidate models failed to generate SQL. Last error: {last_error}")

        raw_text = response.text or ""

        # Clean markdown code blocks if present
        sql = raw_text.strip()
        if sql.startswith("```"):
            sql = re.sub(r"^```(?:sql)?\s*", "", sql, flags=re.IGNORECASE)
            sql = re.sub(r"\s*```$", "", sql)
        sql = sql.strip().rstrip(";")

        return sql, context

    def process(self, question: str) -> TextToSqlResult:
        """Complete workflow: retrieve context, generate SQL, validate safety, execute on ClickHouse."""
        result = TextToSqlResult(question=question, generated_sql="")

        try:
            sql, context = self.generate_sql(question)
            result.generated_sql = sql
            result.retrieved_context = context

            # Validate SQL
            is_valid, validation_err = self.clickhouse.validate_safe_sql(sql)
            result.is_valid = is_valid
            result.validation_error = validation_err if not is_valid else None

            if not is_valid:
                return result

            # Execute SQL
            df = self.clickhouse.run_query(sql)
            result.dataframe = df
            result.row_count = len(df)
            return result

        except SqlValidationError as e:
            result.is_valid = False
            result.validation_error = str(e)
            return result
        except Exception as e:
            logger.error(f"Error processing question '{question}': {e}")
            result.execution_error = str(e)
            return result
