"""Unit tests for ArticleDeskAgent and OrchestrationPipeline."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from src.article_desk_agent import (
    ArticleDeskAgent,
    DeskAgentResponse,
    DeskPlanProposal,
)
from src.multi_article_service import MultiArticleService
from src.multi_article_synthesizer import (
    ArticleOutline,
    ArticleOutlineSection,
    DataRequirement,
)
from src.orchestration_pipeline import OrchestrationPipeline
from src.postgres_client import Article


def test_parse_desk_response_json():
    """Verify parsing of valid JSON output from desk agent."""
    agent = ArticleDeskAgent(gemini_api_key="dummy")

    json_payload = {
        "reply": "3選手の比較ですね！非常に面白いテーマです。",
        "is_finalized": False,
        "proposal": {
            "title": "2026年 鈴木・村上・岡本 打撃徹底比較",
            "theme": "MLBで激突する3大スラッガーの打撃特性の比較",
            "sections": [
                {
                    "title": "基本指標の対比",
                    "description": "打率、HR、OPSの比較",
                    "material_label": "素材①: 総合生産性",
                }
            ],
            "requirements": [
                {
                    "label": "素材①: 総合生産性",
                    "prompt": "2026年の3選手のOPSを集計",
                    "section_hint": "基本指標の対比",
                }
            ],
        },
    }

    raw_text = f"```json\n{json.dumps(json_payload, ensure_ascii=False)}\n```"

    res = agent._parse_desk_response(raw_text)

    assert "3選手の比較ですね" in res.reply
    assert res.is_finalized is False
    assert res.proposal is not None
    assert res.proposal.title == "2026年 鈴木・村上・岡本 打撃徹底比較"
    assert len(res.proposal.sections) == 1
    assert res.proposal.sections[0].title == "基本指標の対比"
    assert len(res.proposal.requirements) == 1
    assert res.proposal.requirements[0].label == "素材①: 総合生産性"


def test_parse_desk_response_fallback():
    """Verify graceful handling when model does not return valid JSON."""
    agent = ArticleDeskAgent(gemini_api_key="dummy")

    plain_text = "こんにちは！どのような記事を企画したいですか？"
    res = agent._parse_desk_response(plain_text)

    assert res.reply == plain_text
    assert res.proposal is None
    assert res.is_finalized is False


def test_proposal_conversion():
    """Verify conversion from DeskPlanProposal to ArticleOutline and DataRequirement list."""
    sections = [
        ArticleOutlineSection(title="第1章", description="説明", material_label="素材1")
    ]
    reqs = [DataRequirement(label="素材1", prompt="クエリ")]
    proposal = DeskPlanProposal(
        title="テスト記事",
        theme="テーマ",
        sections=sections,
        requirements=reqs,
    )

    outline, requirements = proposal.to_outline_and_requirements()

    assert outline.title == "テスト記事"
    assert outline.theme == "テーマ"
    assert len(outline.sections) == 1
    assert len(requirements) == 1
    assert requirements[0].label == "素材1"


def test_orchestration_pipeline_auto_generate():
    """Verify that pipeline automatically calls MultiArticleService when proposal is finalized."""
    mock_desk_agent = MagicMock(spec=ArticleDeskAgent)
    mock_multi_service = MagicMock(spec=MultiArticleService)

    proposal = DeskPlanProposal(
        title="企画タイトル",
        theme="企画テーマ",
        sections=[ArticleOutlineSection(title="第1章", description="要約")],
        requirements=[DataRequirement(label="素材1", prompt="集計クエリ")],
    )

    mock_desk_response = DeskAgentResponse(
        reply="企画が決定しました！記事を執筆します。",
        proposal=proposal,
        is_finalized=True,
    )
    mock_desk_agent.chat.return_value = mock_desk_response

    mock_created_article = Article(
        id=999,
        title="企画タイトル",
        prompt="企画テーマ",
        content_markdown="# 企画タイトル\n\n本文...",
        model_name="gemini-3.8-flash",
    )
    mock_multi_service.generate_and_save_multi_article.return_value = mock_created_article

    pipeline = OrchestrationPipeline(
        desk_agent=mock_desk_agent,
        multi_article_service=mock_multi_service,
    )

    messages = [{"role": "user", "content": "この構成で記事を書いてください"}]
    progress_calls = []

    def on_progress(stage: str, cur: int, total: int):
        progress_calls.append((stage, cur, total))

    response, article = pipeline.process_chat_and_run(
        messages=messages,
        auto_generate_on_finalize=True,
        progress_callback=on_progress,
    )

    assert response.is_finalized is True
    assert article is not None
    assert article.id == 999
    assert article.title == "企画タイトル"

    mock_multi_service.generate_and_save_multi_article.assert_called_once()
    assert len(progress_calls) == 2
    assert progress_calls[0][0] == "素材収集開始"
    assert progress_calls[1][0] == "記事生成完了"


def test_orchestration_pipeline_not_finalized():
    """Verify that pipeline does not call MultiArticleService when proposal is not yet finalized."""
    mock_desk_agent = MagicMock(spec=ArticleDeskAgent)
    mock_multi_service = MagicMock(spec=MultiArticleService)

    mock_desk_response = DeskAgentResponse(
        reply="切り口としてAとBが考えられます。どちらが良いですか？",
        proposal=None,
        is_finalized=False,
    )
    mock_desk_agent.chat.return_value = mock_desk_response

    pipeline = OrchestrationPipeline(
        desk_agent=mock_desk_agent,
        multi_article_service=mock_multi_service,
    )

    messages = [{"role": "user", "content": "鈴木と村上を比較したい"}]
    response, article = pipeline.process_chat_and_run(messages=messages)

    assert response.is_finalized is False
    assert article is None
    mock_multi_service.generate_and_save_multi_article.assert_not_called()
