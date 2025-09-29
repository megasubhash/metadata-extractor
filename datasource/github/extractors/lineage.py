from typing import Any, Callable, Dict, List

class GitHubLineageExtractor:
    def __init__(self, fetch: Callable[[str, Dict[str, Any] | None], Dict[str, Any]]):
        self.fetch = fetch

    def extract(self, owner: str, repo: str) -> Dict[str, Any]:
        repo_obj = self.fetch(f"/repos/{owner}/{repo}", None)
        edges: List[Dict[str, str]] = []

        if repo_obj.get("fork") and repo_obj.get("parent"):
            parent = repo_obj["parent"]["full_name"]
            edges.append({"source": parent, "target": repo_obj["full_name"], "type": "fork"})

        forks = self.fetch(f"/repos/{owner}/{repo}/forks", {"per_page": 100})
        for f in forks:
            edges.append({"source": repo_obj["full_name"], "target": f["full_name"], "type": "fork"})

        return {"edges": edges}
