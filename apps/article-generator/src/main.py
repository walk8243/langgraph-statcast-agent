"""CLI entrypoint for article-generator Text-to-SQL service."""

from __future__ import annotations

import argparse
import logging
import sys

from src.article_service import ArticleService
from src.clickhouse_client import ClickHouseClient
from src.config import settings
from src.multi_article_service import MultiArticleService
from src.multi_article_synthesizer import (
    ArticleOutline,
    ArticleOutlineSection,
    DataRequirement,
)
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


def cmd_example_multi_config() -> int:
    """Print an example multi-material article configuration JSON."""
    example = {
        "title": "2026年 鈴木誠也・村上宗隆・岡本和真 打撃特性徹底比較",
        "theme": "MLBで競い合う日本屈指のスラッガー3名の打撃特性・パワーの質・速球適応度を詳細スタッツから多角的に分析・比較する。",
        "sections": [
            {
                "title": "シーズン基本成績と総合生産性",
                "description": "打率、本塁打、打点、OPS、wOBAなどの主要指標の比較",
                "material_label": "素材①: 総合生産性",
            },
            {
                "title": "打球品質とパワーの真価（Barrel% & HardHit%）",
                "description": "平均打球速度、最高速度、バレル率、ハードヒット率の差異",
                "material_label": "素材②: 打球質",
            },
        ],
        "requirements": [
            {
                "label": "素材①: 総合生産性",
                "prompt": "2026年の鈴木誠也、村上宗隆、岡本和真のPA, AVG, HR, RBI, OPS, wOBA, BB%, K%を集計",
                "section_hint": "シーズン基本成績と総合生産性",
            },
            {
                "label": "素材②: 打球質",
                "prompt": "2026年の鈴木誠也、村上宗隆、岡本和真の平均打球速度, 最高打球速度, HardHit%, Barrel%を集計",
                "section_hint": "打球品質とパワーの真価",
            },
        ],
    }
    import json

    print(json.dumps(example, ensure_ascii=False, indent=2))
    return 0


def cmd_generate_multi_article(config_path_or_json: str) -> int:
    """Generate comprehensive multi-material article from config JSON and save to PostgreSQL."""
    import json
    import os

    try:
        if os.path.exists(config_path_or_json):
            with open(config_path_or_json, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = json.loads(config_path_or_json)
    except Exception as e:
        print(f"Failed to parse config file/JSON: {e}")
        return 1

    title = data.get("title", "Statcast 総合分析レポート")
    theme = data.get("theme", "")
    sections_raw = data.get("sections", [])
    requirements_raw = data.get("requirements", [])

    if not requirements_raw:
        print("Error: 'requirements' array is required in multi-article configuration.")
        return 1

    sections = [
        ArticleOutlineSection(
            title=s.get("title", ""),
            description=s.get("description", ""),
            material_label=s.get("material_label"),
        )
        for s in sections_raw
    ]
    outline = ArticleOutline(title=title, theme=theme, sections=sections)

    requirements = [
        DataRequirement(
            label=r.get("label", f"素材 {idx + 1}"),
            prompt=r.get("prompt", ""),
            section_hint=r.get("section_hint"),
        )
        for idx, r in enumerate(requirements_raw)
    ]

    print(f"\nStarting Multi-Material Article Generation: '{outline.title}'")
    print(f"Theme: {outline.theme}")
    print(f"Materials to collect: {len(requirements)}")
    print("=" * 60)

    service = MultiArticleService()
    try:
        article = service.generate_and_save_multi_article(outline, requirements)
    except Exception as e:
        print(f"\nMulti-material article generation failed: {e}")
        return 1

    print(f"\n[Success] Multi-Material Article Saved with ID: {article.id}")
    print(f"Title: {article.title}")
    print(f"Model: {article.model_name}")
    print("\nGenerated SQLs:")
    print("-" * 60)
    print(article.generated_sql)
    print("-" * 60)
    print("\nExecution Summary:")
    print(article.execution_summary)
    print("\nArticle Markdown Preview:")
    print("=" * 60)
    print(article.content_markdown)
    print("=" * 60)
    return 0


def cmd_desk_interactive() -> int:
    """Run interactive terminal session with Editorial Desk Agent to brainstorm and generate article."""
    from src.orchestration_pipeline import OrchestrationPipeline

    print("\n" + "=" * 65)
    print("MLB Statcast AI 編集デスク（企画立案・取材壁打ちエージェント）")
    print("=" * 65)
    print("編集デスクAIと対話して、記事のテーマ、切り口、取材データ項目を決めましょう。")
    print("終了したいときは 'exit' または 'quit' と入力してください。\n")

    pipeline = OrchestrationPipeline()
    messages: list[dict[str, str]] = []

    while True:
        try:
            user_input = input("\n[あなた (ライター)] > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nセッションを終了します。")
            break

        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit", "q"]:
            print("セッションを終了します。")
            break

        messages.append({"role": "user", "content": user_input})
        print("\n[編集デスクが思考・企画案を策定中...]")

        try:
            response, article = pipeline.process_chat_and_run(messages)
        except Exception as e:
            print(f"\nエラーが発生しました: {e}")
            continue

        messages.append({"role": "assistant", "content": response.reply})

        print(f"\n[編集デスク] >\n{response.reply}")

        if response.proposal:
            print("\n" + "-" * 50)
            print(f"【企画案ドラフト】: {response.proposal.title}")
            print(f"主旨: {response.proposal.theme}")
            print("章構成:")
            for idx, sec in enumerate(response.proposal.sections, 1):
                mat_str = f" (参照: {sec.material_label})" if sec.material_label else ""
                print(f"  {idx}. {sec.title}{mat_str} - {sec.description}")
            print("取材データ要求リスト:")
            for idx, req in enumerate(response.proposal.requirements, 1):
                print(f"  [{req.label}]: {req.prompt}")
            print("-" * 50)

        if article:
            print("\n" + "=" * 65)
            print(f"[成功] 総合解説記事が生成・保存されました！ (ID: {article.id})")
            print(f"タイトル: {article.title}")
            print(f"モデル: {article.model_name}")
            print("=" * 65)
            preview = article.content_markdown[:600] + ("..." if len(article.content_markdown) > 600 else "")
            print(f"\nプレビュー:\n{preview}")
            print("\n" + "=" * 65)
            print("記事一覧は `python -m src.main --list-articles` で確認できます。")
            break

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
        "--generate-multi-article",
        type=str,
        help="Generate multi-material analytical article from JSON configuration file or string",
    )
    parser.add_argument(
        "--example-multi-config",
        action="store_true",
        help="Print an example JSON configuration for multi-material article generation",
    )
    parser.add_argument(
        "--desk-interactive",
        action="store_true",
        help="Start interactive conversational session with Editorial Desk Agent to plan and write article",
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
    elif args.generate_multi_article:
        sys.exit(cmd_generate_multi_article(args.generate_multi_article))
    elif args.example_multi_config:
        sys.exit(cmd_example_multi_config())
    elif args.desk_interactive:
        sys.exit(cmd_desk_interactive())
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
