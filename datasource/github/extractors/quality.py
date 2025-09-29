from typing import Any, Callable, Dict, List, Optional

class GitHubQualityExtractor:
    def __init__(self, fetch: Callable[[str, Dict[str, Any] | None], Dict[str, Any]]):
        self.fetch = fetch

    def _parse_ts(self, ts: Optional[str]) -> Optional[float]:
        if not ts:
            return None
        try:
            from datetime import datetime
            if ts.endswith("Z"):
                ts = ts[:-1]
            return datetime.fromisoformat(ts).timestamp()
        except Exception:
            return None

    def extract(self, owner: str, repo: str) -> Dict[str, Any]:
        repo_obj = self.fetch(f"/repos/{owner}/{repo}", None)

        issues = self.fetch(
            f"/repos/{owner}/{repo}/issues",
            {"state": "all", "per_page": 100},
        )
        issue_items = [i for i in issues if "pull_request" not in i]
        issue_open = sum(1 for i in issue_items if i.get("state") == "open")
        issue_closed = sum(1 for i in issue_items if i.get("state") == "closed")

        prs = self.fetch(
            f"/repos/{owner}/{repo}/pulls",
            {"state": "all", "per_page": 100},
        )
        pr_open = sum(1 for p in prs if p.get("state") == "open")
        pr_closed = sum(1 for p in prs if p.get("state") == "closed")

        durations: List[float] = []
        for it in issue_items:
            if it.get("state") == "closed":
                c = self._parse_ts(it.get("created_at"))
                d = self._parse_ts(it.get("closed_at"))
                if c and d and d > c:
                    durations.append(d - c)
        avg_close_seconds = sum(durations) / len(durations) if durations else None

        return {
            "repo": {
                "stargazers_count": repo_obj.get("stargazers_count"),
                "forks_count": repo_obj.get("forks_count"),
                "watchers_count": repo_obj.get("watchers_count"),
                "open_issues_count": repo_obj.get("open_issues_count"),
            },
            "issues": {"open": issue_open, "closed": issue_closed},
            "pull_requests": {"open": pr_open, "closed": pr_closed},
            "average_issue_close_time_seconds": avg_close_seconds,
        }
