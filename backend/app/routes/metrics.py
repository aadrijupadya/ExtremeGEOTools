from __future__ import annotations
from typing import Dict, List, Any, Optional
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from collections import defaultdict
import sys
import os

# Add the scripts directory to the path for importing post-processing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scripts'))

from ..services.database import get_db
from ..services.metrics import MetricsService
from ..models.metrics import DailyMetrics
from ..models.run import Run
from ..models.automated_run import AutomatedRun


router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/daily")
def get_daily_metrics(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    engine: Optional[str] = Query(None, description="Filter by engine"),
    brand_context: Optional[str] = Query(None, description="Filter by brand context: overall, extreme_networks, competitors"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get daily metrics for a date range with optional filtering."""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    if start > end:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    
    # Limit date range to prevent excessive queries
    if (end - start).days > 90:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 90 days")
    
    metrics_service = MetricsService(db)
    metrics = metrics_service.get_daily_metrics(start, end, engine, brand_context)
    
    # Serialize metrics for API response
    serialized_metrics = []
    for metric in metrics:
        serialized_metrics.append({
            "date": metric.date.isoformat(),
            "engine": metric.engine,
            "brand_context": metric.brand_context,
            "total_runs": metric.total_runs,
            "total_cost_usd": float(metric.total_cost_usd),
            "total_citations": metric.total_citations,
            "unique_domains": metric.unique_domains,
            "top_domains": metric.top_domains,
            "brand_mentions": metric.brand_mentions,
            "competitor_mentions": metric.competitor_mentions,
            "share_of_voice_pct": float(metric.share_of_voice_pct),
            "avg_visibility_score": float(metric.avg_visibility_score),
            "high_quality_citations": metric.high_quality_citations,
            "last_updated": metric.last_updated
        })
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "filters": {
            "engine": engine,
            "brand_context": brand_context
        },
        "metrics": serialized_metrics,
        "count": len(serialized_metrics)
    }


@router.get("/trends")
def get_metrics_trends(
    days: int = Query(default=30, ge=7, le=90, description="Number of days to analyze"),
    engine: Optional[str] = Query(None, description="Filter by engine"),
    metric_type: str = Query(default="visibility", description="Metric to trend: visibility, citations, costs, share_of_voice"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get time-series trends for specific metrics."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    metrics_service = MetricsService(db)
    metrics = metrics_service.get_daily_metrics(start_date, end_date, engine)
    
    if not metrics:
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "trends": [],
            "summary": {}
        }
    
    # Group metrics by date for trend analysis
    trends_by_date = {}
    for metric in metrics:
        if metric.brand_context == "overall":  # Use overall metrics for trends
            date_key = metric.date.isoformat()
            if date_key not in trends_by_date:
                trends_by_date[date_key] = {
                    "date": date_key,
                    "runs": 0,
                    "costs": 0.0,
                    "citations": 0,
                    "visibility": 0.0,
                    "share_of_voice": 0.0
                }
            
            trends_by_date[date_key]["runs"] += metric.total_runs
            trends_by_date[date_key]["costs"] += float(metric.total_cost_usd)
            trends_by_date[date_key]["citations"] += metric.total_citations
            trends_by_date[date_key]["visibility"] += float(metric.avg_visibility_score)
    
    # Calculate averages for visibility and share of voice
    for date_key in trends_by_date:
        if trends_by_date[date_key]["runs"] > 0:
            trends_by_date[date_key]["visibility"] = round(
                trends_by_date[date_key]["visibility"] / trends_by_date[date_key]["runs"], 2
            )
    
    # Add brand share of voice from brand context metrics
    brand_metrics = [m for m in metrics if m.brand_context == "extreme_networks"]
    for metric in brand_metrics:
        date_key = metric.date.isoformat()
        if date_key in trends_by_date:
            trends_by_date[date_key]["share_of_voice"] = float(metric.share_of_voice_pct)
    
    # Convert to sorted list
    trends = list(trends_by_date.values())
    trends.sort(key=lambda x: x["date"])
    
    # Calculate summary statistics
    summary = {}
    if trends:
        if metric_type == "visibility":
            values = [t["visibility"] for t in trends if t["visibility"] > 0]
            summary = {
                "current": values[-1] if values else 0,
                "average": round(sum(values) / len(values), 2) if values else 0,
                "trend": "up" if len(values) > 1 and values[-1] > values[0] else "down"
            }
        elif metric_type == "citations":
            values = [t["citations"] for t in trends]
            summary = {
                "current": values[-1] if values else 0,
                "total": sum(values),
                "average": round(sum(values) / len(values), 2) if values else 0,
                "trend": "up" if len(values) > 1 and values[-1] > values[0] else "down"
            }
        elif metric_type == "costs":
            values = [t["costs"] for t in trends]
            summary = {
                "current": values[-1] if values else 0,
                "total": round(sum(values), 2),
                "average": round(sum(values) / len(values), 2) if values else 0,
                "trend": "up" if len(values) > 1 and values[-1] > values[0] else "down"
            }
        elif metric_type == "share_of_voice":
            values = [t["share_of_voice"] for t in trends if t["share_of_voice"] > 0]
            summary = {
                "current": values[-1] if values else 0,
                "average": round(sum(values) / len(values), 2) if values else 0,
                "trend": "up" if len(values) > 1 and values[-1] > values[0] else "down"
            }
    
    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "metric_type": metric_type,
        "filters": {"engine": engine},
        "trends": trends,
        "summary": summary
    }


@router.get("/summary")
def get_metrics_summary(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to summarize"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get summary metrics for the last N days."""
    metrics_service = MetricsService(db)
    summary = metrics_service.get_metrics_summary(days)
    
    if not summary:
        return {
            "period_days": days,
            "message": "No metrics available for the specified period"
        }
    
    return summary


@router.get("/entities")
def get_entity_metrics(
    days: int = Query(default=30, ge=1, le=90, description="Number of days to analyze"),
    engine: Optional[str] = Query(None, description="Filter by engine"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get entity visibility and share of voice metrics."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    metrics_service = MetricsService(db)
    metrics = metrics_service.get_daily_metrics(start_date, end_date, engine)
    
    if not metrics:
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "entities": {}
        }
    
    # Aggregate entity metrics
    entity_data = {
        "extreme_networks": {
            "total_mentions": 0,
            "share_of_voice": [],
            "by_engine": defaultdict(lambda: {"mentions": 0, "cost": 0.0})
        },
        "competitors": {
            "total_mentions": 0,
            "share_of_voice": [],
            "by_engine": defaultdict(lambda: {"mentions": 0, "cost": 0.0})
        }
    }
    
    for metric in metrics:
        if metric.brand_context == "extreme_networks":
            entity_data["extreme_networks"]["total_mentions"] += metric.brand_mentions
            if metric.share_of_voice_pct > 0:
                entity_data["extreme_networks"]["share_of_voice"].append(float(metric.share_of_voice_pct))
            
            engine_key = metric.engine
            entity_data["extreme_networks"]["by_engine"][engine_key]["mentions"] += metric.brand_mentions
            entity_data["extreme_networks"]["by_engine"][engine_key]["cost"] += float(metric.total_cost_usd)
        
        elif metric.brand_context == "competitors":
            entity_data["competitors"]["total_mentions"] += metric.competitor_mentions
            if metric.share_of_voice_pct > 0:
                entity_data["competitors"]["share_of_voice"].append(float(metric.share_of_voice_pct))
            
            engine_key = metric.engine
            entity_data["competitors"]["by_engine"][engine_key]["mentions"] += metric.competitor_mentions
            entity_data["competitors"]["by_engine"][engine_key]["cost"] += float(metric.total_cost_usd)
    
    # Calculate averages and convert defaultdicts
    for entity_type in ["extreme_networks", "competitors"]:
        share_values = entity_data[entity_type]["share_of_voice"]
        if share_values:
            entity_data[entity_type]["avg_share_of_voice"] = round(sum(share_values) / len(share_values), 2)
        else:
            entity_data[entity_type]["avg_share_of_voice"] = 0
        
        # Convert defaultdict to regular dict
        entity_data[entity_type]["by_engine"] = dict(entity_data[entity_type]["by_engine"])
    
    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "filters": {"engine": engine},
        "entities": entity_data
    }


@router.post("/compute")
def compute_daily_metrics(
    target_date: str = Query(..., description="Date to compute metrics for (YYYY-MM-DD)"),
    engine: Optional[str] = Query(None, description="Specific engine to compute for"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Manually trigger computation of daily metrics for a specific date."""
    try:
        target = datetime.strptime(target_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    if target > date.today():
        raise HTTPException(status_code=400, detail="Cannot compute metrics for future dates")
    
    metrics_service = MetricsService(db)
    metrics = metrics_service.compute_daily_metrics(target, engine)
    
    if not metrics:
        return {
            "date": target_date,
            "engine": engine,
            "message": "No runs found for the specified date",
            "metrics_computed": 0
        }
    
    # Upsert the computed metrics
    metrics_service.upsert_daily_metrics(metrics)
    
    return {
        "date": target_date,
        "engine": engine,
        "message": f"Successfully computed {len(metrics)} metrics",
        "metrics_computed": len(metrics),
        "contexts": [m.brand_context for m in metrics]
    }


@router.get("/enhanced-analysis")
def get_enhanced_analysis(
    days: int = Query(default=7, ge=1, le=30, description="Number of days to analyze"),
    engine: Optional[str] = Query(None, description="Filter by engine"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get enhanced citation and competitor analysis from recent AUTOMATED runs only."""
    try:
        # Import the post-processing pipeline
        from post_process_metrics import PostProcessPipeline
        
        # Get recent AUTOMATED runs only
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # First try to query by source = "automated"
        try:
            query = db.query(AutomatedRun).filter(
                AutomatedRun.ts >= start_date
            )
            
            if engine:
                query = query.filter(AutomatedRun.engine == engine)
            
            runs = query.order_by(AutomatedRun.ts.desc()).all()
            
            if runs:
                # We found automated runs, use them
                run_source = "automated"
            else:
                # No automated runs found, fallback to enterprise networking queries
                enterprise_keywords = [
                    "wi-fi", "wifi", "enterprise", "networking", "cisco", "juniper", 
                    "aruba", "extreme", "network", "switch", "router", "aiops", "sd-wan"
                ]
                
                # Build OR condition for enterprise keywords
                from sqlalchemy import or_
                enterprise_conditions = or_(*[AutomatedRun.query.ilike(f"%{keyword}%") for keyword in enterprise_keywords])
                
                query = db.query(AutomatedRun).filter(
                    AutomatedRun.ts >= start_date,
                    enterprise_conditions
                )
                
                if engine:
                    query = query.filter(AutomatedRun.engine == engine)
                
                runs = query.order_by(AutomatedRun.ts.desc()).all()
                run_source = "enterprise_networking_fallback"
                
        except Exception as e:
            # If automated_runs table doesn't exist, return empty result
            runs = []
            run_source = "table_not_found"
        
        if not runs:
            return {
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "message": "No enterprise networking runs found for the specified period",
                "analysis": {},
                "run_source": "none"
            }
        
        # Create pipeline instance and run analysis
        pipeline = PostProcessPipeline()
        
        # Run the enhanced analysis
        citation_analysis = pipeline.compute_citation_analysis(runs)
        competitor_insights = pipeline.compute_competitor_insights(runs)
        
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "filters": {"engine": engine},
            "total_runs_analyzed": len(runs),
            "run_source": run_source,
            "analysis": {
                "citations": citation_analysis,
                "competitors": competitor_insights
            }
        }
        
    except ImportError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Post-processing pipeline not available: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error running enhanced analysis: {str(e)}"
        )
