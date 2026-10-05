"""Ingestion モジュールの単体テスト"""

import datetime
from unittest.mock import patch
import pandas as pd
import pytest
from src.downloader import build_savant_search_params
from src.loader import clean_statcast_df


def test_build_savant_search_params_dates():
    params = build_savant_search_params(start_date="2024-04-01", end_date="2024-04-07")
    assert params["game_date_gt"] == "2024-04-01"
    assert params["game_date_lt"] == "2024-04-07"
    assert params["type"] == "details"
    assert "pitchers_lookup[]" not in params
    assert "batters_lookup[]" not in params


def test_build_savant_search_params_pitcher():
    params = build_savant_search_params(player_id=808967, player_type="pitcher")
    assert params["player_type"] == "pitcher"
    assert params["pitchers_lookup[]"] == "808967"
    assert "batters_lookup[]" not in params


def test_build_savant_search_params_batter():
    params = build_savant_search_params(player_id=673548, player_type="batter")
    assert params["player_type"] == "batter"
    assert params["batters_lookup[]"] == "673548"
    assert "pitchers_lookup[]" not in params


def test_clean_statcast_df():
    raw_data = {
        "pitch_type": ["FF", "SL"],
        "game_date": ["2024-04-01", "2024-04-02"],
        "release_speed": [95.5, None],
        "player_name": ["Yamamoto, Yoshinobu", ""],
    }
    df = pd.DataFrame(raw_data)
    expected_columns = [
        "pitch_type",
        "game_date",
        "release_speed",
        "player_name",
        "batter",
    ]

    cleaned = clean_statcast_df(df, expected_columns)

    # カラム順序と存在確認
    assert list(cleaned.columns) == expected_columns
    # 日付変換確認
    assert cleaned["game_date"].iloc[0] == datetime.date(2024, 4, 1)
    # 不足カラムの補完 (batter)
    assert cleaned["batter"].iloc[0] is None
    # 空文字の None 置換
    assert cleaned["player_name"].iloc[1] is None


def test_clean_statcast_df_without_player_name():
    """テーブル定義から player_name が削除された場合に正しく除外されることを検証"""
    raw_data = {
        "pitch_type": ["FF"],
        "game_date": ["2024-04-06"],
        "release_speed": [95.5],
        "player_name": ["Yamamoto, Yoshinobu"],
        "pitcher": [808967],
        "batter": [673548],
    }
    df = pd.DataFrame(raw_data)
    # ClickHouse の新テーブル定義を模したカラムリスト（player_name を含まない）
    expected_columns = [
        "pitch_type",
        "game_date",
        "release_speed",
        "pitcher",
        "batter",
    ]

    cleaned = clean_statcast_df(df, expected_columns)

    # player_name が除外され、expected_columns のみになっていること
    assert list(cleaned.columns) == expected_columns
    assert "player_name" not in cleaned.columns
    assert cleaned["pitcher"].iloc[0] == 808967
    assert cleaned["batter"].iloc[0] == 673548


def test_cli_fetch_statcast_range_args():
    """--fetch-statcast-range 関連のコマンドライン引数が正しくパースされることを検証"""
    import argparse
    from src.main import main

    # parse_args を個別に検証するため、同様の引数設定をテスト
    # main.py の parser 定義が壊れていないかをチェック
    import sys
    with patch.object(
        sys,
        "argv",
        [
            "main.py",
            "--fetch-statcast-range",
            "--start-date",
            "2024-04-01",
            "--end-date",
            "2024-04-05",
            "--step-days",
            "2",
            "--interval",
            "1.5",
        ],
    ):
        with patch("src.main.get_clickhouse_client"), patch("src.main.initialize_table"), patch(
            "src.main.ingest_statcast_date_range"
        ) as mock_range:
            mock_range.return_value = {
                "total_chunks": 3,
                "success_chunks": 3,
                "skipped_chunks": 0,
                "failed_chunks": 0,
                "total_inserted": 500,
            }
            main()
            mock_range.assert_called_once_with(
                ch_client=mock_range.call_args.kwargs["ch_client"],
                start_date="2024-04-01",
                end_date="2024-04-05",
                interval=1.5,
                step_days=2,
            )


