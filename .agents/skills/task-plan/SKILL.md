---
name: task-plan
description: Use this skill when planning the implementation for a specific GitHub Issue, posting the plan as an issue comment, or determining whether to split the PR into sub-issues.
---

# Task Planning Skill (`task-plan`)

対象となる Issue に対する実行計画を立案し、Issue コメントへ投稿するための手順です。  
**1 issue 1 PR の原則** に基づき、スコープが大きい場合は PR 分割（子Issue起票）の判断を行います。

---

## 実行フロー

### 1. Issue 情報と現行コードベースの確認
1. 対象 Issue の番号を指定し、`issue_read` 等で「前提条件」「達成条件」を取得します。
2. リポジトリ内の関連コード、設定ファイル、ドキュメントを調査します。

### 2. 実行計画の策定
以下の観点で計画をまとめます。

* **アプローチ・方針**: どう実現するか
* **変更対象ファイル**: 新規作成・変更・削除するファイルの一覧
* **実装ステップ**: 作業順序のチェックリスト
* **検証手順**: 自動テストコマンドや動作確認コマンド

### 3. PR 分割要否の判定（1 issue 1 PR 原則）
以下のいずれかに該当する場合は、**PRの分割（子Issue起票）** を検討します。

* 想定される差分行数が 300〜500 行を超える場合
* インフラ（Docker/DB）とアプリケーションコードなど、責務が複数に跨がる場合
* 個別にレビュー・マージした方がリスクが低い場合

#### 💡 分割する場合の手順
1. 元のIssueを「親Issue」と位置づけます。
2. `task-create` スキルを使い、分割した各作業単位で「子Issue」を起票します。
   - 子Issueの「親Issue」欄に `Parent: #<親Issue番号>` を明記。
3. 親Issueのコメントに、子Issueの一覧と分割理由を投稿します。

### 4. Issue コメントへの投稿
分割不要（または子Issue単位）の場合、GitHub MCPツール `add_issue_comment` を使用して対象Issueに実行計画コメントを投稿します。

```markdown
## 実行計画

### 1. 概要・アプローチ
- <方針の要約>

### 2. 変更対象ファイル
- [NEW] `<ファイルパス>`
- [MODIFY] `<ファイルパス>`

### 3. 実装ステップ
1. [ ] <ステップ1>
2. [ ] <ステップ2>

### 4. 検証手順
- `<コマンド等>`

### 5. PR分割の要否
- [x] 分割不要（1 PRで対応完了可能）
- [ ] 分割推奨（理由: ...）
```

### 5. 完了報告
コメント投稿の完了とURLを報告し、ユーザー承認または実装（`task-implement`）への着手を案内します。
