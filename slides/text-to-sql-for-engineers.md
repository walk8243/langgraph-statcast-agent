---
marp: true
theme: statcast-blue
paginate: true
header: "Text-to-SQL 実践導入と新サービス展開提案"
footer: "MLB Statcast Agent Project"
---

<!-- _class: lead -->
<!-- _header: "" -->
<!-- _footer: "" -->

# Text-to-SQL 実践導入と
### 既存データからの新サービス展開提案

LLM と OLAP / RAG の融合がひらく、データ活用アーキテクチャの現在地

---

## 本日のアジェンダ

1. **背景と狙い：蓄積された既存データを「攻めの新サービス」へ**
2. **システムアーキテクチャ（4層レイヤーの全体像）**
3. **コンポーネント構成一覧**
4. **コア設計：Vanna.ai 思想の採用と独自実装の理由**
5. **単一クエリの動作シーケンス**
6. **実装で直面した技術的課題・頑張りどころ（ClickHouse / DB制約）**
7. **単発の限界と「多段オーケストレーション」への進化**
8. **新サービス展開のアイデア提案・ディスカッション**

---

## 背景と狙い：眠っているデータを「攻め」の武器に

### 現場の課題と新サービスへの転換

<div class="columns-2">

<div class="card">
<h3>既存のデータ活用の限界</h3>
<ul>
  <li>膨大なログや生データ（OLAP）が蓄積されているが、SQL が書ける一部の人間しか引き出せない。</li>
  <li>定型ダッシュボードは「過去の把握」に留まり、新しい切り口の分析やコンテンツ生成に繋がりにくい。</li>
</ul>
</div>

<div class="card">
<h3>Text-to-SQL が拓く新展開</h3>
<ul>
  <li>自然言語で即座にデータ集計・比較・抽出が可能に。</li>
  <li>LLM と繋ぎ込むことで、<strong>「データ抽出 ➜ 考察・ライティング ➜ 公開」まで完全自律化</strong>。</li>
  <li>社内業務の効率化だけでなく、<strong>エンドユーザー向けの新機能</strong>として提供可能。</li>
</ul>
</div>

</div>

---

## システムアーキテクチャ（4層レイヤーの全体像）

Text-to-SQL をプロダクション品質で稼働させるための 4 階層構造

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 知識・RAG層 (Qdrant)                                     │
│    - テーブル定義 (DDL) / ドメイン知識 (Doc) / クエリ例 (Few-shot)  │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. 推論・生成層 (LLM + TextToSqlEngine)                     │
│    - プロンプト合成 (厳格制約注入) / モデルフォールバック機構         │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. 安全性・検証層 (sqlparse)                                │
│    - AST構文解析 / SELECT・WITH限定 / 危険キーワード・複数文遮断      │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. データ実行層 (ClickHouse / OLAP)                         │
│    - 型キャスト整合 / ReplacingMergeTree FINAL / CTE粒度分離集約      │
└─────────────────────────────────────────────────────────────┘
```

---

## コンポーネント構成一覧

| コンポーネント | 採用技術・位置づけ | 役割・選定理由 |
| :--- | :--- | :--- |
| **Text-to-SQL 基盤** | **Vanna.ai 思想 ＋ 独自実装** | RAG パターンを骨格とし、ClickHouse 固有制約を内包したカスタムエンジン |
| **ベクトル DB (RAG)** | **Qdrant** | DDL、ドキュメント、サンプル SQL のベクトル検索（Embedding モデル対応） |
| **推論 LLM** | **Google Gemini / OpenAI / Claude 等** | 自然言語からの SQL 生成、解説記事執筆<br>※本実装では Gemini を採用。OpenAI や Anthropic 等でも同様に実装可能 |
| **OLAP データストア** | **ClickHouse** | 大規模な投球・打球・試合データの高速集計（ReplacingMergeTree） |
| **永続化 RDB** | **PostgreSQL** | 生成記事、実行 SQL、メタデータの永続化 |
| **フロントエンド** | **Next.js** | 対話型チャット画面 (`/articles/desk`)、Markdown 表示 |

---

## コア設計：Vanna.ai 思想の採用と独自実装の理由

### Vanna.ai（デファクトスタンダード）の RAG パターンを採用

- **Vanna.ai の設計思想**:
  - DDL（スキーマ）、Documentation（業務ルール）、SQL Examples（お手本）の **3 要素をベクトル DB に蓄積し、質問に応じて動的検索・プロンプト注入**する標準手法。
- **なぜライブラリ直接利用ではなく独自エンジン（`TextToSqlEngine`）にしたのか？**:
  1. **ClickHouse 特有の厳格な制約注入**: 型キャスト、`FINAL` 修飾子、BBE 母数定義など高度なドメインルールの確実なプロンプト制御。
  2. **LLM の柔軟な切り替えとフォールバック**: モデル高負荷時や API エラー時における別モデルへの自動切り替えや温度調整。
  3. **厳格な多重セキュリティ検証**: `sqlparse` による AST 解析と実行前チェック。

---

## 単一クエリの動作シーケンス

```
Caller (CLI/Agent)   TextToSqlEngine       Qdrant              LLM           ClickHouse
       │                    │                 │                 │                │
       │── 1. 質問入力 ────>│                 │                 │                │
       │                    │── 2. RAG検索 ──>│                 │                │
       │                    │<── DDL/Doc/SQL ─│                 │                │
       │                    │                                   │                │
       │                    │── 3. プロンプト生成 (制約注入) ──>│                │
       │                    │<── 4. 生成された SQL ─────────────│                │
       │                    │                                   │                │
       │                    │── 5. 安全性検証 (sqlparse)        │                │
       │                    │── 6. クエリ実行 ──────────────────────────────────>│
       │                    │<── 7. 集計結果 (pandas DataFrame) ─────────────────│
       │<── 8. 結果返却 ────│
```

---

## 技術的な頑張りどころ ①：型厳格性とキャスト

### ClickHouse の JOIN ON 条件は符号の有無まで完全一致が必須！

- **問題**:
  - `statcast.statcast_raw` の `game_pk`, `batter`, `pitcher` は **`Int64` (符号あり)**
  - `statcast.players.player_id` や `statcast.games.game_pk` は **`UInt64` (符号なし)**
  - 単純に `ON s.batter = p.player_id` と書くと **型不一致で実行時エラー！**

<div class="card">
<h3>解決策：プロンプトおよびナレッジベースでの明示的キャスト強制</h3>
<pre><code>-- プロンプトにルールを徹底的に学習
JOIN statcast.players p ON toUInt64(s.batter) = p.player_id
JOIN statcast.games g ON toUInt64(s.game_pk) = g.game_pk</code></pre>
</div>

---

## 技術的な頑張りどころ ②：ReplacingMergeTree と FINAL

### `FINAL` を忘れるとデータが 2 倍以上に増殖（ファンアウト）！

- **問題**:
  - `players` や `games`、`boxscore_*` は `ReplacingMergeTree` を採用。
  - バックグラウンドで非同期マージされるため、未マージの間は同一 ID のレコードが複数行物理的に存在。
  - そのまま JOIN すると、同一打席や本塁打数が **2倍、3倍に重複カウントされる致命的なバグ** に。

<div class="card">
<h3>解決策：テーブルエイリアス直前への <code>FINAL</code> 修飾子の強制</h3>
<pre><code>FROM statcast.boxscore_batting bb FINAL
JOIN statcast.players p FINAL ON bb.player_id = p.player_id
JOIN statcast.games g FINAL ON toUInt64(bb.game_pk) = g.game_pk</code></pre>
</div>

---

## 技術的な頑張りどころ ③：集計母数（BBE）と試合区分

### ドメイン知識をルール化しないと「一見動くが間違った数字」が出る！

<div class="columns-2">

<div class="card">
<h3>インプレー打球（BBE）の母数定義</h3>
<ul>
  <li>平均初速や HardHit% の公式母数はファウルを含まないインプレー打球のみ。</li>
  <li><code>WHERE type = 'X' AND launch_speed IS NOT NULL</code> を必須条件としてプロンプトに注入。</li>
</ul>
</div>

<div class="card">
<h3>試合区分（game_type）の限定</h3>
<ul>
  <li><code>s.game_year = 2026</code> だけだとオープン戦やポストシーズンが混入。</li>
  <li><code>games</code> を結合し、<code>g.season = 2026 AND g.game_type = 'R'</code> を強制。</li>
</ul>
</div>

</div>

> **「文法的に正しい SQL」ではなく「ドメイン的に正しい SQL」を生成させるのが肝！**

---

## 技術的な頑張りどころ ④：テーブル粒度不一致の結合防止

### 異なる粒度のテーブルを直接 JOIN してはならない！

- `boxscore_batting`: **1選手・1試合あたり 1 行**
- `statcast_raw`: **1投球あたり 1 行 (pitch-by-pitch)**（1試合約15〜25投球）
- ❌ **直接 JOIN すると、打席数や安打数が投球数分（約20倍）に爆発する！**

<div class="card">
<h3>解決策：CTE（Common Table Expressions）による事前集約ルールの学習</h3>
<pre><code>WITH batting_stats AS (
    SELECT bb.player_id, sum(bb.hits) AS h ... FROM boxscore_batting bb FINAL GROUP BY ...
),
statcast_metrics AS (
    SELECT toUInt64(s.batter) AS player_id, avg(s.launch_speed) ... FROM statcast_raw s GROUP BY ...
)
SELECT * FROM batting_stats b LEFT JOIN statcast_metrics m ON b.player_id = m.player_id</code></pre>
</div>

---

## 安全性ガードレール：`sqlparse` による検証

### LLM が生成したクエリをそのまま DB で実行するのは厳禁！

```python
# src/clickhouse_client.py での検証ロジック
parsed = sqlparse.parse(cleaned_sql)
if len(parsed) > 1:
    return False, "Multiple statements are not permitted"  # セミコロン連結インジェクション遮断

first_token = tokens[0].value.upper()
if first_token not in ("SELECT", "WITH"):
    return False, "Only SELECT or WITH queries are permitted"  # 読み取り専用に限定

# 破壊的・システムキーワードの全トークン検査
DANGEROUS_KEYWORDS = {"DROP", "TRUNCATE", "ALTER", "DELETE", "UPDATE", "INSERT", "CREATE", ...}
for token in stmt.flatten():
    if token.value.upper() in DANGEROUS_KEYWORDS:
        return False, f"Disallowed keyword detected: {token.value}"
```

---

## 単発の限界：「1プロンプト ➜ 1SQL」のボトルネック

### Issue #54 の初期導入で見えた壁

1. **「問い（仮説・ストーリー）」の欠落**:
   - いきなり「3選手を比較して」と投げると、LLM は無難な平均値テーブルを 1 本出力するだけ。
2. **1本の SQL で表現できる情報密度の限界**:
   - 「基礎指標」「打球質（Barrel%）」「対速球適応度」「打球方向」を 1 本の SQL で集計するのは無理がある（SQL が破綻するか、集計粒度が崩れる）。
3. **データ集計とライティングの責務混同**:
   - 1 つのプロンプトで集計と記事構成を同時にやらせると、LLM は安全運転（要約）に逃げる。

> **Text-to-SQL は「記事を書く主役」ではなく、「データ素材を集めるアナリスト」であるべき！**

---

## 多段オーケストレーションへの進化（Issue #98）

### 編集デスク AI × Text-to-SQL × 執筆 AI の分離パイプライン

```
  [ユーザー] <──対話──> [編集デスク AI (ArticleDeskAgent)]
                                │
                                ▼ 企画構成 ＋ 取材指示リスト (JSON)
                    [オーケストレーター (MultiArticleService)]
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
 [取材①: 基本成績]       [取材②: 打球質]       [取材③: 速球適応]
 (Text-to-SQL #1)        (Text-to-SQL #2)        (Text-to-SQL #3)
        │                       │                       │
        ▼                       ▼                       ▼
    [素材① 表]              [素材② 表]              [素材③ 表]
        └───────────────────────┼───────────────────────┘
                                ▼
                 [執筆 AI (MultiDataArticleSynthesizer)]
                                │
                                ▼
                 [章立て完成記事 (PostgreSQL / Web UI)]
```

---

## 既存データから広がる新サービス展開アイデア

本基盤の仕組みを活用して、どんな新サービス・価値創出ができるか？

<div class="columns-3">

<div class="card">
<h3>① 自然言語セルフ分析</h3>
<p>社内 BI やユーザー向け機能として、「自然言語でグラフや表を動的生成」できる対話型クエリ機能。</p>
</div>

<div class="card">
<h3>② 自動インサイト・レポート</h3>
<p>定期バッチで「異常値やハイライト」を検知し、Text-to-SQL で裏付けデータを集めて解説レポートを自動配信。</p>
</div>

<div class="card">
<h3>③ コンテンツ自動生成</h3>
<p>スポーツ・金融・EC 等の生データから、ファクトに基づいた SEO 記事や要約コンテンツを大量・高精度に自動生成。</p>
</div>

</div>

---

<!-- _class: lead -->

# まとめ & ディスカッション

1. **Text-to-SQL の本質は「DB 専用の RAG 知識蓄積（ドメイン知識）」にある**
   - 単なるプロンプト調整ではなく、DDL / 業務ルール / Few-shot の整備が精度を握る。
2. **ClickHouse 等の OLAP 特有の制約（型・FINAL・粒度）をどう制御するかが実運用のキモ**
3. **「単発 SQL」から「多段オーケストレーション（素材収集ツール）」へ拡張することで、実用的なコンテンツやサービスへ昇華できる**

### 💬 ディスカッション
**「私たちのプロダクト・社内データにおいて、Text-to-SQL をどの領域に導入すれば最大のインパクトを出せるか？」**
