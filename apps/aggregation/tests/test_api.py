"""Aggregation REST API の単体テスト"""

import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from src.api import app

client = TestClient(app)


def test_health_check():
    """GET /health で 200 OK が返ることをテスト"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@patch("src.api.pubsub_v1.PublisherClient")
def test_queue_aggregation_success(mock_client_cls):
    """POST /aggregate 正常系: 202 Accepted と message_id が返ることをテスト"""
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.topic_path.return_value = "projects/local-statcast-project/topics/statcast-raw-ingested"

    mock_future = MagicMock()
    mock_future.result.return_value = "msg-api-123"
    mock_client.publish.return_value = mock_future

    payload = {
        "player_id": 660271,
        "year": 2024,
        "player_type": "both",
    }
    response = client.post("/aggregate", json=payload)

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert data["message_id"] == "msg-api-123"
    assert data["data"] == payload

    mock_client.topic_path.assert_called_once_with("local-statcast-project", "statcast-raw-ingested")
    mock_client.publish.assert_called_once()
    args, kwargs = mock_client.publish.call_args
    assert json.loads(kwargs["data"].decode("utf-8")) == payload


@patch("src.api.pubsub_v1.PublisherClient")
def test_queue_aggregation_api_prefix(mock_client_cls):
    """POST /api/aggregate 正常系: ルートプレフィックスありでも 202 Accepted が返ることをテスト"""
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.topic_path.return_value = "projects/local-statcast-project/topics/statcast-raw-ingested"

    mock_future = MagicMock()
    mock_future.result.return_value = "msg-api-456"
    mock_client.publish.return_value = mock_future

    response = client.post("/api/aggregate", json={"player_id": 808963, "player_type": "pitcher"})
    assert response.status_code == 202
    assert response.json()["message_id"] == "msg-api-456"


def test_queue_aggregation_missing_player_id():
    """player_id 欠落時に 422 Unprocessable Entity が返ることをテスト"""
    response = client.post("/aggregate", json={"year": 2024})
    assert response.status_code == 422


def test_queue_aggregation_invalid_player_type():
    """無効な player_type 時に 422 Unprocessable Entity が返ることをテスト"""
    response = client.post(
        "/aggregate",
        json={"player_id": 660271, "player_type": "invalid"},
    )
    assert response.status_code == 422


@patch("src.api.pubsub_v1.PublisherClient")
def test_queue_aggregation_pubsub_error(mock_client_cls):
    """Pub/Sub 通信エラー時に 503 Service Unavailable が返ることをテスト"""
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.publish.side_effect = RuntimeError("Pub/Sub connection refused")

    response = client.post("/aggregate", json={"player_id": 660271})
    assert response.status_code == 503
    assert "Failed to publish aggregation message" in response.json()["detail"]
