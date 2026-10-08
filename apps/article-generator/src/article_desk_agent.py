"""Article desk agent supporting interactive planning and research requirements formulation."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from google import genai
from google.genai import types

from src.config import settings
from src.multi_article_synthesizer import (
    ArticleOutline,
    ArticleOutlineSection,
    DataRequirement,
)

logger = logging.getLogger(__name__)


@dataclass
class DeskPlanProposal:
    """Structured proposal crafted by the editorial desk agent."""

    title: str
    theme: str
    sections: List[ArticleOutlineSection] = field(default_factory=list)
    requirements: List[DataRequirement] = field(default_factory=list)

    def to_outline_and_requirements(
        self,
    ) -> Tuple[ArticleOutline, List[DataRequirement]]:
        """Convert to ArticleOutline and DataRequirement list for MultiArticleService."""
        outline = ArticleOutline(
            title=self.title,
            theme=self.theme,
            sections=self.sections,
        )
        return outline, self.requirements


@dataclass
class DeskAgentResponse:
    """Response returned by ArticleDeskAgent."""

    reply: str
    proposal: Optional[DeskPlanProposal] = None
    is_finalized: bool = False
    raw_response: Optional[str] = None


class ArticleDeskAgent:
    """Editorial Desk Agent that brainstorms, plans, and structures research queries with user."""

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        gemini_model: Optional[str] = None,
    ):
        self.gemini_api_key = gemini_api_key or settings.gemini_api_key
        self.gemini_model = gemini_model or settings.gemini_model

        self._gemini_client: Optional[genai.Client] = None
        if self.gemini_api_key:
            try:
                self._gemini_client = genai.Client(api_key=self.gemini_api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Gemini client for DeskAgent: {e}")

    def _build_system_instruction(self) -> str:
        return """
あなたはメジャーリーグベースボール（MLB）および Statcast データ分析専門メディアの「シニア編集デスク（チーフアナリスト）」AIです。
ライター（ユーザー）が持ち込んできた記事のテーマ・アイデアに対して、読者を魅了する多角的な解説記事になるよう対話的に壁打ちを行い、企画・アウトライン・取材データ項目を策定します。

### あなたの役割・振る舞い:
1. **アイデアの深掘りと切り口の提示**:
   - ユーザーのお題に対し、単なる打率・本塁打の平均比較にとどまらず、Statcast 特有の指標（バレル率、打球初速、対速球/変化球適応度、打球方向など）を交えた興味深い着眼点を2〜3個提案し、どこに焦点を当てるか対話します。
2. **企画構成（アウトライン）と取材リストの策定**:
   - 記事を3〜4章程度の立体的な構成にまとめ、各章を裏付ける「取材データ収集指示（Text-to-SQLでClickHouseから集計する自然言語クエリ）」を具体的に策定します。
3. **対話的ブラッシュアップ**:
   - ユーザーのフィードバック（「剛速球への適応をハイライトしたい」「〇〇選手も加えて」など）を受け入れ、柔軟に企画書を更新します。
4. **企画確定の判定**:
   - ユーザーが「これでOK」「執筆して」「生成して」「進めて」などと合意・生成を希望した場合、あるいは企画が十分に合意に至った場合は、`is_finalized: true` に設定します。

### 出力フォーマット:
回答は必ず以下の JSON オブジェクトのみを出力してください（Markdown の ```json ブロックで囲んでください）:
```json
{
  "reply": "ユーザーへの親しみやすくプロフェッショナルな対話メッセージ（日本語）",
  "is_finalized": false,
  "proposal": {
    "title": "仮タイトル（または確定タイトル）",
    "theme": "記事の全体テーマ・分析主旨",
    "sections": [
      {
        "title": "章のタイトル（例: 2026年シーズン基本スタッツと生産性の比較）",
        "description": "この章で検証・論考する内容",
        "material_label": "素材①: 総合生産性"
      }
    ],
    "requirements": [
      {
        "label": "素材①: 総合生産性",
        "prompt": "Text-to-SQLに渡す具体的なデータ集計指示（例: 2026年の鈴木誠也、村上宗隆、岡本和真のPA, AVG, HR, RBI, OPS, wOBAを集計）",
        "section_hint": "2026年シーズン基本スタッツと生産性の比較"
      }
    ]
  }
}
```
""".strip()

    def chat(self, messages: List[Dict[str, str]]) -> DeskAgentResponse:
        """Process chat conversation history and return desk agent reply and proposal.

        messages is a list of {"role": "user" | "assistant", "content": "..."}
        """
        if not self._gemini_client:
            raise RuntimeError("Gemini API key is not configured or client failed to initialize.")

        system_instruction = self._build_system_instruction()

        # Build prompt from conversation history
        conv_text = "これまでの編集部での対話履歴:\n"
        for m in messages:
            role_name = "ライター（ユーザー）" if m.get("role") == "user" else "編集デスク（あなた）"
            conv_text += f"{role_name}: {m.get('content', '')}\n"

        prompt = f"""
{conv_text}

上記の対話履歴を踏まえ、シニア編集デスクとして次の返答および最新の企画書ドラフトを JSON 形式で出力してください。
""".strip()

        candidate_models = [self.gemini_model]
        for fallback in [
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.8-flash",
            "gemini-3.7-flash",
        ]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        response = None
        last_error = None

        for model_name in candidate_models:
            try:
                response = self._gemini_client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.4,
                    ),
                )
                if response and response.text:
                    break
            except Exception as e:
                logger.warning(f"DeskAgent failed with {model_name} ({e}), trying fallback...")
                last_error = e

        if not response or not response.text:
            raise RuntimeError(f"DeskAgent failed across all candidate models. Last error: {last_error}")

        return self._parse_desk_response(response.text)

    def _parse_desk_response(self, text: str) -> DeskAgentResponse:
        """Parse JSON response from Gemini model."""
        clean_text = text.strip()

        # Extract ```json ... ``` block if present
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean_text)
        if match:
            clean_text = match.group(1).strip()

        try:
            data = json.loads(clean_text)
        except Exception as e:
            logger.warning(f"Could not parse desk agent response as JSON: {e}. Raw text: {text}")
            return DeskAgentResponse(
                reply=text,
                proposal=None,
                is_finalized=False,
                raw_response=text,
            )

        reply = data.get("reply", "")
        is_finalized = bool(data.get("is_finalized", False))

        proposal_raw = data.get("proposal")
        proposal = None
        if proposal_raw and isinstance(proposal_raw, dict):
            title = proposal_raw.get("title", "Statcast 企画レポート")
            theme = proposal_raw.get("theme", "")

            sections = [
                ArticleOutlineSection(
                    title=s.get("title", ""),
                    description=s.get("description", ""),
                    material_label=s.get("material_label"),
                )
                for s in proposal_raw.get("sections", [])
            ]

            requirements = [
                DataRequirement(
                    label=r.get("label", f"素材 {idx + 1}"),
                    prompt=r.get("prompt", ""),
                    section_hint=r.get("section_hint"),
                )
                for idx, r in enumerate(proposal_raw.get("requirements", []))
            ]

            proposal = DeskPlanProposal(
                title=title,
                theme=theme,
                sections=sections,
                requirements=requirements,
            )

        return DeskAgentResponse(
            reply=reply,
            proposal=proposal,
            is_finalized=is_finalized,
            raw_response=text,
        )
