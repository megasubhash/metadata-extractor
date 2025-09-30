from typing import Any, Dict
import logging
import os

import redis

from ..base import DataSourceStrategy

logger = logging.getLogger(__name__)
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
        logger.info("Initializing Redis extractors")
        self._schema_extractor = RedisSchemaExtractor(config)
        self._business_extractor = RedisBusinessExtractor(config)
        self._quality_extractor = RedisQualityExtractor(config)
        logger.info("Redis strategy initialized successfully")

    def connect(self):
        if not self._client:
            # Check for REDIS_URL environment variable first (for Docker)
            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                logger.info(f"Connecting to Redis using REDIS_URL: {redis_url}")
                self._client = redis.from_url(redis_url, decode_responses=False)
            else:
                # Fallback to individual config parameters
                host = self.config.get("host", "localhost")
                port = int(self.config.get("port", 6379))
                db = int(self.config.get("db", 0))
                logger.info(f"Connecting to Redis using config parameters: {host}:{port}/{db}")
                self._client = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    password=self.config.get("password"),
                    decode_responses=False,
                )
            
            # Test the connection
            try:
                self._client.ping()
                logger.info("Redis connection established successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise

    def extract_schema(self) -> Dict[str, Any]:
        logger.info("Starting Redis schema extraction")
        self.connect()
        result = self._schema_extractor.extract(self._client)
        logger.info(f"Redis schema extraction completed, found {len(result.get('key_samples', []))} key samples")
        return result

    def extract_business_context(self) -> Dict[str, Any]:
        logger.info("Starting Redis business context extraction")
        self.connect()
        result = self._business_extractor.extract(self._client)
        logger.info("Redis business context extraction completed")
        return result

    def extract_quality_metrics(self) -> Dict[str, Any]:
        logger.info("Starting Redis quality metrics extraction")
        self.connect()
        result = self._quality_extractor.extract(self._client)
        logger.info(f"Redis quality metrics extraction completed, found {result.get('total_keys', 0)} total keys")
        return result

    def extract_lineage(self) -> Dict[str, Any]:
        logger.info("Redis lineage extraction - returning empty structure (Redis has no built-in lineage)")
        # Redis does not have built-in lineage; returning empty structure
        return {"edges": []}
