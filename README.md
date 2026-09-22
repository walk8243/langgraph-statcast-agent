# langgraph-statcast-agent

Baseball Savant (Statcast) および MLB Stats API からのデータ蓄積・集計から、LangGraph による解説生成までを一気通貫で検証するための PoC (Proof of Concept) リポジトリです。

Docker Compose 上で列指向データベース、リレーショナルデータベース (RDB)、Google Cloud Pub/Sub エミュレータを組み合わせたイベント駆動型マイクロサービスアーキテクチャを採用し、将来的な GCP 移行を見据えた構成検証を行います。

---

## データソース

本プロジェクトでは、用途に応じて以下の2つの外部データソースを組み合わせて活用します。

1. **Baseball Savant (Statcast)**
   - **Base URL**: `https://baseballsavant.mlb.com`
   - **用途**: 投球・打球単位（Pitch-by-Pitch）のトラッキングデータ取得
   - **内容**: 球速、回転数、変化量、打球初速、打球角度、着弾座標などの詳細な物理・トラッキング生データ。
2. **MLB Stats API (公式 REST API)**
   - **Base URL**: `https://statsapi.mlb.com`
   - **用途**: 試合日程、チーム・選手マスタ、公式記録（Box Score）等の取得
   - **内容**: 試合一覧、ロスター情報、確定した打点 (RBI)・得点 (R)・打順・交代記録などの公式集計スタッツ。

---

## システム概要

```
[ Baseball Savant / MLB API ]
              │ (Batch / On-demand)
              ▼
  ┌───────────────────────┐
  │ Ingestion Service     │ (Python / TS)
  │ ・生データ収集         │
  └──────────┬────────────┘
             │ ① 生データ Bulk Insert
             ▼
  ┌───────────────────────┐      ② Publish (完了通知)      ┌─────────────────────────┐
  │ 列指向データベース    │ ─────────────────────────────▶ │ Cloud Pub/Sub Emulator │
  │ (Pitch-by-Pitch Raw)  │                                └────────────┬────────────┘
  └──────────┬────────────┘                                             │ ③ Pull
             │                                                          ▼
             │ ④ 集計クエリ実行                               ┌─────────────────────────┐
             └─────────────────────────────────────────────── │ Aggregation Service     │
                                                              │ ・指標計算 (Barrel% 等) │
                                                              └────────────┬────────────┘
                                                                           │ ⑤ 集計結果 Upsert
                                                                           ▼
                                                              ┌─────────────────────────┐
                                                              │ RDB                     │
                                                              │ ・選手マスタ / サマリー  │
                                                              │ ・解説キャッシュ        │
                                                              └────────────┬────────────┘
                                                                           │ ⑥ データ参照
                                                                           ▼
                                                              ┌─────────────────────────┐
                                                              │ AI Agent Service        │
                                                              │ (LangGraph / TS)        │
                                                              └────────────┬────────────┘
                                                                           │ ⑦ 選手解説
                                                                           ▼
                                                                        [ User ]

```

---

## 主な検証テーマ

1. **ハイブリッドデータストアの使い分け**
* **列指向DB**: 投球・打球単位（Pitch-by-pitch）の膨大な生ログ（全80+カラム）を圧縮・高速スキャン用に保持。
* **RDB**: 選手マスタ、LLMへ即座に渡すための事前集計指標（Barrel%、HardHit%、xwOBA、各球種割合など）、LangGraph の会話ステートを保持。


2. **イベント駆動によるデータパイプライン**
* Ingestion サービス完了後、Google Cloud Pub/Sub (エミュレータ) を介して非同期で Aggregation サービスをトリガー。


3. **LangGraph (TypeScript) による専門的なデータ解説**
* ユーザー入力から選手・期間を特定し、RDB のサマリーデータと列指向DBの詳細集計を状況に応じて参照・解説文を生成。



---

## ディレクトリ構成

```text
langgraph-statcast-agent/
├── apps/
│   ├── ingestion/             # Baseball Savant / MLB Stats API からのデータ収集 (Collector)
│   │   ├── Dockerfile
│   │   └── ...
│   ├── aggregator/            # 生データを指標に変換・RDBへ格納するワーカー
│   │   ├── Dockerfile
│   │   └── ...
│   └── agent/                 # LangGraph による分析・解説エージェント (TypeScript)
│       ├── Dockerfile
│       ├── src/
│       │   ├── agent/         # LangGraph ワークフロー定義
│       │   ├── tools/         # DB 参照・集計ツール定義
│       │   └── index.ts
│       └── package.json
├── docker/
│   └── pubsub/                # Pub/Sub エミュレータ初期設定スクリプト
│       └── init-topics.sh
├── docker-compose.yml
├── .env.example
└── README.md

```

---

## 技術スタック

* **Agent Core:** TypeScript, LangGraph (`@langchain/langgraph`), LangChain
* **Messaging:** Google Cloud Pub/Sub (Local Emulator via `@google-cloud/pubsub`)
* **Databases:**
* 列指向ストレージ（Raw Data & 大規模集計用）
* リレーショナルデータベース（マスタ、事前集計サマリー、エージェントステート）


* **Infrastructure:** Docker Compose

---

## クイックスタート

### 1. 環境変数の設定

```bash
cp .env.example .env

```

### 2. コンテナ群の起動

```bash
docker compose up -d --build

```

### 3. 初期セットアップの確認

Pub/Sub エミュレータ、各DBが正常にヘルスチェックを通過していることを確認します。

```bash
docker compose ps

```

### 4. データの取得とエージェント実行

```bash
# 1. データの収集実行 (Ingestion - MLBチーム一覧の取得と登録)
docker compose run --rm ingestion --fetch-teams

# データの収集実行 (Ingestion - MLB登録選手一覧の取得と登録)
docker compose run --rm ingestion --fetch-players --season 2024

# データの収集実行 (Ingestion - MLB試合日程・結果一覧の取得と登録)
docker compose run --rm ingestion --fetch-games --season 2024

# データの収集実行 (Ingestion - MLB打者シーズン成績の取得と RDB 登録: 打点・得点・盗塁等の公式スタッツ)
docker compose run --rm ingestion --fetch-hitting-stats --season 2024

# データの収集実行 (Ingestion - 登録全選手の Statcast データ一括取得例: 上限10選手、特定期間)
docker compose run --rm ingestion --fetch-all-statcast --limit 10 --start-date 2024-04-01 --end-date 2024-04-07

# 個別選手の Statcast データ収集 (投手データ取得例)
docker compose run --rm ingestion --player-id 808967 --start-date 2024-04-01 --end-date 2024-04-07

# 個別選手の Statcast データ収集 (打者データ取得例)
docker compose run --rm ingestion --player-id 673548 --player-type batter --start-date 2024-04-01 --end-date 2024-04-07

# 2. データの集計実行 (Aggregation - 打者基本指標の集計と RDB 登録)
docker compose run --rm aggregation --player-id 673548 --year 2024

# 3. Agent CLI の対話起動
docker compose run --rm agent
```

---

## プロジェクト管理・開発ワークフロー

本リポジトリでは **「タスク起票」→「実行計画立案」→「実装」→「PR作成」→「レビュー」** を標準サイクルとしたプロジェクト管理・開発ワークフローを導入しています。

- タスク起票時は詳細設計不要（前提条件と達成条件の記載のみでOK）
- 着手前に実行計画を立案し、Issueコメントに投稿
- **1 issue 1 PR** を原則とし、PR分割時は子Issueを起票して親子関係を紐付け

詳細なルールやテンプレートの使い方は [docs/workflow.md](docs/workflow.md) を参照してください。

---

## 検証ステータス

* [ ] Docker Compose 環境の構築（DB群 + Pub/Sub エミュレータ）
* [x] Ingestion サービスの実装（Savant CSV 取得 → 列指向DB 投入）
* [ ] Pub/Sub を経由した Aggregator のトリガー実装
* [ ] Aggregator による指標算出（Barrel%, xwOBA 等）と RDB 格納
* [ ] LangGraph による基本解説ワークフローの実装
* [ ] 列指向DB へのオンデマンド深掘りクエリツールの統合
