"""MLB Boxscore 取得および ClickHouse 登録モジュールのユニットテスト"""

from unittest.mock import MagicMock, patch
import pytest
from src.mlb_boxscores import (
    fetch_and_insert_boxscore,
    fetch_and_insert_boxscores_batch,
    fetch_mlb_boxscore,
    initialize_clickhouse_boxscore_tables,
    insert_boxscore_to_clickhouse,
    parse_boxscore_data,
    safe_float,
    safe_int,
)


@pytest.fixture
def sample_boxscore_response():
    return {
        "teams": {
            "away": {
                "team": {
                    "id": 143,
                    "name": "Philadelphia Phillies",
                },
                "teamStats": {
                    "batting": {
                        "flyOuts": 9,
                        "groundOuts": 8,
                        "airOuts": 10,
                        "runs": 7,
                        "doubles": 1,
                        "triples": 1,
                        "homeRuns": 0,
                        "strikeOuts": 8,
                        "baseOnBalls": 9,
                        "intentionalWalks": 0,
                        "hits": 7,
                        "hitByPitch": 0,
                        "avg": ".241",
                        "atBats": 32,
                        "obp": ".312",
                        "slg": ".397",
                        "ops": ".709",
                        "caughtStealing": 0,
                        "stolenBases": 0,
                        "groundIntoDoublePlay": 1,
                        "plateAppearances": 42,
                        "totalBases": 10,
                        "rbi": 7,
                        "leftOnBase": 17,
                        "sacBunts": 0,
                        "sacFlies": 1,
                    },
                    "pitching": {
                        "runs": 2,
                        "doubles": 1,
                        "triples": 0,
                        "homeRuns": 1,
                        "strikeOuts": 8,
                        "baseOnBalls": 0,
                        "hits": 10,
                        "numberOfPitches": 149,
                        "era": "4.00",
                        "inningsPitched": "9.0",
                        "earnedRuns": 2,
                        "whip": "1.29",
                        "battersFaced": 37,
                        "outs": 27,
                        "pitchesThrown": 149,
                        "balls": 41,
                        "strikes": 108,
                        "strikePercentage": ".720",
                    },
                    "fielding": {
                        "assists": 6,
                        "putOuts": 27,
                        "errors": 0,
                        "chances": 33,
                    },
                },
                "pitchers": [650911, 621237],
                "players": {
                    "ID669016": {
                        "person": {
                            "id": 669016,
                            "fullName": "Brandon Marsh",
                        },
                        "jerseyNumber": "16",
                        "position": {
                            "code": "7",
                            "name": "Outfielder",
                            "type": "Outfielder",
                            "abbreviation": "LF",
                        },
                        "allPositions": [
                            {"code": "7", "name": "Outfielder", "type": "Outfielder", "abbreviation": "LF"},
                            {"code": "8", "name": "Outfielder", "type": "Outfielder", "abbreviation": "CF"},
                        ],
                        "battingOrder": "700",
                        "gameStatus": {"isSubstitute": False},
                        "stats": {
                            "batting": {
                                "summary": "1-4 | 3 K, R",
                                "gamesPlayed": 1,
                                "runs": 1,
                                "doubles": 0,
                                "triples": 0,
                                "homeRuns": 0,
                                "strikeOuts": 3,
                                "baseOnBalls": 0,
                                "hits": 1,
                                "atBats": 4,
                                "plateAppearances": 4,
                                "totalBases": 1,
                                "rbi": 0,
                                "leftOnBase": 0,
                            },
                        },
                    },
                    "ID650911": {
                        "person": {
                            "id": 650911,
                            "fullName": "Cristopher Sánchez",
                        },
                        "jerseyNumber": "61",
                        "position": {
                            "code": "1",
                            "name": "Pitcher",
                            "type": "Pitcher",
                            "abbreviation": "P",
                        },
                        "allPositions": [
                            {"code": "1", "name": "Pitcher", "type": "Pitcher", "abbreviation": "P"},
                        ],
                        "stats": {
                            "pitching": {
                                "note": "(W, 18-6)",
                                "summary": "6.1 IP, 2 ER, 6 K, 0 BB",
                                "gamesPlayed": 1,
                                "gamesStarted": 1,
                                "runs": 2,
                                "doubles": 0,
                                "triples": 0,
                                "homeRuns": 1,
                                "strikeOuts": 6,
                                "baseOnBalls": 0,
                                "hits": 6,
                                "numberOfPitches": 98,
                                "inningsPitched": "6.1",
                                "wins": 1,
                                "losses": 0,
                                "earnedRuns": 2,
                                "battersFaced": 25,
                                "outs": 19,
                                "pitchesThrown": 98,
                                "balls": 27,
                                "strikes": 71,
                                "strikePercentage": ".720",
                            },
                        },
                    },
                },
            },
            "home": {
                "team": {
                    "id": 121,
                    "name": "New York Mets",
                },
                "teamStats": {
                    "batting": {
                        "runs": 2,
                        "hits": 10,
                        "atBats": 37,
                    },
                    "pitching": {
                        "runs": 7,
                        "hits": 7,
                        "inningsPitched": "9.0",
                    },
                    "fielding": {
                        "putOuts": 27,
                    },
                },
                "pitchers": [111111],
                "players": {
                    "ID222222": {
                        "person": {
                            "id": 222222,
                            "fullName": "Francisco Lindor",
                        },
                        "jerseyNumber": "12",
                        "position": {
                            "code": "6",
                            "name": "Shortstop",
                            "type": "Infielder",
                            "abbreviation": "SS",
                        },
                        "battingOrder": "100",
                        "gameStatus": {"isSubstitute": False},
                        "stats": {
                            "batting": {
                                "summary": "2-4 | HR, 2 RBI",
                                "gamesPlayed": 1,
                                "runs": 1,
                                "hits": 2,
                                "homeRuns": 1,
                                "rbi": 2,
                                "atBats": 4,
                            },
                        },
                    },
                },
            },
        }
    }


def test_safe_helpers():
    assert safe_int("123") == 123
    assert safe_int(None) == 0
    assert safe_int("abc", default=99) == 99

    assert safe_float(".241") == 0.241
    assert safe_float(None) is None
    assert safe_float(".---") is None
    assert safe_float("invalid", default=0.0) == 0.0


def test_fetch_mlb_boxscore(sample_boxscore_response):
    with patch("src.mlb_boxscores.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_boxscore_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        data = fetch_mlb_boxscore(game_pk=823570)
        assert "teams" in data
        assert "away" in data["teams"]
        mock_get.assert_called_once_with(
            "https://statsapi.mlb.com/api/v1/game/823570/boxscore", timeout=30
        )


def test_parse_boxscore_data(sample_boxscore_response):
    team_rows, batting_rows, pitching_rows, position_rows = parse_boxscore_data(
        game_pk=823570, raw_boxscore=sample_boxscore_response
    )

    # 1. チーム成績の検証
    assert len(team_rows) == 2
    away_team = next(t for t in team_rows if t["is_home"] == 0)
    assert away_team["game_pk"] == 823570
    assert away_team["team_id"] == 143
    assert away_team["team_name"] == "Philadelphia Phillies"
    assert away_team["runs"] == 7
    assert away_team["hits"] == 7
    assert away_team["avg"] == 0.241
    assert away_team["pitching_runs"] == 2
    assert away_team["fielding_put_outs"] == 27

    home_team = next(t for t in team_rows if t["is_home"] == 1)
    assert home_team["team_id"] == 121
    assert home_team["runs"] == 2

    # 2. 個人打撃成績の検証
    assert len(batting_rows) == 2  # Marsh & Lindor
    marsh = next(b for b in batting_rows if b["player_id"] == 669016)
    assert marsh["game_pk"] == 823570
    assert marsh["team_id"] == 143
    assert marsh["player_name"] == "Brandon Marsh"
    assert marsh["jersey_number"] == "16"
    assert marsh["position_abbreviation"] == "LF"
    assert marsh["all_positions"] == ["LF", "CF"]
    assert "all_position_codes" not in marsh
    assert marsh["batting_order"] == "700"
    assert marsh["is_starter"] == 1
    assert marsh["is_substitute"] == 0
    assert marsh["hits"] == 1
    assert marsh["strike_outs"] == 3
    assert marsh["summary"] == "1-4 | 3 K, R"

    lindor = next(b for b in batting_rows if b["player_id"] == 222222)
    assert lindor["team_id"] == 121
    assert lindor["home_runs"] == 1
    # allPositions 未指定時のフォールバック検証
    assert lindor["all_positions"] == ["SS"]

    # 3. 個人投球成績の検証
    assert len(pitching_rows) == 1  # Sánchez
    sanchez = pitching_rows[0]
    assert sanchez["game_pk"] == 823570
    assert sanchez["player_id"] == 650911
    assert sanchez["player_name"] == "Cristopher Sánchez"
    assert sanchez["all_positions"] == ["P"]
    assert "all_position_codes" not in sanchez
    assert sanchez["pitching_order"] == 1
    assert sanchez["is_starter"] == 1
    assert sanchez["innings_pitched"] == "6.1"
    assert sanchez["strike_outs"] == 6
    assert sanchez["earned_runs"] == 2
    assert sanchez["wins"] == 1
    assert sanchez["note"] == "(W, 18-6)"

    # 4. 守備位置詳細テーブルの検証
    # Marsh (LF, CF), Sánchez (P), Lindor (SS) -> 計4行
    assert len(position_rows) == 4
    marsh_pos = [p for p in position_rows if p["player_id"] == 669016]
    assert len(marsh_pos) == 2
    assert marsh_pos[0]["position_order"] == 1
    assert marsh_pos[0]["position_abbreviation"] == "LF"
    assert marsh_pos[0]["position_code"] == "7"
    assert marsh_pos[1]["position_order"] == 2
    assert marsh_pos[1]["position_abbreviation"] == "CF"
    assert marsh_pos[1]["position_code"] == "8"

    sanchez_pos = [p for p in position_rows if p["player_id"] == 650911]
    assert len(sanchez_pos) == 1
    assert sanchez_pos[0]["position_abbreviation"] == "P"
    assert sanchez_pos[0]["position_code"] == "1"


def test_initialize_clickhouse_boxscore_tables():
    mock_client = MagicMock()
    initialize_clickhouse_boxscore_tables(mock_client)
    assert mock_client.command.call_count == 4


def test_insert_boxscore_to_clickhouse():
    mock_client = MagicMock()
    team_rows = [{"game_pk": 823570, "team_id": 143, "runs": 7}]
    batting_rows = [{"game_pk": 823570, "player_id": 669016, "hits": 1}]
    pitching_rows = [{"game_pk": 823570, "player_id": 650911, "strike_outs": 6}]
    position_rows = [{"game_pk": 823570, "player_id": 669016, "position_order": 1, "position_code": "7"}]

    counts = insert_boxscore_to_clickhouse(
        mock_client, team_rows, batting_rows, pitching_rows, position_rows
    )

    assert counts == {"teams": 1, "batting": 1, "pitching": 1, "positions": 1}
    assert mock_client.insert.call_count == 4
    insert_tables = [call[1]["table"] for call in mock_client.insert.call_args_list]
    assert "boxscore_teams" in insert_tables
    assert "boxscore_batting" in insert_tables
    assert "boxscore_pitching" in insert_tables
    assert "boxscore_positions" in insert_tables


def test_fetch_and_insert_boxscore(sample_boxscore_response):
    mock_client = MagicMock()
    with patch("src.mlb_boxscores.fetch_mlb_boxscore", return_value=sample_boxscore_response):
        counts = fetch_and_insert_boxscore(mock_client, game_pk=823570)
        assert counts["teams"] == 2
        assert counts["batting"] == 2
        assert counts["pitching"] == 1
        assert counts["positions"] == 4


def test_fetch_and_insert_boxscores_batch(sample_boxscore_response):
    mock_client = MagicMock()
    with patch("src.mlb_boxscores.fetch_mlb_boxscore", return_value=sample_boxscore_response):
        total = fetch_and_insert_boxscores_batch(mock_client, game_pks=[823570, 823571])
        assert total["games"] == 2
        assert total["teams"] == 4
        assert total["batting"] == 4
        assert total["pitching"] == 2
        assert total["positions"] == 8
