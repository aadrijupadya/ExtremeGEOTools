from __future__ import annotations
from typing import Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from .database import SessionLocal
from ..models.run import Run


def append_run_to_csv(row: Dict[str, Any]) -> None:
    """Persist a run to the database (DB migration replacement for CSV).

    Keeps the function name so the rest of the codebase doesn't change.
    """
    db: Session = SessionLocal()
    try:
        run = Run(
            id=str(row.get("run_id")),
            ts=datetime.fromisoformat(str(row.get("ts").replace("Z", "+00:00"))),
            engine=row.get("engine"),
            model=row.get("model"),
            prompt_version=row.get("prompt_version"),
            intent=row.get("intent"),
            query=row.get("query"),
            status=row.get("status"),
            latency_ms=int(row.get("latency_ms", 0) or 0),
            input_tokens=int(row.get("input_tokens", 0) or 0),
            output_tokens=int(row.get("output_tokens", 0) or 0),
            cost_usd=float(row.get("cost_usd", 0.0) or 0.0),
            raw_excerpt=row.get("raw_excerpt"),
            vendors=row.get("vendors") or [],
            links=row.get("links") or [],
            domains=row.get("domains") or [],
            extreme_mentioned=bool(row.get("extreme_mentioned", False)),
            extreme_rank=row.get("extreme_rank"),
        )
        db.add(run)
        db.commit()
    finally:
        db.close()