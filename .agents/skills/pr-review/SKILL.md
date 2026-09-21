---
name: pr-review
description: Use this skill when reviewing and testing a Pull Request, checking Acceptance Criteria, and changing the Project status to In review for human final review and merge.
---

# PR Review Skill (`pr-review`)

作成された Pull Request の動作確認・レビューを行い、Issue の達成条件（DoD）を満たしているかを検証するための手順です。  
**PR のマージは最後に必ず人の目を通すため、本スキル内ではマージを実行せず、人間による最終確認・マージ待ちとします。**

---

## 実行フロー

### 1. PR 内容と達成条件の突き合わせ
1. GitHub MCPツール `pull_request_read` を用いて PR の変更差分（diff）と説明文を確認します。
2. 紐付いている Issue（`Closes #<num>`）の「達成条件 (DoD)」がすべて網羅されているかを照合します。

### 2. 動作確認・検証の実施
* PR の「動作確認・検証手順」に記載されたコマンドをローカル環境で実行します。
* ユニットテスト、Lint、ビルド、コンテナヘルスチェック等が正常にパスすることを確認します。

### 3. レビュー結果のコメント
* 不備や修正が必要な点があれば、GitHub MCPツール `add_issue_comment` や `pull_request_review_write` を用いて PR にコメントを投稿し、開発者に修正を促します。
* すべて問題なければ、PR にレビューコメントまたは承認（Approve）を投稿します。

### 4. Project ステータス (`In review`) と End date の更新
* レビューおよび動作検証を通過したら、[GitHub Project](https://github.com/users/walk8243/projects/6/views/1) 上で対象 Issue に対し以下を設定します。
  1. **Status**: **`In review`** に変更
  2. **End date**: 本日日付（形式: `YYYY-MM-DD`）を設定

### 5. 人間による最終確認・マージの依頼（終了）
* **エージェントはマージを実行しません。**
* レビューおよび検証結果をまとめ、「人による最終確認およびマージ」をユーザーに依頼して本スキルを終了します。

---

## （参考）マージ完了後のクリーンアップ
人間による PR マージ（通常のマージ / Create a merge commit）が完了した後、ローカル環境で以下のクリーンアップを行います。

1. メインブランチを最新化:
   ```bash
   git checkout main
   git pull origin main
   ```
2. 作業完了ブランチの削除:
   ```bash
   git branch -d feature/issue-<num>-...
   ```
3. 対象 Issue が自動クローズされ、Project 上で **`Done`** になったことを確認します（子Issueの場合は親Issueの完了状態も確認）。
