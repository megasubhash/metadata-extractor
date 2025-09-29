from abc import ABC, abstractmethod
from typing import Any, Dict

class DataSourceStrategy(ABC):
    """
    Abstract base class for all data source strategies.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def extract_schema(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def extract_business_context(self) -> Dict[str, Any]:
        pass

    def extract_lineage(self) -> Dict[str, Any]:
        """Optional: Override if lineage extraction is supported."""
        return {}

    def extract_quality_metrics(self) -> Dict[str, Any]:
        """Optional: Override if quality metrics extraction is supported."""
        return {}
