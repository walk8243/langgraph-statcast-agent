"""Model Context Protocol (MCP) server exposing Statcast Text-to-SQL tools."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Any, Dict, List, Optional

from mcp.server.mcpserver import MCPServer
import pandas as pd

from src.text_to_sql import TextToSqlEngine

logger = logging.getLogger(__name__)

mcp = MCPServer("statcast-text-to-sql")

_engine: Optional[TextToSqlEngine] = None


def get_engine() -> TextToSqlEngine:
    """Retrieve or lazily initialize the TextToSqlEngine singleton."""
    global _engine
    if _engine is None:
        _engine = TextToSqlEngine()
    return _engine


def set_engine(engine: Optional[TextToSqlEngine]) -> None:
    """Set the TextToSqlEngine instance (useful for testing and dependency injection)."""
    global _engine
    _engine = engine


@mcp.tool()
def query_statcast(question: str) -> str:
    """MLB Statcastのデータを自然言語で質問し、ClickHouseから集計結果を取得します。

    Args:
        question: 自然言語での質問（例: '2024年の大谷翔平の月別本塁打数と平均打球速度を教えて'）

    Returns:
        実行されたSQLと集計結果データ（Markdownテーブル形式）
    """
    engine = get_engine()
    res = engine.process(question)

    if res.validation_error:
        return (
            f"### SQL安全性バリデーションエラー\n"
            f"**エラー内容**: {res.validation_error}\n\n"
            f"**生成されたSQL**:\n```sql\n{res.generated_sql}\n```"
        )

    if res.execution_error:
        return (
            f"### クエリ実行エラー\n"
            f"**エラー内容**: {res.execution_error}\n\n"
            f"**生成されたSQL**:\n```sql\n{res.generated_sql}\n```"
        )

    if res.dataframe is None or res.dataframe.empty:
        return (
            f"### 実行結果 (0件)\n"
            f"条件に一致するデータが見つかりませんでした。\n\n"
            f"**実行されたSQL**:\n```sql\n{res.generated_sql}\n```"
        )

    table_md = res.dataframe.to_markdown(index=False)
    return (
        f"### 実行結果 ({res.row_count}件)\n\n"
        f"{table_md}\n\n"
        f"**実行されたSQL**:\n```sql\n{res.generated_sql}\n```"
    )


@mcp.tool()
def generate_sql(question: str) -> str:
    """自然言語の質問から ClickHouse 用の Statcast SQL クエリのみを生成します（DB実行は行いません）。

    Args:
        question: 自然言語での質問（例: '2024年レギュラーシーズンの規定打席到達者の打率トップ10'）

    Returns:
        生成されたClickHouse SQLクエリ
    """
    engine = get_engine()
    try:
        sql, _ = engine.generate_sql(question)
        return f"```sql\n{sql}\n```"
    except Exception as e:
        return f"SQL生成エラー: {e}"


@mcp.tool()
def search_statcast_schema(keyword: str, item_type: Optional[str] = None) -> str:
    """Statcastのテーブル定義(DDL)、用語・指標解説ドキュメント、過去のSQL例文を検索します。

    Args:
        keyword: 検索キーワード（例: 'launch_speed', 'バレル', 'boxscore_batting'）
        item_type: 検索対象タイプ ('ddl', 'doc', 'sql_example' のいずれか。未指定時は全て)

    Returns:
        検索結果のリスト（Markdown形式）
    """
    engine = get_engine()
    try:
        results = []
        if item_type in (None, "ddl"):
            hits = engine.qdrant.search(keyword, limit=3, item_type="ddl")
            if hits:
                results.append("### テーブル定義 (DDL)")
                for h in hits:
                    p = h.get("payload", {})
                    results.append(f"**{p.get('table_name', 'table')}**:\n```sql\n{p.get('content', '')}\n```")

        if item_type in (None, "doc"):
            hits = engine.qdrant.search(keyword, limit=3, item_type="doc")
            if hits:
                results.append("### ドキュメント・用語解説")
                for h in hits:
                    p = h.get("payload", {})
                    results.append(f"**{p.get('title', '')}**:\n{p.get('content', '')}")

        if item_type in (None, "sql_example"):
            hits = engine.qdrant.search(keyword, limit=3, item_type="sql_example")
            if hits:
                results.append("### 参考SQL例文")
                for h in hits:
                    p = h.get("payload", {})
                    results.append(f"**Q: {p.get('question', '')}**\n```sql\n{p.get('sql', '')}\n```")

        if not results:
            return f"キーワード '{keyword}' に一致するナレッジは見つかりませんでした。"

        return "\n\n".join(results)
    except Exception as e:
        return f"スキーマ検索エラー: {e}"


def main():
    """CLI entry point for running the MCP server."""
    parser = argparse.ArgumentParser(description="Statcast Text-to-SQL MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport type (default: stdio)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind for SSE/HTTP transport (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8003,
        help="Port for SSE/HTTP transport (default: 8003)",
    )
    parser.add_argument(
        "--path",
        type=str,
        default="/sse",
        help="Path for SSE or Streamable HTTP endpoint (default: /sse)",
    )
    args = parser.parse_args()

    # For stdio transport, stdout is used for JSON-RPC messages, so route logs strictly to stderr
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )
    logger.info(f"Starting Statcast MCP server using {args.transport} transport on {args.host}:{args.port}{args.path}...")

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port, sse_path=args.path)
    elif args.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port, streamable_http_path=args.path)


if __name__ == "__main__":
    main()
