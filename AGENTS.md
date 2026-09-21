# Agent Guidelines (AGENTS.md)

このリポジトリで作業するすべての AI コーディングエージェント（Antigravity, Copilot, etc.）および開発者は、以下のプロジェクト管理・開発ワークフローを遵守してください。

詳細な規定は [docs/workflow.md](file:///d:/git/langgraph-statcast-agent/docs/workflow.md) を参照してください。

---

## 開発ワークフローの基本サイクル

作業は必ず以下のステップに従って進めてください。

1. **タスク起票 (Issue Creation)**
   - 新しいタスクは必ず Issue に起票します。起票すると [GitHub Project](https://github.com/users/walk8243/projects/6/views/1) に自動追加されます（初期Status: `Todo` / `Backlog`）。
   - 起票段階では詳細な実装計画は不要です。**「前提条件 (Prerequisites)」** と **「達成条件 (Acceptance Criteria / DoD)」** を必ず記載してください。
   - テンプレート: `.github/ISSUE_TEMPLATE/task.yml`

2. **実行計画立案 (Planning)**
   - コーディングに入る前に、必ず方針・変更対象ファイル・実装ステップ・検証手順を整理した「実行計画」を立案します。
   - **立案した実行計画は、必ず対象 Issue のコメントとして投稿してください。**
   - **計画立案後、ProjectのIssueステータスを「`Ready`」に変更してください。**
   - **1 issue 1 PR の原則**:
     - 実行計画立案中に「PRの変更量が大きすぎる」「責務が複数に分かれている」と判断した場合は、無理に1つのPRにまとめず、**PRを分割**します。
     - PRを分割する場合は、**新規子Issueを起票し、元の親Issueと親子関係として紐付け**を行ってください（例: Issue本文で `Parent: #XX`、またはタスクリスト `- [ ] #YY` で参照）。

3. **実装 (Implementation)**
   - **実装を開始する際、ProjectのIssueステータスを「`In progress`」に変更してください。**
   - ブランチ名は `feature/issue-<num>-<short-description>` または `fix/issue-<num>-<short-description>` としてください。
   - Issueコメントの実行計画に沿って実装を進め、テストを記述・実行してください。

4. **PR作成 (Pull Request)**
   - **1 issue 1 PR**: 1つのPRが対応するIssueは原則1つです。
   - PR本文には必ず `Closes #<Issue番号>` を含めてください。
   - テンプレート: `.github/pull_request_template.md` を使用し、達成条件のチェックリストと動作確認手順を記載してください。

5. **レビュー & マージ (Review & Merge)**
   - **PRレビューを行い、通過・確認待ちとなったら、ProjectのIssueステータスを「`In review`」に変更してください。**
   - レビュー指摘対応および検証が完了したらマージします（Squash and Merge推奨）。マージ完了によりStatusは「`Done`」となります。

---

## 支援スキル (Workspace Skills)

本ワークフローをスムーズに実行するため、以下のスキルが `.agents/skills/` 配下に整備されています。必要に応じて参照・実行してください。

| スキル名 | 格納場所 | 用途 |
| :--- | :--- | :--- |
| `task-create` | [.agents/skills/task-create/SKILL.md](file:///d:/git/langgraph-statcast-agent/.agents/skills/task-create/SKILL.md) | タスク起票（前提条件・達成条件を整理して Issue 作成） |
| `task-plan` | [.agents/skills/task-plan/SKILL.md](file:///d:/git/langgraph-statcast-agent/.agents/skills/task-plan/SKILL.md) | 実行計画立案（Issueコメント投稿、1 issue 1 PR 判定、子Issue起票） |
| `task-implement` | [.agents/skills/task-implement/SKILL.md](file:///d:/git/langgraph-statcast-agent/.agents/skills/task-implement/SKILL.md) | 実装（ブランチ作成、コーディング、テスト実行） |
| `pr-create` | [.agents/skills/pr-create/SKILL.md](file:///d:/git/langgraph-statcast-agent/.agents/skills/pr-create/SKILL.md) | PR作成（1 issue 1 PR、`Closes #XX`、テンプレート適用） |
| `pr-review-merge` | [.agents/skills/pr-review-merge/SKILL.md](file:///d:/git/langgraph-statcast-agent/.agents/skills/pr-review-merge/SKILL.md) | レビュー・マージ（差分・DoD確認、マージ実行、Issueクローズ確認） |

