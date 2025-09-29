from typing import Any, Dict

class PostgresQualityExtractor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def extract(self, cursor) -> Dict[str, Any]:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            """
        )
        tables = [row[0] for row in cursor.fetchall()]
        metrics: Dict[str, Dict[str, Any]] = {}
        for table in tables:
            cursor.execute(f"SELECT * FROM {table} LIMIT 0")
            columns = [desc[0] for desc in cursor.description]
            table_metrics: Dict[str, Any] = {}
            for col in columns:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL")
                null_count = cursor.fetchone()[0]
                cursor.execute(f"SELECT COUNT(DISTINCT {col}) FROM {table}")
                unique_count = cursor.fetchone()[0]
                table_metrics[col] = {"null_count": null_count, "unique_count": unique_count}
            metrics[table] = table_metrics
        return metrics
