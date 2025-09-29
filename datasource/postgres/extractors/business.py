from typing import Any, Dict

class PostgresBusinessExtractor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def extract(self, cursor) -> Dict[str, Any]:
        # Table comments
        cursor.execute(
            """
            SELECT c.relname AS table_name, obj_description(c.oid) AS table_comment
            FROM pg_class c
            WHERE c.relkind = 'r' AND c.relname NOT LIKE 'pg_%' AND c.relname NOT LIKE 'sql_%'
            """
        )
        table_comments = {row[0]: row[1] for row in cursor.fetchall()}

        # Column comments
        cursor.execute(
            """
            SELECT c.relname AS table_name, a.attname AS column_name, col_description(a.attrelid, a.attnum) AS column_comment
            FROM pg_class c
            JOIN pg_attribute a ON a.attrelid = c.oid
            WHERE c.relkind = 'r' AND a.attnum > 0 AND c.relname NOT LIKE 'pg_%' AND c.relname NOT LIKE 'sql_%'
            """
        )
        column_comments: Dict[str, Dict[str, Any]] = {}
        for table, col, comment in cursor.fetchall():
            if table not in column_comments:
                column_comments[table] = {}
            column_comments[table][col] = comment
        return {"tables": table_comments, "columns": column_comments}
