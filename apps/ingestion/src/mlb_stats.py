"""MLB Stats API からの打者・投手シーズン成績取得および PostgreSQL への登録モジュール"""

from __future__ import annotations

import logging
from typing import Any, Optional
import psycopg
import requests

logger = logging.getLogger(__name__)

MLB_STATS_API_BASE_URL = "https://statsapi.mlb.com"


def safe_int(val: Any, default: int = 0) -> int:
    """数値を安全に整数に変換する"""
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def safe_float(val: Any, default: float = 0.0) -> float:
    """数値を安全に浮動小数点数に変換する"""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def fetch_mlb_hitting_stats(
    season: int = 2024,
    sport_id: int = 1,
    base_url: str = MLB_STATS_API_BASE_URL,
    timeout: int = 30,
) -> list[dict[str, Any]]:
    """MLB Stats API から指定シーズンの打者シーズン成績（全打者）を取得する

    Args:
        season: 対象シーズン (デフォルト: 2024)
        sport_id: 競技区分ID (デフォルト: 1 = MLB)
        base_url: APIベースURL
        timeout: タイムアウト秒数

    Returns:
        各打者のシーズン打撃成績 (split 辞書のリスト)
    """
    url = f"{base_url}/api/v1/stats"
    params: dict[str, Any] = {
        "stats": "season",
        "group": "hitting",
        "season": season,
        "sportId": sport_id,
        "playerPool": "all",
        "limit": 2000,
    }

    logger.info("Fetching hitting stats from %s with params %s", url, params)
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()

    data = resp.json()
    stats_list = data.get("stats", [])
    if not stats_list:
        logger.warning("No stats container found in response")
        return []

    splits = stats_list[0].get("splits", [])
    logger.info("Fetched %d hitting stat records for season %d", len(splits), season)
    return splits


def parse_batter_season_stat(split: dict[str, Any], default_season: int = 2024) -> dict[str, Any]:
    """API レスポンスの split 辞書から batter_season_stats 用のレコード辞書を生成する"""
    player = split.get("player", {})
    stat = split.get("stat", {})
    season_val = safe_int(split.get("season"), default=default_season)

    return {
        "player_id": safe_int(player.get("id")),
        "year": season_val,
        "games": safe_int(stat.get("gamesPlayed")),
        "plate_appearances": safe_int(stat.get("plateAppearances")),
        "at_bats": safe_int(stat.get("atBats")),
        "runs": safe_int(stat.get("runs")),
        "hits": safe_int(stat.get("hits")),
        "doubles": safe_int(stat.get("doubles")),
        "triples": safe_int(stat.get("triples")),
        "home_runs": safe_int(stat.get("homeRuns")),
        "rbi": safe_int(stat.get("rbi")),
        "total_bases": safe_int(stat.get("totalBases")),
        "strikeouts": safe_int(stat.get("strikeOuts")),
        "walks": safe_int(stat.get("baseOnBalls")),
        "intentional_walks": safe_int(stat.get("intentionalWalks")),
        "hit_by_pitch": safe_int(stat.get("hitByPitch")),
        "sac_bunts": safe_int(stat.get("sacBunts")),
        "sac_flies": safe_int(stat.get("sacFlies")),
        "grounded_into_double_play": safe_int(stat.get("groundIntoDoublePlay")),
        "stolen_bases": safe_int(stat.get("stolenBases")),
        "caught_stealing": safe_int(stat.get("caughtStealing")),
        "batting_average": safe_float(stat.get("avg")),
        "on_base_percentage": safe_float(stat.get("obp")),
        "slugging_percentage": safe_float(stat.get("slg")),
        "ops": safe_float(stat.get("ops")),
    }


def upsert_batter_season_stats_to_postgres(
    conn: psycopg.Connection,
    splits: list[dict[str, Any]],
    season: int = 2024,
    ensure_players: bool = True,
) -> int:
    """打者シーズン成績を PostgreSQL の batter_season_stats テーブルへ Upsert する

    Args:
        conn: PostgreSQL コネクション
        splits: MLB Stats API から取得した split 辞書リスト
        season: デフォルトシーズン
        ensure_players: 未登録選手を players テーブルへ事前 Upsert するかどうか

    Returns:
        登録・更新された件数
    """
    if not splits:
        return 0

    # 1. 選手マスタへの事前登録（整合性担保）
    if ensure_players:
        player_sql = """
        INSERT INTO players (
            player_id, name_en, team_id, updated_at
        ) VALUES (
            %(player_id)s, %(name_en)s, %(team_id)s, CURRENT_TIMESTAMP
        )
        ON CONFLICT (player_id) DO UPDATE SET
            name_en = COALESCE(EXCLUDED.name_en, players.name_en),
            team_id = COALESCE(EXCLUDED.team_id, players.team_id),
            updated_at = CURRENT_TIMESTAMP;
        """
        player_rows = []
        for s in splits:
            p = s.get("player", {})
            t = s.get("team", {})
            pid = safe_int(p.get("id"))
            if pid > 0:
                player_rows.append(
                    {
                        "player_id": pid,
                        "name_en": p.get("fullName") or f"Player {pid}",
                        "team_id": safe_int(t.get("id")) if t and t.get("id") else None,
                    }
                )

        if player_rows:
            with conn.cursor() as cur:
                cur.executemany(player_sql, player_rows)
            conn.commit()
            logger.info("Ensured %d players in players table", len(player_rows))

    # 2. batter_season_stats への Upsert
    stats_sql = """
    INSERT INTO batter_season_stats (
        player_id,
        year,
        games,
        plate_appearances,
        at_bats,
        runs,
        hits,
        doubles,
        triples,
        home_runs,
        rbi,
        total_bases,
        strikeouts,
        walks,
        intentional_walks,
        hit_by_pitch,
        sac_bunts,
        sac_flies,
        grounded_into_double_play,
        stolen_bases,
        caught_stealing,
        batting_average,
        on_base_percentage,
        slugging_percentage,
        ops,
        updated_at
    ) VALUES (
        %(player_id)s,
        %(year)s,
        %(games)s,
        %(plate_appearances)s,
        %(at_bats)s,
        %(runs)s,
        %(hits)s,
        %(doubles)s,
        %(triples)s,
        %(home_runs)s,
        %(rbi)s,
        %(total_bases)s,
        %(strikeouts)s,
        %(walks)s,
        %(intentional_walks)s,
        %(hit_by_pitch)s,
        %(sac_bunts)s,
        %(sac_flies)s,
        %(grounded_into_double_play)s,
        %(stolen_bases)s,
        %(caught_stealing)s,
        %(batting_average)s,
        %(on_base_percentage)s,
        %(slugging_percentage)s,
        %(ops)s,
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (player_id, year) DO UPDATE SET
        games = EXCLUDED.games,
        plate_appearances = EXCLUDED.plate_appearances,
        at_bats = EXCLUDED.at_bats,
        runs = EXCLUDED.runs,
        hits = EXCLUDED.hits,
        doubles = EXCLUDED.doubles,
        triples = EXCLUDED.triples,
        home_runs = EXCLUDED.home_runs,
        rbi = EXCLUDED.rbi,
        total_bases = EXCLUDED.total_bases,
        strikeouts = EXCLUDED.strikeouts,
        walks = EXCLUDED.walks,
        intentional_walks = EXCLUDED.intentional_walks,
        hit_by_pitch = EXCLUDED.hit_by_pitch,
        sac_bunts = EXCLUDED.sac_bunts,
        sac_flies = EXCLUDED.sac_flies,
        grounded_into_double_play = EXCLUDED.grounded_into_double_play,
        stolen_bases = EXCLUDED.stolen_bases,
        caught_stealing = EXCLUDED.caught_stealing,
        batting_average = EXCLUDED.batting_average,
        on_base_percentage = EXCLUDED.on_base_percentage,
        slugging_percentage = EXCLUDED.slugging_percentage,
        ops = EXCLUDED.ops,
        updated_at = CURRENT_TIMESTAMP;
    """

    parsed_stats = [
        parse_batter_season_stat(s, default_season=season)
        for s in splits
        if safe_int(s.get("player", {}).get("id")) > 0
    ]

    with conn.cursor() as cur:
        cur.executemany(stats_sql, parsed_stats)
    conn.commit()

    logger.info("Upserted %d batter season stats into PostgreSQL", len(parsed_stats))
    return len(parsed_stats)


def fetch_mlb_pitching_stats(
    season: int = 2024,
    sport_id: int = 1,
    base_url: str = MLB_STATS_API_BASE_URL,
    timeout: int = 30,
) -> list[dict[str, Any]]:
    """MLB Stats API から指定シーズンの投手シーズン成績（全投手）を取得する

    Args:
        season: 対象シーズン (デフォルト: 2024)
        sport_id: 競技区分ID (デフォルト: 1 = MLB)
        base_url: APIベースURL
        timeout: タイムアウト秒数

    Returns:
        各投手のシーズン投球成績 (split 辞書のリスト)
    """
    url = f"{base_url}/api/v1/stats"
    params: dict[str, Any] = {
        "stats": "season",
        "group": "pitching",
        "season": season,
        "sportId": sport_id,
        "playerPool": "all",
        "limit": 2000,
    }

    logger.info("Fetching pitching stats from %s with params %s", url, params)
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()

    data = resp.json()
    stats_list = data.get("stats", [])
    if not stats_list:
        logger.warning("No stats container found in response")
        return []

    splits = stats_list[0].get("splits", [])
    logger.info("Fetched %d pitching stat records for season %d", len(splits), season)
    return splits


def parse_pitcher_season_stat(split: dict[str, Any], default_season: int = 2024) -> dict[str, Any]:
    """API レスポンスの split 辞書から pitcher_season_stats 用のレコード辞書を生成する"""
    player = split.get("player", {})
    stat = split.get("stat", {})
    season_val = safe_int(split.get("season"), default=default_season)

    return {
        "player_id": safe_int(player.get("id")),
        "year": season_val,
        "wins": safe_int(stat.get("wins")),
        "losses": safe_int(stat.get("losses")),
        "era": safe_float(stat.get("era")),
        "games_pitched": safe_int(stat.get("gamesPitched") or stat.get("gamesPlayed")),
        "games_started": safe_int(stat.get("gamesStarted")),
        "complete_games": safe_int(stat.get("completeGames")),
        "shutouts": safe_int(stat.get("shutouts")),
        "saves": safe_int(stat.get("saves")),
        "save_opportunities": safe_int(stat.get("saveOpportunities")),
        "holds": safe_int(stat.get("holds")),
        "blown_saves": safe_int(stat.get("blownSaves")),
        "innings_pitched": str(stat.get("inningsPitched") or "0.0"),
        "outs": safe_int(stat.get("outs")),
        "hits": safe_int(stat.get("hits")),
        "runs": safe_int(stat.get("runs")),
        "earned_runs": safe_int(stat.get("earnedRuns")),
        "home_runs": safe_int(stat.get("homeRuns")),
        "walks": safe_int(stat.get("baseOnBalls")),
        "intentional_walks": safe_int(stat.get("intentionalWalks")),
        "strikeouts": safe_int(stat.get("strikeOuts")),
        "hit_by_pitch": safe_int(stat.get("hitBatsmen") or stat.get("hitByPitch")),
        "whip": safe_float(stat.get("whip")),
        "batting_average_against": safe_float(stat.get("avg")),
        "batters_faced": safe_int(stat.get("battersFaced")),
        "number_of_pitches": safe_int(stat.get("numberOfPitches")),
    }


def upsert_pitcher_season_stats_to_postgres(
    conn: psycopg.Connection,
    splits: list[dict[str, Any]],
    season: int = 2024,
    ensure_players: bool = True,
) -> int:
    """投手シーズン成績を PostgreSQL の pitcher_season_stats テーブルへ Upsert する

    Args:
        conn: PostgreSQL コネクション
        splits: MLB Stats API から取得した split 辞書リスト
        season: デフォルトシーズン
        ensure_players: 未登録選手を players テーブルへ事前 Upsert するかどうか

    Returns:
        登録・更新された件数
    """
    if not splits:
        return 0

    # 1. 選手マスタへの事前登録（整合性担保）
    if ensure_players:
        player_sql = """
        INSERT INTO players (
            player_id, name_en, team_id, updated_at
        ) VALUES (
            %(player_id)s, %(name_en)s, %(team_id)s, CURRENT_TIMESTAMP
        )
        ON CONFLICT (player_id) DO UPDATE SET
            name_en = COALESCE(EXCLUDED.name_en, players.name_en),
            team_id = COALESCE(EXCLUDED.team_id, players.team_id),
            updated_at = CURRENT_TIMESTAMP;
        """
        player_rows = []
        for s in splits:
            p = s.get("player", {})
            t = s.get("team", {})
            pid = safe_int(p.get("id"))
            if pid > 0:
                player_rows.append(
                    {
                        "player_id": pid,
                        "name_en": p.get("fullName") or f"Player {pid}",
                        "team_id": safe_int(t.get("id")) if t and t.get("id") else None,
                    }
                )

        if player_rows:
            with conn.cursor() as cur:
                cur.executemany(player_sql, player_rows)
            conn.commit()
            logger.info("Ensured %d players in players table", len(player_rows))

    # 2. pitcher_season_stats への Upsert
    stats_sql = """
    INSERT INTO pitcher_season_stats (
        player_id,
        year,
        wins,
        losses,
        era,
        games_pitched,
        games_started,
        complete_games,
        shutouts,
        saves,
        save_opportunities,
        holds,
        blown_saves,
        innings_pitched,
        outs,
        hits,
        runs,
        earned_runs,
        home_runs,
        walks,
        intentional_walks,
        strikeouts,
        hit_by_pitch,
        whip,
        batting_average_against,
        batters_faced,
        number_of_pitches,
        updated_at
    ) VALUES (
        %(player_id)s,
        %(year)s,
        %(wins)s,
        %(losses)s,
        %(era)s,
        %(games_pitched)s,
        %(games_started)s,
        %(complete_games)s,
        %(shutouts)s,
        %(saves)s,
        %(save_opportunities)s,
        %(holds)s,
        %(blown_saves)s,
        %(innings_pitched)s,
        %(outs)s,
        %(hits)s,
        %(runs)s,
        %(earned_runs)s,
        %(home_runs)s,
        %(walks)s,
        %(intentional_walks)s,
        %(strikeouts)s,
        %(hit_by_pitch)s,
        %(whip)s,
        %(batting_average_against)s,
        %(batters_faced)s,
        %(number_of_pitches)s,
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (player_id, year) DO UPDATE SET
        wins = EXCLUDED.wins,
        losses = EXCLUDED.losses,
        era = EXCLUDED.era,
        games_pitched = EXCLUDED.games_pitched,
        games_started = EXCLUDED.games_started,
        complete_games = EXCLUDED.complete_games,
        shutouts = EXCLUDED.shutouts,
        saves = EXCLUDED.saves,
        save_opportunities = EXCLUDED.save_opportunities,
        holds = EXCLUDED.holds,
        blown_saves = EXCLUDED.blown_saves,
        innings_pitched = EXCLUDED.innings_pitched,
        outs = EXCLUDED.outs,
        hits = EXCLUDED.hits,
        runs = EXCLUDED.runs,
        earned_runs = EXCLUDED.earned_runs,
        home_runs = EXCLUDED.home_runs,
        walks = EXCLUDED.walks,
        intentional_walks = EXCLUDED.intentional_walks,
        strikeouts = EXCLUDED.strikeouts,
        hit_by_pitch = EXCLUDED.hit_by_pitch,
        whip = EXCLUDED.whip,
        batting_average_against = EXCLUDED.batting_average_against,
        batters_faced = EXCLUDED.batters_faced,
        number_of_pitches = EXCLUDED.number_of_pitches,
        updated_at = CURRENT_TIMESTAMP;
    """

    parsed_stats = [
        parse_pitcher_season_stat(s, default_season=season)
        for s in splits
        if safe_int(s.get("player", {}).get("id")) > 0
    ]

    with conn.cursor() as cur:
        cur.executemany(stats_sql, parsed_stats)
    conn.commit()

    logger.info("Upserted %d pitcher season stats into PostgreSQL", len(parsed_stats))
    return len(parsed_stats)
