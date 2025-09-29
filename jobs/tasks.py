from __future__ import annotations

from typing import Any, Dict

# RQ worker entrypoint. This module must be importable by the worker process.
# It delegates to the core extract function implemented in app.py.

def task_extract(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Import locally to avoid circular imports at module load time
    from app import extract_metadata  # type: ignore

    return extract_metadata(payload)
