"""MLB Stats API からの Boxscore (試合詳細成績) 取得および ClickHouse への登録モジュール"""

from __future__ import annotations

import logging
from typing import Any, Optional
from clickhouse_connect.driver.client import Client
import requests

logger = logging.getLogger(__name__)

MLB_STATS_API_BASE_URL = "https://statsapi.mlb.com"

DEFAULT_CLICKHOUSE_BOXSCORE_TEAMS_DDL = """
CREATE TABLE IF NOT EXISTS statcast.boxscore_teams (
    `game_pk` UInt64,
    `team_id` UInt32,
    `team_name` String,
    `is_home` UInt8,
    -- チーム打撃 (batting)
    `fly_outs` UInt16,
    `ground_outs` UInt16,
    `air_outs` UInt16,
    `runs` UInt16,
    `doubles` UInt16,
    `triples` UInt16,
    `home_runs` UInt16,
    `strike_outs` UInt16,
    `base_on_balls` UInt16,
    `intentional_walks` UInt16,
    `hits` UInt16,
    `hit_by_pitch` UInt16,
    `at_bats` UInt16,
    `obp` Nullable(Float32),
    `slg` Nullable(Float32),
    `ops` Nullable(Float32),
    `avg` Nullable(Float32),
    `caught_stealing` UInt16,
    `stolen_bases` UInt16,
    `ground_into_double_play` UInt16,
    `plate_appearances` UInt16,
    `total_bases` UInt16,
    `rbi` UInt16,
    `left_on_base` UInt16,
    `sac_bunts` UInt16,
    `sac_flies` UInt16,
    -- チーム投球 (pitching)
    `pitching_runs` UInt16,
    `pitching_doubles` UInt16,
    `pitching_triples` UInt16,
    `pitching_home_runs` UInt16,
    `pitching_strike_outs` UInt16,
    `pitching_base_on_balls` UInt16,
    `pitching_intentional_walks` UInt16,
    `pitching_hits` UInt16,
    `pitching_at_bats` UInt16,
    `number_of_pitches` UInt16,
    `era` Nullable(Float32),
    `innings_pitched` String,
    `earned_runs` UInt16,
    `whip` Nullable(Float32),
    `batters_faced` UInt16,
    `outs` UInt16,
    `pitches_thrown` UInt16,
    `balls` UInt16,
    `strikes` UInt16,
    `strike_percentage` Nullable(Float32),
    `hit_batsmen` UInt16,
    `balks` UInt16,
    `wild_pitches` UInt16,
    `pickoffs` UInt16,
    -- チーム守備 (fielding)
    `fielding_assists` UInt16,
    `fielding_put_outs` UInt16,
    `fielding_errors` UInt16,
    `fielding_chances` UInt16,
    `fielding_passed_ball` UInt16,
    `fielding_pickoffs` UInt16,
    `created_at` DateTime DEFAULT now(),
    `updated_at` DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (game_pk, team_id);
"""

DEFAULT_CLICKHOUSE_BOXSCORE_BATTING_DDL = """
CREATE TABLE IF NOT EXISTS statcast.boxscore_batting (
    `game_pk` UInt64,
    `team_id` UInt32,
    `player_id` UInt64,
    `player_name` String,
    `jersey_number` Nullable(String),
    `position_code` Nullable(String),
    `position_name` Nullable(String),
    `position_type` Nullable(String),
    `position_abbreviation` Nullable(String),
    `all_positions` Array(String),
    `all_position_codes` Array(String),
    `batting_order` Nullable(String),
    `is_starter` UInt8,
    `is_substitute` UInt8,
    -- 打撃成績
    `summary` Nullable(String),
    `games_played` UInt8,
    `fly_outs` UInt16,
    `ground_outs` UInt16,
    `air_outs` UInt16,
    `runs` UInt16,
    `doubles` UInt16,
    `triples` UInt16,
    `home_runs` UInt16,
    `strike_outs` UInt16,
    `base_on_balls` UInt16,
    `intentional_walks` UInt16,
    `hits` UInt16,
    `hit_by_pitch` UInt16,
    `at_bats` UInt16,
    `caught_stealing` UInt16,
    `stolen_bases` UInt16,
    `ground_into_double_play` UInt16,
    `ground_into_triple_play` UInt16,
    `plate_appearances` UInt16,
    `total_bases` UInt16,
    `rbi` UInt16,
    `left_on_base` UInt16,
    `sac_bunts` UInt16,
    `sac_flies` UInt16,
    `catchers_interference` UInt16,
    `pickoffs` UInt16,
    `pop_outs` UInt16,
    `line_outs` UInt16,
    `created_at` DateTime DEFAULT now(),
    `updated_at` DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (game_pk, team_id, player_id);
"""

DEFAULT_CLICKHOUSE_BOXSCORE_PITCHING_DDL = """
CREATE TABLE IF NOT EXISTS statcast.boxscore_pitching (
    `game_pk` UInt64,
    `team_id` UInt32,
    `player_id` UInt64,
    `player_name` String,
    `jersey_number` Nullable(String),
    `position_code` Nullable(String),
    `position_name` Nullable(String),
    `position_type` Nullable(String),
    `position_abbreviation` Nullable(String),
    `all_positions` Array(String),
    `all_position_codes` Array(String),
    `pitching_order` UInt8,
    `is_starter` UInt8,
    -- 投球成績
    `summary` Nullable(String),
    `note` Nullable(String),
    `games_played` UInt8,
    `games_started` UInt8,
    `fly_outs` UInt16,
    `ground_outs` UInt16,
    `air_outs` UInt16,
    `runs` UInt16,
    `doubles` UInt16,
    `triples` UInt16,
    `home_runs` UInt16,
    `strike_outs` UInt16,
    `base_on_balls` UInt16,
    `intentional_walks` UInt16,
    `hits` UInt16,
    `hit_by_pitch` UInt16,
    `at_bats` UInt16,
    `number_of_pitches` UInt16,
    `innings_pitched` String,
    `wins` UInt8,
    `losses` UInt8,
    `saves` UInt8,
    `save_opportunities` UInt8,
    `holds` UInt8,
    `blown_saves` UInt8,
    `earned_runs` UInt16,
    `batters_faced` UInt16,
    `outs` UInt16,
    `complete_games` UInt8,
    `shutouts` UInt8,
    `pitches_thrown` UInt16,
    `balls` UInt16,
    `strikes` UInt16,
    `strike_percentage` Nullable(Float32),
    `hit_batsmen` UInt16,
    `balks` UInt16,
    `wild_pitches` UInt16,
    `pickoffs` UInt16,
    `rbi` UInt16,
    `games_finished` UInt8,
    `inherited_runners` UInt16,
    `inherited_runners_scored` UInt16,
    `catchers_interference` UInt16,
    `sac_bunts` UInt16,
    `sac_flies` UInt16,
    `passed_ball` UInt16,
    `pop_outs` UInt16,
    `line_outs` UInt16,
    `created_at` DateTime DEFAULT now(),
    `updated_at` DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (game_pk, team_id, player_id);
"""


def safe_int(val: Any, default: int = 0) -> int:
    """数値を安全に整数に変換する"""
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def safe_float(val: Any, default: Optional[float] = None) -> Optional[float]:
    """数値を安全に浮動小数点数に変換する"""
    if val is None:
        return default
    try:
        cleaned = str(val).strip()
        if cleaned in ("", "-", ".---", "-.--"):
            return default
        return float(cleaned)
    except (ValueError, TypeError):
        return default


def initialize_clickhouse_boxscore_tables(client: Client) -> None:
    """ClickHouse の Boxscore 関連テーブルを初期化する"""
    client.command(DEFAULT_CLICKHOUSE_BOXSCORE_TEAMS_DDL)
    client.command(DEFAULT_CLICKHOUSE_BOXSCORE_BATTING_DDL)
    client.command(DEFAULT_CLICKHOUSE_BOXSCORE_PITCHING_DDL)
    logger.info("Initialized ClickHouse boxscore tables")


def fetch_mlb_boxscore(
    game_pk: int,
    base_url: str = MLB_STATS_API_BASE_URL,
    timeout: int = 30,
) -> dict[str, Any]:
    """MLB Stats API から指定した game_pk の Boxscore を取得する

    Args:
        game_pk: 試合ID (MLB gamePk)
        base_url: APIベースURL
        timeout: タイムアウト秒数

    Returns:
        Boxscore JSONレスポンスの辞書
    """
    url = f"{base_url}/api/v1/game/{game_pk}/boxscore"
    logger.info("Fetching boxscore from %s", url)
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data


def parse_boxscore_data(
    game_pk: int,
    raw_boxscore: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Boxscore JSON をパースして、チーム成績、個人打撃成績、個人投球成績のリストを生成する

    Args:
        game_pk: 試合ID
        raw_boxscore: MLB Stats API の Boxscore レスポンス辞書

    Returns:
        (team_rows, batting_rows, pitching_rows) のタプル
    """
    teams_data = raw_boxscore.get("teams", {})
    team_rows: list[dict[str, Any]] = []
    batting_rows: list[dict[str, Any]] = []
    pitching_rows: list[dict[str, Any]] = []

    for is_home, side in [(0, "away"), (1, "home")]:
        team_entry = teams_data.get(side, {})
        team_info = team_entry.get("team", {})
        team_id = safe_int(team_info.get("id"))
        team_name = team_info.get("name", "")

        team_stats = team_entry.get("teamStats", {})
        b_stats = team_stats.get("batting", {})
        p_stats = team_stats.get("pitching", {})
        f_stats = team_stats.get("fielding", {})

        # 1. チーム成績行
        team_row = {
            "game_pk": game_pk,
            "team_id": team_id,
            "team_name": team_name,
            "is_home": is_home,
            # 打撃
            "fly_outs": safe_int(b_stats.get("flyOuts")),
            "ground_outs": safe_int(b_stats.get("groundOuts")),
            "air_outs": safe_int(b_stats.get("airOuts")),
            "runs": safe_int(b_stats.get("runs")),
            "doubles": safe_int(b_stats.get("doubles")),
            "triples": safe_int(b_stats.get("triples")),
            "home_runs": safe_int(b_stats.get("homeRuns")),
            "strike_outs": safe_int(b_stats.get("strikeOuts")),
            "base_on_balls": safe_int(b_stats.get("baseOnBalls")),
            "intentional_walks": safe_int(b_stats.get("intentionalWalks")),
            "hits": safe_int(b_stats.get("hits")),
            "hit_by_pitch": safe_int(b_stats.get("hitByPitch")),
            "at_bats": safe_int(b_stats.get("atBats")),
            "obp": safe_float(b_stats.get("obp")),
            "slg": safe_float(b_stats.get("slg")),
            "ops": safe_float(b_stats.get("ops")),
            "avg": safe_float(b_stats.get("avg")),
            "caught_stealing": safe_int(b_stats.get("caughtStealing")),
            "stolen_bases": safe_int(b_stats.get("stolenBases")),
            "ground_into_double_play": safe_int(b_stats.get("groundIntoDoublePlay")),
            "plate_appearances": safe_int(b_stats.get("plateAppearances")),
            "total_bases": safe_int(b_stats.get("totalBases")),
            "rbi": safe_int(b_stats.get("rbi")),
            "left_on_base": safe_int(b_stats.get("leftOnBase")),
            "sac_bunts": safe_int(b_stats.get("sacBunts")),
            "sac_flies": safe_int(b_stats.get("sacFlies")),
            # 投球
            "pitching_runs": safe_int(p_stats.get("runs")),
            "pitching_doubles": safe_int(p_stats.get("doubles")),
            "pitching_triples": safe_int(p_stats.get("triples")),
            "pitching_home_runs": safe_int(p_stats.get("homeRuns")),
            "pitching_strike_outs": safe_int(p_stats.get("strikeOuts")),
            "pitching_base_on_balls": safe_int(p_stats.get("baseOnBalls")),
            "pitching_intentional_walks": safe_int(p_stats.get("intentionalWalks")),
            "pitching_hits": safe_int(p_stats.get("hits")),
            "pitching_at_bats": safe_int(p_stats.get("atBats")),
            "number_of_pitches": safe_int(p_stats.get("numberOfPitches")),
            "era": safe_float(p_stats.get("era")),
            "innings_pitched": str(p_stats.get("inningsPitched") or "0.0"),
            "earned_runs": safe_int(p_stats.get("earnedRuns")),
            "whip": safe_float(p_stats.get("whip")),
            "batters_faced": safe_int(p_stats.get("battersFaced")),
            "outs": safe_int(p_stats.get("outs")),
            "pitches_thrown": safe_int(p_stats.get("pitchesThrown")),
            "balls": safe_int(p_stats.get("balls")),
            "strikes": safe_int(p_stats.get("strikes")),
            "strike_percentage": safe_float(p_stats.get("strikePercentage")),
            "hit_batsmen": safe_int(p_stats.get("hitBatsmen")),
            "balks": safe_int(p_stats.get("balks")),
            "wild_pitches": safe_int(p_stats.get("wildPitches")),
            "pickoffs": safe_int(p_stats.get("pickoffs")),
            # 守備
            "fielding_assists": safe_int(f_stats.get("assists")),
            "fielding_put_outs": safe_int(f_stats.get("putOuts")),
            "fielding_errors": safe_int(f_stats.get("errors")),
            "fielding_chances": safe_int(f_stats.get("chances")),
            "fielding_passed_ball": safe_int(f_stats.get("passedBall")),
            "fielding_pickoffs": safe_int(f_stats.get("pickoffs")),
        }
        team_rows.append(team_row)

        # 2. 個人成績
        players_dict = team_entry.get("players", {})
        pitchers_order_list = team_entry.get("pitchers", [])

        # 投手登板順インデックスのマップを作成
        pitcher_order_map: dict[int, int] = {}
        for idx, p_id in enumerate(pitchers_order_list, start=1):
            pitcher_order_map[safe_int(p_id)] = idx

        for p_key, p_val in players_dict.items():
            person = p_val.get("person", {})
            player_id = safe_int(person.get("id"))
            if not player_id:
                continue
            player_name = person.get("fullName", "")
            jersey_number = p_val.get("jerseyNumber")
            position = p_val.get("position", {})
            pos_code = position.get("code")
            pos_name = position.get("name")
            pos_type = position.get("type")
            pos_abbrev = position.get("abbreviation")

            all_positions_raw = p_val.get("allPositions", [])
            all_positions = [
                pos.get("abbreviation") or pos.get("name") or str(pos.get("code"))
                for pos in all_positions_raw
                if pos and (pos.get("abbreviation") or pos.get("name") or pos.get("code"))
            ]
            all_position_codes = [
                str(pos.get("code"))
                for pos in all_positions_raw
                if pos and pos.get("code") is not None
            ]
            # allPositions が空の場合のフォールバック
            if not all_positions and pos_abbrev:
                all_positions = [pos_abbrev]
            if not all_position_codes and pos_code:
                all_position_codes = [str(pos_code)]

            batting_order = p_val.get("battingOrder")
            game_status = p_val.get("gameStatus", {})
            is_sub = 1 if game_status.get("isSubstitute") else 0
            is_starter = 1 if (batting_order and batting_order.endswith("00") and not is_sub) else 0

            stats_dict = p_val.get("stats", {})
            player_batting = stats_dict.get("batting", {})
            player_pitching = stats_dict.get("pitching", {})

            # 個人打撃成績: stats.batting が存在し、打席/試合出場/打順のいずれかがある場合
            if player_batting or batting_order:
                b_row = {
                    "game_pk": game_pk,
                    "team_id": team_id,
                    "player_id": player_id,
                    "player_name": player_name,
                    "jersey_number": jersey_number,
                    "position_code": pos_code,
                    "position_name": pos_name,
                    "position_type": pos_type,
                    "position_abbreviation": pos_abbrev,
                    "all_positions": all_positions,
                    "all_position_codes": all_position_codes,
                    "batting_order": batting_order,
                    "is_starter": is_starter,
                    "is_substitute": is_sub,
                    "summary": player_batting.get("summary"),
                    "games_played": safe_int(player_batting.get("gamesPlayed")),
                    "fly_outs": safe_int(player_batting.get("flyOuts")),
                    "ground_outs": safe_int(player_batting.get("groundOuts")),
                    "air_outs": safe_int(player_batting.get("airOuts")),
                    "runs": safe_int(player_batting.get("runs")),
                    "doubles": safe_int(player_batting.get("doubles")),
                    "triples": safe_int(player_batting.get("triples")),
                    "home_runs": safe_int(player_batting.get("homeRuns")),
                    "strike_outs": safe_int(player_batting.get("strikeOuts")),
                    "base_on_balls": safe_int(player_batting.get("baseOnBalls")),
                    "intentional_walks": safe_int(player_batting.get("intentionalWalks")),
                    "hits": safe_int(player_batting.get("hits")),
                    "hit_by_pitch": safe_int(player_batting.get("hitByPitch")),
                    "at_bats": safe_int(player_batting.get("atBats")),
                    "caught_stealing": safe_int(player_batting.get("caughtStealing")),
                    "stolen_bases": safe_int(player_batting.get("stolenBases")),
                    "ground_into_double_play": safe_int(player_batting.get("groundIntoDoublePlay")),
                    "ground_into_triple_play": safe_int(player_batting.get("groundIntoTriplePlay")),
                    "plate_appearances": safe_int(player_batting.get("plateAppearances")),
                    "total_bases": safe_int(player_batting.get("totalBases")),
                    "rbi": safe_int(player_batting.get("rbi")),
                    "left_on_base": safe_int(player_batting.get("leftOnBase")),
                    "sac_bunts": safe_int(player_batting.get("sacBunts")),
                    "sac_flies": safe_int(player_batting.get("sacFlies")),
                    "catchers_interference": safe_int(player_batting.get("catchersInterference")),
                    "pickoffs": safe_int(player_batting.get("pickoffs")),
                    "pop_outs": safe_int(player_batting.get("popOuts")),
                    "line_outs": safe_int(player_batting.get("lineOuts")),
                }
                batting_rows.append(b_row)

            # 個人投球成績: stats.pitching が存在し、登板がある場合
            if player_pitching and (
                player_pitching.get("gamesPitched")
                or player_pitching.get("inningsPitched")
                or player_pitching.get("numberOfPitches")
                or player_id in pitcher_order_map
            ):
                pitch_order = pitcher_order_map.get(player_id, 0)
                is_p_starter = 1 if safe_int(player_pitching.get("gamesStarted")) == 1 or pitch_order == 1 else 0

                p_row = {
                    "game_pk": game_pk,
                    "team_id": team_id,
                    "player_id": player_id,
                    "player_name": player_name,
                    "jersey_number": jersey_number,
                    "position_code": pos_code,
                    "position_name": pos_name,
                    "position_type": pos_type,
                    "position_abbreviation": pos_abbrev,
                    "all_positions": all_positions,
                    "all_position_codes": all_position_codes,
                    "pitching_order": pitch_order,
                    "is_starter": is_p_starter,
                    "summary": player_pitching.get("summary"),
                    "note": player_pitching.get("note"),
                    "games_played": safe_int(player_pitching.get("gamesPlayed")),
                    "games_started": safe_int(player_pitching.get("gamesStarted")),
                    "fly_outs": safe_int(player_pitching.get("flyOuts")),
                    "ground_outs": safe_int(player_pitching.get("groundOuts")),
                    "air_outs": safe_int(player_pitching.get("airOuts")),
                    "runs": safe_int(player_pitching.get("runs")),
                    "doubles": safe_int(player_pitching.get("doubles")),
                    "triples": safe_int(player_pitching.get("triples")),
                    "home_runs": safe_int(player_pitching.get("homeRuns")),
                    "strike_outs": safe_int(player_pitching.get("strikeOuts")),
                    "base_on_balls": safe_int(player_pitching.get("baseOnBalls")),
                    "intentional_walks": safe_int(player_pitching.get("intentionalWalks")),
                    "hits": safe_int(player_pitching.get("hits")),
                    "hit_by_pitch": safe_int(player_pitching.get("hitByPitch")),
                    "at_bats": safe_int(player_pitching.get("atBats")),
                    "number_of_pitches": safe_int(player_pitching.get("numberOfPitches")),
                    "innings_pitched": str(player_pitching.get("inningsPitched") or "0.0"),
                    "wins": safe_int(player_pitching.get("wins")),
                    "losses": safe_int(player_pitching.get("losses")),
                    "saves": safe_int(player_pitching.get("saves")),
                    "save_opportunities": safe_int(player_pitching.get("saveOpportunities")),
                    "holds": safe_int(player_pitching.get("holds")),
                    "blown_saves": safe_int(player_pitching.get("blownSaves")),
                    "earned_runs": safe_int(player_pitching.get("earnedRuns")),
                    "batters_faced": safe_int(player_pitching.get("battersFaced")),
                    "outs": safe_int(player_pitching.get("outs")),
                    "complete_games": safe_int(player_pitching.get("completeGames")),
                    "shutouts": safe_int(player_pitching.get("shutouts")),
                    "pitches_thrown": safe_int(player_pitching.get("pitchesThrown")),
                    "balls": safe_int(player_pitching.get("balls")),
                    "strikes": safe_int(player_pitching.get("strikes")),
                    "strike_percentage": safe_float(player_pitching.get("strikePercentage")),
                    "hit_batsmen": safe_int(player_pitching.get("hitBatsmen")),
                    "balks": safe_int(player_pitching.get("balks")),
                    "wild_pitches": safe_int(player_pitching.get("wildPitches")),
                    "pickoffs": safe_int(player_pitching.get("pickoffs")),
                    "rbi": safe_int(player_pitching.get("rbi")),
                    "games_finished": safe_int(player_pitching.get("gamesFinished")),
                    "inherited_runners": safe_int(player_pitching.get("inheritedRunners")),
                    "inherited_runners_scored": safe_int(player_pitching.get("inheritedRunnersScored")),
                    "catchers_interference": safe_int(player_pitching.get("catchersInterference")),
                    "sac_bunts": safe_int(player_pitching.get("sacBunts")),
                    "sac_flies": safe_int(player_pitching.get("sacFlies")),
                    "passed_ball": safe_int(player_pitching.get("passedBall")),
                    "pop_outs": safe_int(player_pitching.get("popOuts")),
                    "line_outs": safe_int(player_pitching.get("lineOuts")),
                }
                pitching_rows.append(p_row)

    return team_rows, batting_rows, pitching_rows


def insert_boxscore_to_clickhouse(
    client: Client,
    team_rows: list[dict[str, Any]],
    batting_rows: list[dict[str, Any]],
    pitching_rows: list[dict[str, Any]],
) -> dict[str, int]:
    """Boxscore の各データを ClickHouse (列指向DB) に一括挿入する

    Args:
        client: ClickHouse クライアント
        team_rows: チーム成績の辞書リスト
        batting_rows: 個人打撃成績の辞書リスト
        pitching_rows: 個人投球成績の辞書リスト

    Returns:
        テーブルごとの登録件数 {"teams": int, "batting": int, "pitching": int}
    """
    initialize_clickhouse_boxscore_tables(client)
    counts = {"teams": 0, "batting": 0, "pitching": 0}

    # 1. チーム成績挿入
    if team_rows:
        cols_teams = list(team_rows[0].keys())
        data_teams = [[row[col] for col in cols_teams] for row in team_rows]
        client.insert(
            table="boxscore_teams",
            data=data_teams,
            column_names=cols_teams,
            database="statcast",
        )
        counts["teams"] = len(team_rows)
        logger.info("Inserted %d rows into statcast.boxscore_teams", len(team_rows))

    # 2. 個人打撃成績挿入
    if batting_rows:
        cols_batting = list(batting_rows[0].keys())
        data_batting = [[row[col] for col in cols_batting] for row in batting_rows]
        client.insert(
            table="boxscore_batting",
            data=data_batting,
            column_names=cols_batting,
            database="statcast",
        )
        counts["batting"] = len(batting_rows)
        logger.info("Inserted %d rows into statcast.boxscore_batting", len(batting_rows))

    # 3. 個人投球成績挿入
    if pitching_rows:
        cols_pitching = list(pitching_rows[0].keys())
        data_pitching = [[row[col] for col in cols_pitching] for row in pitching_rows]
        client.insert(
            table="boxscore_pitching",
            data=data_pitching,
            column_names=cols_pitching,
            database="statcast",
        )
        counts["pitching"] = len(pitching_rows)
        logger.info("Inserted %d rows into statcast.boxscore_pitching", len(pitching_rows))

    return counts


def fetch_and_insert_boxscore(
    client: Client,
    game_pk: int,
    base_url: str = MLB_STATS_API_BASE_URL,
    timeout: int = 30,
) -> dict[str, int]:
    """指定した game_pk の Boxscore を取得して ClickHouse に登録する

    Args:
        client: ClickHouse クライアント
        game_pk: 試合ID
        base_url: APIベースURL
        timeout: タイムアウト秒数

    Returns:
        登録件数辞書
    """
    raw_data = fetch_mlb_boxscore(game_pk=game_pk, base_url=base_url, timeout=timeout)
    team_rows, batting_rows, pitching_rows = parse_boxscore_data(game_pk, raw_data)
    counts = insert_boxscore_to_clickhouse(client, team_rows, batting_rows, pitching_rows)
    logger.info(
        "Successfully ingested boxscore for game %d (teams: %d, batting: %d, pitching: %d)",
        game_pk,
        counts["teams"],
        counts["batting"],
        counts["pitching"],
    )
    return counts


def fetch_and_insert_boxscores_batch(
    client: Client,
    game_pks: list[int],
    base_url: str = MLB_STATS_API_BASE_URL,
    timeout: int = 30,
) -> dict[str, int]:
    """指定した複数の game_pk の Boxscore を取得して ClickHouse に一括登録する

    Args:
        client: ClickHouse クライアント
        game_pks: 試合IDのリスト
        base_url: APIベースURL
        timeout: タイムアウト秒数

    Returns:
        合計登録件数辞書
    """
    total_counts = {"games": 0, "teams": 0, "batting": 0, "pitching": 0}
    for pk in game_pks:
        try:
            counts = fetch_and_insert_boxscore(
                client=client,
                game_pk=pk,
                base_url=base_url,
                timeout=timeout,
            )
            total_counts["games"] += 1
            total_counts["teams"] += counts["teams"]
            total_counts["batting"] += counts["batting"]
            total_counts["pitching"] += counts["pitching"]
        except Exception as e:
            logger.error("Failed to fetch or insert boxscore for game_pk %d: %s", pk, e)

    logger.info("Batch boxscore ingestion complete: %s", total_counts)
    return total_counts
