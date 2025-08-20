from __future__ import annotations
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel

from ..services.query_scheduler import QueryScheduler, run_daily_queries
from ..services.metrics import MetricsService
from ..services.database import get_db

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


class SchedulerConfig(BaseModel):
    """Scheduler configuration response."""
    cadence: str
    runs_per_day: int
    morning_time: str
    evening_time: str
    total_queries_per_day: int
    engine_distribution: Dict[str, int]
    competitor_set: List[str]
    query_types: Dict[str, int]


class QueryExecutionRequest(BaseModel):
    """Request to execute daily queries."""
    target_date: Optional[str] = None  # YYYY-MM-DD format
    dry_run: bool = True
    limit: Optional[int] = None


class QueryExecutionResponse(BaseModel):
    """Response from query execution."""
    target_date: str
    total_queries: int
    executed_queries: int
    status_distribution: Dict[str, int]
    execution_time: str
    dry_run: bool


@router.get("/config", response_model=SchedulerConfig)
async def get_scheduler_config():
    """Get the current scheduler configuration."""
    scheduler = QueryScheduler()
    config = scheduler.get_schedule_info()
    
    if not config:
        raise HTTPException(status_code=500, detail="Failed to load scheduler configuration")
    
    return SchedulerConfig(**config)


@router.post("/execute", response_model=QueryExecutionResponse)
async def execute_daily_queries(
    request: QueryExecutionRequest,
    background_tasks: BackgroundTasks
):
    """Execute daily queries for a specific date."""
    try:
        # Parse target date
        if request.target_date:
            try:
                target_date = datetime.strptime(request.target_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid date format. Use YYYY-MM-DD"
                )
        else:
            target_date = date.today()
        
        # Get scheduler
        scheduler = QueryScheduler()
        
        # Get daily queries
        queries = scheduler.get_daily_queries(target_date)
        
        if not queries:
            raise HTTPException(
                status_code=404, 
                detail=f"No queries found for {target_date}"
            )
        
        # Apply limit if specified
        if request.limit:
            queries = queries[:request.limit]
        
        # Execute queries
        start_time = datetime.utcnow()
        results = scheduler.execute_daily_queries(target_date, dry_run=request.dry_run)
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Calculate status distribution
        status_distribution = {}
        for result in results:
            status = result['status']
            status_distribution[status] = status_distribution.get(status, 0) + 1
        
        # If not a dry run, compute metrics in background
        if not request.dry_run:
            background_tasks.add_task(
                _compute_metrics_for_date,
                target_date.isoformat()
            )
        
        return QueryExecutionResponse(
            target_date=target_date.isoformat(),
            total_queries=len(queries),
            executed_queries=len(results),
            status_distribution=status_distribution,
            execution_time=f"{execution_time:.2f}s",
            dry_run=request.dry_run
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_scheduler_status():
    """Get the current status of the scheduler."""
    try:
        scheduler = QueryScheduler()
        config = scheduler.get_schedule_info()
        
        # Get today's queries
        today = date.today()
        queries = scheduler.get_daily_queries(today)
        
        # Check if we have any recent runs
        db = next(get_db())
        recent_runs = db.query(Run).filter(
            Run.ts >= datetime.combine(today, datetime.min.time()),
            Run.deleted.is_(False)
        ).count()
        
        return {
            "date": today.isoformat(),
            "total_queries_scheduled": len(queries),
            "queries_executed_today": recent_runs,
            "queries_remaining": max(0, len(queries) - recent_runs),
            "next_run_time": config.get("morning_time"),
            "status": "active" if len(queries) > 0 else "inactive"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _compute_metrics_for_date(date_str: str):
    """Background task to compute metrics for a specific date."""
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        db = next(get_db())
        metrics_service = MetricsService(db)
        
        # Compute metrics for all engines
        metrics = metrics_service.compute_daily_metrics(target_date)
        
        # Upsert to database
        metrics_service.upsert_daily_metrics(metrics)
        
        print(f"✅ Metrics computed and stored for {date_str}")
        
    except Exception as e:
        print(f"❌ Error computing metrics for {date_str}: {e}")


# Import Run model at the top level
from ..models.run import Run
