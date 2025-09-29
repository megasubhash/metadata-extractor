import psycopg2
from typing import Any, Dict, List

from ..base import DataSourceStrategy
from .extractors.schema import PostgresSchemaExtractor
from .extractors.business import PostgresBusinessExtractor
from .extractors.lineage import PostgresLineageExtractor
from .extractors.quality import PostgresQualityExtractor


class PostgresStrategy(DataSourceStrategy):
    """
    Strategy for extracting metadata from PostgreSQL.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connection = None
        # Compose extractors
        self._schema_extractor = PostgresSchemaExtractor(config)
        self._business_extractor = PostgresBusinessExtractor(config)
        self._lineage_extractor = PostgresLineageExtractor(config)
        self._quality_extractor = PostgresQualityExtractor(config)

    def connect(self):
        if not self.connection:
            self.connection = psycopg2.connect(
                host=self.config["host"],
                port=self.config["port"],
                database=self.config["database"],
                user=self.config["user"],
                password=self.config["password"],
            )

    def extract_schema(self) -> Dict[str, Any]:
        self.connect()
        cursor = self.connection.cursor()
        return self._schema_extractor.extract(cursor)

    def extract_business_context(self) -> Dict[str, Any]:
        self.connect()
        cursor = self.connection.cursor()
        return self._business_extractor.extract(cursor)

    def extract_quality_metrics(self) -> Dict[str, Any]:
        self.connect()
        cursor = self.connection.cursor()
        return self._quality_extractor.extract(cursor)

    def extract_lineage(self) -> Dict[str, Any]:
        self.connect()
        cursor = self.connection.cursor()
        return self._lineage_extractor.extract(cursor)

    def __del__(self):
        if self.connection:
            self.connection.close()
