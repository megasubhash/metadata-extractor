from typing import Any, Callable, Dict

class GitHubBusinessExtractor:
    def __init__(self, fetch: Callable[[str, Dict[str, Any] | None], Dict[str, Any]]):
        self.fetch = fetch

    def extract(self, owner: str, repo: str) -> Dict[str, Any]:
        repo_obj = self.fetch(f"/repos/{owner}/{repo}", None)
        topics = self.fetch(f"/repos/{owner}/{repo}/topics", None)
        return {
            "repository": {
                "full_name": repo_obj.get("full_name"),
                "description": repo_obj.get("description"),
                "homepage": repo_obj.get("homepage"),
                "default_branch": repo_obj.get("default_branch"),
                "license": (repo_obj.get("license") or {}).get("spdx_id"),
                "topics": topics.get("names", []),
            }
        }
