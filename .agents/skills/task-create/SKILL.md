---
name: task-create
description: Use this skill when the user asks to create, register, or file a new task or issue in GitHub for project management.
---

# Task Creation Skill (`task-create`)

新しいタスクを GitHub Issue に起票するための標準手順です。  
タスク起票の段階では詳細な設計は不要であり、**「前提条件」** と **「達成条件」** を明確にすることを最優先とします。

---

## 実行フロー

### 1. 要件のヒアリング・整理
ユーザーの要望から以下の項目を整理します。情報が不足している場合は、推測せずユーザーに確認します。

1. **タイトル**: `[Task]: <簡潔なタスク名>`
2. **概要**: タスクの背景や目的
3. **前提条件 (Prerequisites)**:
   - このタスクに着手・完了するために必要な依存関係（他Issueの完了、環境構築、リソース等）。
   - なければ「なし」とする。
4. **達成条件 (Acceptance Criteria / DoD)**:
   - 何が完了したらこのIssueをクローズできるかのチェックリスト（`- [ ] ...` 形式）。
5. **親Issue / 関連Issue**:
   - 既存タスクの分割から生じた子タスクの場合、親Issue番号（例: `#1`）。

### 2. Issue 本文の生成
`.github/ISSUE_TEMPLATE/task.yml` の構成に従って本文を作成します。

```markdown
## 概要
<目的や背景>

## 前提条件 (Prerequisites)
- [ ] #XX の完了（または「なし」）

## 達成条件 (Acceptance Criteria / Definition of Done)
- [ ] 〇〇が作成されていること
- [ ] 〇〇で動作確認ができること

## 親Issue / 関連Issue
<#XX または「なし」>

## 備考 / 参考情報
<参考リンクや関連情報（任意）>
```

### 3. Issue の作成
GitHub MCPツール `issue_write` を使用して起票します。

* **method**: `"create"`
* **owner**: リポジトリオーナー（例: `"walk8243"`）
* **repo**: `"langgraph-statcast-agent"`
* **title**: `[Task]: <タスク名>`
* **body**: 上記で生成した本文
* **labels**: `["task"]`

### 4. 完了報告
作成された Issue の番号と URL をユーザーに報告し、次のステップ（実行計画立案 `task-plan`）への移行を案内します。
