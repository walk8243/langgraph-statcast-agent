"""Unit tests for export_docs module."""

from datetime import datetime, timezone
from pathlib import Path
import tempfile

from src.export_docs import (
    export_articles,
    format_jst,
    generate_article_html,
    generate_index_html,
    render_markdown,
)
from src.postgres_client import Article


def test_format_jst():
    dt_utc = datetime(2026, 10, 19, 14, 30, 0, tzinfo=timezone.utc)
    res = format_jst(dt_utc)
    assert res == "2026-10-19 23:30:00 JST"


def test_render_markdown():
    md = "# Title\n\n| Col1 | Col2 |\n| --- | --- |\n| Val1 | Val2 |"
    rendered = render_markdown(md)
    assert "<h1>Title</h1>" in rendered
    assert "<table>" in rendered
    assert "Val1" in rendered


def test_generate_article_html():
    art = Article(
        id=1,
        title="Test Article Title",
        prompt="Test Prompt",
        content_markdown="## Heading\n\nContent paragraph",
        model_name="gemini-3.5-flash-lite",
        generated_sql="SELECT 1;",
        created_at=datetime(2026, 10, 19, 14, 0, 0, tzinfo=timezone.utc),
    )
    html_output = generate_article_html(art, prev_id=None, next_id=2)
    assert "Test Article Title" in html_output
    assert "Test Prompt" in html_output
    assert "SELECT 1;" in html_output
    assert "gemini-3.5-flash-lite" in html_output
    assert "2.html" in html_output


def test_generate_index_html():
    articles = [
        Article(
            id=1,
            title="Article 1",
            prompt="Prompt 1",
            content_markdown="Body 1",
            model_name="gemini-3.5-flash-lite",
            created_at=datetime(2026, 10, 19, 14, 0, 0, tzinfo=timezone.utc),
        ),
        Article(
            id=2,
            title="Article 2",
            prompt="Prompt 2",
            content_markdown="Body 2",
            model_name="gemini-3.5-flash-lite",
            created_at=datetime(2026, 10, 20, 14, 0, 0, tzinfo=timezone.utc),
        ),
    ]
    index_html = generate_index_html(articles)
    assert "Article 1" in index_html
    assert "Article 2" in index_html
    assert "1.html" in index_html
    assert "2.html" in index_html


def test_default_published_article_ids():
    from src.export_docs import DEFAULT_PUBLISHED_ARTICLE_IDS
    assert 11 in DEFAULT_PUBLISHED_ARTICLE_IDS
    assert len(DEFAULT_PUBLISHED_ARTICLE_IDS) >= 1

