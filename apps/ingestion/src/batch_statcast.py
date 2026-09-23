"""全登録選手の Statcast データ一括取得・投入バッチモジュール"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional
from clickhouse_connect.driver.client import Client
import pandas as pd
import psycopg

from .downloader import download_statcast_csv
from .loader import insert_statcast_data
from .publisher import publish_statcast_raw_message

logger = logging.getLogger(__name__)


def extract_year_from_dates(
    start_date: Optional[str] = None, end_date: Optional[str] = None
) -> Optional[int]:
    """日付文字列から西暦年 (YYYY) を抽出する"""
    for d in (start_date, end_date):
        if d and len(d) >= 4 and d[:4].isdigit():
            return int(d[:4])
    return None


def get_registered_players(
    conn: psycopg.Connection, limit: Optional[int] = None
) -> list[dict[str, Any]]:
    """PostgreSQL の players テーブルから登録済み選手一覧を取得する

    Args:
        conn: PostgreSQL コネクション
        limit: 取得上限件数 (任意)

    Returns:
        選手情報の辞書リスト [{"player_id": int, "name_en": str}, ...]
    """
    sql = "SELECT player_id, name_en FROM players ORDER BY player_id"
    if limit is not None and limit > 0:
        sql += f" LIMIT {int(limit)}"

    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()

    return [{"player_id": r["player_id"], "name_en": r["name_en"]} for r in rows]


def ingest_player_statcast(
    ch_client: Client,
    player_id: int,
    player_name: str,
    player_type: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    enable_pubsub: bool = True,
) -> int:
    """単一選手の Statcast データをダウンロードし、ClickHouse へ投入する

    データが存在しない選手（打席のない投手、登板のない野手など）は安全に 0 件スキップします。
    データ登録成功時には、Cloud Pub/Sub へ集計トリガーメッセージを発行します。

    Returns:
        投入された行数
    """
    logger.info(
        "Downloading Statcast for player %s (%s, type=%s, start=%s, end=%s)...",
        player_id,
        player_name,
        player_type,
        start_date,
        end_date,
    )
    try:
        df = download_statcast_csv(
            start_date=start_date,
            end_date=end_date,
            player_id=player_id,
            player_type=player_type,
        )
    except Exception as e:
        logger.warning(
            "Failed or empty response for player %s (%s, type=%s): %s",
            player_id,
            player_name,
            player_type,
            e,
        )
        return 0

    if df is None or df.empty:
        logger.info(
            "No Statcast data found for player %s (%s, type=%s). Skipping.",
            player_id,
            player_name,
            player_type,
        )
        return 0

    inserted = insert_statcast_data(ch_client, df)
    logger.info(
        "Inserted %d rows for player %s (%s, type=%s).",
        inserted,
        player_id,
        player_name,
        player_type,
    )

    if inserted > 0 and enable_pubsub:
        year = extract_year_from_dates(start_date, end_date)
        publish_statcast_raw_message(
            player_id=player_id,
            year=year,
            player_type=player_type,
        )

    return inserted


def ingest_all_players_statcast(
    pg_conn: psycopg.Connection,
    ch_client: Client,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    player_type: str = "both",
    limit: Optional[int] = None,
    sleep_sec: float = 0.5,
    enable_pubsub: bool = True,
) -> dict[str, int]:
    """登録済み全選手を対象として Baseball Savant から Statcast データを取得・投入する

    Args:
        pg_conn: PostgreSQL コネクション
        ch_client: ClickHouse クライアント
        start_date: 取得開始日 (YYYY-MM-DD)
        end_date: 取得終了日 (YYYY-MM-DD)
        player_type: "pitcher", "batter", または "both" (デフォルト: "both")
        limit: 対象選手数の上限 (任意)
        sleep_sec: 各リクエスト間の待機秒数

    Returns:
        処理結果のサマリー {"total_players": int, "total_inserted": int}
    """
    players = get_registered_players(pg_conn, limit=limit)
    logger.info("Found %d players in PostgreSQL players table to ingest.", len(players))

    total_inserted = 0
    types_to_fetch = ["pitcher", "batter"] if player_type == "both" else [player_type]

    for idx, p in enumerate(players, 1):
        pid = p["player_id"]
        pname = p["name_en"]
        logger.info("[%d/%d] Processing player %s (ID: %s)...", idx, len(players), pname, pid)

        for ptype in types_to_fetch:
            rows = ingest_player_statcast(
                ch_client=ch_client,
                player_id=pid,
                player_name=pname,
                player_type=ptype,
                start_date=start_date,
                end_date=end_date,
                enable_pubsub=enable_pubsub,
            )
            total_inserted += rows
            if sleep_sec > 0:
                time.sleep(sleep_sec)

    logger.info(
        "Completed all Statcast ingestion. Total players: %d, Total inserted rows: %d",
        len(players),
        total_inserted,
    )
    return {"total_players": len(players), "total_inserted": total_inserted}
