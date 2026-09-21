"""ClickHouse からの打者指標集計モジュール"""

from __future__ import annotations

import os
from typing import Optional
import clickhouse_connect
from clickhouse_connect.driver.client import Client

from src.aggregator import BatterRawCounts


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
        countIf(events = 'grounded_into_double_play') AS grounded_into_double_play,
        countIf(
            ((on_2b IS NOT NULL AND on_2b > 0) OR (on_3b IS NOT NULL AND on_3b > 0))
            AND events IS NOT NULL AND events != ''
        ) AS risp_plate_appearances,
        countIf(
            ((on_2b IS NOT NULL AND on_2b > 0) OR (on_3b IS NOT NULL AND on_3b > 0))
            AND events NOT IN (
                'walk', 'intent_walk', 'hit_by_pitch',
                'sac_bunt', 'sac_bunt_double_play',
                'sac_fly', 'sac_fly_double_play',
                'catcher_interf'
            ) AND events IS NOT NULL AND events != ''
        ) AS risp_at_bats,
        countIf(
            ((on_2b IS NOT NULL AND on_2b > 0) OR (on_3b IS NOT NULL AND on_3b > 0))
            AND events IN ('single', 'double', 'triple', 'home_run')
        ) AS risp_hits
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
