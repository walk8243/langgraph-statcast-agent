# MLB Statcast Text-to-SQL & AI Article Generator

MLB Statcast データ（ClickHouse）に対する自然言語指示からの動的 SQL 生成・集計、および解説記事生成を行う Python サービスです。

## 主な機能
- **Text-to-SQL 基盤**: Vanna.ai / Google Gemini LLM / Qdrant ベクトルDB
- **ベクトル知識ベース**: ClickHouse のテーブルスキーマ (DDL)、Statcast 指標解説ドキュメント、SQL サンプルを Qdrant に登録・ベクトル検索
- **SQL 安全性検証**: SELECT / WITH 句のみを許可し、変更系（DROP/ALTER/DELETE 等）のクエリをブロック
- **高速 OLAP 集計**: ClickHouse での大規模投球・打球データの動的集計

## 使い方

### サービスの接続確認
```bash
python -m src.main --check-services
```

### Qdrant へのスキーマ・ドキュメント学習
```bash
python -m src.main --train
```

### 自然言語によるクエリ実行
```bash
python -m src.main --query "2024年のチーム別本塁打数ランキング"
```

### Docker での実行
```bash
docker compose run --rm article-generator --check-services
docker compose run --rm article-generator --train
docker compose run --rm article-generator --query "登録されている球団一覧を表示して"
```

### テスト実行
```bash
uv run pytest
```
