from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, HTTPException

from ..schemas.query_schemas import QueryRequest, QueryResponse
from ..services.run_query import run_single_engine, run_single_engine_error

#query endpoint 
router = APIRouter(prefix="/query", tags=["query"])

@router.post("/run", response_model=QueryResponse)
def run_query(req: QueryRequest) -> QueryResponse:
    if not req.query or len(req.query.strip()) < 3: #validating query length
        raise HTTPException(status_code=400, detail="Query too short.")

    ts_iso = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    runs = []

    for eng in req.engines:
        try:
            runs.append(run_single_engine(req, eng, ts_iso))
        except Exception as e:
            runs.append(run_single_engine_error(req, eng, ts_iso, e))

    return QueryResponse(status="ok", runs=runs)