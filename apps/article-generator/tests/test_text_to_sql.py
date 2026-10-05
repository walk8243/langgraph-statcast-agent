"""Unit tests for SQL validation, Qdrant store, and Text-to-SQL logic."""

from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from src.clickhouse_client import ClickHouseClient, SqlValidationError
from src.config import Settings
from src.qdrant_memory import QdrantKnowledgeStore
from src.text_to_sql import TextToSqlEngine, TextToSqlResult
from src.training_data import SQL_EXAMPLES, STATCAST_DOCS


def test_validate_safe_sql_valid_queries():
    """Verify that legitimate SELECT queries pass validation."""
    valid_queries = [
        "SELECT * FROM statcast.statcast_raw LIMIT 10",
        "SELECT count(), avg(launch_speed) FROM statcast.statcast_raw WHERE game_year = 2024",
        """
        WITH top_batters AS (
            SELECT batter, count() AS hrs FROM statcast.statcast_raw WHERE events = 'home_run' GROUP BY batter
        )
        SELECT * FROM top_batters ORDER BY hrs DESC LIMIT 5
        """,
        "SELECT p.full_name, s.launch_speed FROM statcast.statcast_raw s JOIN statcast.players p ON s.batter = p.player_id",
    ]

    for q in valid_queries:
        is_valid, msg = ClickHouseClient.validate_safe_sql(q)
        assert is_valid is True, f"Expected '{q}' to be valid, but got error: {msg}"


def test_validate_safe_sql_disallowed_queries():
    """Verify that destructive or non-SELECT queries are rejected."""
    invalid_queries = [
        ("DROP TABLE statcast.statcast_raw", "Only SELECT or WITH queries are permitted"),
        ("TRUNCATE TABLE statcast.statcast_raw", "Only SELECT or WITH queries are permitted"),
        ("DELETE FROM statcast.statcast_raw WHERE game_year = 2024", "Only SELECT or WITH queries are permitted"),
        ("UPDATE statcast.players SET full_name = 'Hacked' WHERE player_id = 1", "Only SELECT or WITH queries are permitted"),
        ("INSERT INTO statcast.statcast_raw VALUES (1, 2)", "Only SELECT or WITH queries are permitted"),
        ("ALTER TABLE statcast.statcast_raw ADD COLUMN test String", "Only SELECT or WITH queries are permitted"),
        ("WITH cte AS (SELECT 1) DELETE FROM statcast.statcast_raw", "Disallowed keyword detected: DELETE"),
        ("SELECT 1; DROP TABLE statcast.statcast_raw", "Multiple statements are not permitted"),
        ("", "SQL statement is empty"),
    ]

    for q, expected_err in invalid_queries:
        is_valid, msg = ClickHouseClient.validate_safe_sql(q)
        assert is_valid is False, f"Expected '{q}' to be invalid"
        assert expected_err in msg, f"Expected '{expected_err}' in '{msg}'"


def test_settings_defaults():
    """Verify that settings load with expected defaults."""
    settings = Settings(gemini_api_key="test-key")
    assert settings.clickhouse_host == "localhost"
    assert settings.clickhouse_http_port == 8123
    assert settings.clickhouse_db == "statcast"
    assert settings.qdrant_host == "localhost"
    assert settings.qdrant_http_port == 6333
    assert settings.qdrant_url == "http://localhost:6333"
    assert settings.gemini_embedding_model == "gemini-embedding-001"


def test_training_data_structure():
    """Verify that Statcast docs and SQL examples are defined properly."""
    assert len(STATCAST_DOCS) >= 3
    for title, doc in STATCAST_DOCS:
        assert isinstance(title, str) and len(title) > 0
        assert isinstance(doc, str) and len(doc) > 0

    assert len(SQL_EXAMPLES) >= 5
    for question, sql in SQL_EXAMPLES:
        assert isinstance(question, str) and len(question) > 0
        assert isinstance(sql, str) and len(sql) > 0
        # Each sample SQL must pass safety validation
        is_valid, msg = ClickHouseClient.validate_safe_sql(sql)
        assert is_valid is True, f"Sample SQL for '{question}' failed validation: {msg}"


def test_qdrant_fallback_embedding():
    """Verify that QdrantKnowledgeStore provides deterministic vector when Gemini is offline."""
    store = QdrantKnowledgeStore(url="http://localhost:6333", gemini_api_key="")
    emb1 = store.generate_embedding("Exit velocity test")
    emb2 = store.generate_embedding("Exit velocity test")
    emb3 = store.generate_embedding("Different text")

    assert len(emb1) == store.dimension
    assert emb1 == emb2  # Deterministic for same text
    assert emb1 != emb3  # Different for different text


def test_text_to_sql_prompt_construction():
    """Verify that TextToSqlEngine builds rich prompt with context."""
    engine = TextToSqlEngine(gemini_api_key="dummy")
    context = {
        "ddls": [{"table_name": "statcast_raw", "content": "CREATE TABLE statcast_raw ..."}],
        "docs": [{"title": "Launch Speed", "content": "95 mph is hard hit"}],
        "sql_examples": [{"question": "Top HRs", "sql": "SELECT count() ..."}],
    }
    prompt = engine._build_prompt("Show me top home runs", context)
    assert "statcast_raw" in prompt
    assert "Launch Speed" in prompt
    assert "Top HRs" in prompt
    assert "Show me top home runs" in prompt


@patch.object(ClickHouseClient, "run_query")
@patch.object(TextToSqlEngine, "generate_sql")
def test_text_to_sql_process_success(mock_generate, mock_run_query):
    """Verify successful end-to-end processing with mocked generator and DB."""
    mock_generate.return_value = (
        "SELECT home_team, count() AS hrs FROM statcast.statcast_raw WHERE events = 'home_run' GROUP BY home_team",
        {"ddls": [], "docs": [], "sql_examples": []},
    )
    mock_run_query.return_value = pd.DataFrame([{"home_team": "LAD", "hrs": 233}])

    engine = TextToSqlEngine(gemini_api_key="dummy")
    result = engine.process("2024年チーム別本塁打数")

    assert result.is_valid is True
    assert result.validation_error is None
    assert result.execution_error is None
    assert result.row_count == 1
    assert result.dataframe is not None
    assert result.dataframe.iloc[0]["home_team"] == "LAD"


@patch.object(TextToSqlEngine, "generate_sql")
def test_text_to_sql_process_invalid_sql(mock_generate):
    """Verify that process() halts if generated SQL is dangerous."""
    mock_generate.return_value = (
        "DROP TABLE statcast.statcast_raw",
        {"ddls": [], "docs": [], "sql_examples": []},
    )

    engine = TextToSqlEngine(gemini_api_key="dummy")
    result = engine.process("テーブルを削除して")

    assert result.is_valid is False
    assert result.validation_error is not None
    assert "Only SELECT or WITH queries are permitted" in result.validation_error
    assert result.dataframe is None
