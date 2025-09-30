from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from typing import Any, Dict, Optional

from flask import Flask, jsonify, request

from datasource.factory import DataSourceFactory

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('metadata_extractor.log')
    ]
)
logger = logging.getLogger(__name__)


app = Flask(__name__)

# Optional RQ/Redis integration for background jobs
HAS_RQ = False
HAS_REDIS = False
try:
    import rq
    HAS_RQ = True
    logger.info("RQ library loaded successfully")
except Exception as e:
    HAS_RQ = False
    logger.warning(f"RQ library not available: {e}")

try:
    import redis 
    HAS_REDIS = True
    logger.info("Redis library loaded successfully")
except Exception as e:
    HAS_REDIS = False
    logger.warning(f"Redis library not available: {e}")

redis_conn = None
rq_queue = None
if HAS_REDIS:
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_conn = redis.from_url(redis_url)
        logger.info(f"Connected to Redis at {redis_url}")
        if HAS_RQ:
            rq_queue = rq.Queue("extract", connection=redis_conn)
            logger.info("RQ queue 'extract' initialized successfully")
    except Exception as e:
        redis_conn = None
        rq_queue = None
        logger.error(f"Failed to connect to Redis: {e}")

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
      }
    }
    """
    logger.info("Starting metadata extraction")
    
    # Load config from body
    config = payload.get("config")
    if not config:
        logger.info("No inline config found, checking for config file path")
        # Optional file-based config
        config_path = payload.get("configPath")
        if config_path:
            import yaml
            from pathlib import Path

            p = Path(config_path)
            if not p.exists():
                logger.error(f"Config file not found: {config_path}")
                raise ValueError(f"Config file not found: {config_path}")
            logger.info(f"Loading config from file: {config_path}")
            with open(p, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
        else:
            logger.error("No config provided - neither inline nor file path")
            raise ValueError("Either 'config' object or 'configPath' must be provided")

    data_source_type = config.get("type", "unknown")
    logger.info(f"Extracting metadata from data source type: {data_source_type}")
    
    flags = payload.get("flags", {})
    all_flag = bool(flags.get("all"))
    logger.info(f"Extraction flags: {flags}, all_flag: {all_flag}")

    try:
        strategy = DataSourceFactory.get_strategy(config)
        logger.info(f"Successfully created strategy for {data_source_type}")
    except Exception as e:
        logger.error(f"Failed to create strategy for {data_source_type}: {e}")
        raise

    output: Dict[str, Any] = {}
    
    if all_flag or flags.get("schema"):
        logger.info("Extracting schema metadata")
        try:
            output["schema"] = strategy.extract_schema()
            logger.info("Schema extraction completed successfully")
        except Exception as e:
            logger.error(f"Schema extraction failed: {e}")
            raise
            
    if all_flag or flags.get("business"):
        logger.info("Extracting business context metadata")
        try:
            output["business_context"] = strategy.extract_business_context()
            logger.info("Business context extraction completed successfully")
        except Exception as e:
            logger.error(f"Business context extraction failed: {e}")
            raise
            
    if all_flag or flags.get("quality"):
        logger.info("Extracting quality metrics")
        try:
            output["quality_metrics"] = strategy.extract_quality_metrics()
            logger.info("Quality metrics extraction completed successfully")
        except Exception as e:
            logger.error(f"Quality metrics extraction failed: {e}")
            raise
            
    if all_flag or flags.get("lineage"):
        logger.info("Extracting lineage information")
        try:
            output["lineage"] = strategy.extract_lineage()
            logger.info("Lineage extraction completed successfully")
        except Exception as e:
            logger.error(f"Lineage extraction failed: {e}")
            raise

    logger.info(f"Metadata extraction completed successfully for {data_source_type}")
    return output


@app.get("/health")
def health():
    logger.info("Health check requested")
    return jsonify({"status": "ok"})


@app.post("/extract")
def extract():
    logger.info("Synchronous extraction request received")
    try:
        payload = request.get_json(force=True, silent=False) or {}
        logger.info(f"Processing extraction request with payload keys: {list(payload.keys())}")
        result = extract_metadata(payload)
        logger.info("Synchronous extraction completed successfully")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Synchronous extraction failed: {e}")
        return jsonify({"error": str(e)}), 400


# Background job runner for in-memory fallback
def _run_job_in_thread(job_id: str, payload: Dict[str, Any]):
    logger.info(f"Starting background job {job_id}")
    try:
        JOBS[job_id]["status"] = "running"
        logger.info(f"Job {job_id} status updated to running")
        result = extract_metadata(payload)
        JOBS[job_id]["status"] = "done"
        JOBS[job_id]["result"] = result
        logger.info(f"Background job {job_id} completed successfully")
    except Exception as e:
        JOBS[job_id]["status"] = "error"
        JOBS[job_id]["error"] = str(e)
        logger.error(f"Background job {job_id} failed: {e}")



@app.post("/jobs")
def create_job():
    logger.info("Background job creation request received")
    try:
        payload = request.get_json(force=True, silent=False) or {}
        logger.info(f"Processing job creation request with payload keys: {list(payload.keys())}")
        
        # Prefer RQ if available and Redis is connected
        if rq_queue is not None:
            logger.info("Using RQ backend for job processing")
            from jobs.tasks import task_extract  # type: ignore
            job = rq_queue.enqueue(task_extract, payload, job_timeout=1800, result_ttl=3600)  # 30m timeout, 1h result TTL
            logger.info(f"RQ job created with ID: {job.id}")
            return jsonify({"jobId": job.id, "backend": "rq"}), 202

        # In-memory fallback
        logger.info("Using in-memory backend for job processing")
        job_id = str(uuid.uuid4())
        JOBS[job_id] = {"status": "queued"}
        t = threading.Thread(target=_run_job_in_thread, args=(job_id, payload), daemon=True)
        t.start()
        logger.info(f"In-memory job created with ID: {job_id}")
        return jsonify({"jobId": job_id, "backend": "memory"}), 202
    except Exception as e:
        logger.error(f"Job creation failed: {e}")
        return jsonify({"error": str(e)}), 400


@app.get("/jobs/<job_id>")
def get_job(job_id: str):
    logger.info(f"Job status request for job ID: {job_id}")
    
    if rq_queue is not None:
        try:
            logger.info(f"Checking RQ backend for job {job_id}")
            from rq.job import Job  # type: ignore

            job = Job.fetch(job_id, connection=rq_queue.connection)
            status = job.get_status(refresh=True)
            logger.info(f"RQ job {job_id} status: {status}")
            resp: Dict[str, Any] = {"jobId": job.id, "status": status}
            if job.is_finished:
                resp["result"] = job.result
                logger.info(f"RQ job {job_id} completed successfully")
            if job.is_failed:
                resp["error"] = str(job.exc_info or "job failed")
                logger.error(f"RQ job {job_id} failed: {resp['error']}")
            return jsonify(resp)
        except Exception as e:
            logger.warning(f"Failed to fetch RQ job {job_id}: {e}, falling back to memory store")
            pass

    logger.info(f"Checking in-memory backend for job {job_id}")
    if job_id in JOBS:
        job_status = JOBS[job_id].get("status", "unknown")
        logger.info(f"In-memory job {job_id} status: {job_status}")
        return jsonify({"jobId": job_id, **JOBS[job_id]})
    
    logger.warning(f"Job {job_id} not found in any backend")
    return jsonify({"error": "job not found"}), 404


if __name__ == "__main__":
    logger.info("Starting Flask application on host 0.0.0.0:8000")
    app.run(host="0.0.0.0", port=8000, debug=False)
