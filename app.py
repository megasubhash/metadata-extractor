from __future__ import annotations

import json
import os
import threading
import uuid
from typing import Any, Dict, Optional

from flask import Flask, jsonify, request

from datasource.factory import DataSourceFactory

# Optional OpenMetadata import is handled lazily in the adapter
from integrations.openmetadata_adapter import OpenMetadataAdapter  # type: ignore

app = Flask(__name__)

# Optional RQ/Redis integration for background jobs
HAS_RQ = False
HAS_REDIS = False
try:
    import rq  # type: ignore
    HAS_RQ = True
except Exception:
    HAS_RQ = False

try:
    import redis  # type: ignore
    HAS_REDIS = True
except Exception:
    HAS_REDIS = False

redis_conn = None
rq_queue = None
if HAS_REDIS:
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_conn = redis.from_url(redis_url)
        if HAS_RQ:
            rq_queue = rq.Queue("extract", connection=redis_conn)
    except Exception:
        redis_conn = None
        rq_queue = None

# In-memory fallback job store
JOBS: Dict[str, Dict[str, Any]] = {}


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


# Background job runner for in-memory fallback
def _run_job_in_thread(job_id: str, payload: Dict[str, Any]):
    try:
        JOBS[job_id]["status"] = "running"
        result = extract_metadata(payload)
        JOBS[job_id]["status"] = "done"
        JOBS[job_id]["result"] = result
    except Exception as e:
        JOBS[job_id]["status"] = "error"
        JOBS[job_id]["error"] = str(e)


# RQ task function is defined in jobs/tasks.py to avoid __main__ import issues


@app.post("/jobs")
def create_job():
    try:
        payload = request.get_json(force=True, silent=False) or {}
        # Prefer RQ if available and Redis is connected
        if rq_queue is not None:
            # Import the task from an importable module (not __main__)
            from jobs.tasks import task_extract  # type: ignore
            job = rq_queue.enqueue(task_extract, payload, job_timeout=1800, result_ttl=3600)  # 30m timeout, 1h result TTL
            return jsonify({"jobId": job.id, "backend": "rq"}), 202

        # In-memory fallback
        job_id = str(uuid.uuid4())
        JOBS[job_id] = {"status": "queued"}
        t = threading.Thread(target=_run_job_in_thread, args=(job_id, payload), daemon=True)
        t.start()
        return jsonify({"jobId": job_id, "backend": "memory"}), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.get("/jobs/<job_id>")
def get_job(job_id: str):
    # Try RQ first
    if rq_queue is not None:
        try:
            from rq.job import Job  # type: ignore

            job = Job.fetch(job_id, connection=rq_queue.connection)
            status = job.get_status(refresh=True)
            resp: Dict[str, Any] = {"jobId": job.id, "status": status}
            if job.is_finished:
                resp["result"] = job.result
            if job.is_failed:
                resp["error"] = str(job.exc_info or "job failed")
            return jsonify(resp)
        except Exception:
            # Fall through to memory store
            pass

    # In-memory fallback
    if job_id in JOBS:
        return jsonify({"jobId": job_id, **JOBS[job_id]})
    return jsonify({"error": "job not found"}), 404


if __name__ == "__main__":
    # Simple dev server. For prod, use gunicorn/uwsgi.
    app.run(host="0.0.0.0", port=8000, debug=False)
