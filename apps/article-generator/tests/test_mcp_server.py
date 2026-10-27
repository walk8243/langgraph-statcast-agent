"""Unit tests for Statcast Text-to-SQL MCP Server."""

from unittest.mock import MagicMock
import pandas as pd
import pytest

from src.mcp_server import generate_sql, mcp, query_statcast, search_statcast_schema, set_engine
from src.text_to_sql import TextToSqlResult


@pytest.fixture(autouse=True)
def cleanup_engine():
    """Reset engine singleton before and after each test."""
    yield
    set_engine(None)


@pytest.mark.asyncio
async def test_mcp_server_tool_registration():
    """Verify that all Statcast tools are properly registered on the MCP server."""
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]

    assert "query_statcast" in tool_names
    assert "generate_sql" in tool_names
    assert "search_statcast_schema" in tool_names


@pytest.mark.asyncio
async def test_query_statcast_success():
    """Verify query_statcast successfully formats dataframe results as markdown table."""
    mock_engine = MagicMock()
    df = pd.DataFrame([
        {"player_name": "Shohei Ohtani", "home_runs": 54, "avg_exit_velo": 95.8},
        {"player_name": "Aaron Judge", "home_runs": 58, "avg_exit_velo": 96.2},
    ])
    mock_engine.process.return_value = TextToSqlResult(
        question="Top HR hitters",
        generated_sql="SELECT full_name, hr, avg_ev FROM stats",
        is_valid=True,
        dataframe=df,
        row_count=2,
    )
    set_engine(mock_engine)

    result = await mcp.call_tool("query_statcast", {"question": "Top HR hitters"})
    text_content = result.content[0].text

    assert "実行結果 (2件)" in text_content
    assert "Shohei Ohtani" in text_content
    assert "Aaron Judge" in text_content
    assert "SELECT full_name, hr, avg_ev FROM stats" in text_content


@pytest.mark.asyncio
async def test_query_statcast_empty_results():
    """Verify query_statcast handles empty dataframe response gracefully."""
    mock_engine = MagicMock()
    mock_engine.process.return_value = TextToSqlResult(
        question="Empty question",
        generated_sql="SELECT * FROM stats WHERE 1=0",
        is_valid=True,
        dataframe=pd.DataFrame(),
        row_count=0,
    )
    set_engine(mock_engine)

    result = await mcp.call_tool("query_statcast", {"question": "Empty question"})
    text_content = result.content[0].text

    assert "実行結果 (0件)" in text_content
    assert "条件に一致するデータが見つかりませんでした" in text_content
    assert "SELECT * FROM stats WHERE 1=0" in text_content


@pytest.mark.asyncio
async def test_query_statcast_validation_error():
    """Verify query_statcast returns safety validation error details."""
    mock_engine = MagicMock()
    mock_engine.process.return_value = TextToSqlResult(
        question="Drop table",
        generated_sql="DROP TABLE stats",
        is_valid=False,
        validation_error="Only SELECT or WITH queries are permitted",
    )
    set_engine(mock_engine)

    result = await mcp.call_tool("query_statcast", {"question": "Drop table"})
    text_content = result.content[0].text

    assert "SQL安全性バリデーションエラー" in text_content
    assert "Only SELECT or WITH queries are permitted" in text_content
    assert "DROP TABLE stats" in text_content


@pytest.mark.asyncio
async def test_query_statcast_execution_error():
    """Verify query_statcast returns DB execution error details."""
    mock_engine = MagicMock()
    mock_engine.process.return_value = TextToSqlResult(
        question="Bad query",
        generated_sql="SELECT unknown_col FROM stats",
        is_valid=True,
        execution_error="ClickHouse exception: Unknown column unknown_col",
    )
    set_engine(mock_engine)

    result = await mcp.call_tool("query_statcast", {"question": "Bad query"})
    text_content = result.content[0].text

    assert "クエリ実行エラー" in text_content
    assert "Unknown column unknown_col" in text_content


@pytest.mark.asyncio
async def test_generate_sql_success():
    """Verify generate_sql returns formatted SQL code block."""
    mock_engine = MagicMock()
    mock_engine.generate_sql.return_value = (
        "SELECT batter, count() FROM statcast.statcast_raw GROUP BY batter",
        {},
    )
    set_engine(mock_engine)

    result = await mcp.call_tool("generate_sql", {"question": "Pitch count by batter"})
    text_content = result.content[0].text

    assert "```sql" in text_content
    assert "SELECT batter, count() FROM statcast.statcast_raw GROUP BY batter" in text_content


@pytest.mark.asyncio
async def test_generate_sql_exception():
    """Verify generate_sql formats exception message when generation fails."""
    mock_engine = MagicMock()
    mock_engine.generate_sql.side_effect = RuntimeError("Gemini quota exceeded")
    set_engine(mock_engine)

    result = await mcp.call_tool("generate_sql", {"question": "Any question"})
    text_content = result.content[0].text

    assert "SQL生成エラー: Gemini quota exceeded" in text_content


@pytest.mark.asyncio
async def test_search_statcast_schema_all():
    """Verify search_statcast_schema queries Qdrant for DDLs, docs, and SQL examples."""
    mock_engine = MagicMock()
    mock_qdrant = MagicMock()

    def fake_search(keyword, limit=3, item_type=None):
        if item_type == "ddl":
            return [{"payload": {"table_name": "statcast_raw", "content": "CREATE TABLE ..."}}]
        elif item_type == "doc":
            return [{"payload": {"title": "Exit Velocity", "content": "Speed off bat"}}]
        elif item_type == "sql_example":
            return [{"payload": {"question": "HR Leaders", "sql": "SELECT ... FROM ..."}}]
        return []

    mock_qdrant.search.side_effect = fake_search
    mock_engine.qdrant = mock_qdrant
    set_engine(mock_engine)

    result = await mcp.call_tool("search_statcast_schema", {"keyword": "exit velocity"})
    text_content = result.content[0].text

    assert "テーブル定義 (DDL)" in text_content
    assert "statcast_raw" in text_content
    assert "ドキュメント・用語解説" in text_content
    assert "Exit Velocity" in text_content
    assert "参考SQL例文" in text_content
    assert "HR Leaders" in text_content


@pytest.mark.asyncio
async def test_search_statcast_schema_not_found():
    """Verify search_statcast_schema notifies user when no knowledge is found."""
    mock_engine = MagicMock()
    mock_qdrant = MagicMock()
    mock_qdrant.search.return_value = []
    mock_engine.qdrant = mock_qdrant
    set_engine(mock_engine)

    result = await mcp.call_tool("search_statcast_schema", {"keyword": "nonexistent_term"})
    text_content = result.content[0].text

    assert "キーワード 'nonexistent_term' に一致するナレッジは見つかりませんでした。" in text_content
