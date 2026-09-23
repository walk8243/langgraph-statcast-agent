# Web フロントエンド表示基盤 (`apps/web`)

MLB Statcast のデータ分析・可視化、全30球団・選手ロスターの閲覧、および LangGraph + Google Gemini による選手解説レポートを表示するための Web アプリケーションです。

## 技術スタック

- **フレームワーク**: Next.js 16 (App Router / Turbopack)
- **言語 / ランタイム**: TypeScript / Node.js
- **UI コンポーネントライブラリ**: Microsoft Fluent UI React v9 (`@fluentui/react-components`, `@fluentui/react-icons`)
- **データベース接続**: PostgreSQL (`pg` クライアントによる Server Components / Route Handlers からの直接データフェッチ)
- **リンター**: ESLint (Flat Config)

## アーキテクチャの特長

- **フルスタック Next.js 構成**:
  - Next.js の Server Components や Route Handlers から直接 PostgreSQL に接続してクエリを実行できるため、別途独立したバックエンド API サーバーを立てることなくデータアクセスが完結します。
- **Fluent UI v9 SSR 対応**:
  - `src/app/providers.tsx` にて `createDOMRenderer` および `renderToStyleElements` を使用し、App Router の SSR (サーバーサイドレンダリング) 時にも CSS スタイルが崩れず最適に適用されるようセットアップされています。
- **PostgreSQL 接続プール**:
  - `src/lib/db.ts` では Next.js の開発時ホットリロードでもコネクションが増殖しないよう、グローバルシングルトンパターンで接続プールを管理しています。

## ディレクトリ構成

```text
apps/web/
├── public/                 # 静的アセット
├── src/
│   ├── app/
│   │   ├── favicon.ico
│   │   ├── globals.css     # Fluent UI に合わせたベーススタイル
│   │   ├── layout.tsx      # ルートレイアウト（Providers ラップ）
│   │   ├── page.tsx        # ダッシュボードトップ画面
│   │   └── providers.tsx   # Fluent UI SSR スタイル・テーマプロバイダー
│   └── lib/
│       └── db.ts           # PostgreSQL クライアント (pg.Pool)
├── eslint.config.mjs
├── next.config.ts
├── package.json
└── tsconfig.json
```

## 環境変数

プロジェクトルートの `.env` または本ディレクトリの `.env.local` に以下の接続情報を設定します。

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=statcast
POSTGRES_USER=statcast
POSTGRES_PASSWORD=statcast_pass
```

## 開発・実行コマンド

```bash
# 依存関係のインストール
npm install

# 開発サーバーの起動 (http://localhost:3000)
npm run dev

# 型チェック & プロダクションビルド
npm run build

# 本番サーバーの起動
npm run start

# リント実行
npm run lint
```
