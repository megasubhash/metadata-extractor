import types
from datasource.github.strategy import GitHubStrategy


def make_strategy():
    cfg = {"type": "github", "owner": "octocat", "repo": "Hello-World"}
    return GitHubStrategy(cfg)


def test_github_schema_structure():
    strat = make_strategy()
    schema = strat.extract_schema()
    assert "entities" in schema
    assert set(schema["entities"].keys()) >= {"repository", "issue", "pull_request"}
    assert isinstance(schema["entities"]["repository"]["fields"], list)


def test_github_business_context(monkeypatch):
    strat = make_strategy()

    def fake_get(path, params=None):
        if path == "/repos/octocat/Hello-World":
            return {
                "full_name": "octocat/Hello-World",
                "description": "demo repo",
                "homepage": None,
                "default_branch": "main",
                "license": {"spdx_id": "MIT"},
            }
        if path == "/repos/octocat/Hello-World/topics":
            return {"names": ["demo", "sample"]}
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(strat, "_get", fake_get)
    ctx = strat.extract_business_context()
    repo = ctx["repository"]
    assert repo["full_name"] == "octocat/Hello-World"
    assert repo["license"] == "MIT"
    assert repo["topics"] == ["demo", "sample"]


def test_github_lineage(monkeypatch):
    strat = make_strategy()

    def fake_get(path, params=None):
        if path == "/repos/octocat/Hello-World":
            return {
                "full_name": "octocat/Hello-World",
                "fork": True,
                "parent": {"full_name": "upstream/Project"},
            }
        if path == "/repos/octocat/Hello-World/forks":
            return [
                {"full_name": "user1/Hello-World"},
                {"full_name": "user2/Hello-World"},
            ]
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(strat, "_get", fake_get)
    lin = strat.extract_lineage()
    edges = lin["edges"]
    assert {e["source"] for e in edges} >= {"upstream/Project", "octocat/Hello-World"}


def test_github_quality_metrics(monkeypatch):
    strat = make_strategy()

    def fake_get(path, params=None):
        if path == "/repos/octocat/Hello-World":
            return {
                "stargazers_count": 10,
                "forks_count": 5,
                "watchers_count": 10,
                "open_issues_count": 3,
            }
        if path == "/repos/octocat/Hello-World/issues":
            # 2 issues (1 open, 1 closed). Exclude PRs by lack of 'pull_request' key.
            return [
                {"id": 1, "state": "open", "created_at": "2024-01-01T00:00:00Z"},
                {
                    "id": 2,
                    "state": "closed",
                    "created_at": "2024-01-01T00:00:00Z",
                    "closed_at": "2024-01-02T00:00:00Z",
                },
                {"id": 3, "pull_request": {}},  # PR disguised in issues endpoint, should be filtered out
            ]
        if path == "/repos/octocat/Hello-World/pulls":
            return [
                {"id": 11, "state": "open"},
                {"id": 12, "state": "closed"},
            ]
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(strat, "_get", fake_get)
    qm = strat.extract_quality_metrics()
    assert qm["repo"]["stargazers_count"] == 10
    assert qm["issues"]["open"] == 1
    assert qm["issues"]["closed"] == 1
    assert qm["pull_requests"]["open"] == 1
    assert qm["pull_requests"]["closed"] == 1
