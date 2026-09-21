---
name: pr-review-merge
description: Use this skill when reviewing, testing, approving, or merging a Pull Request, and verifying that the corresponding issue is properly closed.
---

# PR Review & Merge Skill (`pr-review-merge`)

作成された Pull Request の動作確認・レビューを行い、安全にマージして Issue をクローズ完了させるための手順です。

---

## 実行フロー

### 1. PR 内容と達成条件の突き合わせ
1. `pull_request_read` 等を用いて PR の変更ファイル（diff）と説明文を確認します。
2. 紐付いている Issue（`Closes #<num>`）の「達成条件」がすべて網羅されているかを照合します。

### 2. 動作確認・検証の実施
* PR の「動作確認・検証手順」に記載されたコマンドをローカル環境で実行します。
* テストスイートや Lint、コンテナヘルスチェックがパスすることを確認します。

### 3. レビュー結果の対応 / Project ステータス更新 (`In review`)
* PR の内容および動作検証を実施します。
* レビュー指摘対応および検証が通過したら、[GitHub Project](https://github.com/users/walk8243/projects/6/views/1) 上の Issue ステータスを **`In review`** に変更し、PR を承認（Approve）します。

### 4. マージの実行
* 原則 **Squash and Merge** を推奨します。
* GitHub MCPツール `merge_pull_request` または GitHub CLI (`gh pr merge --squash`) を使用します。
  * **merge_method**: `"squash"`

### 5. 完了後のステータス確認 (`Done`)
* 対応 Issue が自動クローズされ、Project 上のステータスが **`Done`** に遷移したことを確認します。
* 親Issueがある場合:
  * 他のすべての子Issueが完了しているか確認します。
  * すべて完了していれば親Issueも完了・クローズとします。
* 作業ブランチをローカルおよびリモートから削除します。
  ```bash
  git checkout main
  git pull origin main
  git branch -d feature/issue-<num>-...
  ```
