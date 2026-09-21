"""Ingestion モジュールの単体テスト"""

import datetime
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
