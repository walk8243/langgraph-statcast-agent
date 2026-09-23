"""ClickHouse からの打者指標集計モジュール"""

from __future__ import annotations

import os
from typing import Optional
import clickhouse_connect
from clickhouse_connect.driver.client import Client

from src.aggregator import (
    BatterRawCounts,
    BatterStatcastRawCounts,
    PitcherPitchTypeRawCounts,
    PitcherStatcastRawCounts,
)


def get_clickhouse_client(
    host: Optional[str] = None,
    port: Optional[int] = None,
    database: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> Client:
    """ClickHouse クライアントを取得する"""
    return clickhouse_connect.get_client(
        host=host or os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(port or os.getenv("CLICKHOUSE_HTTP_PORT", 8123)),
        database=database or os.getenv("CLICKHOUSE_DB", "statcast"),
        username=username or os.getenv("CLICKHOUSE_USER", "statcast"),
        password=password or os.getenv("CLICKHOUSE_PASSWORD", "statcast_pass"),
    )


def fetch_batter_raw_counts(
    client: Client,
    player_id: int,
    year: Optional[int] = None,
    table: str = "statcast.statcast_raw",
) -> list[BatterRawCounts]:
    """ClickHouse から指定打者のシーズン別基本指標カウントを取得する"""
    params: dict[str, object] = {"player_id": player_id}
    year_filter = ""
    if year is not None:
        year_filter = "AND (game_year = %(year)s OR (game_year IS NULL AND toYear(game_date) = %(year)s))"
        params["year"] = year

    query = f"""
    SELECT
        batter AS player_id,
        coalesce(game_year, toYear(game_date)) AS year,
        count(DISTINCT game_pk) AS games,
        countIf(events IS NOT NULL AND events != '') AS plate_appearances,
        countIf(
            events NOT IN (
                'walk', 'intent_walk', 'hit_by_pitch',
                'sac_bunt', 'sac_bunt_double_play',
                'sac_fly', 'sac_fly_double_play',
                'catcher_interf'
            ) AND events IS NOT NULL AND events != ''
        ) AS at_bats,
        countIf(events IN ('single', 'double', 'triple', 'home_run')) AS hits,
        countIf(events = 'double') AS doubles,
        countIf(events = 'triple') AS triples,
        countIf(events = 'home_run') AS home_runs,
        countIf(events = 'single') * 1 +
            countIf(events = 'double') * 2 +
            countIf(events = 'triple') * 3 +
            countIf(events = 'home_run') * 4 AS total_bases,
        countIf(events IN ('strikeout', 'strikeout_looking')) AS strikeouts,
        countIf(events IN ('walk', 'intent_walk')) AS walks,
        countIf(events = 'hit_by_pitch') AS hit_by_pitch,
        countIf(events IN ('sac_bunt', 'sac_bunt_double_play')) AS sac_bunts,
        countIf(events IN ('sac_fly', 'sac_fly_double_play')) AS sac_flies,
        countIf(events = 'grounded_into_double_play') AS grounded_into_double_play
    FROM {table} FINAL
    WHERE batter = %(player_id)s
      {year_filter}
    GROUP BY batter, year
    ORDER BY year ASC
    """

    result = client.query(query, parameters=params)
    rows = result.named_results()

    counts_list: list[BatterRawCounts] = []
    for row in rows:
        counts_list.append(BatterRawCounts(**row))

    return counts_list


def fetch_batter_statcast_raw_counts(
    client: Client,
    player_id: int,
    year: Optional[int] = None,
    table: str = "statcast.statcast_raw",
) -> list[BatterStatcastRawCounts]:
    """ClickHouse から指定打者の Statcast 打球指標生カウントを取得する"""
    params: dict[str, object] = {"player_id": player_id}
    year_filter = ""
    if year is not None:
        year_filter = "AND (game_year = %(year)s OR (game_year IS NULL AND toYear(game_date) = %(year)s))"
        params["year"] = year

    query = f"""
    SELECT
        batter AS player_id,
        coalesce(game_year, toYear(game_date)) AS year,
        count() AS pitches_seen,
        countIf(launch_speed IS NOT NULL) AS batted_balls,
        countIf(launch_speed_angle = 6) AS barrels,
        countIf(launch_speed >= 95.0) AS hard_hit_count,
        coalesce(sumIf(launch_speed, launch_speed IS NOT NULL), 0.0) AS sum_exit_velocity,
        coalesce(maxIf(launch_speed, launch_speed IS NOT NULL), 0.0) AS max_exit_velocity,
        coalesce(sumIf(launch_angle, launch_speed IS NOT NULL), 0.0) AS sum_launch_angle,
        countIf(launch_speed IS NOT NULL AND launch_angle >= 8.0 AND launch_angle <= 32.0) AS sweet_spot_count
    FROM {table} FINAL
    WHERE batter = %(player_id)s
      {year_filter}
    GROUP BY batter, year
    ORDER BY year ASC
    """

    result = client.query(query, parameters=params)
    rows = result.named_results()

    return [BatterStatcastRawCounts(**row) for row in rows]


def fetch_pitcher_statcast_raw_counts(
    client: Client,
    player_id: int,
    year: Optional[int] = None,
    table: str = "statcast.statcast_raw",
) -> list[PitcherStatcastRawCounts]:
    """ClickHouse から指定投手の Statcast 総合指標生カウントを取得する"""
    params: dict[str, object] = {"player_id": player_id}
    year_filter = ""
    if year is not None:
        year_filter = "AND (game_year = %(year)s OR (game_year IS NULL AND toYear(game_date) = %(year)s))"
        params["year"] = year

    query = f"""
    SELECT
        pitcher AS player_id,
        coalesce(game_year, toYear(game_date)) AS year,
        count() AS total_pitches,
        countIf(launch_speed IS NOT NULL) AS batted_balls,
        countIf(launch_speed_angle = 6) AS barrels_allowed,
        countIf(launch_speed >= 95.0) AS hard_hit_count,
        coalesce(sumIf(launch_speed, launch_speed IS NOT NULL), 0.0) AS sum_exit_velocity,
        countIf(description IN ('swinging_strike', 'swinging_strike_blocked', 'foul', 'foul_tip', 'foul_bunt', 'hit_into_play', 'missed_bunt')) AS swings,
        countIf(description IN ('swinging_strike', 'swinging_strike_blocked', 'missed_bunt')) AS whiffs,
        countIf(description = 'called_strike') AS called_strikes
    FROM {table} FINAL
    WHERE pitcher = %(player_id)s
      {year_filter}
    GROUP BY pitcher, year
    ORDER BY year ASC
    """

    result = client.query(query, parameters=params)
    rows = result.named_results()

    return [PitcherStatcastRawCounts(**row) for row in rows]


def fetch_pitcher_pitch_type_raw_counts(
    client: Client,
    player_id: int,
    year: Optional[int] = None,
    table: str = "statcast.statcast_raw",
) -> list[PitcherPitchTypeRawCounts]:
    """ClickHouse から指定投手の球種別 Statcast 生カウントを取得する"""
    params: dict[str, object] = {"player_id": player_id}
    year_filter = ""
    if year is not None:
        year_filter = "AND (game_year = %(year)s OR (game_year IS NULL AND toYear(game_date) = %(year)s))"
        params["year"] = year

    query = f"""
    SELECT
        pitcher AS player_id,
        coalesce(game_year, toYear(game_date)) AS year,
        pitch_type,
        coalesce(any(pitch_name), '') AS pitch_name,
        count() AS pitches,
        sum(count()) OVER (PARTITION BY coalesce(game_year, toYear(game_date))) AS total_pitches,
        coalesce(sumIf(release_speed, release_speed IS NOT NULL), 0.0) AS sum_speed,
        countIf(release_speed IS NOT NULL) AS speed_count,
        coalesce(sumIf(release_spin_rate, release_spin_rate IS NOT NULL), 0.0) AS sum_spin_rate,
        countIf(release_spin_rate IS NOT NULL) AS spin_count,
        coalesce(sumIf(pfx_x, pfx_x IS NOT NULL AND pfx_z IS NOT NULL), 0.0) AS sum_pfx_x,
        coalesce(sumIf(pfx_z, pfx_x IS NOT NULL AND pfx_z IS NOT NULL), 0.0) AS sum_pfx_z,
        countIf(pfx_x IS NOT NULL AND pfx_z IS NOT NULL) AS movement_count,
        countIf(description IN ('swinging_strike', 'swinging_strike_blocked', 'foul', 'foul_tip', 'foul_bunt', 'hit_into_play', 'missed_bunt')) AS swings,
        countIf(description IN ('swinging_strike', 'swinging_strike_blocked', 'missed_bunt')) AS whiffs
    FROM {table} FINAL
    WHERE pitcher = %(player_id)s
      AND pitch_type IS NOT NULL
      AND pitch_type != ''
      {year_filter}
    GROUP BY pitcher, year, pitch_type
    ORDER BY year ASC, pitches DESC
    """

    result = client.query(query, parameters=params)
    rows = result.named_results()

    return [PitcherPitchTypeRawCounts(**row) for row in rows]

