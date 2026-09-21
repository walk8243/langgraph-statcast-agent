"""Statcast Ingestion 実行エントリポイント (CLI)"""

from __future__ import annotations

import argparse
import os
import sys
from dotenv import load_dotenv

# プロジェクトルートの .env を読み込み
load_dotenv()

from .downloader import download_statcast_csv, load_local_csv
from .loader import get_clickhouse_client, initialize_table, insert_statcast_data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Baseball Savant から Statcast データを取得し、ClickHouse に登録します。"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="取得開始日 (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="取得終了日 (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--player-id",
        type=int,
        help="対象選手ID (MLB AM ID)",
    )
    parser.add_argument(
        "--player-type",
        choices=["pitcher", "batter"],
        default="pitcher",
        help="選手種別 (pitcher または batter、デフォルト: pitcher)",
    )
    parser.add_argument(
        "--csv-path",
        type=str,
        help="指定したローカル CSV ファイルから直接インポートします",
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="ClickHouse テーブルの初期化のみを実行します",
    )

    args = parser.parse_args()

    client = get_clickhouse_client()

    if args.init_db:
        print("Initializing ClickHouse tables...")
        initialize_table(client)
        print("ClickHouse tables initialized successfully.")
        return

    # テーブルが存在しない場合は初期化
    initialize_table(client)

    if args.csv_path:
        print(f"Loading data from local CSV: {args.csv_path}")
        df = load_local_csv(args.csv_path)
    elif args.start_date or args.player_id:
        print(
            f"Downloading Statcast data from Baseball Savant "
            f"(start_date={args.start_date}, end_date={args.end_date}, "
            f"player_id={args.player_id}, player_type={args.player_type})..."
        )
        df = download_statcast_csv(
            start_date=args.start_date,
            end_date=args.end_date,
            player_id=args.player_id,
            player_type=args.player_type,
        )
    else:
        parser.print_help()
        sys.exit(1)

    print(f"Loaded {len(df)} rows. Inserting into ClickHouse...")
    inserted = insert_statcast_data(client, df)
    print(f"Successfully inserted {inserted} rows into statcast.statcast_raw.")

    # 登録状況のサマリーを表示
    summary = client.query(
        "SELECT count() as total, uniq(pitcher) as pitchers, uniq(batter) as batters FROM statcast.statcast_raw"
    ).result_rows
    if summary:
        print(
            f"Current DB Summary -> Total Pitches: {summary[0][0]}, "
            f"Unique Pitchers: {summary[0][1]}, Unique Batters: {summary[0][2]}"
        )


if __name__ == "__main__":
    main()
