from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

from datasource.factory import DataSourceFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    logger.info(f"Loading configuration from: {config_path}")
    path = Path(config_path)
    if not path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        logger.info(f"Configuration loaded successfully for data source type: {config.get('type', 'unknown')}")
        return config


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
    
    logger.info("Starting metadata extraction CLI")
    logger.info(f"Arguments: {vars(args)}")

    config = load_config(args.config)
    try:
        strategy = DataSourceFactory.get_strategy(config)
    except Exception as e:
        logger.error(f"Failed to create strategy: {e}")
        sys.exit(1)

    output = {}

    if args.all or args.schema:
        logger.info("Extracting schema metadata")
        try:
            output["schema"] = strategy.extract_schema()
            logger.info("Schema extraction completed")
        except Exception as e:
            logger.error(f"Schema extraction failed: {e}")
            sys.exit(1)

    if args.all or args.business:
        logger.info("Extracting business context metadata")
        try:
            output["business_context"] = strategy.extract_business_context()
            logger.info("Business context extraction completed")
        except Exception as e:
            logger.error(f"Business context extraction failed: {e}")
            sys.exit(1)

    if args.all or args.quality:
        logger.info("Extracting quality metrics")
        try:
            output["quality_metrics"] = strategy.extract_quality_metrics()
            logger.info("Quality metrics extraction completed")
        except Exception as e:
            logger.error(f"Quality metrics extraction failed: {e}")
            sys.exit(1)

    if args.all or args.lineage:
        logger.info("Extracting lineage information")
        try:
            output["lineage"] = strategy.extract_lineage()
            logger.info("Lineage extraction completed")
        except Exception as e:
            logger.error(f"Lineage extraction failed: {e}")
            sys.exit(1)

    logger.info("All metadata extraction completed successfully")
    print(json.dumps(output, indent=2, default=str))

    


if __name__ == "__main__":
    main()
