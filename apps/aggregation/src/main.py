"""Aggregation Service CLI エントリポイント"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional
from dotenv import load_dotenv

from src.aggregator import (
    calculate_batter_statcast_stats,
    calculate_batter_stats,
    calculate_pitcher_pitch_type_stats,
    calculate_pitcher_statcast_stats,
)
from src.clickhouse import (
    fetch_batter_raw_counts,
    fetch_batter_statcast_raw_counts,
    fetch_pitcher_pitch_type_raw_counts,
    fetch_pitcher_statcast_raw_counts,
    get_clickhouse_client,
)
from src.postgres import (
    get_postgres_connection,
    initialize_tables,
    upsert_batter_season_stats,
    upsert_batter_statcast_stats,
    upsert_pitcher_pitch_type_stats,
    upsert_pitcher_statcast_stats,
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


def aggregate_batter_statcast(
    player_id: int,
    year: Optional[int] = None,
    init_db: bool = False,
) -> int:
    """指定した打者の Statcast 詳細指標を集計し、PostgreSQL へ登録する"""
    ch_client = get_clickhouse_client()
    pg_conn = get_postgres_connection()

    if init_db:
        logger.info("PostgreSQL テーブルの初期化を実行中...")
        initialize_tables(pg_conn)
        logger.info("PostgreSQL テーブル初期化完了")

    logger.info(
        f"ClickHouse から打者 Statcast 指標を集計中 (player_id={player_id}, year={year or 'all'})..."
    )
    raw_counts_list = fetch_batter_statcast_raw_counts(ch_client, player_id=player_id, year=year)

    if not raw_counts_list:
        logger.warning(
            f"対象打者 (player_id={player_id}, year={year}) の Statcast データが見つかりませんでした。"
        )
        return 0

    saved_count = 0
    for raw in raw_counts_list:
        stats = calculate_batter_statcast_stats(raw)
        logger.info(
            f"打者 Statcast 集計完了: [Year: {stats.year}] 投球数: {stats.pitches_seen}, "
            f"打球数: {stats.batted_balls}, Barrel: {stats.barrels} ({stats.barrel_pct:.1f}%), "
            f"HardHit: {stats.hard_hit_count} ({stats.hard_hit_pct:.1f}%), "
            f"平均打球初速: {stats.avg_exit_velocity:.1f} mph (最大: {stats.max_exit_velocity:.1f} mph), "
            f"平均打球角度: {stats.avg_launch_angle:.1f}°, SweetSpot: {stats.sweet_spot_pct:.1f}%"
        )
        upsert_batter_statcast_stats(pg_conn, stats)
        saved_count += 1

    logger.info(
        f"PostgreSQL への登録完了: {saved_count} 件の打者 Statcast 指標を Upsert しました。"
    )
    return saved_count


def aggregate_pitcher_statcast(
    player_id: int,
    year: Optional[int] = None,
    init_db: bool = False,
) -> tuple[int, int]:
    """指定した投手の Statcast 指標（総合および球種別）を集計し、PostgreSQL へ登録する"""
    ch_client = get_clickhouse_client()
    pg_conn = get_postgres_connection()

    if init_db:
        logger.info("PostgreSQL テーブルの初期化を実行中...")
        initialize_tables(pg_conn)
        logger.info("PostgreSQL テーブル初期化完了")

    logger.info(
        f"ClickHouse から投手 Statcast 指標を集計中 (player_id={player_id}, year={year or 'all'})..."
    )
    overall_raw_list = fetch_pitcher_statcast_raw_counts(ch_client, player_id=player_id, year=year)
    pitch_type_raw_list = fetch_pitcher_pitch_type_raw_counts(ch_client, player_id=player_id, year=year)

    if not overall_raw_list and not pitch_type_raw_list:
        logger.warning(
            f"対象投手 (player_id={player_id}, year={year}) の Statcast データが見つかりませんでした。"
        )
        return 0, 0

    saved_overall = 0
    for raw in overall_raw_list:
        stats = calculate_pitcher_statcast_stats(raw)
        logger.info(
            f"投手 Statcast 総合集計完了: [Year: {stats.year}] 投球数: {stats.total_pitches}, "
            f"被打球数: {stats.batted_balls}, 被Barrel: {stats.barrels_allowed} ({stats.barrel_pct:.1f}%), "
            f"被HardHit: {stats.hard_hit_count} ({stats.hard_hit_pct:.1f}%), "
            f"平均被打球初速: {stats.avg_exit_velocity:.1f} mph, "
            f"Whiff%: {stats.whiff_pct:.1f}%, CSW%: {stats.csw_pct:.1f}%"
        )
        upsert_pitcher_statcast_stats(pg_conn, stats)
        saved_overall += 1

    saved_pitch_types = 0
    for raw in pitch_type_raw_list:
        pt_stats = calculate_pitcher_pitch_type_stats(raw)
        logger.info(
            f"球種別集計完了: [Year: {pt_stats.year}] {pt_stats.pitch_name} ({pt_stats.pitch_type}): "
            f"{pt_stats.pitches}球 ({pt_stats.usage_pct:.1f}%), "
            f"平均球速: {pt_stats.avg_speed:.1f} mph, 回転数: {pt_stats.avg_spin_rate:.0f} rpm, "
            f"横変化: {pt_stats.avg_pfx_x:.1f} in, 縦変化: {pt_stats.avg_pfx_z:.1f} in, "
            f"Whiff%: {pt_stats.whiff_pct:.1f}%"
        )
        upsert_pitcher_pitch_type_stats(pg_conn, pt_stats)
        saved_pitch_types += 1

    logger.info(
        f"PostgreSQL への登録完了: 総合 {saved_overall} 件, 球種別 {saved_pitch_types} 件の Statcast 指標を Upsert しました。"
    )
    return saved_overall, saved_pitch_types


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    """コマンドライン引数をパースする"""
    parser = argparse.ArgumentParser(
        description="Statcast 指標集計サービス (ClickHouse -> PostgreSQL: batter_statcast_stats / pitcher_statcast_stats / pitcher_pitch_type_stats)"
    )
    parser.add_argument(
        "--worker",
        action="store_true",
        help="Cloud Pub/Sub サブスクリプションを受信する常駐ワーカーモードとして起動する",
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default=None,
        help="GCP プロジェクトID (未指定時は環境変数 GCP_PROJECT_ID または local-statcast-project)",
    )
    parser.add_argument(
        "--subscription-id",
        type=str,
        default=None,
        help="Pub/Sub サブスクリプションID (未指定時は環境変数 PUBSUB_SUBSCRIPTION_STATCAST_RAW または statcast-raw-ingested-sub)",
    )
    parser.add_argument(
        "--player-id",
        type=int,
        default=None,
        help="集計対象の選手ID (MLB player ID, 例: 660271)。ワンショット実行時は必須",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="集計対象のシーズン年 (例: 2024)。指定しない場合は全年度",
    )
    parser.add_argument(
        "--player-type",
        choices=["batter", "pitcher", "both"],
        default="both",
        help="集計対象の選手タイプ (batter, pitcher, both, デフォルト: both)",
    )
    parser.add_argument(
        "--legacy-basic-stats",
        action="store_true",
        help="【旧仕様】ClickHouse 生データから打者基本指標を集計して batter_season_stats へ保存する（通常は MLB Stats API Ingestion を使用するため非推奨）",
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="実行前に PostgreSQL テーブルの初期化 DDL を実行する",
    )
    parsed = parser.parse_args(args)
    if not parsed.worker and parsed.player_id is None:
        parser.error("--player-id はワンショット実行時に必須です (常駐実行時は --worker を指定してください)")
    return parsed


def main() -> None:
    """メイン関数"""
    load_dotenv()
    parsed = parse_args()
    try:
        if parsed.worker:
            from src.subscriber import run_subscriber

            run_subscriber(
                project_id=parsed.project_id,
                subscription_id=parsed.subscription_id,
            )
            return

        init_db = parsed.init_db

        # 打者 Statcast 詳細指標集計 -> batter_statcast_stats
        if parsed.player_type in ("batter", "both"):
            aggregate_batter_statcast(
                player_id=parsed.player_id,
                year=parsed.year,
                init_db=init_db,
            )
            init_db = False

        # 投手 Statcast 詳細指標集計 -> pitcher_statcast_stats, pitcher_pitch_type_stats
        if parsed.player_type in ("pitcher", "both"):
            aggregate_pitcher_statcast(
                player_id=parsed.player_id,
                year=parsed.year,
                init_db=init_db,
            )
            init_db = False

        # 旧基本指標の集計（明示的に指定された場合のみ実行）
        if parsed.legacy_basic_stats and parsed.player_type in ("batter", "both"):
            aggregate_batter(
                player_id=parsed.player_id,
                year=parsed.year,
                init_db=init_db,
            )

    except Exception as e:
        logger.error(f"集計処理中にエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()


