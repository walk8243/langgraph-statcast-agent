"""MLB チーム取得・登録モジュールのユニットテスト"""

from unittest.mock import MagicMock, patch
import pytest
from src.mlb_teams import fetch_mlb_teams, upsert_teams


@pytest.fixture
def sample_mlb_teams_response():
    return {
        "teams": [
            {
                "id": 141,
                "name": "Toronto Blue Jays",
                "abbreviation": "TOR",
                "teamName": "Blue Jays",
                "locationName": "Toronto",
                "active": True,
                "league": {"id": 103, "name": "American League"},
                "division": {"id": 201, "name": "American League East"},
                "venue": {"id": 14, "name": "Rogers Centre"},
            },
            {
                "id": 110,
                "name": "Baltimore Orioles",
                "abbreviation": "BAL",
                "teamName": "Orioles",
                "locationName": "Baltimore",
                "active": True,
                "league": {"id": 103, "name": "American League"},
                "division": {"id": 201, "name": "American League East"},
                "venue": {"id": 2, "name": "Oriole Park at Camden Yards"},
            },
        ]
    }


def test_fetch_mlb_teams(sample_mlb_teams_response):
    with patch("src.mlb_teams.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_mlb_teams_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        teams = fetch_mlb_teams(sport_id=1)

        assert len(teams) == 2
        tor = teams[0]
        assert tor["team_id"] == 141
        assert tor["name"] == "Toronto Blue Jays"
        assert tor["abbreviation"] == "TOR"
        assert tor["team_name"] == "Blue Jays"
        assert tor["location_name"] == "Toronto"
        assert tor["league_id"] == 103
        assert tor["league_name"] == "American League"
        assert tor["division_id"] == 201
        assert tor["division_name"] == "American League East"
        assert tor["venue_id"] == 14
        assert tor["venue_name"] == "Rogers Centre"
        assert tor["active"] is True

        mock_get.assert_called_once_with(
            "https://statsapi.mlb.com/api/v1/teams",
            params={"sportId": 1},
            timeout=30,
        )


def test_upsert_teams():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    sample_teams = [
        {
            "team_id": 141,
            "name": "Toronto Blue Jays",
            "abbreviation": "TOR",
            "team_name": "Blue Jays",
            "location_name": "Toronto",
            "league_id": 103,
            "league_name": "American League",
            "division_id": 201,
            "division_name": "American League East",
            "venue_id": 14,
            "venue_name": "Rogers Centre",
            "active": True,
        }
    ]

    result = upsert_teams(mock_conn, sample_teams)
    assert result == 1
    mock_cursor.executemany.assert_called_once()
    mock_conn.commit.assert_called_once()


def test_upsert_teams_empty():
    mock_conn = MagicMock()
    result = upsert_teams(mock_conn, [])
    assert result == 0
    mock_conn.cursor.assert_not_called()
