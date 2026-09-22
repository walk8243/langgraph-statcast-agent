"""MLB Stats API からのチーム情報取得および PostgreSQL への登録モジュール"""

from __future__ import annotations

import logging
from typing import Any, Optional
import psycopg
import requests

logger = logging.getLogger(__name__)

MLB_STATS_API_BASE_URL = "https://statsapi.mlb.com"


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
        チーム情報の辞書リスト
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


def upsert_teams(conn: psycopg.Connection, teams: list[dict[str, Any]]) -> int:
    """チーム情報を PostgreSQL の teams テーブルへ Upsert する

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
        team_id, name, abbreviation, team_name, location_name,
        league_id, league_name, division_id, division_name,
        venue_id, venue_name, active, updated_at
    ) VALUES (
        %(team_id)s, %(name)s, %(abbreviation)s, %(team_name)s, %(location_name)s,
        %(league_id)s, %(league_name)s, %(division_id)s, %(division_name)s,
        %(venue_id)s, %(venue_name)s, %(active)s, CURRENT_TIMESTAMP
    )
    ON CONFLICT (team_id) DO UPDATE SET
        name = EXCLUDED.name,
        abbreviation = EXCLUDED.abbreviation,
        team_name = EXCLUDED.team_name,
        location_name = EXCLUDED.location_name,
        league_id = EXCLUDED.league_id,
        league_name = EXCLUDED.league_name,
        division_id = EXCLUDED.division_id,
        division_name = EXCLUDED.division_name,
        venue_id = EXCLUDED.venue_id,
        venue_name = EXCLUDED.venue_name,
        active = EXCLUDED.active,
        updated_at = CURRENT_TIMESTAMP;
    """

    with conn.cursor() as cur:
        cur.executemany(sql, teams)
    conn.commit()

    logger.info("Upserted %d teams into teams table", len(teams))
    return len(teams)
