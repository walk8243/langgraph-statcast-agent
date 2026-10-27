# MLB Statcast Text-to-SQL & AI Article Generator

MLB Statcast データ（ClickHouse）に対する自然言語指示からの動的 SQL 生成・集計、および解説記事生成を行う Python サービスです。

## 主な機能
- **Text-to-SQL 基盤**: Vanna.ai / Google Gemini LLM / Qdrant ベクトルDB
- **ベクトル知識ベース**: ClickHouse のテーブルスキーマ (DDL)、Statcast 指標解説ドキュメント、SQL サンプルを Qdrant に登録・ベクトル検索
- **SQL 安全性検証**: SELECT / WITH 句のみを許可し、変更系（DROP/ALTER/DELETE 等）のクエリをブロック
- **高速 OLAP 集計**: ClickHouse での大規模投球・打球データの動的集計
- **Model Context Protocol (MCP) サーバー**: Claude Desktop, Cursor, Antigravity などの AI クライアントから直接 Statcast データ分析や SQL 生成を呼び出せるインターフェースを提供

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

### AI解説記事の生成（単一SQL）
```bash
python -m src.main --generate-article "2024年ドジャースのチーム本塁打と得点力の要因分析"
```

### 多段オーケストレーション解説記事の生成（複数データ素材集計）
複数の集計素材と章構成を指定して、立体的な解説記事を生成・PostgreSQLへ保存します。

```bash
# 雛形設定JSONの確認
python -m src.main --example-multi-config

# 設定JSONファイルを指定して生成
python -m src.main --generate-multi-article config.json
```

### 対話型AI編集デスク（企画立案・壁打ちからの自動執筆）
ターミナル上でAI編集デスクと対話し、テーマの深掘りや章立て・取材項目を決定して一気通貫で記事を生成します。

```bash
python -m src.main --desk-interactive
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

### GitHub Pages 向け記事エクスポート
PostgreSQL に保存されている生成記事を `docs/articles/` 配下に静的 HTML および Markdown として出力します。
デフォルトでは公開対象に指定された記事（Article #11）のみが出力されます。

```bash
# デフォルト公開記事（#11）をエクスポート
uv run python -m src.export_docs

# 特定の記事IDを指定してエクスポート
uv run python -m src.export_docs --article-ids 10 11

# 全記事をエクスポート
uv run python -m src.export_docs --all
```

## Model Context Protocol (MCP) サーバー

Statcast Text-to-SQL エンジンを MCP サーバーとして公開し、Claude Desktop, Cursor, Antigravity などの AI ツールから自然言語でデータを直接検索・集計できます。

### 提供するツール一覧
| ツール名 | 引数 | 説明 |
| :--- | :--- | :--- |
| `query_statcast` | `question: str` | 自然言語で質問を受け取り、SQL 生成 → ClickHouse 実行 → 結果テーブル（Markdown形式）を返却 |
| `generate_sql` | `question: str` | 自然言語から ClickHouse 用 SQL のみを生成して返却（DB実行なし） |
| `search_statcast_schema` | `keyword: str`, `item_type?: str` | Qdrant から Statcast のテーブル定義 (DDL)、指標ドキュメント、SQL例文を検索して返却 |

### サーバー起動コマンド
```bash
# 標準入出力 (stdio) モード（Claude Desktop / Cursor 等での連携用）
uv run statcast-mcp --transport stdio

# SSE / HTTP モード
uv run statcast-mcp --transport sse --port 8003
```

### Claude Desktop / Cursor の設定例
Claude Desktop (`claude_desktop_config.json`) や Cursor の MCP 設定に以下を追加します：

```json
{
  "mcpServers": {
    "statcast-text-to-sql": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "d:/git/langgraph-statcast-agent/apps/article-generator",
        "statcast-mcp"
      ],
      "env": {
        "GEMINI_API_KEY": "YOUR_GEMINI_API_KEY",
        "CLICKHOUSE_HOST": "localhost",
        "CLICKHOUSE_HTTP_PORT": "8123",
        "QDRANT_HOST": "localhost",
        "QDRANT_HTTP_PORT": "6333"
      }
    }
  }
}
```



