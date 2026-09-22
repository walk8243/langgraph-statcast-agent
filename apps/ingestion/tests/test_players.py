"""MLB 選手一覧取得および Statcast バッチ登録モジュールのユニットテスト"""

from unittest.mock import MagicMock, patch
import pandas as pd
import pytest
from src.batch_statcast import (
    get_registered_players,
    ingest_all_players_statcast,
    ingest_player_statcast,
)
from src.mlb_players import (
    fetch_mlb_players,
    insert_players_to_clickhouse,
    upsert_players_to_postgres,
)


@pytest.fixture
def sample_mlb_players_response():
    return {
        "people": [
            {
                "id": 671096,
                "fullName": "Andrew Abbott",
                "firstName": "Andrew",
                "lastName": "Abbott",
                "lastFirstName": "Abbott, Andrew",
                "primaryNumber": "41",
                "active": True,
                "currentTeam": {"id": 113, "name": "Cincinnati Reds"},
                "primaryPosition": {
                    "code": "1",
                    "name": "Pitcher",
                    "type": "Pitcher",
                    "abbreviation": "P",
                },
                "batSide": {"code": "L"},
                "pitchHand": {"code": "L"},
            },
            {
                "id": 682928,
                "fullName": "CJ Abrams",
                "firstName": "Paul",
                "lastName": "Abrams",
                "lastFirstName": "Abrams, CJ",
                "primaryNumber": "5",
                "active": True,
                "currentTeam": {"id": 120, "name": "Washington Nationals"},
                "primaryPosition": {
                    "code": "6",
                    "name": "Shortstop",
                    "type": "Infielder",
                    "abbreviation": "SS",
                },
                "batSide": {"code": "L"},
                "pitchHand": {"code": "R"},
            },
        ]
    }


def test_fetch_mlb_players(sample_mlb_players_response):
    with patch("src.mlb_players.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_mlb_players_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        players = fetch_mlb_players(season=2024, sport_id=1)

        assert len(players) == 2
        p1 = players[0]
        assert p1["player_id"] == 671096
        assert p1["full_name"] == "Andrew Abbott"
        assert p1["last_first_name"] == "Abbott, Andrew"
        assert p1["current_team_id"] == 113
        assert p1["primary_position_code"] == "1"
        assert p1["primary_position_abbreviation"] == "P"
        assert p1["bat_side"] == "L"
        assert p1["pitch_hand"] == "L"
        assert p1["active"] == 1

        mock_get.assert_called_once_with(
            "https://statsapi.mlb.com/api/v1/sports/1/players",
            params={"season": 2024},
            timeout=30,
        )


def test_insert_players_to_clickhouse():
    mock_client = MagicMock()
    sample_players = [
        {
            "player_id": 671096,
            "full_name": "Andrew Abbott",
            "first_name": "Andrew",
            "last_name": "Abbott",
            "last_first_name": "Abbott, Andrew",
            "primary_number": "41",
            "current_team_id": 113,
            "primary_position_code": "1",
            "primary_position_name": "Pitcher",
            "primary_position_type": "Pitcher",
            "primary_position_abbreviation": "P",
            "bat_side": "L",
            "pitch_hand": "L",
            "active": 1,
        }
    ]

    count = insert_players_to_clickhouse(mock_client, sample_players)
    assert count == 1
    mock_client.command.assert_called_once()  # table init
    mock_client.insert.assert_called_once()
    call_args = mock_client.insert.call_args[1]
    assert call_args["table"] == "players"
    assert call_args["database"] == "statcast"
    assert len(call_args["data"]) == 1


def test_insert_players_to_clickhouse_empty():
    mock_client = MagicMock()
    assert insert_players_to_clickhouse(mock_client, []) == 0
    mock_client.insert.assert_not_called()


def test_upsert_players_to_postgres():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    sample_players = [
        {
            "player_id": 671096,
            "full_name": "Andrew Abbott",
            "last_first_name": "Abbott, Andrew",
        }
    ]

    count = upsert_players_to_postgres(mock_conn, sample_players)
    assert count == 1
    mock_cursor.executemany.assert_called_once()
    mock_conn.commit.assert_called_once()


def test_upsert_players_to_postgres_empty():
    mock_conn = MagicMock()
    assert upsert_players_to_postgres(mock_conn, []) == 0
    mock_conn.cursor.assert_not_called()


def test_get_registered_players():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        {"player_id": 660271, "name_en": "Ohtani, Shohei"},
        {"player_id": 808967, "name_en": "Yamamoto, Yoshinobu"},
    ]

    players = get_registered_players(mock_conn, limit=2)
    assert len(players) == 2
    assert players[0]["player_id"] == 660271
    mock_cursor.execute.assert_called_once_with(
        "SELECT player_id, name_en FROM players ORDER BY player_id LIMIT 2"
    )


def test_ingest_player_statcast_with_data():
    mock_client = MagicMock()
    fake_df = pd.DataFrame([{"pitch_type": "FF", "release_speed": 98.5}])

    with patch("src.batch_statcast.download_statcast_csv", return_value=fake_df):
        with patch("src.batch_statcast.insert_statcast_data", return_value=1) as mock_insert:
            rows = ingest_player_statcast(
                ch_client=mock_client,
                player_id=660271,
                player_name="Ohtani, Shohei",
                player_type="pitcher",
                start_date="2024-04-01",
                end_date="2024-04-07",
            )
            assert rows == 1
            mock_insert.assert_called_once_with(mock_client, fake_df)


def test_ingest_player_statcast_empty_skip():
    mock_client = MagicMock()
    empty_df = pd.DataFrame()

    with patch("src.batch_statcast.download_statcast_csv", return_value=empty_df):
        with patch("src.batch_statcast.insert_statcast_data") as mock_insert:
            rows = ingest_player_statcast(
                ch_client=mock_client,
                player_id=673548,
                player_name="Suzuki, Seiya",
                player_type="pitcher",  # 投手登板なし
            )
            # エラーにならず安全に0件スキップされること
            assert rows == 0
            mock_insert.assert_not_called()


def test_ingest_all_players_statcast():
    mock_conn = MagicMock()
    mock_client = MagicMock()

    fake_players = [
        {"player_id": 660271, "name_en": "Ohtani, Shohei"},
        {"player_id": 673548, "name_en": "Suzuki, Seiya"},
    ]

    with patch("src.batch_statcast.get_registered_players", return_value=fake_players):
        with patch("src.batch_statcast.ingest_player_statcast", side_effect=[10, 5, 0, 15]):
            summary = ingest_all_players_statcast(
                pg_conn=mock_conn,
                ch_client=mock_client,
                player_type="both",
                sleep_sec=0.0,
            )
            assert summary["total_players"] == 2
            assert summary["total_inserted"] == 30  # 10 + 5 + 0 + 15
