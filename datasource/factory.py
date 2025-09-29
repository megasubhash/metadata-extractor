from typing import Dict, Any
from .base import DataSourceStrategy

class DataSourceFactory:
    """
    Factory to instantiate the correct DataSourceStrategy based on config.
    """
    @staticmethod
    def get_strategy(config: Dict[str, Any]) -> DataSourceStrategy:
        source_type = config.get('type')
        if source_type == 'postgres':
            from .postgres.strategy import PostgresStrategy
            return PostgresStrategy(config)
        if source_type == 'github':
            from .github.strategy import GitHubStrategy
            return GitHubStrategy(config)
        raise ValueError(f"Unsupported data source type: {source_type}")
