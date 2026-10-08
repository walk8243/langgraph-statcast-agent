"""Multi-material article synthesis engine using Google Gemini LLM."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from google import genai
from google.genai import types
import pandas as pd

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class DataRequirement:
    """Requirement for a single piece of fact/data material."""

    label: str
    prompt: str
    section_hint: Optional[str] = None


@dataclass
class CollectedMaterial:
    """Collected data material from Text-to-SQL + ClickHouse."""

    label: str
    prompt: str
    sql: str
    df: Optional[pd.DataFrame] = None
    row_count: int = 0
    error: Optional[str] = None
    section_hint: Optional[str] = None


@dataclass
class ArticleOutlineSection:
    """Section in an article outline."""

    title: str
    description: str
    material_label: Optional[str] = None


@dataclass
class ArticleOutline:
    """Article outline and theme guiding multi-material synthesis."""

    title: str
    theme: str
    sections: List[ArticleOutlineSection] = field(default_factory=list)


class MultiDataArticleSynthesizer:
    """Synthesizes comprehensive analytical articles from multiple data materials."""

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
                logger.warning(f"Could not initialize Gemini client: {e}")

    def _build_multi_article_prompt(
        self,
        outline: ArticleOutline,
        materials: List[CollectedMaterial],
    ) -> str:
        """Construct synthesis prompt from outline and multiple collected data materials."""
        # Format sections guideline
        sections_text = ""
        if outline.sections:
            for idx, sec in enumerate(outline.sections, start=1):
                mat_hint = f" (参照素材: {sec.material_label})" if sec.material_label else ""
                sections_text += f"{idx}. **{sec.title}**{mat_hint}\n   - 着眼点・論点: {sec.description}\n"
        else:
            sections_text = "（特定の章立て指定なし。分析テーマに最適な章構成を自律的に構築してください）"

        # Format materials
        materials_text = ""
        for idx, mat in enumerate(materials, start=1):
            table_preview = ""
            if mat.df is not None and not mat.df.empty:
                table_preview = mat.df.head(25).to_markdown(index=False)
            elif mat.error:
                table_preview = f"（集計エラー: {mat.error}）"
            else:
                table_preview = "（集計データなし / 0件）"

            materials_text += f"""
---
#### 素材 {idx}: {mat.label}
- **収集プロンプト**: {mat.prompt}
- **実行SQL**:
```sql
{mat.sql}
```
- **集計結果 ({mat.row_count} 件)**:
{table_preview}
"""

        prompt = f"""
あなたはメジャーリーグベースボール（MLB）および Statcast データ分析の専門スポーツライター・アナリストです。
以下の企画構成（アウトライン）と複数のデータベース集計素材（ファクト）に基づいて、読者を惹きつける立体感と説得力のある日本語の総合解説記事（Markdown 形式）を作成してください。

### 記事企画情報:
- **仮タイトル / テーマ**: {outline.title}
- **企画意図・主旨**: {outline.theme}

### 指定された章構成（アウトライン）:
{sections_text}

### 収集されたデータ素材一覧:
{materials_text}

### 記事作成のガイドライン・構成要件:
1. **タイトル**: 記事の1行目に `# <キャッチーで内容が具体的に伝わるタイトル>` を記述してください（仮タイトルをブラッシュアップしても構いません）。
2. **導入・エグゼクティブサマリー**:
   - `## 概要・エグゼクティブサマリー`
   - 記事全体の背景、何が判明したかの主要な発見・ハイライト（箇条書き）
3. **本編（章立て）**:
   - 上記アウトラインに沿って各章を展開してください（見出しは `## <章タイトル>`）。
   - 各章には、該当するデータ素材の集計結果表（Markdown テーブル）を必ず埋め込んでください。
   - 単に表を載せるだけでなく、各指標（打球初速、バレル率、球種別適応度など）の意味を解説し、選手同士やリーグ平均との比較考察を深く記述してください。
4. **結論・展望**:
   - `## まとめと今後の展望`
   - 複数の素材から導き出される総合的な考察、今後の注目ポイントや戦術的示唆。
5. **厳守ルール**:
   - **数値の忠実性**: 提供された集計結果の数値に絶対に従い、架空の数字を捏造しないこと。
   - **客観性とドラマの両立**: データに基づく客観的な裏付けと、野球ファンがワクワクするストーリー性・読み応えを両立させること。
   - **整形**: Markdown の見出し（`##`, `###`）、強調（`**太字**`）、箇条書き（`- `）、表（Markdown テーブル）を適切に活用すること。

それでは、完成した総合解説記事の Markdown 全文を出力してください。
""".strip()
        return prompt

    def generate_article(
        self,
        outline: ArticleOutline,
        materials: List[CollectedMaterial],
    ) -> Tuple[str, str, str]:
        """Synthesize article from outline and multiple materials.

        Returns:
            Tuple of (title, markdown_content, model_used)
        """
        if not self._gemini_client:
            raise RuntimeError("Gemini API key is not configured or client failed to initialize.")

        prompt = self._build_multi_article_prompt(outline, materials)

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
        model_used = self.gemini_model

        for model_name in candidate_models:
            try:
                response = self._gemini_client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                    ),
                )
                if response and response.text:
                    model_used = model_name
                    break
            except Exception as e:
                logger.warning(
                    f"Failed to generate multi-article with {model_name} ({e}), trying fallback..."
                )
                last_error = e

        if not response or not response.text:
            raise RuntimeError(
                f"All candidate models failed to generate multi-article. Last error: {last_error}"
            )

        markdown = response.text.strip()

        # Extract title from first line (# Title)
        title = outline.title
        match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
        if match:
            title = match.group(1).strip()

        return title, markdown, model_used
