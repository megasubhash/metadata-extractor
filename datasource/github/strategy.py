import os
from typing import Any, Dict, Optional
import logging

import requests

from ..base import DataSourceStrategy

logger = logging.getLogger(__name__)
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
        logger.info(f"Initializing GitHub strategy for {self.owner}/{self.repo}")
        self.token = config.get("token") or os.getenv("GITHUB_TOKEN")
        if self.token:
            logger.info("GitHub token found, using authenticated requests")
        else:
            logger.warning("No GitHub token found, using unauthenticated requests (rate limited)")
            
        self.session = requests.Session()
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self.session.headers.update(headers)

        # Compose extractors
        logger.info("Initializing GitHub extractors")
        self._schema_extractor = GitHubSchemaExtractor(config)
        # Pass a lightweight fetch wrapper to extractor components
        self._business_extractor = GitHubBusinessExtractor(self._get)
        self._lineage_extractor = GitHubLineageExtractor(self._get)
        self._quality_extractor = GitHubQualityExtractor(self._get)
        logger.info("GitHub strategy initialized successfully")

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None):
        url = f"{self.api_base}{path}"
        logger.debug(f"Making GitHub API request to: {url}")
        try:
            resp = self.session.get(url, params=params or {})
            resp.raise_for_status()
            logger.debug(f"GitHub API request successful: {resp.status_code}")
            return resp.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API request failed for {url}: {e}")
            raise

    def extract_schema(self) -> Dict[str, Any]:
        logger.info("Starting GitHub schema extraction")
        result = self._schema_extractor.extract()
        logger.info("GitHub schema extraction completed")
        return result

    def extract_business_context(self) -> Dict[str, Any]:
        logger.info(f"Starting GitHub business context extraction for {self.owner}/{self.repo}")
        result = self._business_extractor.extract(self.owner, self.repo)
        logger.info("GitHub business context extraction completed")
        return result

    def extract_lineage(self) -> Dict[str, Any]:
        logger.info(f"Starting GitHub lineage extraction for {self.owner}/{self.repo}")
        result = self._lineage_extractor.extract(self.owner, self.repo)
        logger.info(f"GitHub lineage extraction completed, found {len(result.get('edges', []))} relationships")
        return result

    def extract_quality_metrics(self) -> Dict[str, Any]:
        logger.info(f"Starting GitHub quality metrics extraction for {self.owner}/{self.repo}")
        result = self._quality_extractor.extract(self.owner, self.repo)
        logger.info("GitHub quality metrics extraction completed")
        return result
