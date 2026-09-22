"""MLB 打者・投手シーズン成績取得および DB 登録モジュールのユニットテスト"""

from unittest.mock import MagicMock, patch
import pytest
from src.mlb_stats import (
    fetch_mlb_hitting_stats,
    fetch_mlb_pitching_stats,
    parse_batter_season_stat,
    parse_pitcher_season_stat,
    safe_float,
    safe_int,
    upsert_batter_season_stats_to_postgres,
    upsert_pitcher_season_stats_to_postgres,
)


@pytest.fixture
def sample_stats_response():
    return {
        "stats": [
            {
                "type": {"displayName": "season"},
                "group": {"displayName": "hitting"},
                "totalSplits": 2,
                "splits": [
                    {
                        "season": "2024",
                        "stat": {
                            "gamesPlayed": 159,
                            "plateAppearances": 731,
                            "atBats": 636,
                            "runs": 134,
                            "hits": 197,
                            "doubles": 38,
                            "triples": 7,
                            "homeRuns": 54,
                            "rbi": 130,
                            "totalBases": 411,
                            "strikeOuts": 162,
                            "baseOnBalls": 81,
                            "intentionalWalks": 10,
                            "hitByPitch": 6,
                            "sacBunts": 0,
                            "sacFlies": 5,
                            "groundIntoDoublePlay": 7,
                            "stolenBases": 59,
                            "caughtStealing": 4,
                            "avg": ".310",
                            "obp": ".390",
                            "slg": ".646",
                            "ops": "1.036",
                        },
                        "team": {
                            "id": 119,
                            "name": "Los Angeles Dodgers",
                        },
                        "player": {
                            "id": 660271,
                            "fullName": "Shohei Ohtani",
                        },
                    },
                    {
                        "season": "2024",
                        "stat": {
                            "gamesPlayed": 161,
                            "plateAppearances": 709,
                            "atBats": 636,
                            "runs": 125,
                            "hits": 211,
                            "doubles": 45,
                            "triples": 11,
                            "homeRuns": 32,
                            "rbi": 109,
                            "totalBases": 374,
                            "strikeOuts": 106,
                            "baseOnBalls": 57,
                            "intentionalWalks": 9,
                            "hitByPitch": 8,
                            "sacBunts": 0,
                            "sacFlies": 8,
                            "groundIntoDoublePlay": 4,
                            "stolenBases": 31,
                            "caughtStealing": 12,
                            "avg": ".332",
                            "obp": ".389",
                            "slg": ".588",
                            "ops": ".977",
                        },
                        "team": {
                            "id": 118,
                            "name": "Kansas City Royals",
                        },
                        "player": {
                            "id": 677951,
                            "fullName": "Bobby Witt Jr.",
                        },
                    },
                ],
            }
        ]
    }


def test_safe_converters():
    assert safe_int(10) == 10
    assert safe_int("42") == 42
    assert safe_int(None, 0) == 0
    assert safe_int("invalid", 5) == 5

    assert safe_float(3.14) == 3.14
    assert safe_float(".310") == 0.31
    assert safe_float(None, 0.0) == 0.0
    assert safe_float(".---", 0.0) == 0.0


def test_fetch_mlb_hitting_stats(sample_stats_response):
    with patch("src.mlb_stats.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_stats_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        splits = fetch_mlb_hitting_stats(season=2024, sport_id=1)

        assert len(splits) == 2
        assert splits[0]["player"]["fullName"] == "Shohei Ohtani"
        assert splits[0]["stat"]["homeRuns"] == 54
        assert splits[0]["stat"]["rbi"] == 130
        assert splits[0]["stat"]["stolenBases"] == 59
        mock_get.assert_called_once()


def test_parse_batter_season_stat(sample_stats_response):
    split = sample_stats_response["stats"][0]["splits"][0]
    parsed = parse_batter_season_stat(split, default_season=2024)

    assert parsed["player_id"] == 660271
    assert parsed["year"] == 2024
    assert parsed["games"] == 159
    assert parsed["plate_appearances"] == 731
    assert parsed["at_bats"] == 636
    assert parsed["runs"] == 134
    assert parsed["hits"] == 197
    assert parsed["doubles"] == 38
    assert parsed["triples"] == 7
    assert parsed["home_runs"] == 54
    assert parsed["rbi"] == 130
    assert parsed["total_bases"] == 411
    assert parsed["strikeouts"] == 162
    assert parsed["walks"] == 81
    assert parsed["intentional_walks"] == 10
    assert parsed["hit_by_pitch"] == 6
    assert parsed["sac_bunts"] == 0
    assert parsed["sac_flies"] == 5
    assert parsed["grounded_into_double_play"] == 7
    assert parsed["stolen_bases"] == 59
    assert parsed["caught_stealing"] == 4
    assert parsed["batting_average"] == 0.310
    assert parsed["on_base_percentage"] == 0.390
    assert parsed["slugging_percentage"] == 0.646
    assert parsed["ops"] == 1.036


def test_upsert_batter_season_stats_to_postgres(sample_stats_response):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    splits = sample_stats_response["stats"][0]["splits"]
    count = upsert_batter_season_stats_to_postgres(mock_conn, splits, season=2024, ensure_players=True)

    assert count == 2
    assert mock_cursor.executemany.call_count == 2  # 1 for players, 1 for batter_season_stats
    assert mock_conn.commit.call_count == 2

    # Without ensure_players
    mock_conn.reset_mock()
    mock_cursor.reset_mock()
    count = upsert_batter_season_stats_to_postgres(mock_conn, splits, season=2024, ensure_players=False)
    assert count == 2
    assert mock_cursor.executemany.call_count == 1  # only batter_season_stats
    assert mock_conn.commit.call_count == 1


def test_upsert_batter_season_stats_empty():
    mock_conn = MagicMock()
    count = upsert_batter_season_stats_to_postgres(mock_conn, [])
    assert count == 0
    mock_conn.cursor.assert_not_called()


@pytest.fixture
def sample_pitching_response():
    return {
        "stats": [
            {
                "type": {"displayName": "season"},
                "group": {"displayName": "pitching"},
                "totalSplits": 2,
                "splits": [
                    {
                        "season": "2024",
                        "stat": {
                            "gamesPlayed": 32,
                            "gamesPitched": 32,
                            "gamesStarted": 32,
                            "wins": 18,
                            "losses": 3,
                            "era": "2.38",
                            "completeGames": 0,
                            "shutouts": 0,
                            "saves": 0,
                            "saveOpportunities": 0,
                            "holds": 0,
                            "blownSaves": 0,
                            "inningsPitched": "177.2",
                            "outs": 533,
                            "hits": 141,
                            "runs": 51,
                            "earnedRuns": 47,
                            "homeRuns": 9,
                            "baseOnBalls": 41,
                            "intentionalWalks": 0,
                            "strikeOuts": 228,
                            "hitBatsmen": 2,
                            "whip": "1.02",
                            "avg": ".215",
                            "battersFaced": 703,
                            "numberOfPitches": 2724,
                        },
                        "team": {
                            "id": 140,
                            "name": "Texas Rangers",
                        },
                        "player": {
                            "id": 668933,
                            "fullName": "Tarik Skubal",
                        },
                    },
                    {
                        "season": "2024",
                        "stat": {
                            "gamesPlayed": 32,
                            "gamesPitched": 32,
                            "gamesStarted": 32,
                            "wins": 18,
                            "losses": 8,
                            "era": "2.57",
                            "completeGames": 1,
                            "shutouts": 0,
                            "saves": 0,
                            "saveOpportunities": 0,
                            "holds": 0,
                            "blownSaves": 0,
                            "inningsPitched": "185.1",
                            "outs": 556,
                            "hits": 150,
                            "runs": 58,
                            "earnedRuns": 53,
                            "homeRuns": 18,
                            "baseOnBalls": 43,
                            "intentionalWalks": 0,
                            "strikeOuts": 225,
                            "hitBatsmen": 6,
                            "whip": "1.04",
                            "avg": ".219",
                            "battersFaced": 738,
                            "numberOfPitches": 2865,
                        },
                        "team": {
                            "id": 144,
                            "name": "Atlanta Braves",
                        },
                        "player": {
                            "id": 453286,
                            "fullName": "Chris Sale",
                        },
                    },
                ],
            }
        ]
    }


def test_fetch_mlb_pitching_stats(sample_pitching_response):
    with patch("src.mlb_stats.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_pitching_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        splits = fetch_mlb_pitching_stats(season=2024, sport_id=1)

        assert len(splits) == 2
        assert splits[0]["player"]["fullName"] == "Tarik Skubal"
        assert splits[0]["stat"]["wins"] == 18
        assert splits[0]["stat"]["era"] == "2.38"
        mock_get.assert_called_once()


def test_parse_pitcher_season_stat(sample_pitching_response):
    split = sample_pitching_response["stats"][0]["splits"][0]
    parsed = parse_pitcher_season_stat(split, default_season=2024)

    assert parsed["player_id"] == 668933
    assert parsed["year"] == 2024
    assert parsed["wins"] == 18
    assert parsed["losses"] == 3
    assert parsed["era"] == 2.38
    assert parsed["games_pitched"] == 32
    assert parsed["games_started"] == 32
    assert parsed["complete_games"] == 0
    assert parsed["shutouts"] == 0
    assert parsed["saves"] == 0
    assert parsed["save_opportunities"] == 0
    assert parsed["holds"] == 0
    assert parsed["blown_saves"] == 0
    assert parsed["innings_pitched"] == "177.2"
    assert parsed["outs"] == 533
    assert parsed["hits"] == 141
    assert parsed["runs"] == 51
    assert parsed["earned_runs"] == 47
    assert parsed["home_runs"] == 9
    assert parsed["walks"] == 41
    assert parsed["intentional_walks"] == 0
    assert parsed["strikeouts"] == 228
    assert parsed["hit_by_pitch"] == 2
    assert parsed["whip"] == 1.02
    assert parsed["batting_average_against"] == 0.215
    assert parsed["batters_faced"] == 703
    assert parsed["number_of_pitches"] == 2724


def test_upsert_pitcher_season_stats_to_postgres(sample_pitching_response):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    splits = sample_pitching_response["stats"][0]["splits"]
    count = upsert_pitcher_season_stats_to_postgres(mock_conn, splits, season=2024, ensure_players=True)

    assert count == 2
    assert mock_cursor.executemany.call_count == 2  # 1 for players, 1 for pitcher_season_stats
    assert mock_conn.commit.call_count == 2

    # Without ensure_players
    mock_conn.reset_mock()
    mock_cursor.reset_mock()
    count = upsert_pitcher_season_stats_to_postgres(mock_conn, splits, season=2024, ensure_players=False)
    assert count == 2
    assert mock_cursor.executemany.call_count == 1  # only pitcher_season_stats
    assert mock_conn.commit.call_count == 1


def test_upsert_pitcher_season_stats_empty():
    mock_conn = MagicMock()
    count = upsert_pitcher_season_stats_to_postgres(mock_conn, [])
    assert count == 0
    mock_conn.cursor.assert_not_called()
