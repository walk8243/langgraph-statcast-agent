"""PostgreSQL への打者基本指標保存モジュール"""

from __future__ import annotations

import os
from typing import Optional
import psycopg
from psycopg.rows import dict_row

from src.aggregator import BatterSeasonStats


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
        conn.commit()



def upsert_batter_season_stats(
    conn: psycopg.Connection, stats: BatterSeasonStats
) -> None:
    """打者のシーズン基本指標を PostgreSQL に保存・更新（Upsert）する"""
    query = """
    INSERT INTO batter_season_stats (
        player_id,
        year,
        games,
        plate_appearances,
        at_bats,
        hits,
        doubles,
        triples,
        home_runs,
        total_bases,
        strikeouts,
        walks,
        hit_by_pitch,
        sac_bunts,
        sac_flies,
        grounded_into_double_play,
        batting_average,
        on_base_percentage,
        slugging_percentage,
        ops,
        risp_plate_appearances,
        risp_at_bats,
        risp_hits,
        risp_batting_average,
        updated_at
    ) VALUES (
        %(player_id)s,
        %(year)s,
        %(games)s,
        %(plate_appearances)s,
        %(at_bats)s,
        %(hits)s,
        %(doubles)s,
        %(triples)s,
        %(home_runs)s,
        %(total_bases)s,
        %(strikeouts)s,
        %(walks)s,
        %(hit_by_pitch)s,
        %(sac_bunts)s,
        %(sac_flies)s,
        %(grounded_into_double_play)s,
        %(batting_average)s,
        %(on_base_percentage)s,
        %(slugging_percentage)s,
        %(ops)s,
        %(risp_plate_appearances)s,
        %(risp_at_bats)s,
        %(risp_hits)s,
        %(risp_batting_average)s,
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (player_id, year) DO UPDATE SET
        games = EXCLUDED.games,
        plate_appearances = EXCLUDED.plate_appearances,
        at_bats = EXCLUDED.at_bats,
        hits = EXCLUDED.hits,
        doubles = EXCLUDED.doubles,
        triples = EXCLUDED.triples,
        home_runs = EXCLUDED.home_runs,
        total_bases = EXCLUDED.total_bases,
        strikeouts = EXCLUDED.strikeouts,
        walks = EXCLUDED.walks,
        hit_by_pitch = EXCLUDED.hit_by_pitch,
        sac_bunts = EXCLUDED.sac_bunts,
        sac_flies = EXCLUDED.sac_flies,
        grounded_into_double_play = EXCLUDED.grounded_into_double_play,
        batting_average = EXCLUDED.batting_average,
        on_base_percentage = EXCLUDED.on_base_percentage,
        slugging_percentage = EXCLUDED.slugging_percentage,
        ops = EXCLUDED.ops,
        risp_plate_appearances = EXCLUDED.risp_plate_appearances,
        risp_at_bats = EXCLUDED.risp_at_bats,
        risp_hits = EXCLUDED.risp_hits,
        risp_batting_average = EXCLUDED.risp_batting_average,
        updated_at = CURRENT_TIMESTAMP;
    """

    with conn.cursor() as cur:
        cur.execute(query, stats.model_dump())
    conn.commit()
