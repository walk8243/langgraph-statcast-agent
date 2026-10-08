"""Unit tests for MultiDataArticleSynthesizer and MultiArticleService."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from src.multi_article_service import MultiArticleService, MultiArticleServiceError
from src.multi_article_synthesizer import (
    ArticleOutline,
    ArticleOutlineSection,
    CollectedMaterial,
    DataRequirement,
    MultiDataArticleSynthesizer,
)
from src.postgres_client import PostgresClient
from src.text_to_sql import TextToSqlEngine, TextToSqlResult


def test_multi_synthesizer_prompt_construction():
    """Verify that multi-article prompt contains outline, sections, and multiple tables."""
    synthesizer = MultiDataArticleSynthesizer(gemini_api_key="dummy")

    outline = ArticleOutline(
        title="2026年 3選手打撃比較",
        theme="鈴木、村上、岡本の打撃特性の多角的な比較",
        sections=[
            ArticleOutlineSection(
                title="基本スタッツ比較",
                description="打率とOPSの比較",
                material_label="素材1: 基本指標",
            ),
            ArticleOutlineSection(
                title="打球初速とバレル率",
                description="パワーと打球質の比較",
                material_label="素材2: 打球質",
            ),
        ],
    )

    df1 = pd.DataFrame([{"player": "Suzuki", "ops": 0.850}, {"player": "Murakami", "ops": 0.920}])
    df2 = pd.DataFrame([{"player": "Suzuki", "barrel_pct": 12.5}, {"player": "Murakami", "barrel_pct": 16.2}])

    materials = [
        CollectedMaterial(
            label="素材1: 基本指標",
            prompt="2026年 鈴木と村上のOPS集計",
            sql="SELECT player, ops FROM stats",
            df=df1,
            row_count=2,
        ),
        CollectedMaterial(
            label="素材2: 打球質",
            prompt="2026年 鈴木と村上のバレル率集計",
            sql="SELECT player, barrel_pct FROM statcast",
            df=df2,
            row_count=2,
        ),
    ]

    prompt = synthesizer._build_multi_article_prompt(outline, materials)

    assert "2026年 3選手打撃比較" in prompt
    assert "鈴木、村上、岡本の打撃特性の多角的な比較" in prompt
    assert "基本スタッツ比較" in prompt
    assert "打球初速とバレル率" in prompt
    assert "素材 1: 素材1: 基本指標" in prompt
    assert "素材 2: 素材2: 打球質" in prompt
    assert "0.85" in prompt
    assert "16.2" in prompt
    assert "## 概要・エグゼクティブサマリー" in prompt
    assert "## まとめと今後の展望" in prompt


@patch.object(MultiDataArticleSynthesizer, "generate_article")
def test_multi_synthesizer_mock(mock_generate):
    """Test MultiDataArticleSynthesizer return values with mock."""
    mock_generate.return_value = (
        "日米スラッガー徹底比較レポート",
        "# 日米スラッガー徹底比較レポート\n\n## 概要\n- 考察内容",
        "gemini-3.8-flash",
    )
    synthesizer = MultiDataArticleSynthesizer(gemini_api_key="dummy")
    title, md, model = synthesizer.generate_article(
        ArticleOutline(title="test", theme="test"),
        [],
    )
    assert title == "日米スラッガー徹底比較レポート"
    assert "概要" in md
    assert model == "gemini-3.8-flash"


def test_collect_materials():
    """Verify material collection with mix of success and failure."""
    mock_sql_engine = MagicMock(spec=TextToSqlEngine)

    df = pd.DataFrame([{"player": "Suzuki", "hr": 30}])
    # 1st call: success
    # 2nd call: execution error
    mock_sql_engine.process.side_effect = [
        TextToSqlResult(
            question="q1",
            generated_sql="SELECT hr FROM table1",
            is_valid=True,
            dataframe=df,
            row_count=1,
        ),
        TextToSqlResult(
            question="q2",
            generated_sql="SELECT invalid FROM table2",
            is_valid=True,
            execution_error="Table not found",
        ),
    ]

    service = MultiArticleService(text_to_sql_engine=mock_sql_engine)

    requirements = [
        DataRequirement(label="req1", prompt="q1"),
        DataRequirement(label="req2", prompt="q2"),
    ]

    materials = service.collect_materials(requirements)

    assert len(materials) == 2
    assert materials[0].label == "req1"
    assert materials[0].row_count == 1
    assert materials[0].df is not None
    assert materials[0].error is None

    assert materials[1].label == "req2"
    assert materials[1].row_count == 0
    assert materials[1].df is None
    assert "Execution Error" in materials[1].error


def test_format_combined_sql_and_summary():
    """Verify combined SQL formatting and summary construction."""
    service = MultiArticleService()

    df = pd.DataFrame([{"colA": 1, "colB": 2}])
    materials = [
        CollectedMaterial(
            label="素材1",
            prompt="p1",
            sql="SELECT colA, colB FROM table1;",
            df=df,
            row_count=1,
        ),
        CollectedMaterial(
            label="素材2",
            prompt="p2",
            sql="SELECT colC FROM table2;",
            df=None,
            row_count=0,
            error="Connection timeout",
        ),
    ]

    combined_sql = service.format_combined_sql(materials)
    assert "-- [素材 1: 素材1]" in combined_sql
    assert "SELECT colA, colB FROM table1;" in combined_sql
    assert "-- [素材 2: 素材2]" in combined_sql
    assert "-- 状態: エラー (Connection timeout)" in combined_sql

    summary = service.build_execution_summary(materials)
    assert summary["type"] == "multi_material"
    assert summary["total_materials"] == 2
    assert summary["successful_materials"] == 1
    assert summary["total_rows_collected"] == 1
    assert summary["materials"][0]["columns"] == ["colA", "colB"]
    assert summary["materials"][1]["success"] is False


def test_multi_article_service_end_to_end_mock():
    """Test full multi-article generation workflow with mocked dependencies."""
    mock_sql_engine = MagicMock(spec=TextToSqlEngine)
    mock_synthesizer = MagicMock(spec=MultiDataArticleSynthesizer)
    mock_postgres = MagicMock(spec=PostgresClient)

    df1 = pd.DataFrame([{"player": "Suzuki", "avg": 0.285}])
    mock_sql_engine.process.return_value = TextToSqlResult(
        question="q1",
        generated_sql="SELECT player, avg FROM stats",
        is_valid=True,
        dataframe=df1,
        row_count=1,
    )

    mock_synthesizer.generate_article.return_value = (
        "鈴木誠也 2026年打撃進化論",
        "# 鈴木誠也 2026年打撃進化論\n\n## 概要\n進化の軌跡",
        "gemini-3.8-flash",
    )

    mock_postgres.save_article.return_value = 205

    service = MultiArticleService(
        text_to_sql_engine=mock_sql_engine,
        synthesizer=mock_synthesizer,
        postgres_client=mock_postgres,
    )

    outline = ArticleOutline(
        title="鈴木誠也 打撃分析",
        theme="2026年シーズンのアプローチと打撃傾向",
        sections=[
            ArticleOutlineSection(title="打撃成績", description="基礎指標の確認", material_label="素材1")
        ],
    )
    requirements = [DataRequirement(label="素材1", prompt="鈴木誠也の打率")]

    article = service.generate_and_save_multi_article(outline, requirements)

    assert article.id == 205
    assert article.title == "鈴木誠也 2026年打撃進化論"
    assert article.model_name == "gemini-3.8-flash"
    assert "素材 1: 素材1" in article.generated_sql

    summary = json.loads(article.execution_summary)
    assert summary["total_materials"] == 1
    assert summary["successful_materials"] == 1

    mock_postgres.save_article.assert_called_once()


def test_multi_article_service_all_materials_fail():
    """Verify that MultiArticleService raises error if all material collections fail."""
    mock_sql_engine = MagicMock(spec=TextToSqlEngine)
    mock_synthesizer = MagicMock(spec=MultiDataArticleSynthesizer)
    mock_postgres = MagicMock(spec=PostgresClient)

    mock_sql_engine.process.return_value = TextToSqlResult(
        question="bad query",
        generated_sql="INVALID SQL",
        is_valid=False,
        validation_error="Invalid syntax",
    )

    service = MultiArticleService(
        text_to_sql_engine=mock_sql_engine,
        synthesizer=mock_synthesizer,
        postgres_client=mock_postgres,
    )

    outline = ArticleOutline(title="Fail Test", theme="Test")
    requirements = [DataRequirement(label="req1", prompt="bad query")]

    with pytest.raises(MultiArticleServiceError) as exc_info:
        service.generate_and_save_multi_article(outline, requirements)

    assert "All data material extractions failed" in str(exc_info.value)
    mock_synthesizer.generate_article.assert_not_called()
    mock_postgres.save_article.assert_not_called()
