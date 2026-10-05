"""Unit tests for ArticleSynthesizer, PostgresClient, and ArticleService."""

from datetime import datetime
import json
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from src.article_service import ArticleService, ArticleServiceError
from src.article_synthesizer import ArticleSynthesizer
from src.postgres_client import Article, PostgresClient
from src.text_to_sql import TextToSqlEngine, TextToSqlResult


def test_article_synthesizer_prompt_construction():
    """Verify prompt formatting for article synthesis."""
    synthesizer = ArticleSynthesizer(gemini_api_key="dummy")
    df = pd.DataFrame([
        {"team": "LAD", "hrs": 233},
        {"team": "NYY", "hrs": 237},
    ])
    prompt = synthesizer._build_article_prompt(
        user_prompt="2024年のチーム別本塁打数と特徴",
        sql="SELECT team, hrs FROM test",
        df=df,
    )
    assert "2024年のチーム別本塁打数と特徴" in prompt
    assert "SELECT team, hrs FROM test" in prompt
    assert "LAD" in prompt
    assert "233" in prompt
    assert "## 概要・エグゼクティブサマリー" in prompt


@patch.object(ArticleSynthesizer, "generate_article")
def test_article_synthesizer_mock(mock_generate):
    """Test ArticleSynthesizer return values with mock."""
    mock_generate.return_value = (
        "2024年MLB本塁打分析レポート",
        "# 2024年MLB本塁打分析レポート\n\n## 概要\n- テスト",
        "gemini-3.8-flash",
    )
    synthesizer = ArticleSynthesizer(gemini_api_key="dummy")
    title, md, model = synthesizer.generate_article("test", "sql", pd.DataFrame())
    assert title == "2024年MLB本塁打分析レポート"
    assert "概要" in md
    assert model == "gemini-3.8-flash"


def test_postgres_client_save_and_retrieve_mock():
    """Verify PostgresClient save and get logic with mock connection."""
    client = PostgresClient()

    article = Article(
        title="Test Article",
        prompt="Test Prompt",
        content_markdown="# Test Markdown",
        model_name="gemini-3.8-flash",
        generated_sql="SELECT 1",
        execution_summary=json.dumps({"row_count": 1}),
    )

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.__enter__.return_value = mock_conn

    # Mock RETURNING id
    mock_cur.fetchone.return_value = {"id": 42}

    with patch.object(client, "get_connection", return_value=mock_conn):
        with patch.object(client, "ensure_table_exists"):
            article_id = client.save_article(article)
            assert article_id == 42
            assert article.id == 42


def test_article_service_end_to_end_mock():
    """Test complete ArticleService workflow with mocked dependencies."""
    mock_sql_engine = MagicMock(spec=TextToSqlEngine)
    mock_synthesizer = MagicMock(spec=ArticleSynthesizer)
    mock_postgres = MagicMock(spec=PostgresClient)

    # Mock SQL execution result
    df = pd.DataFrame([{"team": "LAD", "total_home_runs": 233}])
    mock_sql_engine.process.return_value = TextToSqlResult(
        question="2024年チーム別本塁打",
        generated_sql="SELECT team, count() FROM statcast_raw",
        is_valid=True,
        dataframe=df,
        row_count=1,
    )

    # Mock Synthesizer
    mock_synthesizer.generate_article.return_value = (
        "2024年本塁打ランキング分析",
        "# 2024年本塁打ランキング分析\n\n## 概要\n詳細分析",
        "gemini-3.8-flash",
    )

    # Mock Postgres save
    mock_postgres.save_article.return_value = 100

    service = ArticleService(
        text_to_sql_engine=mock_sql_engine,
        article_synthesizer=mock_synthesizer,
        postgres_client=mock_postgres,
    )

    article = service.generate_and_save_article("2024年チーム別本塁打")

    assert article.title == "2024年本塁打ランキング分析"
    assert article.model_name == "gemini-3.8-flash"
    assert "2024年本塁打ランキング分析" in article.content_markdown
    mock_postgres.save_article.assert_called_once()


def test_article_service_handles_sql_error():
    """Verify that ArticleService raises error if SQL validation or execution fails."""
    mock_sql_engine = MagicMock(spec=TextToSqlEngine)
    mock_synthesizer = MagicMock(spec=ArticleSynthesizer)
    mock_postgres = MagicMock(spec=PostgresClient)

    mock_sql_engine.process.return_value = TextToSqlResult(
        question="Invalid query",
        generated_sql="DROP TABLE test",
        is_valid=False,
        validation_error="Disallowed keyword detected",
    )

    service = ArticleService(
        text_to_sql_engine=mock_sql_engine,
        article_synthesizer=mock_synthesizer,
        postgres_client=mock_postgres,
    )

    with pytest.raises(ArticleServiceError) as exc_info:
        service.generate_and_save_article("Invalid query")

    assert "SQL validation failed" in str(exc_info.value)
    mock_synthesizer.generate_article.assert_not_called()
    mock_postgres.save_article.assert_not_called()
