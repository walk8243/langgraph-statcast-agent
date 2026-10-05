"""CLI entrypoint for article-generator Text-to-SQL service."""

from __future__ import annotations

import argparse
import logging
import sys

from src.article_service import ArticleService
from src.clickhouse_client import ClickHouseClient
from src.config import settings
from src.postgres_client import PostgresClient
from src.qdrant_memory import QdrantKnowledgeStore
from src.text_to_sql import TextToSqlEngine
from src.training_data import train_knowledge_base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("article-generator")


def cmd_check_services() -> int:
    """Check connectivity to ClickHouse, Qdrant, and PostgreSQL."""
    print("Checking services status...")
    ch = ClickHouseClient()
    ch_ok = ch.ping()
    print(f"ClickHouse ({settings.clickhouse_host}:{settings.clickhouse_http_port}): {'[OK]' if ch_ok else '[FAILED]'}")

    qdrant = QdrantKnowledgeStore()
    try:
        count = qdrant.count()
        print(f"Qdrant ({settings.qdrant_url}): [OK] (Items: {count})")
        qdrant_ok = True
    except Exception as e:
        print(f"Qdrant ({settings.qdrant_url}): [FAILED] ({e})")
        qdrant_ok = False

    pg = PostgresClient()
    try:
        with pg.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        print(f"PostgreSQL ({settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}): [OK]")
        pg_ok = True
    except Exception as e:
        print(f"PostgreSQL ({settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}): [FAILED] ({e})")
        pg_ok = False

    return 0 if (ch_ok and qdrant_ok and pg_ok) else 1


def cmd_train() -> int:
    """Train/populate Qdrant with ClickHouse schemas and Statcast knowledge."""
    print("Starting Qdrant training for Statcast Text-to-SQL...")
    ch = ClickHouseClient()
    store = QdrantKnowledgeStore()

    stats = train_knowledge_base(store, ch)
    print("\nTraining completed successfully!")
    print(f"  - Table DDLs registered: {stats['ddls']}")
    print(f"  - Documentation topics registered: {stats['docs']}")
    print(f"  - SQL Examples registered: {stats['sql_examples']}")
    print(f"  - Total items: {stats['total']}")
    return 0


def cmd_query(question: str) -> int:
    """Execute natural language query to generate and run SQL."""
    print(f"\nUser Question: {question}")
    print("=" * 60)

    engine = TextToSqlEngine()
    result = engine.process(question)

    print("\nGenerated SQL:")
    print("-" * 60)
    print(result.generated_sql)
    print("-" * 60)

    if not result.is_valid:
        print(f"\nValidation Error: {result.validation_error}")
        return 1

    if result.execution_error:
        print(f"\nExecution Error: {result.execution_error}")
        return 1

    print(f"\nClickHouse Results ({result.row_count} rows):")
    print("-" * 60)
    if result.dataframe is not None and not result.dataframe.empty:
        # Display nicely formatted dataframe
        print(result.dataframe.to_string(index=False))
    else:
        print("No rows returned.")
    print("=" * 60)
    return 0


def cmd_generate_article(prompt: str) -> int:
    """Generate analytical article and persist to PostgreSQL."""
    print(f"\nGenerating Article for Topic: '{prompt}'")
    print("=" * 60)

    service = ArticleService()
    try:
        article = service.generate_and_save_article(prompt)
    except Exception as e:
        print(f"\nArticle generation failed: {e}")
        return 1

    print(f"\n[Success] Article Saved with ID: {article.id}")
    print(f"Title: {article.title}")
    print(f"Model: {article.model_name}")
    print("\nGenerated SQL:")
    print("-" * 60)
    print(article.generated_sql)
    print("-" * 60)
    print("\nArticle Markdown Preview:")
    print("=" * 60)
    print(article.content_markdown)
    print("=" * 60)
    return 0


def cmd_list_articles() -> int:
    """List recent saved articles."""
    service = ArticleService()
    articles = service.list_articles(limit=20)
    if not articles:
        print("No articles found.")
        return 0

    print(f"\nSaved Articles ({len(articles)} items):")
    print(f"{'ID':<6} {'Created At':<26} {'Title'}")
    print("-" * 70)
    for a in articles:
        created = a.created_at.strftime("%Y-%m-%d %H:%M:%S") if a.created_at else "-"
        print(f"{a.id:<6} {created:<26} {a.title}")
    return 0


def cmd_get_article(article_id: int) -> int:
    """Display the full content of an article."""
    service = ArticleService()
    article = service.get_article(article_id)
    if not article:
        print(f"Article #{article_id} not found.")
        return 1

    print(f"\nArticle #{article.id}: {article.title}")
    print(f"Prompt: {article.prompt}")
    print(f"Model: {article.model_name}")
    print(f"Created: {article.created_at}")
    print("\nSQL Used:")
    print(article.generated_sql)
    print("\nMarkdown Content:")
    print("=" * 60)
    print(article.content_markdown)
    print("=" * 60)
    return 0


def cmd_validate_sql(sql: str) -> int:
    """Validate SQL query for safety constraints."""
    is_valid, msg = ClickHouseClient.validate_safe_sql(sql)
    if is_valid:
        print(f"SQL is valid and safe: {sql}")
        return 0
    else:
        print(f"SQL validation failed: {msg}")
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MLB Statcast Text-to-SQL & AI Article Generator CLI"
    )
    parser.add_argument(
        "--check-services",
        action="store_true",
        help="Check connectivity to ClickHouse, Qdrant, and PostgreSQL",
    )
    parser.add_argument(
        "--train",
        action="store_true",
        help="Train/populate Qdrant with ClickHouse schema DDL, documentation, and SQL examples",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Natural language question to convert to ClickHouse SQL and execute",
    )
    parser.add_argument(
        "--generate-article",
        type=str,
        help="Generate a complete Markdown analysis article from topic and save to PostgreSQL",
    )
    parser.add_argument(
        "--list-articles",
        action="store_true",
        help="List all saved articles in PostgreSQL",
    )
    parser.add_argument(
        "--get-article",
        type=int,
        help="Retrieve and display article by ID",
    )
    parser.add_argument(
        "--validate-sql",
        type=str,
        help="Validate a SQL query string for security rules",
    )

    args = parser.parse_args()

    if args.check_services:
        sys.exit(cmd_check_services())
    elif args.train:
        sys.exit(cmd_train())
    elif args.query:
        sys.exit(cmd_query(args.query))
    elif args.generate_article:
        sys.exit(cmd_generate_article(args.generate_article))
    elif args.list_articles:
        sys.exit(cmd_list_articles())
    elif args.get_article is not None:
        sys.exit(cmd_get_article(args.get_article))
    elif args.validate_sql:
        sys.exit(cmd_validate_sql(args.validate_sql))
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
