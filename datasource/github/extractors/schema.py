from typing import Any, Dict

class GitHubSchemaExtractor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def extract(self) -> Dict[str, Any]:
        repo_fields = [
            "id",
            "name",
            "full_name",
            "private",
            "owner.login",
            "description",
            "fork",
            "created_at",
            "updated_at",
            "pushed_at",
            "size",
            "stargazers_count",
            "watchers_count",
            "forks_count",
            "open_issues_count",
            "default_branch",
            "language",
            "license.spdx_id",
            "topics",
        ]
        issue_fields = [
            "id",
            "number",
            "title",
            "state",
            "created_at",
            "updated_at",
            "closed_at",
            "user.login",
            "assignees[].login",
            "labels[].name",
            "comments",
            "is_pull_request",
        ]
        pr_fields = [
            "id",
            "number",
            "title",
            "state",
            "created_at",
            "updated_at",
            "closed_at",
            "merged_at",
            "user.login",
            "base.ref",
            "head.ref",
        ]
        return {
            "entities": {
                "repository": {"fields": repo_fields},
                "issue": {"fields": issue_fields},
                "pull_request": {"fields": pr_fields},
            }
        }
