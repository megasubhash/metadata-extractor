import argparse
import json
import sys
from pathlib import Path

import yaml

from datasource.factory import DataSourceFactory


def load_config(config_path: str) -> dict:
    path = Path(config_path)
    if not path.exists():
        print(f"Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Data Source Metadata Extractor")
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to YAML config file",
    )
    parser.add_argument(
        "--schema",
        action="store_true",
        help="Extract schema metadata",
    )
    parser.add_argument(
        "--business",
        action="store_true",
        help="Extract business context (comments, tags if available)",
    )
    parser.add_argument(
        "--quality",
        action="store_true",
        help="Extract basic data quality metrics (null/unique counts)",
    )
    parser.add_argument(
        "--lineage",
        action="store_true",
        help="Extract lineage using foreign keys",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Extract all available metadata",
    )
    parser.add_argument(
        "--publish-openmetadata",
        action="store_true",
        help="Publish extracted metadata to OpenMetadata (requires optional dependency)",
    )
    parser.add_argument(
        "--om-config",
        default="config/openmetadata.yaml",
        help="Path to OpenMetadata config YAML",
    )

    args = parser.parse_args()

    config = load_config(args.config)
    strategy = DataSourceFactory.get_strategy(config)

    output = {}

    if args.all or args.schema:
        output["schema"] = strategy.extract_schema()

    if args.all or args.business:
        output["business_context"] = strategy.extract_business_context()

    if args.all or args.quality:
        output["quality_metrics"] = strategy.extract_quality_metrics()

    if args.all or args.lineage:
        output["lineage"] = strategy.extract_lineage()

    print(json.dumps(output, indent=2, default=str))

    # Optional: publish to OpenMetadata
    if args.publish_openmetadata:
        try:
            om_conf = load_config(args.om_config)
            from integrations.openmetadata_adapter import OpenMetadataAdapter

            adapter = OpenMetadataAdapter(om_conf)
            # For Postgres: publish everything
            if config.get("type") == "postgres":
                default_db = config.get("database")
                adapter.publish_postgres(output, default_database=default_db, default_schema=config.get("schema", "public"))
            # Example: attach GitHub topics as tags onto a given schema (if you choose to)
            elif config.get("type") == "github":
                pass  # Typically you’d enrich data entities, not publish a repo as a table
        except Exception as e:
            print(f"OpenMetadata publish failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
