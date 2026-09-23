"""PostgreSQL への打者基本指標保存モジュール"""

from __future__ import annotations

import os
from typing import Optional
import psycopg
from psycopg.rows import dict_row

from src.aggregator import (
    BatterSeasonStats,
    BatterStatcastStats,
    PitcherPitchTypeStats,
    PitcherStatcastStats,
)


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
        updated_at = CURRENT_TIMESTAMP;
    """

    with conn.cursor() as cur:
        cur.execute(query, stats.model_dump())
    conn.commit()


def upsert_batter_statcast_stats(
    conn: psycopg.Connection, stats: BatterStatcastStats
) -> None:
    """打者の Statcast 詳細指標を PostgreSQL に保存・更新（Upsert）する"""
    query = """
    INSERT INTO batter_statcast_stats (
        player_id,
        year,
        pitches_seen,
        batted_balls,
        barrels,
        barrel_pct,
        hard_hit_count,
        hard_hit_pct,
        avg_exit_velocity,
        max_exit_velocity,
        avg_launch_angle,
        sweet_spot_pct,
        updated_at
    ) VALUES (
        %(player_id)s,
        %(year)s,
        %(pitches_seen)s,
        %(batted_balls)s,
        %(barrels)s,
        %(barrel_pct)s,
        %(hard_hit_count)s,
        %(hard_hit_pct)s,
        %(avg_exit_velocity)s,
        %(max_exit_velocity)s,
        %(avg_launch_angle)s,
        %(sweet_spot_pct)s,
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (player_id, year) DO UPDATE SET
        pitches_seen = EXCLUDED.pitches_seen,
        batted_balls = EXCLUDED.batted_balls,
        barrels = EXCLUDED.barrels,
        barrel_pct = EXCLUDED.barrel_pct,
        hard_hit_count = EXCLUDED.hard_hit_count,
        hard_hit_pct = EXCLUDED.hard_hit_pct,
        avg_exit_velocity = EXCLUDED.avg_exit_velocity,
        max_exit_velocity = EXCLUDED.max_exit_velocity,
        avg_launch_angle = EXCLUDED.avg_launch_angle,
        sweet_spot_pct = EXCLUDED.sweet_spot_pct,
        updated_at = CURRENT_TIMESTAMP;
    """

    with conn.cursor() as cur:
        cur.execute(query, stats.model_dump())
    conn.commit()


def upsert_pitcher_statcast_stats(
    conn: psycopg.Connection, stats: PitcherStatcastStats
) -> None:
    """投手の Statcast 総合指標を PostgreSQL に保存・更新（Upsert）する"""
    query = """
    INSERT INTO pitcher_statcast_stats (
        player_id,
        year,
        total_pitches,
        batted_balls,
        barrels_allowed,
        barrel_pct,
        hard_hit_count,
        hard_hit_pct,
        avg_exit_velocity,
        swings,
        whiffs,
        whiff_pct,
        called_strikes,
        csw_pct,
        updated_at
    ) VALUES (
        %(player_id)s,
        %(year)s,
        %(total_pitches)s,
        %(batted_balls)s,
        %(barrels_allowed)s,
        %(barrel_pct)s,
        %(hard_hit_count)s,
        %(hard_hit_pct)s,
        %(avg_exit_velocity)s,
        %(swings)s,
        %(whiffs)s,
        %(whiff_pct)s,
        %(called_strikes)s,
        %(csw_pct)s,
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (player_id, year) DO UPDATE SET
        total_pitches = EXCLUDED.total_pitches,
        batted_balls = EXCLUDED.batted_balls,
        barrels_allowed = EXCLUDED.barrels_allowed,
        barrel_pct = EXCLUDED.barrel_pct,
        hard_hit_count = EXCLUDED.hard_hit_count,
        hard_hit_pct = EXCLUDED.hard_hit_pct,
        avg_exit_velocity = EXCLUDED.avg_exit_velocity,
        swings = EXCLUDED.swings,
        whiffs = EXCLUDED.whiffs,
        whiff_pct = EXCLUDED.whiff_pct,
        called_strikes = EXCLUDED.called_strikes,
        csw_pct = EXCLUDED.csw_pct,
        updated_at = CURRENT_TIMESTAMP;
    """

    with conn.cursor() as cur:
        cur.execute(query, stats.model_dump())
    conn.commit()


def upsert_pitcher_pitch_type_stats(
    conn: psycopg.Connection, stats: PitcherPitchTypeStats
) -> None:
    """投手の球種別 Statcast 指標を PostgreSQL に保存・更新（Upsert）する"""
    query = """
    INSERT INTO pitcher_pitch_type_stats (
        player_id,
        year,
        pitch_type,
        pitch_name,
        pitches,
        usage_pct,
        avg_speed,
        avg_spin_rate,
        avg_pfx_x,
        avg_pfx_z,
        swings,
        whiffs,
        whiff_pct,
        updated_at
    ) VALUES (
        %(player_id)s,
        %(year)s,
        %(pitch_type)s,
        %(pitch_name)s,
        %(pitches)s,
        %(usage_pct)s,
        %(avg_speed)s,
        %(avg_spin_rate)s,
        %(avg_pfx_x)s,
        %(avg_pfx_z)s,
        %(swings)s,
        %(whiffs)s,
        %(whiff_pct)s,
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (player_id, year, pitch_type) DO UPDATE SET
        pitch_name = EXCLUDED.pitch_name,
        pitches = EXCLUDED.pitches,
        usage_pct = EXCLUDED.usage_pct,
        avg_speed = EXCLUDED.avg_speed,
        avg_spin_rate = EXCLUDED.avg_spin_rate,
        avg_pfx_x = EXCLUDED.avg_pfx_x,
        avg_pfx_z = EXCLUDED.avg_pfx_z,
        swings = EXCLUDED.swings,
        whiffs = EXCLUDED.whiffs,
        whiff_pct = EXCLUDED.whiff_pct,
        updated_at = CURRENT_TIMESTAMP;
    """

    with conn.cursor() as cur:
        cur.execute(query, stats.model_dump())
    conn.commit()

