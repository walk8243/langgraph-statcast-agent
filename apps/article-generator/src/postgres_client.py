"""PostgreSQL client and repository for articles persistence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional

import psycopg
from psycopg.rows import dict_row

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class Article:
    """Represents a generated analytical article."""

    title: str
    prompt: str
    content_markdown: str
    model_name: str
    generated_sql: Optional[str] = None
    execution_summary: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PostgresClient:
    """Client for PostgreSQL operations on articles."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        dbname: Optional[str] = None,
    ):
        self.host = host or settings.postgres_host
        self.port = port or settings.postgres_port
        self.user = user or settings.postgres_user
        self.password = password or settings.postgres_password
        self.dbname = dbname or settings.postgres_db

    def get_connection(self) -> psycopg.Connection:
        """Create and return a new PostgreSQL connection."""
        return psycopg.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            dbname=self.dbname,
            row_factory=dict_row,
        )

    def ensure_table_exists(self) -> None:
        """Ensure the articles table exists in PostgreSQL."""
        query = """
        CREATE TABLE IF NOT EXISTS articles (
            id BIGSERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            prompt TEXT NOT NULL,
            generated_sql TEXT,
            execution_summary TEXT,
            content_markdown TEXT NOT NULL,
            model_name VARCHAR(100) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles (created_at DESC);
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
            conn.commit()

    def save_article(self, article: Article) -> int:
        """Save a new article to PostgreSQL and return its generated ID."""
        self.ensure_table_exists()
        query = """
        INSERT INTO articles (
            title, prompt, generated_sql, execution_summary,
            content_markdown, model_name, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        RETURNING id;
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (
                        article.title,
                        article.prompt,
                        article.generated_sql,
                        article.execution_summary,
                        article.content_markdown,
                        article.model_name,
                    ),
                )
                row = cur.fetchone()
                conn.commit()
                if row and "id" in row:
                    article.id = row["id"]
                    return row["id"]
                raise RuntimeError("Failed to retrieve generated article ID")

    def get_article(self, article_id: int) -> Optional[Article]:
        """Fetch an article by its primary key ID."""
        self.ensure_table_exists()
        query = """
        SELECT id, title, prompt, generated_sql, execution_summary,
               content_markdown, model_name, created_at, updated_at
        FROM articles
        WHERE id = %s;
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (article_id,))
                row = cur.fetchone()
                if not row:
                    return None
                return Article(
                    id=row["id"],
                    title=row["title"],
                    prompt=row["prompt"],
                    generated_sql=row["generated_sql"],
                    execution_summary=row["execution_summary"],
                    content_markdown=row["content_markdown"],
                    model_name=row["model_name"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )

    def list_articles(self, limit: int = 20, offset: int = 0) -> List[Article]:
        """Fetch recent articles ordered by created_at DESC."""
        self.ensure_table_exists()
        query = """
        SELECT id, title, prompt, generated_sql, execution_summary,
               content_markdown, model_name, created_at, updated_at
        FROM articles
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s;
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (limit, offset))
                rows = cur.fetchall()
                return [
                    Article(
                        id=row["id"],
                        title=row["title"],
                        prompt=row["prompt"],
                        generated_sql=row["generated_sql"],
                        execution_summary=row["execution_summary"],
                        content_markdown=row["content_markdown"],
                        model_name=row["model_name"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )
                    for row in rows
                ]
