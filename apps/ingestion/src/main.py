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
from .mlb_teams import (
    fetch_mlb_teams,
    initialize_clickhouse_teams_table,
    insert_teams_to_clickhouse,
    upsert_teams_to_postgres,
)
from .postgres import get_postgres_connection, initialize_tables as initialize_postgres_tables


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Baseball Savant / MLB Stats API からデータを取得し、DBに登録します。"
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
        help="DBテーブル (ClickHouse / PostgreSQL) の初期化を実行します",
    )
    parser.add_argument(
        "--fetch-teams",
        action="store_true",
        help="MLB Stats API からチーム一覧を取得し、ClickHouse (全データ) と PostgreSQL (基本データ) に登録します",
    )
    parser.add_argument(
        "--sport-id",
        type=int,
        default=1,
        help="チーム取得時の競技区分ID (デフォルト: 1 = MLB)",
    )
    parser.add_argument(
        "--season",
        type=int,
        help="チーム取得時の対象シーズン (任意)",
    )

    args = parser.parse_args()

    if args.fetch_teams:
        print(
            f"Fetching teams from MLB Stats API (sport_id={args.sport_id}, season={args.season})..."
        )
        teams = fetch_mlb_teams(sport_id=args.sport_id, season=args.season)
        print(f"Fetched {len(teams)} teams.")

        # 1. 列指向DB (ClickHouse) へ全データ投入
        print("Inserting full team data into ClickHouse (statcast.teams)...")
        ch_client = get_clickhouse_client()
        ch_inserted = insert_teams_to_clickhouse(ch_client, teams)
        print(f"Successfully inserted {ch_inserted} teams into ClickHouse statcast.teams.")

        # 2. RDB (PostgreSQL) へ結合・表示用基本データを Upsert
        print("Upserting essential team data into PostgreSQL (teams)...")
        pg_conn = get_postgres_connection()
        initialize_postgres_tables(pg_conn)
        pg_upserted = upsert_teams_to_postgres(pg_conn, teams)
        print(f"Successfully upserted {pg_upserted} teams into PostgreSQL teams.")
        pg_conn.close()
        return

    client = get_clickhouse_client()

    if args.init_db:
        print("Initializing ClickHouse tables...")
        initialize_table(client)
        print("ClickHouse tables initialized successfully.")
        try:
            pg_conn = get_postgres_connection()
            initialize_postgres_tables(pg_conn)
            pg_conn.close()
            print("PostgreSQL tables initialized successfully.")
        except Exception as e:
            print(f"Note: PostgreSQL initialization skipped or failed: {e}")
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
