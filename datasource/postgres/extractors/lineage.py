from typing import Any, Dict, List

class PostgresLineageExtractor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def extract(self, cursor) -> Dict[str, Any]:
        cursor.execute(
            """
            SELECT
              tc.constraint_name,
              tc.table_name   AS source_table,
              kcu.column_name AS source_column,
              ccu.table_name  AS target_table,
              ccu.column_name AS target_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
            WHERE tc.table_schema = 'public'
              AND tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.table_name, tc.constraint_name, kcu.ordinal_position
            """
        )
        edges: List[Dict[str, Any]] = []
        for cname, s_table, s_col, t_table, t_col in cursor.fetchall():
            edges.append(
                {
                    "constraint_name": cname,
                    "source_table": s_table,
                    "source_column": s_col,
                    "target_table": t_table,
                    "target_column": t_col,
                }
            )
        return {"edges": edges}
