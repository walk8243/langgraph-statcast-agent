"""ClickHouse への Statcast 生データ投入モジュール"""

from __future__ import annotations

import os
from typing import Optional
import clickhouse_connect
from clickhouse_connect.driver.client import Client
import numpy as np
import pandas as pd


def get_clickhouse_client(
    host: Optional[str] = None,
    port: Optional[int] = None,
    database: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> Client:
    """ClickHouse クライアントを取得する"""
    return clickhouse_connect.get_client(
        host=host or os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(port or os.getenv("CLICKHOUSE_HTTP_PORT", 8123)),
        database=database or os.getenv("CLICKHOUSE_DB", "statcast"),
        username=username or os.getenv("CLICKHOUSE_USER", "statcast"),
        password=password or os.getenv("CLICKHOUSE_PASSWORD", "statcast_pass"),
    )


def initialize_table(client: Client, ddl_path: Optional[str] = None) -> None:
    """初期化 DDL を実行してテーブルを作成する"""
    if not ddl_path:
        ddl_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "docker", "clickhouse", "init.sql"
        )
        ddl_path = os.path.abspath(ddl_path)

    if os.path.exists(ddl_path):
        with open(ddl_path, encoding="utf-8") as f:
            sql = f.read()
            # 複数ステートメントを分割して実行
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            for stmt in statements:
                client.command(stmt)


def clean_statcast_df(df: pd.DataFrame, expected_columns: list[str]) -> pd.DataFrame:
    """Statcast DataFrame を ClickHouse 投入用にクレンジング・型変換する"""
    df = df.copy()

    # カラム名のクレンジング（BOMや余分なクォートの除去）
    df.columns = [c.replace('"', "").strip() for c in df.columns]

    # game_date を Date 型に変換
    if "game_date" in df.columns:
        df["game_date"] = pd.to_datetime(df["game_date"]).dt.date

    # 期待されるカラムに合わせる（足りないカラムは None で追加）
    for col in expected_columns:
        if col not in df.columns:
            df[col] = None

    # 期待されるカラムのみを残し、順序を統一
    df = df[expected_columns]

    # NaN や空文字列、無限大を None に置換
    df = df.replace({np.nan: None, "": None})
    return df


def insert_statcast_data(
    client: Client,
    df: pd.DataFrame,
    table: str = "statcast_raw",
    chunk_size: int = 5000,
) -> int:
    """Statcast データを ClickHouse にバルクインサートする"""
    if df.empty:
        return 0

    # 既存のテーブルカラム一覧を取得
    table_columns = client.command(f"DESCRIBE TABLE {table}")
    # table_columns は行ごとのリストまたは文字列
    col_names = [row[0] for row in client.query(f"DESCRIBE TABLE {table}").result_rows]

    cleaned_df = clean_statcast_df(df, col_names)

    total_inserted = 0
    # チャンクごとにバルクインサート
    for start in range(0, len(cleaned_df), chunk_size):
        chunk = cleaned_df.iloc[start : start + chunk_size]
        client.insert_df(table, chunk)
        total_inserted += len(chunk)

    return total_inserted
