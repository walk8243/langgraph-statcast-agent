"""Baseball Savant (Statcast) データダウンロードモジュール"""

from __future__ import annotations

import io
import time
from typing import Literal, Optional
import pandas as pd
import requests

SAVANT_BASE_URL = "https://baseballsavant.mlb.com/statcast_search/csv"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)


def build_savant_search_params(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    player_id: Optional[int] = None,
    player_type: Literal["pitcher", "batter"] = "pitcher",
) -> dict[str, str]:
    """Baseball Savant の検索パラメータ辞書を生成する"""
    params: dict[str, str] = {
        "all": "true",
        "type": "details",
        "hfPT": "",
        "hfAB": "",
        "hfBBT": "",
        "hfPR": "",
        "hfZ": "",
        "hfGT": "R|PO|S|",
        "hfSea": "",
        "hfStadium": "",
        "hfBBL": "",
        "hfNewZones": "",
        "hfPull": "",
        "hfC": "",
        "hfSeaYear": "",
        "hfSit": "",
        "player_type": player_type,
        "hfOuts": "",
        "opponent": "",
        "pitcher_throws": "",
        "batter_stands": "",
        "hfSA": "",
        "team": "",
        "position": "",
        "hfRO": "",
        "home_road": "",
        "hfFlag": "",
        "metric_1": "",
    }

    if start_date:
        params["game_date_gt"] = start_date
    if end_date:
        params["game_date_lt"] = end_date

    if player_id:
        if player_type == "pitcher":
            params["pitchers_lookup[]"] = str(player_id)
        else:
            params["batters_lookup[]"] = str(player_id)

    return params


def download_statcast_csv(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    player_id: Optional[int] = None,
    player_type: Literal["pitcher", "batter"] = "pitcher",
    timeout: int = 60,
    max_retries: int = 3,
) -> pd.DataFrame:
    """Baseball Savant から Statcast CSV をダウンロードし、DataFrame として返す"""
    params = build_savant_search_params(
        start_date=start_date,
        end_date=end_date,
        player_id=player_id,
        player_type=player_type,
    )
    headers = {"User-Agent": DEFAULT_USER_AGENT}

    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                SAVANT_BASE_URL,
                params=params,
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()

            # CSV を読み込み
            csv_content = response.text
            if not csv_content.strip() or csv_content.startswith("<html"):
                raise ValueError("Savant API did not return valid CSV data.")

            df = pd.read_csv(io.StringIO(csv_content), low_memory=False)
            # BOM や余分なクォートを除去
            df.columns = [c.replace('"', "").strip() for c in df.columns]
            return df
        except Exception as e:
            last_exc = e
            if attempt < max_retries:
                time.sleep(2 * attempt)

    raise RuntimeError(
        f"Failed to download Statcast data after {max_retries} attempts: {last_exc}"
    )


def load_local_csv(file_path: str) -> pd.DataFrame:
    """ローカルの Statcast CSV ファイルを読み込む"""
    df = pd.read_csv(file_path, encoding="utf-8-sig", low_memory=False)
    df.columns = [c.replace('"', "").strip() for c in df.columns]
    return df
