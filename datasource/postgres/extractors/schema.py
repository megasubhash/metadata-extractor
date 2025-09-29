from typing import Any, Dict, List

class PostgresSchemaExtractor:
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
        schema: Dict[str, Any] = {}
        for table in tables:
            # Columns
            cursor.execute(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
                """,
                (table,),
            )
            columns = [
                {
                    "name": col[0],
                    "type": col[1],
                    "nullable": col[2],
                    "default": col[3],
                }
                for col in cursor.fetchall()
            ]

            # Primary Key columns
            cursor.execute(
                """
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                WHERE tc.table_schema = 'public'
                  AND tc.table_name = %s
                  AND tc.constraint_type = 'PRIMARY KEY'
                ORDER BY kcu.ordinal_position
                """,
                (table,),
            )
            pk_columns = [r[0] for r in cursor.fetchall()]

            # Unique constraints (group columns by constraint)
            cursor.execute(
                """
                SELECT tc.constraint_name, kcu.column_name, kcu.ordinal_position
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                WHERE tc.table_schema = 'public'
                  AND tc.table_name = %s
                  AND tc.constraint_type = 'UNIQUE'
                ORDER BY tc.constraint_name, kcu.ordinal_position
                """,
                (table,),
            )
            unique_map: Dict[str, List[str]] = {}
            for cname, col, _ord in cursor.fetchall():
                unique_map.setdefault(cname, []).append(col)
            unique_constraints = [
                {"name": name, "columns": cols} for name, cols in unique_map.items()
            ]

            # Foreign keys
            cursor.execute(
                """
                SELECT
                  tc.constraint_name,
                  kcu.column_name,
                  ccu.table_name AS foreign_table,
                  ccu.column_name AS foreign_column,
                  kcu.ordinal_position
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
                WHERE tc.table_schema = 'public'
                  AND tc.table_name = %s
                  AND tc.constraint_type = 'FOREIGN KEY'
                ORDER BY tc.constraint_name, kcu.ordinal_position
                """,
                (table,),
            )
            fk_rows = cursor.fetchall()
            fk_map: Dict[str, Dict[str, Any]] = {}
            for cname, col, ftab, fcol, _ord in fk_rows:
                fk_map[cname] = {
                    "name": cname,
                    "column": col,
                    "references": {"table": ftab, "column": fcol},
                }
            foreign_keys = list(fk_map.values())

            schema[table] = {
                "columns": columns,
                "constraints": {
                    "primary_key": pk_columns,
                    "unique": unique_constraints,
                    "foreign_keys": foreign_keys,
                },
            }
        return schema
