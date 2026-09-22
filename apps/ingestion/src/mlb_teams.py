"""MLB Stats API からのチーム情報取得および ClickHouse / PostgreSQL への登録モジュール"""

from __future__ import annotations

import logging
from typing import Any, Optional
import clickhouse_connect
from clickhouse_connect.driver.client import Client
import psycopg
import requests

logger = logging.getLogger(__name__)

MLB_STATS_API_BASE_URL = "https://statsapi.mlb.com"

DEFAULT_CLICKHOUSE_TEAMS_DDL = """
CREATE TABLE IF NOT EXISTS statcast.teams (
    team_id UInt32,
    name String,
    abbreviation LowCardinality(String),
    team_name String,
    location_name String,
    league_id Nullable(UInt32),
    league_name Nullable(String),
    division_id Nullable(UInt32),
    division_name Nullable(String),
    venue_id Nullable(UInt32),
    venue_name Nullable(String),
    active UInt8 DEFAULT 1,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (team_id);
"""


def fetch_mlb_teams(
    sport_id: int = 1,
    season: Optional[int] = None,
    base_url: str = MLB_STATS_API_BASE_URL,
    timeout: int = 30,
) -> list[dict[str, Any]]:
    """MLB Stats API から指定した sportId のチーム一覧を取得する

    Args:
        sport_id: 競技区分ID (デフォルト: 1 = MLB)
        season: 対象シーズン (任意)
        base_url: APIベースURL
        timeout: タイムアウト秒数

    Returns:
        チーム情報の辞書リスト (全属性)
    """
    url = f"{base_url}/api/v1/teams"
    params: dict[str, Any] = {"sportId": sport_id}
    if season:
        params["season"] = season

    logger.info("Fetching teams from %s with params %s", url, params)
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()

    data = resp.json()
    teams_raw = data.get("teams", [])
    logger.info("Fetched %d teams from MLB Stats API", len(teams_raw))

    parsed_teams: list[dict[str, Any]] = []
    for t in teams_raw:
        league = t.get("league") or {}
        division = t.get("division") or {}
        venue = t.get("venue") or {}

        parsed = {
            "team_id": t.get("id"),
            "name": t.get("name"),
            "abbreviation": t.get("abbreviation") or t.get("fileCode", "").upper(),
            "team_name": t.get("teamName"),
            "location_name": t.get("locationName"),
            "league_id": league.get("id"),
            "league_name": league.get("name"),
            "division_id": division.get("id"),
            "division_name": division.get("name"),
            "venue_id": venue.get("id"),
            "venue_name": venue.get("name"),
            "active": t.get("active", True),
        }
        parsed_teams.append(parsed)

    return parsed_teams


def initialize_clickhouse_teams_table(client: Client) -> None:
    """ClickHouse の statcast.teams テーブルを初期化する"""
    client.command(DEFAULT_CLICKHOUSE_TEAMS_DDL)


def insert_teams_to_clickhouse(client: Client, teams: list[dict[str, Any]]) -> int:
    """チーム全情報を ClickHouse (列指向DB) の statcast.teams テーブルへ投入する

    Args:
        client: ClickHouse クライアント
        teams: チーム情報の辞書リスト (全属性)

    Returns:
        登録されたチーム件数
    """
    if not teams:
        return 0

    initialize_clickhouse_teams_table(client)

    column_names = [
        "team_id",
        "name",
        "abbreviation",
        "team_name",
        "location_name",
        "league_id",
        "league_name",
        "division_id",
        "division_name",
        "venue_id",
        "venue_name",
        "active",
    ]

    rows = []
    for t in teams:
        row = [
            t.get("team_id"),
            t.get("name") or "",
            t.get("abbreviation") or "",
            t.get("team_name") or "",
            t.get("location_name") or "",
            t.get("league_id"),
            t.get("league_name"),
            t.get("division_id"),
            t.get("division_name"),
            t.get("venue_id"),
            t.get("venue_name"),
            1 if t.get("active", True) else 0,
        ]
        rows.append(row)

    client.insert(
        table="teams",
        data=rows,
        column_names=column_names,
        database="statcast",
    )
    logger.info("Inserted %d teams into ClickHouse statcast.teams table", len(rows))
    return len(rows)


def upsert_teams_to_postgres(conn: psycopg.Connection, teams: list[dict[str, Any]]) -> int:
    """チームの主要情報（結合キー・画面表示用）を PostgreSQL (RDB) の teams テーブルへ Upsert する

    Args:
        conn: PostgreSQL コネクション
        teams: チーム情報の辞書リスト

    Returns:
        登録・更新されたチーム件数
    """
    if not teams:
        return 0

    sql = """
    INSERT INTO teams (
        team_id, name, abbreviation, updated_at
    ) VALUES (
        %(team_id)s, %(name)s, %(abbreviation)s, CURRENT_TIMESTAMP
    )
    ON CONFLICT (team_id) DO UPDATE SET
        name = EXCLUDED.name,
        abbreviation = EXCLUDED.abbreviation,
        updated_at = CURRENT_TIMESTAMP;
    """

    with conn.cursor() as cur:
        cur.executemany(sql, teams)
    conn.commit()

    logger.info("Upserted %d teams into PostgreSQL teams table", len(teams))
    return len(teams)
