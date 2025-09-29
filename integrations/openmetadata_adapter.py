"""
OpenMetadata adapter (optional dependency).

If the OpenMetadata client is installed (openmetadata-ingestion), this module can
push extracted metadata into an OpenMetadata server instance.

Install (optional):
  pip install "openmetadata-ingestion>=1.3,<2"

Config example (config/openmetadata.yaml):
  server: http://localhost:8585/api
  auth_provider: no-auth   # or google, okta, azure, openmetadata
  jwt_token: ""            # if using openmetadata auth provider
  service:
    name: local_pg
    type: Postgres
    connection:
      hostPort: localhost:5432
      database: sample_db
      username: sample_user
      password: sample_password
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def _om_available() -> bool:
    try:
        import metadata  # type: ignore
        return True
    except Exception:
        return False


class OpenMetadataAdapter:
    def __init__(self, om_config: Dict[str, Any]):
        self.om_config = om_config
        self._client = None
        self._service_ref = None

    def _ensure_client(self):
        if self._client is not None:
            return
        if not _om_available():
            raise RuntimeError(
                "OpenMetadata client not installed. Install 'openmetadata-ingestion' to enable publishing."
            )
        # Lazy imports to keep optional
        from metadata.ingestion.ometa.ometa_api import OpenMetadata  # type: ignore
        from metadata.generated.schema.security.client.openMetadataJWTClientConfig import (  # type: ignore
            OpenMetadataJWTClientConfig,
        )
        from metadata.generated.schema.entity.services.connections.metadata.openMetadataConnection import (  # type: ignore
            OpenMetadataConnection,
        )

        server = self.om_config.get("server")
        auth_provider = self.om_config.get("auth_provider", "no-auth")
        jwt_token = self.om_config.get("jwt_token", "")
        security_config = None
        if auth_provider == "openmetadata" and jwt_token:
            security_config = OpenMetadataJWTClientConfig(jwtToken=jwt_token)

        om_conn = OpenMetadataConnection(hostPort=server, authProvider=auth_provider, securityConfig=security_config)
        self._client = OpenMetadata(om_conn)

    def _ensure_database_service(self):
        if self._service_ref is not None:
            return
        from metadata.generated.schema.api.services.createDatabaseService import CreateDatabaseServiceRequest  # type: ignore
        from metadata.generated.schema.entity.services.databaseService import DatabaseServiceType  # type: ignore
        from metadata.generated.schema.entity.services.connections.database.postgresConnection import (  # type: ignore
            PostgresConnection,
        )

        svc_cfg = self.om_config.get("service", {})
        name = svc_cfg.get("name", "local_pg")
        conn = svc_cfg.get("connection", {})
        pg_conn = PostgresConnection(
            hostPort=conn.get("hostPort", "localhost:5432"),
            username=conn.get("username", "postgres"),
            password=conn.get("password", ""),
            database=conn.get("database", "postgres"),
        )
        req = CreateDatabaseServiceRequest(
            name=name,
            serviceType=DatabaseServiceType.Postgres,
            connection=pg_conn,
        )
        svc = self._client.create_or_update_database_service(request=req)
        self._service_ref = svc.fullyQualifiedName

    def publish_postgres(self, outputs: Dict[str, Any], default_database: Optional[str] = None, default_schema: str = "public"):
        """
        Publish Postgres results into OM:
        - schema: tables/columns/types/constraints
        - business_context: descriptions on tables/columns
        - lineage: FK edges
        - quality_metrics: basic profiles
        """
        self._ensure_client()
        self._ensure_database_service()

        schema = outputs.get("schema", {})
        business = outputs.get("business_context", {})
        lineage = outputs.get("lineage", {})
        quality = outputs.get("quality_metrics", {})

        # Lazy imports to keep optional
        from metadata.generated.schema.api.data.createTable import CreateTableRequest  # type: ignore
        from metadata.generated.schema.entity.data.table import Column, DataType  # type: ignore
        from metadata.generated.schema.type.entityReference import EntityReference  # type: ignore
        from metadata.generated.schema.api.lineage.addLineage import AddLineageRequest, EntitiesEdge  # type: ignore
        from metadata.generated.schema.api.data.createDatabase import CreateDatabaseRequest  # type: ignore
        from metadata.generated.schema.api.data.createDatabaseSchema import CreateDatabaseSchemaRequest  # type: ignore
        from metadata.generated.schema.api.data.createTableProfile import CreateTableProfileRequest  # type: ignore
        from metadata.generated.schema.entity.data.table import TableProfile, ColumnProfile  # type: ignore

        owner_ref = None  # could be wired to a Team/User later

        # Ensure Database and Schema
        db_name = default_database or self.om_config.get("service", {}).get("connection", {}).get("database", "postgres")
        db_req = CreateDatabaseRequest(name=db_name, service=self._service_ref)
        db = self._client.create_or_update_database(db_req)
        db_schema_req = CreateDatabaseSchemaRequest(name=default_schema, database=db.fullyQualifiedName)
        db_schema = self._client.create_or_update_database_schema(db_schema_req)

        # Create/Update tables
        table_comments = business.get("tables", {}) if isinstance(business, dict) else {}
        column_comments = business.get("columns", {}) if isinstance(business, dict) else {}

        for table_name, columns in schema.items():
            cols: List[Column] = []
            for col in columns["columns"] if isinstance(columns, dict) and "columns" in columns else columns:
                # DataType mapping (very naive; improve as needed)
                dtype = str(col.get("type", "STRING")).upper()
                om_dtype = DataType.String
                if "INT" in dtype:
                    om_dtype = DataType.Int
                elif "CHAR" in dtype or "TEXT" in dtype or "STRING" in dtype:
                    om_dtype = DataType.String
                elif "DATE" in dtype or "TIME" in dtype:
                    om_dtype = DataType.DateTime
                elif "BOOL" in dtype:
                    om_dtype = DataType.Boolean
                elif "FLOAT" in dtype or "DOUBLE" in dtype or "NUMERIC" in dtype or "DEC" in dtype:
                    om_dtype = DataType.Number

                cols.append(
                    Column(
                        name=col["name"],
                        dataType=om_dtype,
                        description=(column_comments.get(table_name, {}) or {}).get(col["name"]) if column_comments else None,
                    )
                )

            table_req = CreateTableRequest(
                name=table_name,
                databaseSchema=db_schema.fullyQualifiedName,
                columns=cols,
                description=table_comments.get(table_name),
                owner=owner_ref,
            )
            table = self._client.create_or_update_table(table_req)

            # Table/Column profiles (quality metrics)
            if table_name in quality:
                col_profiles: List[ColumnProfile] = []
                for col_name, metrics in quality[table_name].items():
                    col_profiles.append(
                        ColumnProfile(
                            name=col_name,
                            nullCount=metrics.get("null_count"),
                            distinctCount=metrics.get("unique_count"),
                        )
                    )
                tp = TableProfile(columnProfile=col_profiles)
                tp_req = CreateTableProfileRequest(table=table.fullyQualifiedName, tableProfile=tp)
                self._client.create_or_update_table_profile(tp_req)

        # Lineage edges
        for edge in lineage.get("edges", []):
            src_t = f"{db_name}.{default_schema}.{edge['source_table']}"
            dst_t = f"{db_name}.{default_schema}.{edge['target_table']}"
            src = self._client.get_by_name(entity=CreateTableRequest.entity, fqn=src_t)  # type: ignore
            dst = self._client.get_by_name(entity=CreateTableRequest.entity, fqn=dst_t)  # type: ignore
            if src and dst:
                self._client.add_lineage(AddLineageRequest(edge=EntitiesEdge(fromEntity=src.fullyQualifiedName, toEntity=dst.fullyQualifiedName)))

    # GitHub: map topics to tags and attach to tables (as an example)
    def attach_github_topics_as_tags(self, db_fqn_prefix: str, business_ctx: Dict[str, Any]):
        """
        Attach GitHub topics from business context to OM tables under db_fqn_prefix
        Example db_fqn_prefix: "local_pg.sample_db.public"
        """
        self._ensure_client()
        from metadata.generated.schema.type.tagLabel import TagLabel, TagLabelStyle, TagSource  # type: ignore
        topics = (business_ctx.get("repository") or {}).get("topics", [])
        if not topics:
            return
        # Example: attach tags to all tables under the schema
        tables = self._client.list_all_entities(entity=CreateTableProfileRequest.entity, fields=["tags"])  # type: ignore
        for t in tables or []:
            if not str(t.fullyQualifiedName).startswith(db_fqn_prefix):
                continue
            labels = [TagLabel(tagFQN=f"Topic.{topic}", source=TagSource.Classification, labelType=TagLabelStyle.Manual)]
            self._client.patch_tag_labels(entity=t, tag_labels=labels)
