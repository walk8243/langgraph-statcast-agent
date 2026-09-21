---
name: pr-create
description: Use this skill when creating a Pull Request for a completed task or issue, following the 1 issue 1 PR principle.
---

# Pull Request Creation Skill (`pr-create`)

実装が完了したタスクについて、**1 issue 1 PR** の原則に沿って Pull Request を作成・起票するための手順です。

---

## 実行フロー

### 1. 事前準備
1. 現在のブランチ名が `feature/issue-<num>-...` であることを確認します。
2. 対象Issueの「達成条件」がすべて満たされていることをセルフチェックします。
3. リモートブランチへプッシュします。
   ```bash
   git push -u origin <branch-name>
   ```

### 2. PR 本文の作成
`.github/pull_request_template.md` に従ってPR本文を作成します。

* **必須**: `Closes #<num>`（対応するIssue番号）を必ず含めます。
* **項目**:
  * 変更の概要
  * 実行計画との対応状況
  * 達成条件の確認（チェックボックス）
  * 動作確認・検証手順（レビュアーが追試できるコマンド）
  * レビュー観点 / 特記事項

```markdown
## 関連Issue
Closes #<num>

## 変更の概要
<概要を簡潔に記載>

## 実行計画との対応
- [x] Issueコメントの実行計画に沿って実装した
- [ ] 計画からの差分・追加変更点: なし

## 達成条件の確認
- [x] <達成条件1>
- [x] <達成条件2>

## 動作確認・検証手順
1. <手順1>
2. <手順2>

## レビュー観点 / 特記事項
<レビュアーに見てもらいたいポイント>
```

### 3. Pull Request の作成
GitHub MCPツール `create_pull_request` または GitHub CLI (`gh pr create`) を使用してPRを作成します。

* **title**: `feat: <変更内容> (#<num>)`
* **head**: 現在の作業ブランチ
* **base**: `main`
* **body**: 上記で作成したPR本文

### 4. 完了報告
作成された PR の番号と URL をユーザーに報告し、レビューフェーズ（`pr-review-merge`）へ案内します。
