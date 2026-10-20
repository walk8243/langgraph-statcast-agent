"""Unit tests for export_docs module."""

from datetime import datetime, timezone

from src.export_docs import (
    DEFAULT_PUBLISHED_ARTICLE_IDS,
    format_jst,
    generate_article_html,
    get_article_filename,
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


def test_get_article_filename():
    assert get_article_filename(11) == "11_japanese-sluggers-comparison-2026.html"
    assert get_article_filename(999) == "999_article.html"


def test_generate_article_html():
    art = Article(
        id=11,
        title="Test Article Title",
        prompt="Test Prompt",
        content_markdown="## Heading\n\nContent paragraph",
        model_name="gemini-3.5-flash-lite",
        generated_sql="SELECT 1;",
        created_at=datetime(2026, 10, 19, 14, 0, 0, tzinfo=timezone.utc),
    )
    html_output = generate_article_html(art)
    assert "Test Article Title" in html_output
    assert "Test Prompt" in html_output
    assert "SELECT 1;" in html_output
    assert "gemini-3.5-flash-lite" in html_output
    assert "ポータルへ戻る" in html_output


def test_default_published_article_ids():
    assert 11 in DEFAULT_PUBLISHED_ARTICLE_IDS
    assert len(DEFAULT_PUBLISHED_ARTICLE_IDS) == 1
