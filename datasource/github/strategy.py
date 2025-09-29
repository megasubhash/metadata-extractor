import os
from typing import Any, Dict, List, Optional

import requests

from ..base import DataSourceStrategy
from .extractors.schema import GitHubSchemaExtractor
from .extractors.business import GitHubBusinessExtractor
from .extractors.lineage import GitHubLineageExtractor
from .extractors.quality import GitHubQualityExtractor


class GitHubStrategy(DataSourceStrategy):
    """
    Strategy for extracting metadata from GitHub REST API.

    Config keys:
      - type: github
      - owner: <org_or_user>
      - repo: <repository_name>
      - token: <optional_github_token> (or via GITHUB_TOKEN env var)
      - api_base: optional, default https://api.github.com
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_base = config.get("api_base", "https://api.github.com")
        self.owner = config["owner"]
        self.repo = config["repo"]
        self.token = config.get("token") or os.getenv("GITHUB_TOKEN")
        self.session = requests.Session()
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self.session.headers.update(headers)

        # Compose extractors
        self._schema_extractor = GitHubSchemaExtractor(config)
        # Pass a lightweight fetch wrapper to extractor components
        self._business_extractor = GitHubBusinessExtractor(self._get)
        self._lineage_extractor = GitHubLineageExtractor(self._get)
        self._quality_extractor = GitHubQualityExtractor(self._get)

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None):
        url = f"{self.api_base}{path}"
        resp = self.session.get(url, params=params or {})
        resp.raise_for_status()
        return resp.json()

    def extract_schema(self) -> Dict[str, Any]:
        return self._schema_extractor.extract()

    def extract_business_context(self) -> Dict[str, Any]:
        return self._business_extractor.extract(self.owner, self.repo)

    def extract_lineage(self) -> Dict[str, Any]:
        return self._lineage_extractor.extract(self.owner, self.repo)

    def extract_quality_metrics(self) -> Dict[str, Any]:
        return self._quality_extractor.extract(self.owner, self.repo)
