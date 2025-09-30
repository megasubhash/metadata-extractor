from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# It delegates to the core extract function implemented in app.py.

def task_extract(payload: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("RQ worker task started")
    try:
        from app import extract_metadata  # type: ignore

        result = extract_metadata(payload)
        logger.info("RQ worker task completed successfully")
        return result
    except Exception as e:
        logger.error(f"RQ worker task failed: {e}")
        raise
