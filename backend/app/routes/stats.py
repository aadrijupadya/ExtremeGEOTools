from __future__ import annotations
from typing import Dict, Any
from fastapi import APIRouter, Query, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..services.database import get_db
from ..models.run import Run


router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/costs")
def get_costs(start: str | None = Query(default=None), end: str | None = Query(default=None), db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Return aggregate costs and counts from the database (all time for now)."""
    total_cost, total_runs = db.execute(
        select(func.coalesce(func.sum(Run.cost_usd), 0), func.count(Run.id))
    ).one()

    # by engine
    by_engine_rows = db.execute(
        select(Run.engine, func.coalesce(func.sum(Run.cost_usd), 0), func.count(Run.id)).group_by(Run.engine)
    ).all()
    by_engine = {eng or "unknown": {"cost": float(cost), "runs": int(runs)} for eng, cost, runs in by_engine_rows}

    # by model
    by_model_rows = db.execute(
        select(Run.model, func.coalesce(func.sum(Run.cost_usd), 0), func.count(Run.id)).group_by(Run.model)
    ).all()
    by_model = {model or "unknown": {"cost": float(cost), "runs": int(runs)} for model, cost, runs in by_model_rows}

    return {
        "total_cost_usd": float(total_cost or 0.0),
        "total_runs": int(total_runs or 0),
        "by_engine": by_engine,
        "by_model": by_model,
    }


