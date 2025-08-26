#function to write run data to database

from __future__ import annotations
from typing import Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from .database import SessionLocal
from ..models.run import Run


def persist_run_to_db(row: Dict[str, Any]) -> None:
    """Persist a run to the database. Legacy function name kept for compatibility."""
    db: Session = SessionLocal()
    try:
        # Heuristic to classify branded vs non-branded
        q = (row.get("query") or "").lower()
        intent = (row.get("intent") or "").lower()
        branded_terms = ["extreme", "cisco", "juniper", "aruba", "vs", "versus", "compare", "comparison"]
        is_branded = intent in {"brand_focused", "comparison"} or any(t in q for t in branded_terms)

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
            citations_enriched=row.get("citations_enriched") or [],
            entities_normalized=row.get("entities_normalized") or [],
            extreme_mentioned=bool(row.get("extreme_mentioned", False)),
            extreme_rank=row.get("extreme_rank"),
            is_branded=is_branded,
        )
        db.add(run)
        db.commit()
    finally:
        db.close()