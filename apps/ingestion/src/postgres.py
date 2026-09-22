"""PostgreSQL 接続および初期化ユーティリティモジュール (Ingestion)"""

from __future__ import annotations

import os
from typing import Optional
import psycopg
from psycopg.rows import dict_row


def get_postgres_connection(
    host: Optional[str] = None,
    port: Optional[int] = None,
    dbname: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
) -> psycopg.Connection:
    """PostgreSQL 接続を取得する"""
    return psycopg.connect(
        host=host or os.getenv("POSTGRES_HOST", "localhost"),
        port=int(port or os.getenv("POSTGRES_PORT", 5432)),
        dbname=dbname or os.getenv("POSTGRES_DB", "statcast"),
        user=user or os.getenv("POSTGRES_USER", "statcast"),
        password=password or os.getenv("POSTGRES_PASSWORD", "statcast_pass"),
        row_factory=dict_row,
    )


DEFAULT_INIT_DDL = """
CREATE TABLE IF NOT EXISTS teams (
    team_id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    abbreviation VARCHAR(10) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS players (
    player_id BIGINT PRIMARY KEY,
    name_en VARCHAR(255) NOT NULL,
    name_ja VARCHAR(255),
    team_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE players ADD COLUMN IF NOT EXISTS team_id BIGINT;
CREATE INDEX IF NOT EXISTS idx_players_team_id ON players (team_id);

CREATE TABLE IF NOT EXISTS games (
    game_pk BIGINT PRIMARY KEY,
    game_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
    season INT NOT NULL,
    game_type VARCHAR(10),
    status VARCHAR(50),
    home_team_id BIGINT,
    away_team_id BIGINT,
    home_score INT,
    away_score INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_games_game_date_time ON games (game_date_time);
CREATE INDEX IF NOT EXISTS idx_games_season ON games (season);
CREATE INDEX IF NOT EXISTS idx_games_home_team_id ON games (home_team_id);
CREATE INDEX IF NOT EXISTS idx_games_away_team_id ON games (away_team_id);
"""


def initialize_tables(conn: psycopg.Connection, ddl_path: Optional[str] = None) -> None:
    """初期化 DDL を実行して PostgreSQL テーブルを作成する"""
    if not ddl_path:
        ddl_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "docker", "postgres", "init.sql"
        )
        ddl_path = os.path.abspath(ddl_path)

    if os.path.exists(ddl_path):
        with open(ddl_path, encoding="utf-8") as f:
            sql = f.read()
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS team_id BIGINT;")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_players_team_id ON players (team_id);")
        conn.commit()
    else:
        # コンテナ環境などでファイルがマウントされていない場合のフォールバック
        with conn.cursor() as cur:
            cur.execute(DEFAULT_INIT_DDL)
        conn.commit()
