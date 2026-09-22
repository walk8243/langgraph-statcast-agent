"""MLB Stats API からの選手情報取得および ClickHouse / PostgreSQL への登録モジュール"""

from __future__ import annotations

import logging
from typing import Any, Optional
import clickhouse_connect
from clickhouse_connect.driver.client import Client
import psycopg
import requests

logger = logging.getLogger(__name__)

MLB_STATS_API_BASE_URL = "https://statsapi.mlb.com"

DEFAULT_CLICKHOUSE_PLAYERS_DDL = """
CREATE TABLE IF NOT EXISTS statcast.players (
    player_id UInt64,
    full_name String,
    first_name String,
    last_name String,
    last_first_name String,
    primary_number Nullable(String),
    current_team_id Nullable(UInt32),
    primary_position_code Nullable(String),
    primary_position_name Nullable(String),
    primary_position_type Nullable(String),
    primary_position_abbreviation LowCardinality(Nullable(String)),
    bat_side LowCardinality(Nullable(String)),
    pitch_hand LowCardinality(Nullable(String)),
    active UInt8 DEFAULT 1,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (player_id);
"""


def fetch_mlb_players(
    season: int = 2024,
    sport_id: int = 1,
    base_url: str = MLB_STATS_API_BASE_URL,
    timeout: int = 30,
) -> list[dict[str, Any]]:
    """MLB Stats API から指定したシーズンの選手一覧を取得する

    Args:
        season: 対象シーズン (デフォルト: 2024)
        sport_id: 競技区分ID (デフォルト: 1 = MLB)
        base_url: APIベースURL
        timeout: タイムアウト秒数

    Returns:
        選手情報の辞書リスト (全属性)
    """
    url = f"{base_url}/api/v1/sports/{sport_id}/players"
    params: dict[str, Any] = {"season": season}

    logger.info("Fetching players from %s with params %s", url, params)
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()

    data = resp.json()
    people_raw = data.get("people", [])
    logger.info("Fetched %d players from MLB Stats API", len(people_raw))

    parsed_players: list[dict[str, Any]] = []
    for p in people_raw:
        current_team = p.get("currentTeam") or {}
        pos = p.get("primaryPosition") or {}
        bat_side = p.get("batSide") or {}
        pitch_hand = p.get("pitchHand") or {}

        last_first = p.get("lastFirstName")
        if not last_first:
            first = p.get("firstName", "")
            last = p.get("lastName", "")
            last_first = f"{last}, {first}".strip(" ,")

        parsed = {
            "player_id": p.get("id"),
            "full_name": p.get("fullName") or "",
            "first_name": p.get("firstName") or "",
            "last_name": p.get("lastName") or "",
            "last_first_name": last_first,
            "primary_number": p.get("primaryNumber"),
            "current_team_id": current_team.get("id"),
            "primary_position_code": pos.get("code"),
            "primary_position_name": pos.get("name"),
            "primary_position_type": pos.get("type"),
            "primary_position_abbreviation": pos.get("abbreviation"),
            "bat_side": bat_side.get("code"),
            "pitch_hand": pitch_hand.get("code"),
            "active": 1 if p.get("active", True) else 0,
        }
        parsed_players.append(parsed)

    return parsed_players


def initialize_clickhouse_players_table(client: Client) -> None:
    """ClickHouse の statcast.players テーブルを初期化する"""
    client.command(DEFAULT_CLICKHOUSE_PLAYERS_DDL)


def insert_players_to_clickhouse(client: Client, players: list[dict[str, Any]]) -> int:
    """選手全情報を ClickHouse (列指向DB) の statcast.players テーブルへ投入する

    Args:
        client: ClickHouse クライアント
        players: 選手情報の辞書リスト (全属性)

    Returns:
        登録された選手件数
    """
    if not players:
        return 0

    initialize_clickhouse_players_table(client)

    column_names = [
        "player_id",
        "full_name",
        "first_name",
        "last_name",
        "last_first_name",
        "primary_number",
        "current_team_id",
        "primary_position_code",
        "primary_position_name",
        "primary_position_type",
        "primary_position_abbreviation",
        "bat_side",
        "pitch_hand",
        "active",
    ]

    rows = []
    for p in players:
        row = [
            p.get("player_id"),
            p.get("full_name") or "",
            p.get("first_name") or "",
            p.get("last_name") or "",
            p.get("last_first_name") or "",
            p.get("primary_number"),
            p.get("current_team_id"),
            p.get("primary_position_code"),
            p.get("primary_position_name"),
            p.get("primary_position_type"),
            p.get("primary_position_abbreviation"),
            p.get("bat_side"),
            p.get("pitch_hand"),
            p.get("active", 1),
        ]
        rows.append(row)

    client.insert(
        table="players",
        data=rows,
        column_names=column_names,
        database="statcast",
    )
    logger.info("Inserted %d players into ClickHouse statcast.players table", len(rows))
    return len(rows)


def upsert_players_to_postgres(
    conn: psycopg.Connection, players: list[dict[str, Any]]
) -> int:
    """選手の基本情報（ID・英名）を PostgreSQL (RDB) の players テーブルへ Upsert する
    ※ 既存の name_ja (日本語名) は上書きせず保持します。

    Args:
        conn: PostgreSQL コネクション
        players: 選手情報の辞書リスト

    Returns:
        登録・更新された選手件数
    """
    if not players:
        return 0

    sql = """
    INSERT INTO players (
        player_id, name_en, updated_at
    ) VALUES (
        %(player_id)s, %(name_en)s, CURRENT_TIMESTAMP
    )
    ON CONFLICT (player_id) DO UPDATE SET
        name_en = EXCLUDED.name_en,
        updated_at = CURRENT_TIMESTAMP;
    """

    data = [
        {
            "player_id": p.get("player_id"),
            "name_en": p.get("last_first_name") or p.get("full_name"),
        }
        for p in players
    ]

    with conn.cursor() as cur:
        cur.executemany(sql, data)
    conn.commit()

    logger.info("Upserted %d players into PostgreSQL players table", len(data))
    return len(data)
