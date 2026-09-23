"""Pub/Sub メッセージ発行機能の単体テスト"""

import json
from unittest.mock import MagicMock, patch
import pytest

from src.batch_statcast import extract_year_from_dates, ingest_player_statcast
from src.publisher import publish_statcast_raw_message


def test_extract_year_from_dates():
    """日付文字列からの年抽出テスト"""
    assert extract_year_from_dates("2024-04-01", "2024-04-10") == 2024
    assert extract_year_from_dates(None, "2023-10-01") == 2023
    assert extract_year_from_dates("2022-01-01", None) == 2022
    assert extract_year_from_dates(None, None) is None
    assert extract_year_from_dates("abc", "def") is None


@patch("src.publisher.pubsub_v1.PublisherClient")
def test_publish_statcast_raw_message_success(mock_client_cls):
    """正常系: Pub/Sub トピックへのメッセージ発行テスト"""
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.topic_path.return_value = "projects/local-statcast-project/topics/statcast-raw-ingested"

    mock_future = MagicMock()
    mock_future.result.return_value = "msg-12345"
    mock_client.publish.return_value = mock_future

    msg_id = publish_statcast_raw_message(
        player_id=660271,
        year=2024,
        player_type="both",
    )

    assert msg_id == "msg-12345"
    mock_client.topic_path.assert_called_once_with("local-statcast-project", "statcast-raw-ingested")

    # publish されたペイロードの検証
    mock_client.publish.assert_called_once()
    args, kwargs = mock_client.publish.call_args
    assert args[0] == "projects/local-statcast-project/topics/statcast-raw-ingested"
    payload = json.loads(kwargs["data"].decode("utf-8"))
    assert payload == {
        "player_id": 660271,
        "year": 2024,
        "player_type": "both",
    }


def test_publish_statcast_raw_message_invalid_player_type():
    """無効な player_type の場合、発行がスキップされて None が返ることをテスト"""
    msg_id = publish_statcast_raw_message(
        player_id=660271,
        year=2024,
        player_type="invalid_type",
    )
    assert msg_id is None


@patch("src.publisher.pubsub_v1.PublisherClient")
def test_publish_statcast_raw_message_failure_fallback(mock_client_cls):
    """Pub/Sub クライアント例外発生時でもエラーを送出せず None を返すテスト (フォールバック)"""
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.publish.side_effect = RuntimeError("Pub/Sub connection refused")

    msg_id = publish_statcast_raw_message(
        player_id=660271,
        year=2024,
        player_type="batter",
    )
    assert msg_id is None


@patch("src.batch_statcast.publish_statcast_raw_message")
@patch("src.batch_statcast.insert_statcast_data", return_value=50)
@patch("src.batch_statcast.download_statcast_csv")
def test_ingest_player_statcast_triggers_pubsub(
    mock_download, mock_insert, mock_publish
):
    """データ投入成功時 (inserted > 0) に Pub/Sub メッセージが発行されるテスト"""
    mock_download.return_value = MagicMock(empty=False)
    mock_client = MagicMock()

    rows = ingest_player_statcast(
        ch_client=mock_client,
        player_id=660271,
        player_name="Shohei Ohtani",
        player_type="both",
        start_date="2024-04-01",
        end_date="2024-04-10",
        enable_pubsub=True,
    )

    assert rows == 50
    mock_publish.assert_called_once_with(
        player_id=660271,
        year=2024,
        player_type="both",
    )


@patch("src.batch_statcast.publish_statcast_raw_message")
@patch("src.batch_statcast.insert_statcast_data", return_value=50)
@patch("src.batch_statcast.download_statcast_csv")
def test_ingest_player_statcast_pubsub_disabled(
    mock_download, mock_insert, mock_publish
):
    """enable_pubsub=False の場合、Pub/Sub メッセージが発行されないテスト"""
    mock_download.return_value = MagicMock(empty=False)
    mock_client = MagicMock()

    rows = ingest_player_statcast(
        ch_client=mock_client,
        player_id=660271,
        player_name="Shohei Ohtani",
        player_type="both",
        start_date="2024-04-01",
        end_date="2024-04-10",
        enable_pubsub=False,
    )

    assert rows == 50
    mock_publish.assert_not_called()


@patch("src.batch_statcast.publish_statcast_raw_message")
@patch("src.batch_statcast.download_statcast_csv", return_value=None)
def test_ingest_player_statcast_zero_rows_no_pubsub(mock_download, mock_publish):
    """データが0件（該当なし）の場合、Pub/Sub メッセージが発行されないテスト"""
    mock_client = MagicMock()

    rows = ingest_player_statcast(
        ch_client=mock_client,
        player_id=808963,
        player_name="Roki Sasaki",
        player_type="batter",
        enable_pubsub=True,
    )

    assert rows == 0
    mock_publish.assert_not_called()
