"""MLB 試合日程・結果一覧取得および DB 登録モジュールのユニットテスト"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch
import pytest
from src.mlb_games import (
    fetch_mlb_schedule,
    insert_games_to_clickhouse,
    upsert_games_to_postgres,
)


@pytest.fixture
def sample_schedule_response():
    return {
        "dates": [
            {
                "date": "2024-03-20",
                "games": [
                    {
                        "gamePk": 745444,
                        "gameDate": "2024-03-20T10:05:00Z",
                        "officialDate": "2024-03-20",
                        "gameType": "R",
                        "season": "2024",
                        "status": {
                            "detailedState": "Final",
                            "statusCode": "F",
                        },
                        "teams": {
                            "away": {
                                "team": {
                                    "id": 119,
                                    "name": "Los Angeles Dodgers",
                                },
                                "score": 5,
                                "isWinner": True,
                            },
                            "home": {
                                "team": {
                                    "id": 135,
                                    "name": "San Diego Padres",
                                },
                                "score": 2,
                                "isWinner": False,
                            },
                        },
                        "venue": {
                            "id": 2680,
                            "name": "Gocheok Sky Dome",
                        },
                    }
                ],
            }
        ]
    }


def test_fetch_mlb_schedule(sample_schedule_response):
    with patch("src.mlb_games.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_schedule_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        games = fetch_mlb_schedule(
            season=2024,
            sport_id=1,
            start_date="2024-03-20",
            end_date="2024-03-20",
        )

        assert len(games) == 1
        g = games[0]
        assert g["game_pk"] == 745444
        assert g["game_date"] == date(2024, 3, 20)
        assert g["game_date_time"] == datetime.fromisoformat("2024-03-20T10:05:00+00:00")
        assert g["season"] == 2024
        assert g["game_type"] == "R"
        assert g["status"] == "Final"
        assert g["status_code"] == "F"
        assert g["home_team_id"] == 135
        assert g["home_team_name"] == "San Diego Padres"
        assert g["away_team_id"] == 119
        assert g["away_team_name"] == "Los Angeles Dodgers"
        assert g["home_score"] == 2
        assert g["away_score"] == 5
        assert g["is_winner_home"] == 0
        assert g["is_winner_away"] == 1
        assert g["venue_id"] == 2680
        assert g["venue_name"] == "Gocheok Sky Dome"

        mock_get.assert_called_once_with(
            "https://statsapi.mlb.com/api/v1/schedule",
            params={
                "sportId": 1,
                "season": 2024,
                "startDate": "2024-03-20",
                "endDate": "2024-03-20",
            },
            timeout=30,
        )


def test_fetch_mlb_schedule_with_game_type(sample_schedule_response):
    with patch("src.mlb_games.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_schedule_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        games = fetch_mlb_schedule(
            season=2026,
            sport_id=1,
            game_type="R",
        )

        assert len(games) == 1
        mock_get.assert_called_once_with(
            "https://statsapi.mlb.com/api/v1/schedule",
            params={
                "sportId": 1,
                "season": 2026,
                "gameType": "R",
            },
            timeout=30,
        )



def test_insert_games_to_clickhouse():
    mock_client = MagicMock()
    sample_games = [
        {
            "game_pk": 745444,
            "game_date": date(2024, 3, 20),
            "game_date_time": datetime.fromisoformat("2024-03-20T10:05:00+00:00"),
            "season": 2024,
            "game_type": "R",
            "status": "Final",
            "status_code": "F",
            "home_team_id": 135,
            "home_team_name": "San Diego Padres",
            "away_team_id": 119,
            "away_team_name": "Los Angeles Dodgers",
            "home_score": 2,
            "away_score": 5,
            "is_winner_home": 0,
            "is_winner_away": 1,
            "venue_id": 2680,
            "venue_name": "Gocheok Sky Dome",
        }
    ]

    count = insert_games_to_clickhouse(mock_client, sample_games)
    assert count == 1
    mock_client.command.assert_called_once()  # table init
    mock_client.insert.assert_called_once()
    call_args = mock_client.insert.call_args[1]
    assert call_args["table"] == "games"
    assert call_args["database"] == "statcast"
    assert len(call_args["data"]) == 1


def test_insert_games_to_clickhouse_empty():
    mock_client = MagicMock()
    assert insert_games_to_clickhouse(mock_client, []) == 0
    mock_client.insert.assert_not_called()


def test_upsert_games_to_postgres():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    sample_games = [
        {
            "game_pk": 745444,
            "game_date": date(2024, 3, 20),
            "game_date_time": datetime.fromisoformat("2024-03-20T10:05:00+00:00"),
            "season": 2024,
            "game_type": "R",
            "status": "Final",
            "home_team_id": 135,
            "away_team_id": 119,
            "home_score": 2,
            "away_score": 5,
            "venue_id": 2680,
            "venue_name": "Gocheok Sky Dome",
        }
    ]

    count = upsert_games_to_postgres(mock_conn, sample_games)
    assert count == 1
    mock_cursor.executemany.assert_called_once()
    called_data = mock_cursor.executemany.call_args[0][1]
    assert called_data[0]["game_pk"] == 745444
    assert called_data[0]["game_date_time"] == datetime.fromisoformat("2024-03-20T10:05:00+00:00")
    assert called_data[0]["home_team_id"] == 135
    assert called_data[0]["away_team_id"] == 119
    assert "game_date" not in called_data[0]
    assert "venue_id" not in called_data[0]
    mock_conn.commit.assert_called_once()


def test_upsert_games_to_postgres_empty():
    mock_conn = MagicMock()
    assert upsert_games_to_postgres(mock_conn, []) == 0
    mock_conn.cursor.assert_not_called()
