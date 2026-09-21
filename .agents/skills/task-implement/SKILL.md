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
* Issueのコメントに実行計画が投稿されていることを確認します。

### 2. 作業ブランチの作成・切り替え
ブランチ命名規則に従って新しいブランチを作成します。

* **命名規則**: `feature/issue-<num>-<short-description>` または `fix/issue-<num>-<short-description>`
* **実行コマンド**:
  ```bash
  git checkout main
  git pull origin main
  git checkout -b feature/issue-<num>-<short-description>
  ```

### 3. コーディングとテスト
* Issueコメントの実行計画に沿って変更を加えます。
* コード変更後、実行計画に記載した検証コマンド（ユニットテスト、ビルド、`docker compose up` 等）を実行して動作確認を行います。
* 計画にない大幅な仕様変更が生じた場合は、独断で進めずにIssueコメントに差分を追記するかユーザーに確認します。

### 4. コミット作成
* コミットメッセージには対応するIssue番号を含めます。
* **例**: `feat: implement ingestion pipeline (#XX)` / `fix: resolve db healthcheck timeout (#XX)`
* **コマンド**:
  ```bash
  git add <files>
  git commit -m "<type>: <description> (#<num>)"
  ```

### 5. 完了報告
実装と検証が完了した旨を報告し、次のステップ（PR作成 `pr-create`）へ進みます。
