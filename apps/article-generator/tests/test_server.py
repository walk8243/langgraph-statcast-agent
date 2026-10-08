"""Unit tests for FastAPI Article Generator server endpoints."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
import pytest

from src.article_desk_agent import DeskAgentResponse, DeskPlanProposal
from src.multi_article_synthesizer import ArticleOutlineSection, DataRequirement
from src.server import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@patch("src.server.ArticleDeskAgent")
def test_desk_chat_success(mock_desk_cls: MagicMock) -> None:
    mock_agent = MagicMock()
    mock_desk_cls.return_value = mock_agent

    mock_agent.chat.return_value = DeskAgentResponse(
        reply="大谷選手の打球品質について分析しましょう。",
        is_finalized=False,
        proposal=DeskPlanProposal(
            title="大谷翔平 2026年打球分析",
            theme="打球速度とバレル率の推移",
            sections=[
                ArticleOutlineSection(
                    title="セクション1",
                    description="概要",
                    material_label="素材1",
                )
            ],
            requirements=[
                DataRequirement(
                    label="素材1",
                    prompt="大谷翔平のバレル率",
                    section_hint="セクション1",
                )
            ],
        ),
    )

    payload = {
        "messages": [
            {"role": "user", "content": "大谷翔平の打球品質について書きたい"}
        ]
    }
    response = client.post("/api/desk/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "大谷選手の打球品質について分析しましょう。"
    assert data["is_finalized"] is False
    assert data["proposal"]["title"] == "大谷翔平 2026年打球分析"
    assert len(data["proposal"]["sections"]) == 1
    assert len(data["proposal"]["requirements"]) == 1


def test_desk_chat_empty_messages() -> None:
    response = client.post("/api/desk/chat", json={"messages": []})
    assert response.status_code == 400


@patch("src.server.MultiArticleService")
def test_desk_generate_success(mock_service_cls: MagicMock) -> None:
    mock_service = MagicMock()
    mock_service_cls.return_value = mock_service

    mock_article = MagicMock()
    mock_article.id = 42
    mock_article.title = "大谷翔平 2026年打球分析"
    mock_article.model_name = "gemini-3.5-flash-lite"
    mock_service.generate_and_save_multi_article.return_value = mock_article

    payload = {
        "proposal": {
            "title": "大谷翔平 2026年打球分析",
            "theme": "打球速度とバレル率",
            "sections": [
                {
                    "title": "セクション1",
                    "description": "概要",
                    "material_label": "素材1",
                }
            ],
            "requirements": [
                {
                    "label": "素材1",
                    "prompt": "大谷翔平のバレル率",
                    "section_hint": "セクション1",
                }
            ],
        }
    }
    response = client.post("/api/desk/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["article_id"] == 42
    assert data["title"] == "大谷翔平 2026年打球分析"


def test_desk_generate_no_requirements() -> None:
    payload = {
        "proposal": {
            "title": "タイトル",
            "theme": "テーマ",
            "sections": [],
            "requirements": [],
        }
    }
    response = client.post("/api/desk/generate", json=payload)
    assert response.status_code == 400
