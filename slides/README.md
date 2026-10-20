# Text-to-SQL プレゼンテーションスライド資料

本ディレクトリには、本リポジトリで導入・検証した Text-to-SQL 基盤をベースにした、ターゲット読者別の 2 パターンのプレゼンテーションスライド資料が格納されています。

スライド生成ツールには **[Marp](https://marp.app/)** を採用し、Markdown から直接 HTML / PDF スライドを出力できます。

---

## 収録スライド一覧

| スライドファイル | 対象読者 | 主なテーマ・目的 |
| :--- | :--- | :--- |
| [`text-to-sql-for-business.md`](text-to-sql-for-business.md) | **非エンジニア**<br>(ビジネス・企画・アナリスト) | **言葉でデータを引き出す技術：Text-to-SQL が変えるデータ活用の現場**<br>- 依頼待ち・固定BIの課題解消<br>- 誰でも使えるセルフサービス化と高速検証<br>- 自動記事生成の実例と「ドメイン知識の蓄積」の重要性 |
| [`text-to-sql-for-engineers.md`](text-to-sql-for-engineers.md) | **エンジニア**<br>(開発者・アーキテクト) | **Text-to-SQL 実践導入と既存データからの新サービス展開提案**<br>- 4層アーキテクチャ（Vanna.ai 設計思想 + 独自実装）<br>- ClickHouse / Qdrant / Gemini 連携のハマりどころ<br>- 多段オーケストレーションと新サービス展開アイデア |

---

## スライドの閲覧・編集方法

### 1. VS Code でのリアルタイムプレビュー（推奨）
1. VS Code 拡張機能 **「[Marp for VS Code](https://marketplace.visualstudio.com/items?itemName=marp-team.marp-vscode)」** をインストールします。
2. 対象の Markdown ファイルを開き、エディタ右上の「プレビュー」アイコンをクリックすると、スライド形式でリアルタイムにプレビューできます。

### 2. コマンドラインでの HTML 出力（ローカルビルド）
Node.js 環境があれば、`npm run build` で GitHub Pages 公開用フォルダ（`../docs/`）に HTML ファイルを出力できます。

```bash
cd slides
npm install

# 両方のスライドを HTML にビルド（../docs/ ディレクトリに出力）
npm run build

# 個別ビルド
npm run build:business
npm run build:engineers
```

生成された `../docs/*.html` はブラウザで直接開くことができ、キーボードの矢印キーでページ送り可能なスライドショーとして動作します。また、リポジトリの `docs/` フォルダを GitHub Pages の配信元に設定することで、Web サイトとしてそのまま一般公開できます。

---

## デザインテーマについて
本スライドでは、`default` テーマをベースにカスタマイズした **`theme.css`（パターン A: テック・モダンブルー）** を適用しています。
- メインカラー: `#1e3a8a` (ネイビー)
- アクセントカラー: `#2563eb` (コバルトブルー)
- 背景色: `#f8fafc` (オフホワイト)
