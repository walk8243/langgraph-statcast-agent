"""Cloud Pub/Sub サブスクライバー常駐処理の単体テスト"""

import json
from unittest.mock import MagicMock, patch
import pytest
from pydantic import ValidationError

from src.subscriber import (
    AggregationMessage,
    create_message_callback,
    process_aggregation_payload,
)


def test_aggregation_message_validation_success():
    """正常なパラメータで AggregationMessage が作成・検証できることをテスト"""
    msg = AggregationMessage(player_id=660271, year=2024, player_type="both")
    msg.validate_player_type()
    assert msg.player_id == 660271
    assert msg.year == 2024
    assert msg.player_type == "both"

    # year なし
    msg2 = AggregationMessage(player_id=660271, player_type="batter")
    msg2.validate_player_type()
    assert msg2.year is None
    assert msg2.player_type == "batter"


def test_aggregation_message_validation_invalid_type():
    """無効な player_type の場合に ValueError が送出されることをテスト"""
    msg = AggregationMessage(player_id=660271, player_type="invalid_type")
    with pytest.raises(ValueError, match="Invalid player_type"):
        msg.validate_player_type()


def test_aggregation_message_missing_player_id():
    """player_id が欠落している場合に ValidationError が送出されることをテスト"""
    with pytest.raises(ValidationError):
        AggregationMessage.model_validate({"year": 2024, "player_type": "batter"})


@patch("src.subscriber.aggregate_pitcher_statcast")
@patch("src.subscriber.aggregate_batter_statcast")
def test_process_aggregation_payload_both(mock_batter, mock_pitcher):
    """player_type='both' の場合に打者と投手の両方の集計処理が呼び出されることをテスト"""
    payload = json.dumps({"player_id": 660271, "year": 2024, "player_type": "both"}).encode("utf-8")
    result = process_aggregation_payload(payload)

    assert result is True
    mock_batter.assert_called_once_with(player_id=660271, year=2024)
    mock_pitcher.assert_called_once_with(player_id=660271, year=2024)


@patch("src.subscriber.aggregate_pitcher_statcast")
@patch("src.subscriber.aggregate_batter_statcast")
def test_process_aggregation_payload_batter_only(mock_batter, mock_pitcher):
    """player_type='batter' の場合に打者指標のみ集計が呼び出されることをテスト"""
    payload = json.dumps({"player_id": 673548, "year": 2024, "player_type": "batter"}).encode("utf-8")
    result = process_aggregation_payload(payload)

    assert result is True
    mock_batter.assert_called_once_with(player_id=673548, year=2024)
    mock_pitcher.assert_not_called()


@patch("src.subscriber.aggregate_pitcher_statcast")
@patch("src.subscriber.aggregate_batter_statcast")
def test_process_aggregation_payload_pitcher_only(mock_batter, mock_pitcher):
    """player_type='pitcher' の場合に投手指標のみ集計が呼び出されることをテスト"""
    payload = json.dumps({"player_id": 808963, "year": None, "player_type": "pitcher"}).encode("utf-8")
    result = process_aggregation_payload(payload)

    assert result is True
    mock_batter.assert_not_called()
    mock_pitcher.assert_called_once_with(player_id=808963, year=None)


def test_process_aggregation_payload_invalid_json():
    """不正な JSON ペイロードの場合、エラーにならず ACK (True) を返すことをテスト (Poison Pill 回避)"""
    payload = b"not a json text"
    result = process_aggregation_payload(payload)
    assert result is True


def test_process_aggregation_payload_validation_error():
    """バリデーションエラーとなる JSON の場合、ACK (True) を返すことをテスト"""
    payload = json.dumps({"year": 2024}).encode("utf-8")  # player_id 欠落
    result = process_aggregation_payload(payload)
    assert result is True


@patch("src.subscriber.aggregate_batter_statcast", side_effect=RuntimeError("DB error"))
def test_process_aggregation_payload_transient_error(mock_batter):
    """集計処理中に例外が発生した場合、再試行のため False を返すことをテスト"""
    payload = json.dumps({"player_id": 660271, "year": 2024, "player_type": "batter"}).encode("utf-8")
    result = process_aggregation_payload(payload)
    assert result is False


@patch("src.subscriber.process_aggregation_payload", return_value=True)
def test_create_message_callback_ack(mock_process):
    """集計処理成功時に message.ack() が呼ばれることをテスト"""
    callback = create_message_callback()
    mock_msg = MagicMock()
    mock_msg.message_id = "test-msg-123"
    mock_msg.data = b'{"player_id": 660271}'

    callback(mock_msg)

    mock_process.assert_called_once_with(mock_msg.data)
    mock_msg.ack.assert_called_once()
    mock_msg.nack.assert_not_called()


@patch("src.subscriber.process_aggregation_payload", return_value=False)
def test_create_message_callback_nack(mock_process):
    """集計処理失敗時に message.nack() が呼ばれることをテスト"""
    callback = create_message_callback()
    mock_msg = MagicMock()
    mock_msg.message_id = "test-msg-456"
    mock_msg.data = b'{"player_id": 660271}'

    callback(mock_msg)

    mock_process.assert_called_once_with(mock_msg.data)
    mock_msg.ack.assert_not_called()
    mock_msg.nack.assert_called_once()
