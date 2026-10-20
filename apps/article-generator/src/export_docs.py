"""Export generated articles from PostgreSQL to static HTML files for GitHub Pages."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import html
import json
import logging
from pathlib import Path
import re
from typing import List, Optional

import markdown
from src.config import settings
from src.postgres_client import Article, PostgresClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))


def format_jst(dt: Optional[datetime]) -> str:
    """Format datetime to JST string."""
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    jst_dt = dt.astimezone(JST)
    return jst_dt.strftime("%Y-%m-%d %H:%M:%S JST")


def render_markdown(md_text: str) -> str:
    """Convert markdown text to HTML with tables, code fences, etc."""
    return markdown.markdown(
        md_text,
        extensions=[
            "markdown.extensions.tables",
            "markdown.extensions.fenced_code",
            "markdown.extensions.nl2br",
            "markdown.extensions.sane_lists",
        ],
    )


SHARED_CSS = """
:root {
  --bg: #f8fafc;
  --card-bg: #ffffff;
  --text-main: #1e293b;
  --text-muted: #64748b;
  --primary: #1e3a8a;
  --accent: #2563eb;
  --accent-hover: #1d4ed8;
  --border: #e2e8f0;
  --code-bg: #1e293b;
  --code-text: #f1f5f9;
  --tag-bg: #eff6ff;
  --tag-text: #2563eb;
  --table-stripe: #f8fafc;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Segoe UI', 'Helvetica Neue', 'Hiragino Sans', 'Noto Sans JP', sans-serif;
  background-color: var(--bg);
  color: var(--text-main);
  line-height: 1.7;
  padding: 32px 16px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.container {
  max-width: 960px;
  width: 100%;
  margin: 0 auto;
}

/* ナビゲーション・ヘッダー */
.nav-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
  font-size: 0.95rem;
}

.breadcrumbs {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
}

.breadcrumbs a {
  color: var(--accent);
  text-decoration: none;
  font-weight: 500;
}

.breadcrumbs a:hover {
  text-decoration: underline;
}

.badge {
  display: inline-block;
  background: var(--tag-bg);
  color: var(--tag-text);
  font-size: 0.8rem;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 9999px;
  border: 1px solid #bfdbfe;
}

.badge-outline {
  display: inline-block;
  background: #f1f5f9;
  color: #475569;
  font-size: 0.8rem;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 9999px;
  border: 1px solid var(--border);
}

/* ヒーローヘッダー */
header.hero {
  text-align: center;
  margin-bottom: 40px;
}

header.hero h1 {
  font-size: 2.2rem;
  color: var(--primary);
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 12px 0;
  line-height: 1.3;
}

header.hero p.subtitle {
  font-size: 1.05rem;
  color: var(--text-muted);
  max-width: 680px;
  margin: 0 auto;
}

/* カードスタイル */
.card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 28px;
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05);
  margin-bottom: 24px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card.hoverable:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.08), 0 4px 6px -4px rgb(0 0 0 / 0.04);
}

/* ボタン */
.btn {
  display: inline-block;
  text-align: center;
  background-color: var(--accent);
  color: #ffffff !important;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.95rem;
  padding: 10px 20px;
  border-radius: 8px;
  transition: background-color 0.2s ease;
}

.btn:hover {
  background-color: var(--accent-hover);
}

.btn-secondary {
  display: inline-block;
  text-align: center;
  background-color: #f1f5f9;
  color: #334155 !important;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.95rem;
  padding: 10px 20px;
  border-radius: 8px;
  border: 1px solid var(--border);
  transition: background-color 0.2s ease;
}

.btn-secondary:hover {
  background-color: #e2e8f0;
}

/* プロンプト・お題ブロック */
.prompt-box {
  background-color: #eff6ff;
  border-left: 4px solid var(--accent);
  border-radius: 0 8px 8px 0;
  padding: 14px 18px;
  margin: 16px 0;
  font-size: 0.95rem;
}

.prompt-label {
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 4px;
}

.prompt-text {
  font-style: italic;
  color: #1e293b;
}

/* アコーディオン・SQLブロック */
details.sql-accordion {
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 8px;
  margin: 16px 0;
  overflow: hidden;
}

details.sql-accordion summary {
  padding: 12px 16px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  color: #334155;
  user-select: none;
  background: #f1f5f9;
}

details.sql-accordion summary:hover {
  background: #e2e8f0;
}

.sql-content {
  padding: 16px;
  background: var(--code-bg);
  color: var(--code-text);
  font-family: Consolas, Monaco, 'Courier New', monospace;
  font-size: 0.85rem;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

/* 記事本文スタイル (Markdown レンダリング) */
.article-body {
  font-size: 1.05rem;
  line-height: 1.85;
  color: #334155;
}

.article-body h1 {
  font-size: 1.85rem;
  font-weight: 800;
  color: var(--primary);
  margin: 36px 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #bfdbfe;
}

.article-body h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--primary);
  margin: 32px 0 14px 0;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}

.article-body h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
  margin: 24px 0 10px 0;
}

.article-body p {
  margin: 14px 0;
}

.article-body ul, .article-body ol {
  margin: 14px 0;
  padding-left: 28px;
}

.article-body li {
  margin: 6px 0;
}

.article-body strong {
  color: #0f172a;
  font-weight: 700;
}

.article-body blockquote {
  border-left: 4px solid var(--accent);
  background: #f1f5f9;
  padding: 12px 18px;
  margin: 18px 0;
  color: #475569;
  border-radius: 0 8px 8px 0;
}

.article-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 24px 0;
  display: block;
  overflow-x: auto;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
  border-radius: 8px;
  border: 1px solid var(--border);
}

.article-body th, .article-body td {
  border: 1px solid var(--border);
  padding: 10px 16px;
  text-align: left;
  font-size: 0.95rem;
}

.article-body th {
  background-color: #f1f5f9;
  font-weight: 700;
  color: var(--primary);
  white-space: nowrap;
}

.article-body tr:nth-child(even) {
  background-color: var(--table-stripe);
}

.article-body tr:hover {
  background-color: #eff6ff;
}

.article-body code {
  background-color: #e2e8f0;
  color: #0f172a;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: Consolas, Monaco, monospace;
  font-size: 0.88em;
}

.article-body pre code {
  background: none;
  color: inherit;
  padding: 0;
}

.article-body pre {
  background: var(--code-bg);
  color: var(--code-text);
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 18px 0;
}

.article-body hr {
  border: none;
  border-top: 1px solid var(--border);
  margin: 36px 0;
}

/* ページネーション・フッター */
.article-nav {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-top: 40px;
  padding-top: 24px;
  border-top: 1px solid var(--border);
}

.article-nav a {
  text-decoration: none;
}

footer {
  text-align: center;
  font-size: 0.9rem;
  color: var(--text-muted);
  border-top: 1px solid var(--border);
  padding-top: 24px;
  margin-top: 48px;
  width: 100%;
}

footer a {
  color: var(--accent);
  text-decoration: none;
  font-weight: 600;
}

footer a:hover {
  text-decoration: underline;
}

@media (max-width: 640px) {
  header.hero h1 {
    font-size: 1.6rem;
  }
  .article-body h1 {
    font-size: 1.5rem;
  }
  .article-body h2 {
    font-size: 1.3rem;
  }
  .card {
    padding: 18px;
  }
}
"""


def generate_article_html(article: Article, prev_id: Optional[int], next_id: Optional[int]) -> str:
    """Generate individual article HTML string."""
    title_escaped = html.escape(article.title)
    prompt_escaped = html.escape(article.prompt)
    model_escaped = html.escape(article.model_name)
    created_str = format_jst(article.created_at)

    body_html = render_markdown(article.content_markdown)

    sql_section = ""
    if article.generated_sql:
        sql_escaped = html.escape(article.generated_sql.strip())
        sql_section = f"""
        <details class="sql-accordion">
          <summary>🔍 実行された Text-to-SQL クエリを確認する</summary>
          <pre class="sql-content"><code>{sql_escaped}</code></pre>
        </details>
        """

    prev_link = (
        f'<a href="{prev_id}.html" class="btn-secondary">← 前の記事 (#{prev_id})</a>'
        if prev_id
        else '<span style="visibility:hidden;"></span>'
    )
    next_link = (
        f'<a href="{next_id}.html" class="btn-secondary">次の記事 (#{next_id}) →</a>'
        if next_id
        else '<span style="visibility:hidden;"></span>'
    )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_escaped} | MLB Statcast Agent</title>
  <meta name="description" content="{prompt_escaped[:160]}">
  <style>{SHARED_CSS}</style>
</head>
<body>

  <div class="container">
    <nav class="nav-bar">
      <div class="breadcrumbs">
        <a href="../index.html">トップ</a>
        <span>&gt;</span>
        <a href="index.html">記事一覧</a>
        <span>&gt;</span>
        <span>Article #{article.id}</span>
      </div>
      <div style="display: flex; gap: 8px;">
        <span class="badge">Article #{article.id}</span>
        <span class="badge-outline">{model_escaped}</span>
      </div>
    </nav>

    <div class="card" style="border-top: 5px solid var(--accent);">
      <h1 style="color: var(--primary); font-size: 1.85rem; font-weight: 800; line-height: 1.4; margin-bottom: 12px;">{title_escaped}</h1>
      
      <div style="display: flex; align-items: center; gap: 16px; font-size: 0.9rem; color: var(--text-muted); margin-bottom: 16px; flex-wrap: wrap;">
        <span>📅 作成日時: {created_str}</span>
        <span>🤖 生成モデル: {model_escaped}</span>
      </div>

      <div class="prompt-box">
        <div class="prompt-label">企画プロンプト / ユーザーの指示</div>
        <div class="prompt-text">「{prompt_escaped}」</div>
      </div>

      {sql_section}
    </div>

    <main class="card">
      <article class="article-body">
        {body_html}
      </article>

      <div class="article-nav">
        <div>{prev_link}</div>
        <div style="text-align: center;">
          <a href="index.html" class="btn-secondary">記事一覧へ戻る</a>
        </div>
        <div>{next_link}</div>
      </div>
    </main>

    <footer>
      <p>
        <a href="../index.html">スライド資料ポータルへ</a> | 
        <a href="index.html">生成記事一覧</a> | 
        GitHub: <a href="https://github.com/walk8243/langgraph-statcast-agent" target="_blank" rel="noopener noreferrer">walk8243/langgraph-statcast-agent</a>
      </p>
    </footer>
  </div>

</body>
</html>
"""


def generate_index_html(articles: List[Article]) -> str:
    """Generate articles index HTML string."""
    cards_html = []
    for art in articles:
        title_escaped = html.escape(art.title)
        prompt_escaped = html.escape(art.prompt)
        model_escaped = html.escape(art.model_name)
        created_str = format_jst(art.created_at)

        cards_html.append(f"""
      <div class="card hoverable">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px;">
          <div style="display: flex; gap: 8px;">
            <span class="badge">Article #{art.id}</span>
            <span class="badge-outline">{model_escaped}</span>
          </div>
          <span style="font-size: 0.85rem; color: var(--text-muted);">📅 {created_str}</span>
        </div>

        <h2 style="font-size: 1.35rem; color: var(--primary); font-weight: 700; margin-bottom: 10px; line-height: 1.4;">
          <a href="{art.id}.html" style="color: inherit; text-decoration: none;">{title_escaped}</a>
        </h2>

        <p style="font-size: 0.92rem; color: #475569; margin-bottom: 16px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
          <strong>お題:</strong> {prompt_escaped}
        </p>

        <div style="display: flex; justify-content: flex-end;">
          <a href="{art.id}.html" class="btn">記事を読む →</a>
        </div>
      </div>
        """)

    articles_list_str = "\n".join(cards_html)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MLB データ分析・解説レポート一覧 | Statcast Agent</title>
  <meta name="description" content="Statcast 投球・打球データから Text-to-SQL と Gemini LLM により自動生成された MLB 解説レポート一覧です。">
  <style>{SHARED_CSS}</style>
</head>
<body>

  <div class="container">
    <nav class="nav-bar">
      <div class="breadcrumbs">
        <a href="../index.html">トップ</a>
        <span>&gt;</span>
        <span>記事一覧</span>
      </div>
      <div>
        <a href="../index.html" class="btn-secondary" style="padding: 6px 14px; font-size: 0.85rem;">スライド資料へ</a>
      </div>
    </nav>

    <header class="hero">
      <div class="badge">MLB Statcast Agent</div>
      <h1>Text-to-SQL 自動生成解説記事</h1>
      <p class="subtitle">自然言語のテーマ指示から、ClickHouse（Statcast投球・打球生データ）を自動集計し、Gemini LLM により多段オーケストレーション執筆された全 {len(articles)} 件の分析記事一覧です。</p>
    </header>

    <div style="display: flex; flex-direction: column; gap: 8px;">
      {articles_list_str}
    </div>

    <footer>
      <p>
        <a href="../index.html">スライド資料ポータルへ</a> | 
        GitHub: <a href="https://github.com/walk8243/langgraph-statcast-agent" target="_blank" rel="noopener noreferrer">walk8243/langgraph-statcast-agent</a>
      </p>
    </footer>
  </div>

</body>
</html>
"""


# デフォルトでGitHub Pagesに公開する記事IDリスト（指定がない場合はこのリストの記事のみエクスポート）
DEFAULT_PUBLISHED_ARTICLE_IDS: List[int] = [11]


def export_articles(
    output_dir: Path,
    article_ids: Optional[List[int]] = None,
    export_all: bool = False,
) -> None:
    """Fetch articles from PostgreSQL and generate HTML files in output_dir.

    Args:
        output_dir: Target directory for docs/articles
        article_ids: Specific article IDs to export. If None and not export_all, DEFAULT_PUBLISHED_ARTICLE_IDS is used.
        export_all: If True, export all articles in the database.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown_dir = output_dir / "markdown"
    markdown_dir.mkdir(parents=True, exist_ok=True)

    client = PostgresClient()
    logger.info("Connecting to PostgreSQL to fetch articles...")
    all_articles = client.list_articles(limit=500, offset=0)
    logger.info(f"Retrieved {len(all_articles)} total articles from database.")

    if not all_articles:
        logger.warning("No articles found in PostgreSQL.")
        return

    # フィルタリング
    target_ids = None
    if not export_all:
        target_ids = set(article_ids if article_ids is not None else DEFAULT_PUBLISHED_ARTICLE_IDS)
        filtered_articles = [a for a in all_articles if a.id in target_ids]
    else:
        filtered_articles = all_articles

    if not filtered_articles:
        logger.warning(f"No articles matched the filter (target IDs: {target_ids}).")
        return

    logger.info(
        f"Exporting {len(filtered_articles)} article(s): {[a.id for a in filtered_articles]}"
    )

    # 既存の出力ディレクトリ内の古いHTML/MDファイルをクリーンアップ（index.htmlは後で上書き）
    for old_file in output_dir.glob("*.html"):
        if old_file.name != "index.html":
            old_file.unlink(missing_ok=True)
    for old_md in markdown_dir.glob("*.md"):
        old_md.unlink(missing_ok=True)

    # Sort by ID asc for proper previous/next chaining
    articles_asc = sorted(filtered_articles, key=lambda a: a.id if a.id else 0)

    # Generate individual article pages
    for i, art in enumerate(articles_asc):
        prev_id = articles_asc[i - 1].id if i > 0 else None
        next_id = articles_asc[i + 1].id if i < len(articles_asc) - 1 else None

        html_content = generate_article_html(art, prev_id, next_id)
        file_path = output_dir / f"{art.id}.html"
        file_path.write_text(html_content, encoding="utf-8")

        # Also save raw markdown for reference
        md_file_path = markdown_dir / f"{art.id}.md"
        md_file_path.write_text(art.content_markdown, encoding="utf-8")
        logger.info(f"Generated {file_path.name}")

    # Generate index page (ordered by created_at DESC, i.e., latest first)
    articles_desc = sorted(
        filtered_articles,
        key=lambda a: a.created_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    index_html = generate_index_html(articles_desc)
    index_path = output_dir / "index.html"
    index_path.write_text(index_html, encoding="utf-8")
    logger.info(f"Generated index: {index_path.name}")

    logger.info("Export completed successfully!")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export articles to docs/articles")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "docs" / "articles",
        help="Target directory for output files (default: docs/articles)",
    )
    parser.add_argument(
        "--article-ids",
        type=int,
        nargs="+",
        default=None,
        help="Specific article IDs to export (e.g. --article-ids 11). Defaults to DEFAULT_PUBLISHED_ARTICLE_IDS [11].",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Export all articles from database (overrides default published list)",
    )
    args = parser.parse_args()

    export_articles(args.output_dir, article_ids=args.article_ids, export_all=args.all)


if __name__ == "__main__":
    main()

