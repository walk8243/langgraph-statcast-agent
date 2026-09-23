from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
import pytest

from src.main import app, publisher
from src.publisher import TriggerPublisher

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "statcast-raw-ingested" in data["topic"]


@patch.object(publisher, "publish_aggregate_request", return_value="test-message-id-12345")
def test_trigger_aggregate_success(mock_publish):
    payload = {
        "player_id": 660271,
        "year": 2024,
        "player_type": "batter",
    }
    response = client.post("/aggregate", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert data["message_id"] == "test-message-id-12345"
    assert data["data"]["player_id"] == 660271
    assert data["data"]["year"] == 2024
    assert data["data"]["player_type"] == "batter"
    mock_publish.assert_called_once_with(
        player_id=660271,
        year=2024,
        player_type="batter",
    )


@patch.object(publisher, "publish_aggregate_request", return_value="test-msg-api-path")
def test_trigger_aggregate_api_path(mock_publish):
    payload = {
        "player_id": 660271,
    }
    response = client.post("/api/aggregate", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["message_id"] == "test-msg-api-path"
    assert data["data"]["player_type"] == "both"
    assert data["data"]["year"] is None
    mock_publish.assert_called_once_with(
        player_id=660271,
        year=None,
        player_type="both",
    )


def test_trigger_aggregate_invalid_player_id():
    response = client.post("/aggregate", json={"player_id": -1})
    assert response.status_code == 422


def test_trigger_aggregate_invalid_player_type():
    response = client.post(
        "/aggregate",
        json={"player_id": 660271, "player_type": "invalid"},
    )
    assert response.status_code == 422


@patch.object(publisher, "publish_aggregate_request", side_effect=RuntimeError("Pub/Sub error"))
def test_trigger_aggregate_server_error(mock_publish):
    response = client.post("/aggregate", json={"player_id": 660271})
    assert response.status_code == 500
    assert "Pub/Sub error" in response.json()["detail"]


@patch("src.publisher.pubsub_v1.PublisherClient")
def test_trigger_publisher_class(mock_publisher_cls):
    mock_pub_instance = MagicMock()
    mock_publisher_cls.return_value = mock_pub_instance
    mock_pub_instance.topic_path.return_value = "projects/test-proj/topics/test-topic"

    future_mock = MagicMock()
    future_mock.result.return_value = "pub-msg-999"
    mock_pub_instance.publish.return_value = future_mock

    pub = TriggerPublisher(project_id="test-proj", topic_id="test-topic")
    msg_id = pub.publish_aggregate_request(player_id=123456, year=2023, player_type="pitcher")

    assert msg_id == "pub-msg-999"
    mock_pub_instance.publish.assert_called_once()
    call_args, call_kwargs = mock_pub_instance.publish.call_args
    assert call_args[0] == "projects/test-proj/topics/test-topic"
    assert b"123456" in call_kwargs["data"]
