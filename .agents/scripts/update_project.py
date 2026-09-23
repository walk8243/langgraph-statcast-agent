#!/usr/bin/env python3
"""GitHub Project V2 のフィールド (Status, Size, Start date, End date) を更新するヘルパースクリプト"""

from __future__ import annotations

import argparse
from datetime import date
import json
import subprocess
import sys
from typing import Any, Optional

DEFAULT_OWNER = "walk8243"
DEFAULT_PROJECT_NUMBER = 6

FALLBACK_PROJECT_ID = "PVT_kwHOANNDn84BkKuL"
FALLBACK_FIELDS = {
    "Status": {
        "id": "PVTSSF_lAHOANNDn84BkKuLzhi8RPI",
        "options": {
            "Backlog": "f75ad846",
            "Ready": "61e4505c",
            "In progress": "47fc9ee4",
            "In review": "df73e18b",
            "Done": "98236657",
        },
    },
    "Size": {
        "id": "PVTSSF_lAHOANNDn84BkKuLzhi8RSU",
        "options": {
            "XS": "6c6483d2",
            "S": "f784b110",
            "M": "7515a9f1",
            "L": "817d0097",
            "XL": "db339eb2",
        },
    },
    "Start date": {
        "id": "PVTF_lAHOANNDn84BkKuLzhi8RSc",
    },
    "End date": {
        "id": "PVTF_lAHOANNDn84BkKuLzhi8hqM",
    },
}


def run_gh_graphql(query: str, variables: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """GitHub CLI (gh api graphql) を実行して JSON レスポンスを取得する"""
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    if variables:
        for k, v in variables.items():
            if isinstance(v, int):
                cmd.extend(["-F", f"{k}={v}"])
            elif isinstance(v, (dict, list)):
                cmd.extend(["-F", f"{k}={json.dumps(v)}"])
            else:
                cmd.extend(["-f", f"{k}={v}"])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gh api graphql failed: {result.stderr.strip() or result.stdout.strip()}")

    return json.loads(result.stdout)


def get_project_metadata(owner: str, project_number: int) -> tuple[str, dict[str, Any]]:
    """プロジェクトIDと各フィールド定義を取得する"""
    query = """
    query($owner: String!, $number: Int!) {
      user(login: $owner) {
        projectV2(number: $number) {
          id
          fields(first: 30) {
            nodes {
              ... on ProjectV2Field {
                id
                name
              }
              ... on ProjectV2SingleSelectField {
                id
                name
                options {
                  id
                  name
                }
              }
            }
          }
        }
      }
    }
    """
    try:
        data = run_gh_graphql(query, {"owner": owner, "number": project_number})
        project = data.get("data", {}).get("user", {}).get("projectV2")
        if not project:
            return FALLBACK_PROJECT_ID, FALLBACK_FIELDS

        project_id = project["id"]
        fields_map: dict[str, Any] = {}
        for f in project.get("fields", {}).get("nodes", []):
            fname = f.get("name")
            if not fname:
                continue
            entry: dict[str, Any] = {"id": f["id"]}
            if "options" in f:
                entry["options"] = {opt["name"]: opt["id"] for opt in f["options"]}
            fields_map[fname] = entry

        return project_id, fields_map
    except Exception as e:
        print(f"Warning: Failed to fetch live project metadata ({e}). Using fallback IDs.", file=sys.stderr)
        return FALLBACK_PROJECT_ID, FALLBACK_FIELDS


DEFAULT_REPO = "langgraph-statcast-agent"


def find_item_id_for_issue(owner: str, project_number: int, issue_number: int, repo: str = DEFAULT_REPO) -> Optional[str]:
    """Issue番号から ProjectV2 の Item ID を検索する"""
    # 1. リポジトリの Issue / PR から projectItems を直接検索
    query_direct = """
    query($owner: String!, $repo: String!, $number: Int!) {
      repository(owner: $owner, name: $repo) {
        issueOrPullRequest(number: $number) {
          ... on Issue {
            projectItems(first: 10) {
              nodes {
                id
                project {
                  ... on ProjectV2 {
                    number
                  }
                }
              }
            }
          }
          ... on PullRequest {
            projectItems(first: 10) {
              nodes {
                id
                project {
                  ... on ProjectV2 {
                    number
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    try:
        data = run_gh_graphql(query_direct, {"owner": owner, "repo": repo, "number": issue_number})
        content = data.get("data", {}).get("repository", {}).get("issueOrPullRequest")
        if content:
            items = content.get("projectItems", {}).get("nodes", [])
            for item in items:
                if item.get("project", {}).get("number") == project_number:
                    return item["id"]
    except Exception:
        pass

    # 2. フォールバック: プロジェクト側から items を検索
    query = """
    query($owner: String!, $number: Int!) {
      user(login: $owner) {
        projectV2(number: $number) {
          items(last: 100) {
            nodes {
              id
              content {
                ... on Issue {
                  number
                }
                ... on PullRequest {
                  number
                }
              }
            }
          }
        }
      }
    }
    """
    data = run_gh_graphql(query, {"owner": owner, "number": project_number})
    items = data.get("data", {}).get("user", {}).get("projectV2", {}).get("items", {}).get("nodes", [])

    for item in items:
        content = item.get("content")
        if content and content.get("number") == issue_number:
            return item["id"]

    return None


def update_single_select_field(project_id: str, item_id: str, field_id: str, option_id: str) -> None:
    """単一選択フィールド (Status, Size 等) を更新する"""
    query = """
    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
      updateProjectV2ItemFieldValue(
        input: {
          projectId: $projectId
          itemId: $itemId
          fieldId: $fieldId
          value: { singleSelectOptionId: $optionId }
        }
      ) {
        projectV2Item { id }
      }
    }
    """
    run_gh_graphql(
        query,
        {
            "projectId": project_id,
            "itemId": item_id,
            "fieldId": field_id,
            "optionId": option_id,
        },
    )


def update_date_field(project_id: str, item_id: str, field_id: str, date_str: str) -> None:
    """日付フィールド (Start date, End date) を更新する"""
    query = """
    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $dateStr: Date!) {
      updateProjectV2ItemFieldValue(
        input: {
          projectId: $projectId
          itemId: $itemId
          fieldId: $fieldId
          value: { date: $dateStr }
        }
      ) {
        projectV2Item { id }
      }
    }
    """
    run_gh_graphql(
        query,
        {
            "projectId": project_id,
            "itemId": item_id,
            "fieldId": field_id,
            "dateStr": date_str,
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="GitHub Project V2 のフィールドを更新します。")
    parser.add_argument("--issue", type=int, required=True, help="対象 Issue / PR 番号")
    parser.add_argument(
        "--status",
        choices=["Backlog", "Ready", "In progress", "In review", "Done"],
        help="変更後のステータス",
    )
    parser.add_argument(
        "--size",
        choices=["XS", "S", "M", "L", "XL"],
        help="設定する工数サイズ",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="着手日 (YYYY-MM-DD または 'today')",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="完了日 (YYYY-MM-DD または 'today')",
    )
    parser.add_argument(
        "--owner",
        type=str,
        default=DEFAULT_OWNER,
        help=f"リポジトリ/プロジェクトオーナー (デフォルト: {DEFAULT_OWNER})",
    )
    parser.add_argument(
        "--project-number",
        type=int,
        default=DEFAULT_PROJECT_NUMBER,
        help=f"プロジェクト番号 (デフォルト: {DEFAULT_PROJECT_NUMBER})",
    )

    args = parser.parse_args()

    project_id, fields_map = get_project_metadata(args.owner, args.project_number)

    item_id = find_item_id_for_issue(args.owner, args.project_number, args.issue)
    if not item_id:
        print(f"Error: Issue #{args.issue} not found in Project {args.project_number}.", file=sys.stderr)
        sys.exit(1)

    updated_fields = []

    # 1. Status 更新
    if args.status:
        status_info = fields_map.get("Status", FALLBACK_FIELDS["Status"])
        option_id = status_info["options"].get(args.status)
        if option_id:
            update_single_select_field(project_id, item_id, status_info["id"], option_id)
            updated_fields.append(f"Status={args.status}")
        else:
            print(f"Warning: Option '{args.status}' not found for Status.", file=sys.stderr)

    # 2. Size 更新
    if args.size:
        size_info = fields_map.get("Size", FALLBACK_FIELDS["Size"])
        option_id = size_info["options"].get(args.size)
        if option_id:
            update_single_select_field(project_id, item_id, size_info["id"], option_id)
            updated_fields.append(f"Size={args.size}")
        else:
            print(f"Warning: Option '{args.size}' not found for Size.", file=sys.stderr)

    # 3. Start date 更新
    if args.start_date:
        start_date_val = date.today().isoformat() if args.start_date.lower() == "today" else args.start_date
        date_field_info = fields_map.get("Start date", FALLBACK_FIELDS["Start date"])
        update_date_field(project_id, item_id, date_field_info["id"], start_date_val)
        updated_fields.append(f"Start date={start_date_val}")

    # 4. End date 更新
    if args.end_date:
        end_date_val = date.today().isoformat() if args.end_date.lower() == "today" else args.end_date
        date_field_info = fields_map.get("End date", FALLBACK_FIELDS["End date"])
        update_date_field(project_id, item_id, date_field_info["id"], end_date_val)
        updated_fields.append(f"End date={end_date_val}")

    if updated_fields:
        print(f"Successfully updated Issue #{args.issue} in Project {args.project_number}: {', '.join(updated_fields)}")
    else:
        print("No fields specified to update.")


if __name__ == "__main__":
    main()
