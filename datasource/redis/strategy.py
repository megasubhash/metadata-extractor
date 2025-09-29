from typing import Any, Dict

import redis

from ..base import DataSourceStrategy
from .extractors.schema import RedisSchemaExtractor
from .extractors.business import RedisBusinessExtractor
from .extractors.quality import RedisQualityExtractor


class RedisStrategy(DataSourceStrategy):
    """
    Strategy for extracting metadata from Redis.

    Config keys:
      - type: redis
      - host, port, db, password
      - scan_count, sample_keys_limit
      - include_patterns, exclude_patterns
      - prefix_tags
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._client = None
        self._schema_extractor = RedisSchemaExtractor(config)
        self._business_extractor = RedisBusinessExtractor(config)
        self._quality_extractor = RedisQualityExtractor(config)

    def connect(self):
        if not self._client:
            self._client = redis.Redis(
                host=self.config.get("host", "localhost"),
                port=int(self.config.get("port", 6379)),
                db=int(self.config.get("db", 0)),
                password=self.config.get("password"),
                decode_responses=False,
            )

    def extract_schema(self) -> Dict[str, Any]:
        self.connect()
        return self._schema_extractor.extract(self._client)

    def extract_business_context(self) -> Dict[str, Any]:
        self.connect()
        return self._business_extractor.extract(self._client)

    def extract_quality_metrics(self) -> Dict[str, Any]:
        self.connect()
        return self._quality_extractor.extract(self._client)

    def extract_lineage(self) -> Dict[str, Any]:
        # Redis does not have built-in lineage; returning empty structure
        return {"edges": []}
