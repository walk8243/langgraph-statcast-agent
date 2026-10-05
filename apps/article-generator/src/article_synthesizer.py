"""Article synthesis engine using Google Gemini LLM."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from google import genai
from google.genai import types
import pandas as pd

from src.config import settings

logger = logging.getLogger(__name__)


class ArticleSynthesizer:
    """Generates structured Markdown analytical articles based on query results and themes."""

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

    def _build_article_prompt(
        self,
        user_prompt: str,
        sql: str,
        df: pd.DataFrame,
    ) -> str:
        """Construct prompt for article synthesis."""
        data_preview = ""
        if df is not None and not df.empty:
            # Markdown table representation of top results
            data_preview = df.head(30).to_markdown(index=False)
            total_rows = len(df)
        else:
            data_preview = "（集計データなし / 0件）"
            total_rows = 0

        prompt = f"""
あなたはメジャーリーグベースボール（MLB）および Statcast データ分析の専門スポーツライター・アナリストです。
以下の集計結果データとユーザーのお題に基づいて、読者を惹きつける高品質で詳細な日本語の解説記事（Markdown 形式）を作成してください。

### 記事のお題 / 分析テーマ:
{user_prompt}

### 実行された ClickHouse 集計 SQL:
```sql
{sql}
```

### データベース集計結果 ({total_rows} 件):
{data_preview}

### 記事作成のガイドライン・構成要件:
1. **タイトル**: 記事の1行目に `# <キャッチーで内容が具体的に伝わるタイトル>` を記述してください。
2. **構成**:
   - `## 概要・エグゼクティブサマリー`: 記事の要点、主要な発見（3〜4個の箇条書きハイライト）
   - `## 集計データ一覧`: 上記データを整形した Markdown テーブル
   - `## 詳細考察・データが示すポイント`:
     - 際立った数値やトレンドの要因分析
     - Statcast の指標（打球初速、角度、球種傾向など）が持つ意味の解説
     - 球団や選手の背景事情・戦術的意図の考察
   - `## まとめと今後の展望`: 分析の結論と注目ポイント
3. **ルール**:
   - 提供された集計結果の数値に忠実であること（架空のデータを捏造しない）。
   - 野球ファンやデータ分析に関心がある読者が興味深く読める、プロフェッショナルで丁寧なトーン。
   - 見出し（`##`, `###`）、箇条書き（`- `）、強調（`**ボールド**`）、表（Markdown テーブル）を適切に活用すること。

それでは、記事の Markdown 全文を出力してください。
""".strip()
        return prompt

    def generate_article(
        self,
        user_prompt: str,
        sql: str,
        df: pd.DataFrame,
    ) -> Tuple[str, str, str]:
        """Synthesize article from data.

        Returns:
            Tuple of (title, markdown_content, model_used)
        """
        if not self._gemini_client:
            raise RuntimeError("Gemini API key is not configured or client failed to initialize.")

        prompt = self._build_article_prompt(user_prompt, sql, df)

        candidate_models = [self.gemini_model]
        for fallback in ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash", "gemini-3.7-flash"]:
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
                logger.warning(f"Failed to generate article with {model_name} ({e}), trying fallback...")
                last_error = e

        if not response or not response.text:
            raise RuntimeError(f"All candidate models failed to generate article. Last error: {last_error}")

        markdown = response.text.strip()

        # Extract title from first line (# Title)
        title = user_prompt
        match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
        if match:
            title = match.group(1).strip()

        return title, markdown, model_used
