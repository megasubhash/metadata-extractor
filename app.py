from __future__ import annotations

import json
from typing import Any, Dict, Optional

from flask import Flask, jsonify, request

from datasource.factory import DataSourceFactory

# Optional OpenMetadata import is handled lazily in the adapter
from integrations.openmetadata_adapter import OpenMetadataAdapter  # type: ignore

app = Flask(__name__)


def extract_metadata(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    payload schema:
    {
      "config": { ... } | null,            # preferred: full config dict
      "configPath": "config/config.yaml",  # optional: fallback path
      "flags": {
        "schema": bool,
        "business": bool,
        "quality": bool,
        "lineage": bool,
        "all": bool
      },
      "publishOpenMetadata": bool,         # optional
      "openMetadataConfig": { ... } | null # optional: OM client config dict
    }
    """
    # Load config from body
    config = payload.get("config")
    if not config:
        # Optional file-based config
        config_path = payload.get("configPath")
        if config_path:
            import yaml
            from pathlib import Path

            p = Path(config_path)
            if not p.exists():
                raise ValueError(f"Config file not found: {config_path}")
            with open(p, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
        else:
            raise ValueError("Either 'config' object or 'configPath' must be provided")

    flags = payload.get("flags", {})
    all_flag = bool(flags.get("all"))

    strategy = DataSourceFactory.get_strategy(config)

    output: Dict[str, Any] = {}
    if all_flag or flags.get("schema"):
        output["schema"] = strategy.extract_schema()
    if all_flag or flags.get("business"):
        output["business_context"] = strategy.extract_business_context()
    if all_flag or flags.get("quality"):
        output["quality_metrics"] = strategy.extract_quality_metrics()
    if all_flag or flags.get("lineage"):
        output["lineage"] = strategy.extract_lineage()

    # Optional: publish to OpenMetadata
    if payload.get("publishOpenMetadata"):
        om_conf = payload.get("openMetadataConfig")
        if om_conf is None:
            # Allow passing by path too
            om_path = payload.get("openMetadataConfigPath")
            if om_path:
                import yaml
                from pathlib import Path

                p = Path(om_path)
                if not p.exists():
                    raise ValueError(f"OpenMetadata config file not found: {om_path}")
                with open(p, "r", encoding="utf-8") as f:
                    om_conf = yaml.safe_load(f)
        if not om_conf:
            raise ValueError("'openMetadataConfig' or 'openMetadataConfigPath' required when publishOpenMetadata is true")

        adapter = OpenMetadataAdapter(om_conf)
        if config.get("type") == "postgres":
            adapter.publish_postgres(
                output,
                default_database=config.get("database"),
                default_schema=config.get("schema", "public"),
            )
        # For GitHub we generally enrich existing entities, not publish standalone

    return output


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/extract")
def extract():
    try:
        payload = request.get_json(force=True, silent=False) or {}
        result = extract_metadata(payload)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    # Simple dev server. For prod, use gunicorn/uwsgi.
    app.run(host="0.0.0.0", port=8000, debug=True)
