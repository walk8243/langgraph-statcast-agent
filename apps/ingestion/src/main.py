"""Statcast Ingestion 実行エントリポイント (CLI)"""

from __future__ import annotations

import argparse
import os
import sys
from dotenv import load_dotenv

# プロジェクトルートの .env を読み込み
load_dotenv()

from .batch_statcast import extract_year_from_dates, ingest_all_players_statcast
from .downloader import download_statcast_csv, load_local_csv
from .loader import get_clickhouse_client, initialize_table, insert_statcast_data
from .publisher import publish_statcast_raw_message
from .mlb_games import (
    fetch_mlb_schedule,
    initialize_clickhouse_games_table,
    insert_games_to_clickhouse,
    upsert_games_to_postgres,
)
from .mlb_players import (
    fetch_mlb_players,
    initialize_clickhouse_players_table,
    insert_players_to_clickhouse,
    upsert_players_to_postgres,
)
from .mlb_stats import (
    fetch_mlb_hitting_stats,
    fetch_mlb_pitching_stats,
    upsert_batter_season_stats_to_postgres,
    upsert_pitcher_season_stats_to_postgres,
)
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
        choices=["pitcher", "batter", "both"],
        default="pitcher",
        help="選手種別 (pitcher, batter, または both、デフォルト: pitcher)",
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
        "--fetch-players",
        action="store_true",
        help="MLB Stats API から選手一覧を取得し、ClickHouse (全データ) と PostgreSQL (基本データ) に登録します",
    )
    parser.add_argument(
        "--fetch-games",
        action="store_true",
        help="MLB Stats API から試合日程・結果一覧を取得し、ClickHouse (全データ) と PostgreSQL (基本データ) に登録します",
    )
    parser.add_argument(
        "--fetch-hitting-stats",
        action="store_true",
        help="MLB Stats API から打者シーズン成績を取得し、PostgreSQL (batter_season_stats) に登録します",
    )
    parser.add_argument(
        "--fetch-pitching-stats",
        action="store_true",
        help="MLB Stats API から投手シーズン成績を取得し、PostgreSQL (pitcher_season_stats) に登録します",
    )
    parser.add_argument(
        "--fetch-all-statcast",
        action="store_true",
        help="登録済み全選手を対象として Baseball Savant から Statcast データを一括取得・投入します",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="一括取得処理の対象選手数の上限",
    )
    parser.add_argument(
        "--sport-id",
        type=int,
        default=1,
        help="データ取得時の競技区分ID (デフォルト: 1 = MLB)",
    )
    parser.add_argument(
        "--season",
        type=int,
        help="データ取得時の対象シーズン (任意、デフォルト: 2024)",
    )
    parser.add_argument(
        "--no-pubsub",
        action="store_true",
        help="データ登録完了後の Cloud Pub/Sub への集計トリガーメッセージ発行をスキップします",
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

    if args.fetch_players:
        season = args.season or 2024
        print(
            f"Fetching players from MLB Stats API (sport_id={args.sport_id}, season={season})..."
        )
        players = fetch_mlb_players(season=season, sport_id=args.sport_id)
        print(f"Fetched {len(players)} players.")

        # 1. 列指向DB (ClickHouse) へ全データ投入
        print("Inserting full player data into ClickHouse (statcast.players)...")
        ch_client = get_clickhouse_client()
        ch_inserted = insert_players_to_clickhouse(ch_client, players)
        print(f"Successfully inserted {ch_inserted} players into ClickHouse statcast.players.")

        # 2. RDB (PostgreSQL) へ結合・表示用基本データを Upsert
        print("Upserting essential player data into PostgreSQL (players)...")
        pg_conn = get_postgres_connection()
        initialize_postgres_tables(pg_conn)
        pg_upserted = upsert_players_to_postgres(pg_conn, players)
        print(f"Successfully upserted {pg_upserted} players into PostgreSQL players.")
        pg_conn.close()
        return

    if args.fetch_games:
        season = args.season or 2024
        print(
            f"Fetching schedule from MLB Stats API (sport_id={args.sport_id}, season={season}, start={args.start_date}, end={args.end_date})..."
        )
        games = fetch_mlb_schedule(
            season=season,
            sport_id=args.sport_id,
            start_date=args.start_date,
            end_date=args.end_date,
        )
        print(f"Fetched {len(games)} games.")

        # 1. 列指向DB (ClickHouse) へ全データ投入
        print("Inserting full game data into ClickHouse (statcast.games)...")
        ch_client = get_clickhouse_client()
        ch_inserted = insert_games_to_clickhouse(ch_client, games)
        print(f"Successfully inserted {ch_inserted} games into ClickHouse statcast.games.")

        # 2. RDB (PostgreSQL) へ結合・表示用基本データを Upsert
        print("Upserting essential game data into PostgreSQL (games)...")
        pg_conn = get_postgres_connection()
        initialize_postgres_tables(pg_conn)
        pg_upserted = upsert_games_to_postgres(pg_conn, games)
        print(f"Successfully upserted {pg_upserted} games into PostgreSQL games.")
        pg_conn.close()
        return

    if args.fetch_hitting_stats:
        season = args.season or 2024
        print(
            f"Fetching hitting stats from MLB Stats API (sport_id={args.sport_id}, season={season})..."
        )
        splits = fetch_mlb_hitting_stats(season=season, sport_id=args.sport_id)
        print(f"Fetched {len(splits)} hitting stat records.")

        print("Upserting hitting stats into PostgreSQL (batter_season_stats)...")
        pg_conn = get_postgres_connection()
        initialize_postgres_tables(pg_conn)
        pg_upserted = upsert_batter_season_stats_to_postgres(pg_conn, splits, season=season)
        print(
            f"Successfully upserted {pg_upserted} batter season stats into PostgreSQL batter_season_stats."
        )
        pg_conn.close()
        return

    if args.fetch_pitching_stats:
        season = args.season or 2024
        print(
            f"Fetching pitching stats from MLB Stats API (sport_id={args.sport_id}, season={season})..."
        )
        splits = fetch_mlb_pitching_stats(season=season, sport_id=args.sport_id)
        print(f"Fetched {len(splits)} pitching stat records.")

        print("Upserting pitching stats into PostgreSQL (pitcher_season_stats)...")
        pg_conn = get_postgres_connection()
        initialize_postgres_tables(pg_conn)
        pg_upserted = upsert_pitcher_season_stats_to_postgres(pg_conn, splits, season=season)
        print(
            f"Successfully upserted {pg_upserted} pitcher season stats into PostgreSQL pitcher_season_stats."
        )
        pg_conn.close()
        return

    if args.fetch_all_statcast:
        print("Starting batch Statcast ingestion for registered players...")
        pg_conn = get_postgres_connection()
        ch_client = get_clickhouse_client()
        initialize_table(ch_client)

        player_type = args.player_type if args.player_type != "pitcher" else "both"
        summary = ingest_all_players_statcast(
            pg_conn=pg_conn,
            ch_client=ch_client,
            start_date=args.start_date,
            end_date=args.end_date,
            player_type=player_type,
            limit=args.limit,
            enable_pubsub=not args.no_pubsub,
        )
        print(
            f"Batch ingestion completed! Total players processed: {summary['total_players']}, "
            f"Total Statcast rows inserted: {summary['total_inserted']}"
        )
        pg_conn.close()
        return

    client = get_clickhouse_client()

    if args.init_db:
        print("Initializing ClickHouse tables...")
        initialize_table(client)
        initialize_clickhouse_teams_table(client)
        initialize_clickhouse_players_table(client)
        initialize_clickhouse_games_table(client)
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

    # 登録成功時、Cloud Pub/Sub へ集計メッセージを発行
    if inserted > 0 and not args.no_pubsub and args.player_id:
        year = extract_year_from_dates(args.start_date, args.end_date)
        publish_statcast_raw_message(
            player_id=args.player_id,
            year=year,
            player_type=args.player_type,
        )

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
