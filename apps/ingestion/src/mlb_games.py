"""MLB Stats API からの試合日程・結果取得および ClickHouse / PostgreSQL への登録モジュール"""

from datetime import date, datetime
import logging
from typing import Any, Optional
from clickhouse_connect.driver.client import Client
import psycopg
import requests

logger = logging.getLogger(__name__)

MLB_STATS_API_BASE_URL = "https://statsapi.mlb.com"

DEFAULT_CLICKHOUSE_GAMES_DDL = """
CREATE TABLE IF NOT EXISTS statcast.games (
    `game_pk` UInt64,
    `game_date` Date,
    `game_date_time` Nullable(DateTime),
    `season` UInt16,
    `game_type` LowCardinality(String),
    `status` LowCardinality(String),
    `status_code` LowCardinality(Nullable(String)),
    `home_team_id` UInt32,
    `home_team_name` String,
    `away_team_id` UInt32,
    `away_team_name` String,
    `home_score` Nullable(UInt16),
    `away_score` Nullable(UInt16),
    `is_winner_home` Nullable(UInt8),
    `is_winner_away` Nullable(UInt8),
    `venue_id` Nullable(UInt32),
    `venue_name` Nullable(String),
    `created_at` DateTime DEFAULT now(),
    `updated_at` DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (season, game_date, game_pk);
"""


def fetch_mlb_schedule(
    season: int = 2024,
    sport_id: int = 1,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    base_url: str = MLB_STATS_API_BASE_URL,
    timeout: int = 30,
) -> list[dict[str, Any]]:
    """MLB Stats API から指定シーズンの試合日程・結果一覧を取得する

    Args:
        season: 対象シーズン (デフォルト: 2024)
        sport_id: 競技区分ID (デフォルト: 1 = MLB)
        start_date: 開始日 (YYYY-MM-DD, 任意)
        end_date: 終了日 (YYYY-MM-DD, 任意)
        base_url: APIベースURL
        timeout: タイムアウト秒数

    Returns:
        試合情報の辞書リスト
    """
    url = f"{base_url}/api/v1/schedule"
    params: dict[str, Any] = {
        "sportId": sport_id,
        "season": season,
    }
    if start_date:
        params["startDate"] = start_date
    if end_date:
        params["endDate"] = end_date

    logger.info("Fetching schedule from %s with params %s", url, params)
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()

    data = resp.json()
    dates_raw = data.get("dates", [])
    logger.info("Fetched %d dates from MLB Stats API", len(dates_raw))

    parsed_games: list[dict[str, Any]] = []
    for d in dates_raw:
        for g in d.get("games", []):
            teams = g.get("teams") or {}
            home = teams.get("home") or {}
            away = teams.get("away") or {}
            home_team = home.get("team") or {}
            away_team = away.get("team") or {}
            status = g.get("status") or {}
            venue = g.get("venue") or {}

            # 日時パース
            game_date_str = g.get("officialDate") or (
                g.get("gameDate")[:10] if g.get("gameDate") else None
            )
            game_date = None
            if game_date_str:
                try:
                    game_date = date.fromisoformat(game_date_str)
                except ValueError:
                    pass

            raw_dt = g.get("gameDate")
            game_date_time = None
            if raw_dt:
                try:
                    # ISO 8601 (2024-02-22T20:10:00Z)
                    game_date_time = datetime.fromisoformat(raw_dt.replace("Z", "+00:00"))
                except ValueError:
                    pass

            is_winner_home = None
            if "isWinner" in home:
                is_winner_home = 1 if home["isWinner"] else 0

            is_winner_away = None
            if "isWinner" in away:
                is_winner_away = 1 if away["isWinner"] else 0

            game_season = g.get("season")
            parsed = {
                "game_pk": g.get("gamePk"),
                "game_date": game_date,
                "game_date_time": game_date_time,
                "season": int(game_season) if game_season else season,
                "game_type": g.get("gameType") or "",
                "status": status.get("detailedState") or "",
                "status_code": status.get("statusCode"),
                "home_team_id": home_team.get("id"),
                "home_team_name": home_team.get("name") or "",
                "away_team_id": away_team.get("id"),
                "away_team_name": away_team.get("name") or "",
                "home_score": home.get("score"),
                "away_score": away.get("score"),
                "is_winner_home": is_winner_home,
                "is_winner_away": is_winner_away,
                "venue_id": venue.get("id"),
                "venue_name": venue.get("name"),
            }
            parsed_games.append(parsed)

    logger.info("Parsed %d games from schedule data", len(parsed_games))
    return parsed_games


def initialize_clickhouse_games_table(client: Client) -> None:
    """ClickHouse の statcast.games テーブルを初期化する"""
    client.command(DEFAULT_CLICKHOUSE_GAMES_DDL)


def insert_games_to_clickhouse(client: Client, games: list[dict[str, Any]]) -> int:
    """試合全情報を ClickHouse (列指向DB) の statcast.games テーブルへ投入する

    Args:
        client: ClickHouse クライアント
        games: 試合情報の辞書リスト

    Returns:
        登録された試合件数
    """
    if not games:
        return 0

    initialize_clickhouse_games_table(client)

    column_names = [
        "game_pk",
        "game_date",
        "game_date_time",
        "season",
        "game_type",
        "status",
        "status_code",
        "home_team_id",
        "home_team_name",
        "away_team_id",
        "away_team_name",
        "home_score",
        "away_score",
        "is_winner_home",
        "is_winner_away",
        "venue_id",
        "venue_name",
    ]

    rows = []
    for g in games:
        row = [
            g.get("game_pk"),
            g.get("game_date"),
            g.get("game_date_time"),
            g.get("season"),
            g.get("game_type") or "",
            g.get("status") or "",
            g.get("status_code"),
            g.get("home_team_id"),
            g.get("home_team_name") or "",
            g.get("away_team_id"),
            g.get("away_team_name") or "",
            g.get("home_score"),
            g.get("away_score"),
            g.get("is_winner_home"),
            g.get("is_winner_away"),
            g.get("venue_id"),
            g.get("venue_name"),
        ]
        rows.append(row)

    client.insert(
        table="games",
        data=rows,
        column_names=column_names,
        database="statcast",
    )
    logger.info("Inserted %d games into ClickHouse statcast.games table", len(rows))
    return len(rows)


def upsert_games_to_postgres(
    conn: psycopg.Connection, games: list[dict[str, Any]]
) -> int:
    """試合の基本情報を PostgreSQL (RDB) の games テーブルへ Upsert する

    Args:
        conn: PostgreSQL コネクション
        games: 試合情報の辞書リスト

    Returns:
        登録・更新された試合件数
    """
    if not games:
        return 0

    sql = """
    INSERT INTO games (
        game_pk, game_date_time, season, game_type, status,
        home_team_id, away_team_id, home_score, away_score,
        updated_at
    ) VALUES (
        %(game_pk)s, %(game_date_time)s, %(season)s, %(game_type)s, %(status)s,
        %(home_team_id)s, %(away_team_id)s, %(home_score)s, %(away_score)s,
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (game_pk) DO UPDATE SET
        game_date_time = EXCLUDED.game_date_time,
        season = EXCLUDED.season,
        game_type = EXCLUDED.game_type,
        status = EXCLUDED.status,
        home_team_id = EXCLUDED.home_team_id,
        away_team_id = EXCLUDED.away_team_id,
        home_score = EXCLUDED.home_score,
        away_score = EXCLUDED.away_score,
        updated_at = CURRENT_TIMESTAMP;
    """

    data = []
    for g in games:
        dt = g.get("game_date_time")
        if dt is None and g.get("game_date") is not None:
            dt = datetime.combine(g["game_date"], datetime.min.time())
        data.append({
            "game_pk": g.get("game_pk"),
            "game_date_time": dt,
            "season": g.get("season"),
            "game_type": g.get("game_type") or "",
            "status": g.get("status") or "",
            "home_team_id": g.get("home_team_id"),
            "away_team_id": g.get("away_team_id"),
            "home_score": g.get("home_score"),
            "away_score": g.get("away_score"),
        })

    with conn.cursor() as cur:
        cur.executemany(sql, data)
    conn.commit()

    logger.info("Upserted %d games into PostgreSQL games table", len(data))
    return len(data)
