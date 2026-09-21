"""Aggregation Service CLI エントリポイント"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional
from dotenv import load_dotenv

from src.aggregator import calculate_batter_stats
from src.clickhouse import fetch_batter_raw_counts, get_clickhouse_client
from src.postgres import (
    get_postgres_connection,
    initialize_tables,
    upsert_batter_season_stats,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aggregation")


def aggregate_batter(
    player_id: int,
    year: Optional[int] = None,
    init_db: bool = False,
) -> int:
    """指定した打者の基本指標を集計し、PostgreSQL へ登録する"""
    ch_client = get_clickhouse_client()
    pg_conn = get_postgres_connection()

    if init_db:
        logger.info("PostgreSQL テーブルの初期化を実行中...")
        initialize_tables(pg_conn)
        logger.info("PostgreSQL テーブル初期化完了")

    logger.info(
        f"ClickHouse から打者基本指標を集計中 (player_id={player_id}, year={year or 'all'})..."
    )
    raw_counts_list = fetch_batter_raw_counts(ch_client, player_id=player_id, year=year)

    if not raw_counts_list:
        logger.warning(
            f"対象打者 (player_id={player_id}, year={year}) のデータが見つかりませんでした。"
        )
        return 0

    saved_count = 0
    for raw in raw_counts_list:
        stats = calculate_batter_stats(raw)
        logger.info(
            f"集計完了: [Year: {stats.year}] G: {stats.games}, PA: {stats.plate_appearances}, "
            f"AB: {stats.at_bats}, H: {stats.hits}, 2B: {stats.doubles}, 3B: {stats.triples}, "
            f"HR: {stats.home_runs}, TB: {stats.total_bases}, SO: {stats.strikeouts}, "
            f"BB: {stats.walks}, HBP: {stats.hit_by_pitch}, SH: {stats.sac_bunts}, "
            f"SF: {stats.sac_flies}, GIDP: {stats.grounded_into_double_play}, "
            f"AVG: {stats.batting_average:.3f}, OBP: {stats.on_base_percentage:.3f}, "
            f"SLG: {stats.slugging_percentage:.3f}, OPS: {stats.ops:.3f}"
        )
        upsert_batter_season_stats(pg_conn, stats)
        saved_count += 1

    logger.info(
        f"PostgreSQL への登録完了: {saved_count} 件のシーズン指標を Upsert しました。"
    )
    return saved_count


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    """コマンドライン引数をパースする"""
    parser = argparse.ArgumentParser(
        description="Statcast 打者基本指標集計サービス (ClickHouse -> PostgreSQL)"
    )
    parser.add_argument(
        "--player-id",
        type=int,
        required=True,
        help="集計対象の選手ID (batter ID, 例: 673548)",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="集計対象のシーズン年 (例: 2024)。指定しない場合は全年度",
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="実行前に PostgreSQL テーブルの初期化 DDL を実行する",
    )
    return parser.parse_args(args)


def main() -> None:
    """メイン関数"""
    load_dotenv()
    parsed = parse_args()
    try:
        aggregate_batter(
            player_id=parsed.player_id,
            year=parsed.year,
            init_db=parsed.init_db,
        )
    except Exception as e:
        logger.error(f"集計処理中にエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
