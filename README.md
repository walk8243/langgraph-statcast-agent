# langgraph-statcast-agent

Baseball Savant (Statcast) の生データ蓄積から集計、LangGraph による解説生成までを一気通貫で検証するための PoC (Proof of Concept) リポジトリです。

Docker Compose 上で列指向データベース、リレーショナルデータベース (RDB)、Google Cloud Pub/Sub エミュレータを組み合わせたイベント駆動型マイクロサービスアーキテクチャを採用し、将来的な GCP 移行を見据えた構成検証を行います。

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
│   ├── ingestion/             # Baseball Savant からの生データ収集 (Collector)
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
# 1. データの収集実行 (Ingestion)
docker compose run --rm ingestion --player-id 660271 --season 2026

# 2. Agent CLI の対話起動
docker compose run --rm agent

```

---

## 検証ステータス

* [ ] Docker Compose 環境の構築（DB群 + Pub/Sub エミュレータ）
* [ ] Ingestion サービスの実装（Savant CSV 取得 → 列指向DB 投入）
* [ ] Pub/Sub を経由した Aggregator のトリガー実装
* [ ] Aggregator による指標算出（Barrel%, xwOBA 等）と RDB 格納
* [ ] LangGraph による基本解説ワークフローの実装
* [ ] 列指向DB へのオンデマンド深掘りクエリツールの統合
