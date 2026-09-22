---
name: task-implement
description: Use this skill when starting the implementation of an approved GitHub Issue and plan, creating feature branches, and executing code changes.
---

# Task Implementation Skill (`task-implement`)

承認された実行計画に沿ってブランチを作成し、実装・テストを進めるための手順です。

---

## 実行フロー

### 1. 前提条件のチェック
* 対象Issueの「前提条件」が満たされているか確認します。
* Issueのコメントに実行計画が投稿され、ステータスが **`Ready`** であることを確認します。

### 2. Issue の Assignee 設定 (`@me`)、Start date 設定、Project ステータス更新 (`In progress`)
実装に着手するタイミングで、対象 Issue に対して以下を行います。

1. **担当者のアサイン (`@me`)**:
   - 対象 Issue の Assignee に自分自身（`@me`）を設定します。
   - **GitHub MCP ツール（優先）**:
     - `get_me` で自身のログインユーザー名を取得後、`issue_write`（`method: "update"`, `issue_number: <num>`, `assignees: ["<username>"]`）を実行します。
   - **GitHub CLI（フォールバック）**:
     ```bash
     gh issue edit <issue-number> --add-assignee "@me"
     ```
2. **Start date 設定 & Project ステータス更新 (`In progress`)**:
   - GitHub MCP サーバーには Project V2 を直接更新するツールがないため、**プロジェクト更新スクリプト（GitHub CLI 経由）** を実行して更新してください。
   ```bash
   python .agents/scripts/update_project.py --issue <num> --status "In progress" --start-date today
   ```

### 3. 作業ブランチの作成・切り替え
ブランチ命名規則に従って新しいブランチを作成します。

* **命名規則**: `feature/issue-<num>-<short-description>` または `fix/issue-<num>-<short-description>`
* **実行コマンド**:
  ```bash
  git checkout main
  git pull origin main
  git checkout -b feature/issue-<num>-<short-description>
  ```

### 4. コーディングとテスト
* Issueコメントの実行計画に沿って変更を加えます。
* コード変更後、実行計画に記載した検証コマンド（ユニットテスト、ビルド、`docker compose up` 等）を実行して動作確認を行います。
* 計画にない大幅な仕様変更が生じた場合は、独断で進めずにIssueコメントに差分を追記するかユーザーに確認します。

### 5. コミット作成
* コミットメッセージは**日本語**で記述します。
* すべての変更は Issue と紐付く PR を経由するため、**コミットメッセージに Issue 番号を記載する必要はありません**。
* **プレフィックス (Conventional Commits)**: `feat:` (新機能), `fix:` (修正), `docs:` (ドキュメント), `refactor:` (リファクタリング), `test:` (テスト追加・修正), `chore:` (雑務・メンテ) 等
* **形式**: `<type>: <日本語の説明>`
* **例**:
  - `feat: データ収集パイプラインの実装`
  - `fix: DBヘルスチェックのタイムアウトを解消`
  - `docs: 開発ワークフロードキュメントの更新`
* **コマンド**:
  ```bash
  git add <files>
  git commit -m "<type>: <日本語の説明>"
  ```

### 6. 完了報告
実装と検証が完了した旨を報告し、次のステップ（PR作成 `pr-create`）へ進みます。
