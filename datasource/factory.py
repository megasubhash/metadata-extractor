import logging
from typing import Any, Dict

from .base import DataSourceStrategy

logger = logging.getLogger(__name__)

class DataSourceFactory:
    """
    Factory to instantiate the correct DataSourceStrategy based on config.
    """
    @staticmethod
    def get_strategy(config: Dict[str, Any]) -> DataSourceStrategy:
        source_type = config.get('type')
        logger.info(f"Creating strategy for data source type: {source_type}")
        
        # if source_type == 'postgres':
        #     logger.info("Initializing PostgresStrategy")
        #     from .postgres.strategy import PostgresStrategy
        #     return PostgresStrategy(config)
        if source_type == 'github':
            logger.info("Initializing GitHubStrategy")
            from .github.strategy import GitHubStrategy
            return GitHubStrategy(config)
        if source_type == 'redis':
            logger.info("Initializing RedisStrategy")
            from .redis.strategy import RedisStrategy
            return RedisStrategy(config)
        
        logger.error(f"Unsupported data source type: {source_type}")
        raise ValueError(f"Unsupported data source type: {source_type}")
