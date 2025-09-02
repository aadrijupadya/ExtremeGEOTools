#metrics routes are the routes that are used to get the metrics for the dashboard, using data from alembic migrations

from __future__ import annotations
from typing import Dict, List, Any, Optional
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from collections import defaultdict
import sys
import os
import json

# Add the scripts directory to the path for importing post-processing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scripts'))

from ..services.database import get_db
from ..services.pricing import prices_for_model
from ..services.metrics import MetricsService
from ..services.extract import extract_competitors, extract_links, to_domains
from ..models.run import Run
from ..models.automated_run import AutomatedRun
from ..models.metrics import DailyMetrics
from sqlalchemy import and_, func, desc, asc, or_
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging


router = APIRouter(prefix="/metrics", tags=["metrics"])

#User provides timeframe, we calculate metrics for that timeframe
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

#provide trends for runs, costs, citations, etc. over time
@router.get("/trends")
def get_metrics_trends(
    days: int = Query(default=30, ge=7, le=365, description="Number of days to analyze"),
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

@router.get("/extreme-trends")
def get_extreme_trends(
    days: int = Query(default=30, ge=7, le=365, description="Number of days to analyze"),
    engine: Optional[str] = Query(None, description="Filter by engine"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get Extreme Networks focused trends from neutral queries only."""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query only non-branded (neutral) queries with Extreme mentions
        query = db.query(AutomatedRun).filter(
            AutomatedRun.ts >= start_date,
            AutomatedRun.is_branded == False,  # Only neutral queries
            AutomatedRun.extreme_mentioned == True  # Must mention Extreme
        )
        
        if engine:
            if engine == 'openai':
                query = query.filter(or_(
                    AutomatedRun.engine.like('gpt%'),
                    AutomatedRun.engine.like('openai%'),
                    AutomatedRun.engine == 'openai'
                ))
            elif engine == 'perplexity':
                query = query.filter(AutomatedRun.engine == 'perplexity')
            else:
                query = query.filter(AutomatedRun.engine == engine)
        
        runs = query.order_by(AutomatedRun.ts.asc()).all()
        
        if not runs:
            return {
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "focus": "extreme_networks_neutral_queries",
                "trends": [],
                "message": "No neutral queries mentioning Extreme Networks found"
            }
        
        # Group runs by date for daily trends
        trends_by_date = {}
        
        for run in runs:
            date_key = run.ts.date().isoformat()
            
            if date_key not in trends_by_date:
                trends_by_date[date_key] = {
                    "date": date_key,
                    "extreme_mentions": 0,
                    "extreme_citations": 0,
                    "total_citations": 0,
                    "avg_rank": 1.0,  # Placeholder for now
                    "runs_count": 0,
                    "total_cost": 0.0
                }
            
            trends_by_date[date_key]["runs_count"] += 1
            trends_by_date[date_key]["total_cost"] += float(run.cost_usd or 0)
            
            # Count Extreme mentions
            if run.extreme_mentioned:
                trends_by_date[date_key]["extreme_mentions"] += 1
            
            # Count Extreme-related citations from links
            if run.links:
                try:
                    links = json.loads(run.links) if isinstance(run.links, str) else run.links
                    if isinstance(links, list):
                        for link in links:
                            if isinstance(link, dict) and 'url' in link:
                                url = link['url'].lower()
                                if 'extremenetworks.com' in url or 'een.extremenetworks.com' in url:
                                    trends_by_date[date_key]["extreme_citations"] += 1
                            elif isinstance(link, str):
                                url = link.lower()
                                if 'extremenetworks.com' in url or 'een.extremenetworks.com' in url:
                                    trends_by_date[date_key]["extreme_citations"] += 1
                except (json.JSONDecodeError, AttributeError):
                    pass
            
            # Count total citations
            if run.links:
                try:
                    links = json.loads(run.links) if isinstance(run.links, str) else run.links
                    if isinstance(links, list):
                        trends_by_date[date_key]["total_citations"] += len(links)
                except (json.JSONDecodeError, AttributeError):
                    pass
        
        # Convert to sorted list
        trends = list(trends_by_date.values())
        trends.sort(key=lambda x: x["date"])
        
        # Calculate summary statistics
        summary = {
            "total_runs": len(runs),
            "total_extreme_mentions": sum(t["extreme_mentions"] for t in trends),
            "total_extreme_citations": sum(t["extreme_citations"] for t in trends),
            "total_citations": sum(t["total_citations"] for t in trends),
            "total_cost": sum(t["total_cost"] for t in trends),
            "avg_cost_per_run": sum(t["total_cost"] for t in trends) / len(runs) if runs else 0
        }
        
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "focus": "extreme_networks_neutral_queries",
            "filters": {"engine": engine},
            "trends": trends,
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating Extreme trends: {str(e)}"
        )


#provide summary metrics for the last N days
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

#provide entity metrics for the last N days, where entity is either extreme_networks or competitor mentions in answers
@router.get("/entities")
def get_entity_metrics(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
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

#enhanced is defined as the ability to compute metrics for the dashboard that are not available in the daily metrics table
@router.get("/enhanced-analysis")
def get_enhanced_analysis(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    engine: Optional[str] = Query(None, description="Filter by engine"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get enhanced citation and competitor analysis from recent AUTOMATED runs only."""
    try:
        # Get recent AUTOMATED runs only
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query automated runs with engine filtering - only non-branded queries
        query = db.query(AutomatedRun).filter(
            AutomatedRun.ts >= start_date,
            AutomatedRun.is_branded == False  # Only neutral queries
        )
        
        if engine:
            # Handle engine filtering more intelligently
            if engine == 'openai':
                # Filter for any OpenAI-related engines
                query = query.filter(or_(
                    AutomatedRun.engine.like('gpt%'),
                    AutomatedRun.engine.like('openai%'),
                    AutomatedRun.engine == 'openai'
                ))
            elif engine == 'perplexity':
                # Filter for Perplexity engines (exact match)
                query = query.filter(AutomatedRun.engine == 'perplexity')
            else:
                # Exact match for other engines
                query = query.filter(AutomatedRun.engine == engine)
        
        runs = query.order_by(AutomatedRun.ts.desc()).all()
        run_source = "automated"
        
        if not runs:
            return {
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "message": "No automated runs found for the specified period and engine filter",
                "analysis": {},
                "run_source": "none"
            }
        
        # Simple analysis without external pipeline dependency
        # Count entities and compute basic insights
        total_runs = len(runs)
        failed_runs = len([r for r in runs if getattr(r, 'status', 'completed') != 'completed'])
        successful_runs = total_runs - failed_runs
        
        # Calculate average response time
        response_times = [r.latency_ms for r in runs if getattr(r, 'latency_ms', None) and r.latency_ms > 0]
        avg_response_time = (sum(response_times) / len(response_times)) / 1000.0 if response_times else None
        
        # Calculate average cost per query
        costs = [r.cost_usd for r in runs if getattr(r, 'cost_usd', None) and r.cost_usd > 0]
        avg_cost_per_query = sum(costs) / len(costs) if costs else None
        
        # Enhanced citation analysis
        runs_with_links = [r for r in runs if getattr(r, 'links', None) and r.links]
        runs_without_links = [r for r in runs if not getattr(r, 'links', None) or not r.links]
        
        # Extract citations and domains from runs
        all_citations = []
        all_domains = set()
        domain_counts = {}
        
        for run in runs_with_links:
            try:
                if isinstance(run.links, str):
                    links = json.loads(run.links)
                else:
                    links = run.links
                
                if isinstance(links, list):
                    for link in links:
                        if isinstance(link, dict) and 'url' in link:
                            all_citations.append(link)
                            try:
                                from urllib.parse import urlparse
                                parsed = urlparse(link['url'])
                                domain = parsed.netloc.lower()
                                if domain.startswith('www.'):
                                    domain = domain[4:]
                                all_domains.add(domain)
                                domain_counts[domain] = domain_counts.get(domain, 0) + 1
                            except Exception:
                                continue
                        elif isinstance(link, str):
                            # Handle case where links is just a list of URLs
                            all_citations.append({"url": link})
                            try:
                                from urllib.parse import urlparse
                                parsed = urlparse(link)
                                domain = parsed.netloc.lower()
                                if domain.startswith('www.'):
                                    domain = domain[4:]
                                all_domains.add(domain)
                                domain_counts[domain] = domain_counts.get(domain, 0) + 1
                            except Exception:
                                continue
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # Sort domains by frequency
        top_domains = sorted(
            [{"domain": domain, "count": count} for domain, count in domain_counts.items()],
            key=lambda x: x["count"], reverse=True
        )[:5]
        
        citation_analysis = {
            "total_citations": len(all_citations),
            "unique_domains": len(all_domains),
            "runs_with_links": len(runs_with_links),
            "runs_without_links": len(runs_without_links),
            "top_5_domains_by_frequency": top_domains,
            "domain_breakdown": {
                "most_frequent_domain": top_domains[0]["domain"] if top_domains else "N/A"
            }
        }
        
        # Basic competitor insights with actual entity data
        # Extract entities from runs that have them
        all_entities = []
        for run in runs:
            if hasattr(run, 'entities_normalized') and run.entities_normalized:
                try:
                    # Parse entities if it's a JSON string
                    if isinstance(run.entities_normalized, str):
                        entities = json.loads(run.entities_normalized)
                    else:
                        entities = run.entities_normalized
                    
                    if isinstance(entities, list):
                        all_entities.extend(entities)
                    elif isinstance(entities, dict):
                        all_entities.append(entities)
                except (json.JSONDecodeError, AttributeError):
                    continue
        
        # Count unique entities and mentions, and track positions for ranking
        entity_counts = {}
        entity_positions = {}  # Track all positions for each entity
        
        for run in runs:
            if run.entities_normalized:
                try:
                    entities = json.loads(run.entities_normalized) if isinstance(run.entities_normalized, str) else run.entities_normalized
                    if isinstance(entities, list):
                        for pos, entity in enumerate(entities, 1):
                            if isinstance(entity, dict):
                                name = entity.get('name', entity.get('entity', 'Unknown'))
                                if name:
                                    if name not in entity_counts:
                                        entity_counts[name] = 0
                                        entity_positions[name] = []
                                    entity_counts[name] += 1
                                    entity_positions[name].append(pos)
                except (json.JSONDecodeError, AttributeError):
                    continue
        
        # Sort by mention count - get top competitors with calculated average rank
        sorted_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)
        top_competitors = []
        
        for name, count in sorted_entities[:15]:  # Get top 15 to allow frontend to show top 10
            positions = entity_positions.get(name, [])
            avg_rank = sum(positions) / len(positions) if positions else "N/A"
            top_competitors.append({
                "name": name, 
                "mentions": count, 
                "avg_rank": round(avg_rank, 1) if isinstance(avg_rank, (int, float)) else avg_rank
            })
        
        competitor_insights = {
            "total_runs_analyzed": total_runs,
            "runs_with_entities": len([r for r in runs if getattr(r, 'entities_normalized', None)]),
            "runs_without_entities": len([r for r in runs if not getattr(r, 'entities_normalized', None)]),
            "entity_detection_rate": len([r for r in runs if getattr(r, 'entities_normalized', None)]) / total_runs if total_runs > 0 else 0.0,
            "unique_entities": len(entity_counts),
            "total_entities_mentions": sum(entity_counts.values()),
            "top_competitors": top_competitors,
            "detection_effectiveness": {
                "entity_extraction_rate": len([r for r in runs if getattr(r, 'entities_normalized', None)]) / total_runs * 100 if total_runs > 0 else 0.0
            }
        }
        
        # Calculate additional metrics for the frontend
        total_runs = len(runs)
        failed_runs = len([r for r in runs if r.status != 'completed'])
        successful_runs = total_runs - failed_runs
        
        # Calculate average response time
        response_times = [r.latency_ms for r in runs if r.latency_ms and r.latency_ms > 0]
        avg_response_time = (sum(response_times) / len(response_times)) / 1000.0 if response_times else None
        
        # Calculate engine breakdown
        engine_counts = {}
        for run in runs:
            engine_name = run.engine
            if engine_name not in engine_counts:
                engine_counts[engine_name] = 0
            engine_counts[engine_name] += 1
        
        # Calculate average cost per query and total cost
        costs = [r.cost_usd for r in runs if r.cost_usd and r.cost_usd > 0]
        avg_cost_per_query = sum(costs) / len(costs) if costs else None
        total_cost = sum(costs) if costs else 0.0
        
        # Add entity associations data for the dashboard
        try:
            from pathlib import Path
            import json
            
            # Load entity associations data
            entity_assoc_file = Path(__file__).parent.parent.parent.parent / "data" / "entity_associations.json"
            entity_assoc_data = {}
            
            if entity_assoc_file.exists():
                with open(entity_assoc_file, 'r') as f:
                    entity_assoc_data = json.load(f)
            
            # Extract entity associations for the dashboard
            entity_associations = entity_assoc_data.get("associations", [])
            
            # Filter by engine if specified
            if engine:
                if engine == 'openai':
                    entity_associations = [a for a in entity_associations if 'gpt' in a.get('model', '').lower()]
                elif engine == 'perplexity':
                    entity_associations = [a for a in entity_associations if a.get('engine') == 'perplexity']
            
            # Count products and keywords
            total_products = 0
            total_keywords = 0
            for assoc in entity_associations:
                if "product" in assoc.get("query", "").lower():
                    total_products += len(assoc.get("products", []))
                else:
                    total_keywords += len(assoc.get("keywords", []))
            
            # Add entity associations to the response
            entity_analysis = {
                "total_products": total_products,
                "total_keywords": total_keywords,
                "associations_count": len(entity_associations)
            }
            
        except Exception as e:
            # If entity associations fail to load, provide empty data
            entity_analysis = {
                "total_products": 0,
                "total_keywords": 0,
                "associations_count": 0
            }
        
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "filters": {"engine": engine},
            "total_runs_analyzed": total_runs,
            "run_source": run_source,
            "analysis": {
                "citations": citation_analysis,
                "competitors": competitor_insights,
                "entity_associations": entity_analysis,
                "engine_breakdown": engine_counts,
                "total_cost": total_cost,
                "failed_runs": failed_runs,
                "avg_response_time": avg_response_time,
                "avg_cost_per_query": avg_cost_per_query
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

#provide recent queries for the last N days, which is displayed in frontend as a table view
@router.get("/recent-queries")
def get_recent_queries(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to look back"),
    engine: Optional[str] = Query(None, description="Filter by engine"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get recent automated queries with full details from the automated_runs table."""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query the automated_runs table for recent queries
        query = db.query(AutomatedRun).filter(
            AutomatedRun.ts >= start_date
        )
        
        if engine:
            # Handle engine filtering more intelligently
            if engine == 'openai':
                # Filter for any OpenAI-related engines
                from sqlalchemy import or_
                query = query.filter(or_(
                    AutomatedRun.engine.like('gpt%'),
                    AutomatedRun.engine.like('openai%'),
                    AutomatedRun.engine == 'openai'
                ))
            elif engine == 'perplexity':
                # Filter for Perplexity engines
                query = query.filter(or_(
                    AutomatedRun.engine.like('perplexity%'),
                    AutomatedRun.engine == 'perplexity'
                ))
            else:
                # Exact match for other engines
                query = query.filter(AutomatedRun.engine == engine)
        
        # Order by timestamp descending (most recent first) - no limit to show all queries
        runs = query.order_by(AutomatedRun.ts.desc()).all()
        
        # Serialize the automated runs data
        serialized_runs = []
        for run in runs:
            # Fallback cost estimate for OpenAI when missing/zero
            computed_cost = 0.0
            try:
                if (not run.cost_usd or float(run.cost_usd) == 0.0) and (run.engine and ('gpt' in run.engine or 'openai' in run.engine)):
                    in_p, out_p = prices_for_model(run.model or 'gpt-4o-search-preview')
                    computed_cost = ((run.input_tokens or 0) / 1000.0 * in_p) + ((run.output_tokens or 0) / 1000.0 * out_p)
            except Exception:
                computed_cost = 0.0
            serialized_run = {
                "id": run.id,
                "query_text": run.query,
                "engine": run.engine,
                "model": run.model,
                "created_at": run.ts.isoformat() if run.ts else None,
                "status": run.status,
                "response_time": run.latency_ms / 1000.0 if run.latency_ms else None,  # Convert ms to seconds
                "cost": float(run.cost_usd) if run.cost_usd and float(run.cost_usd) > 0 else round(float(computed_cost), 6),
                "input_tokens": run.input_tokens,
                "output_tokens": run.output_tokens,
                "intent": run.intent_category,  # Use intent_category from automated_runs
                "source": "automated",  # All queries from this table are automated
                "extreme_mentioned": run.extreme_mentioned,
                "extreme_rank": None,  # Not available in automated_runs
                "total_citations": run.citation_count,
                "total_entities": len(run.entities_normalized) if run.entities_normalized else 0,
                "answer_text": run.answer_text,
                "competitor_mentions": run.competitor_mentions,
                "domains": run.domains,
                "intent_category": run.intent_category,
                "competitor_set": run.competitor_set
            }
            serialized_runs.append(serialized_run)
        
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "filters": {"engine": engine},
            "total_queries": len(serialized_runs),
            "queries": serialized_runs
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching recent automated queries: {str(e)}"
        )

@router.get("/extreme-focus")
def get_extreme_focus_metrics(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    engine: Optional[str] = Query(None, description="Filter by engine"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get comprehensive Extreme Networks AI search visibility metrics."""
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
    
    try:
        # Build query with intelligent engine filtering
        query = db.query(AutomatedRun).filter(
            AutomatedRun.ts >= start,
            AutomatedRun.ts <= end + timedelta(days=1)  # Include end date
        )
        
        # Apply engine filter with intelligent matching
        if engine:
            if engine == 'openai':
                from sqlalchemy import or_
                query = query.filter(or_(
                    AutomatedRun.engine.like('gpt%'),
                    AutomatedRun.engine.like('openai%'),
                    AutomatedRun.engine == 'openai'
                ))
            elif engine == 'perplexity':
                from sqlalchemy import or_
                query = query.filter(or_(
                    AutomatedRun.engine.like('perplexity%'),
                    AutomatedRun.engine == 'perplexity'
                ))
            else:
                query = query.filter(AutomatedRun.engine == engine)
        
        runs = query.all()
        
        if not runs:
            return {
                "start_date": start_date,
                "end_date": end_date,
                "filters": {"engine": engine},
                "message": "No data found for the specified criteria",
                "metrics": {}
            }
        
        # Analyze Extreme Networks visibility
        extreme_metrics = _analyze_extreme_visibility(runs)
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "filters": {"engine": engine},
            "total_runs_analyzed": len(runs),
            "metrics": extreme_metrics
        }
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error in extreme focus metrics: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch extreme focus metrics: {str(e)}"
        )


def _is_branded_query(query: str) -> bool:
    """Check if a query is branded (mentions specific competitors)."""
    query_lower = query.lower()
    
    # List of competitor brand names to check for
    competitor_brands = [
        "cisco", "juniper", "aruba", "fortinet", "palo alto", "check point",
        "f5", "riverbed", "arista", "brocade", "ruckus", "ubiquiti", "netgear",
        "tp-link", "d-link", "linksys", "huawei", "dell", "hpe", "nokia",
        "meraki", "mist", "fortigate", "pan-os", "big-ip", "steelhead"
    ]
    
    # Check if query contains any competitor brand names
    return any(brand in query_lower for brand in competitor_brands)


def _normalize_engine_name(engine: str) -> str:
    """Normalize engine names for cleaner display."""
    if not engine:
        return "Unknown"
    
    engine_lower = engine.lower()
    
    if "gpt" in engine_lower or "openai" in engine_lower:
        return "OpenAI"
    elif "perplexity" in engine_lower:
        return "Perplexity"
    else:
        return engine


def _analyze_extreme_visibility(runs: List[AutomatedRun]) -> Dict[str, Any]:
    """Analyze Extreme Networks visibility across AI runs."""
    
    # Filter to only neutral queries for visibility analysis
    neutral_runs = [run for run in runs if not _is_branded_query(run.query)]
    
    # 1. AI Search Visibility: Mentions from neutral queries only
    total_mentions = sum(1 for run in neutral_runs if run.extreme_mentioned)
    mention_rate = total_mentions / len(neutral_runs) if neutral_runs else 0
    
    # Citation analysis: Only count citations/domains related to Extreme
    extreme_related_citations = 0
    extreme_related_domains = 0
    
    for run in neutral_runs:
        if run.extreme_mentioned:
            # Only count citations if they're related to Extreme
            # For now, we'll count all citations from runs where Extreme was mentioned
            # This could be enhanced later to filter by content relevance
            extreme_related_citations += run.citation_count or 0
            extreme_related_domains += run.domain_count or 0
    
    # 2. Query Coverage Gaps Analysis
    coverage_gaps = _analyze_coverage_gaps(runs)
    
    # 3. Brand Intent Analysis
    brand_intent_analysis = _analyze_brand_intent(runs)
    
    # 4. Entity Association Analysis
    entity_associations = _analyze_entity_associations(runs)
    
    return {
        "ai_search_visibility": {
            "total_mentions": total_mentions,
            "mention_rate_pct": round(mention_rate * 100, 2),
            "total_citations": extreme_related_citations,
            "total_domains": extreme_related_domains,
            "avg_citations_per_mention": round(extreme_related_citations / total_mentions, 2) if total_mentions > 0 else 0,
            "avg_domains_per_mention": round(extreme_related_domains / total_mentions, 2) if total_mentions > 0 else 0,
            "neutral_queries_analyzed": len(neutral_runs),
            "branded_queries_excluded": len(runs) - len(neutral_runs)
        },
        "coverage_gaps": coverage_gaps,
        "answer_positioning": brand_intent_analysis,
        "entity_associations": entity_associations
    }


def _analyze_coverage_gaps(runs: List[AutomatedRun]) -> Dict[str, Any]:
    """Analyze where Extreme should be showing up but is missing."""
    
    # Analyze by intent category
    intent_analysis = {}
    gaps = []
    
    for run in runs:
        # Skip branded queries - only analyze neutral queries for gaps
        if _is_branded_query(run.query):
            continue
            
        intent = run.intent_category or "unknown"
        if intent not in intent_analysis:
            intent_analysis[intent] = {"total": 0, "extreme_mentioned": 0, "gaps": []}
        
        intent_analysis[intent]["total"] += 1
        
        if run.extreme_mentioned:
            intent_analysis[intent]["extreme_mentioned"] += 1
        else:
            # This is a coverage gap - Extreme should have been mentioned
            # Extract competitors from the actual AI response text
            competitors = extract_competitors(run.answer_text)
            
            # Only consider this a gap if Extreme is NOT in the competitors list
            competitor_names = [comp.name for comp in competitors]
            if "Extreme Networks" not in competitor_names:
                gap_info = {
                    "query": run.query,
                    "engine": _normalize_engine_name(run.engine),
                    "why_extreme_should_appear": _classify_why_extreme_should_appear(run.query),
                    "competitors_mentioned": competitor_names,
                    "full_query": run.query,
                    "full_ai_response": run.answer_text
                }
                gaps.append(gap_info)
    
    # Calculate gap rates
    for intent, data in intent_analysis.items():
        if data["total"] > 0:
            data["gap_rate_pct"] = round((len(data["gaps"]) / data["total"]) * 100, 2)
            data["coverage_rate_pct"] = round((data["extreme_mentioned"] / data["total"]) * 100, 2)
    
    return {
        "by_intent_category": intent_analysis,
        "total_gaps": len(gaps),
        "overall_gap_rate_pct": round(len(gaps) / len(runs) * 100, 2) if runs else 0,
        "all_gaps": gaps,  # Include all gaps for detailed analysis
        "total_queries_analyzed": sum(data["total"] for data in intent_analysis.values()),
        "branded_queries_filtered": len([run for run in runs if _is_branded_query(run.query)])
    }


def _classify_why_extreme_should_appear(query: str) -> str:
    """Classify why Extreme should appear in this query response."""
    query_lower = query.lower()
    
    # Network infrastructure
    if any(word in query_lower for word in ["switch", "router", "networking", "network"]):
        return "Network Infrastructure"
    
    # Wi-Fi and wireless
    if any(word in query_lower for word in ["wifi", "wi-fi", "wireless", "802.11", "6e", "7"]):
        return "Wi-Fi & Wireless"
    
    # Security
    if any(word in query_lower for word in ["security", "firewall", "sase", "zero trust"]):
        return "Network Security"
    
    # Enterprise
    if any(word in query_lower for word in ["enterprise", "business", "corporate"]):
        return "Enterprise Solutions"
    
    # Cloud and automation
    if any(word in query_lower for word in ["cloud", "automation", "ai", "ml", "orchestration"]):
        return "Cloud & Automation"
    
    # Data center
    if any(word in query_lower for word in ["data center", "datacenter", "server", "storage"]):
        return "Data Center"
    
    return "General Networking"


def _analyze_brand_intent(runs: List[AutomatedRun]) -> Dict[str, Any]:
    """Analyze the intent split of queries where Extreme Networks was mentioned."""
    
    intent_data = {
        "total_extreme_mentions": 0,
        "intent_breakdown": {
            "informational": 0,      # General info about Extreme
            "branded": 0,            # Brand-specific queries
            "comparison": 0,         # Extreme vs competitor
            "review": 0,             # Review/evaluation of Extreme
            "product_specific": 0,   # Specific product features
            "technical": 0           # Technical specifications
        },
        "context_examples": {
            "informational": [],
            "branded": [],
            "comparison": [],
            "review": [],
            "product_specific": [],
            "technical": []
        }
    }
    
    for run in runs:
        if not run.extreme_mentioned or not run.query:
            continue
            
        intent_data["total_extreme_mentions"] += 1
        query_lower = run.query.lower()
        
        # Categorize intent based on query content
        if any(word in query_lower for word in ["vs", "versus", "compare", "comparison"]):
            intent = "comparison"
        elif any(word in query_lower for word in ["review", "evaluation", "assessment"]):
            intent = "review"
        elif any(word in query_lower for word in ["wifi", "wi-fi", "6e", "7", "switch", "router", "sase", "aiops"]):
            intent = "product_specific"
        elif any(word in query_lower for word in ["specs", "specifications", "technical", "architecture", "protocol"]):
            intent = "technical"
        elif any(word in query_lower for word in ["extreme networks", "extreme"]):
            intent = "branded"
        else:
            intent = "informational"
        
        # Increment count
        intent_data["intent_breakdown"][intent] += 1
        
        # Store context example (limit to 2 per category)
        if len(intent_data["context_examples"][intent]) < 2:
            intent_data["context_examples"][intent].append({
                "query": run.query,
                "answer_preview": run.answer_text[:200] + "..." if run.answer_text and len(run.answer_text) > 200 else (run.answer_text or "No response text"),
                "full_answer": run.answer_text or "No response text",
                "engine": _normalize_engine_name(run.engine),
                "intent": intent
            })
    
    return intent_data


def _analyze_entity_associations(runs: List[AutomatedRun]) -> Dict[str, Any]:
    """Analyze what products/keywords AI associates with Extreme."""
    
    # Extract entities and associations
    entity_counts = {}
    product_associations = {}
    keyword_associations = {}
    
    for run in runs:
        if not run.extreme_mentioned or not run.entities_normalized:
            continue
            
        # Analyze entities
        for entity in run.entities_normalized:
            entity_type = entity.get("type", "unknown")
            entity_name = entity.get("name", "").lower()
            
            if entity_type not in entity_counts:
                entity_counts[entity_type] = {}
            entity_counts[entity_type][entity_name] = entity_counts[entity_type].get(entity_name, 0) + 1
            
            # Look for product associations
            if any(word in entity_name for word in ["wifi", "wi-fi", "6e", "6", "sase", "campus", "networking", "switch", "router"]):
                if entity_name not in product_associations:
                    product_associations[entity_name] = 0
                product_associations[entity_name] += 1
            
            # Look for keyword associations
            if any(word in entity_name for word in ["enterprise", "cloud", "security", "automation", "ai", "ml"]):
                if entity_name not in keyword_associations:
                    keyword_associations[entity_name] = 0
                keyword_associations[entity_name] += 1
    
    # Sort by frequency
    sorted_products = sorted(product_associations.items(), key=lambda x: x[1], reverse=True)
    sorted_keywords = sorted(keyword_associations.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "entity_types": entity_counts,
        "product_associations": dict(sorted_products[:10]),  # Top 10
        "keyword_associations": dict(sorted_keywords[:10]),  # Top 10
        "total_entity_mentions": sum(sum(counts.values()) for counts in entity_counts.values())
    }


def _analyze_visibility_trends(runs: List[AutomatedRun]) -> Dict[str, Any]:
    """Analyze weekly/monthly movement in AI visibility."""
    
    # Group runs by week and month
    weekly_data = {}
    monthly_data = {}
    
    for run in runs:
        run_date = run.ts.date()
        
        # Weekly grouping (Monday as start of week)
        week_start = run_date - timedelta(days=run_date.weekday())
        week_key = week_start.isoformat()
        
        if week_key not in weekly_data:
            weekly_data[week_key] = {"total": 0, "extreme_mentioned": 0, "citations": 0}
        weekly_data[week_key]["total"] += 1
        if run.extreme_mentioned:
            weekly_data[week_key]["extreme_mentioned"] += 1
        weekly_data[week_key]["citations"] += run.citation_count or 0
        
        # Monthly grouping
        month_key = f"{run_date.year}-{run_date.month:02d}"
        if month_key not in monthly_data:
            monthly_data[month_key] = {"total": 0, "extreme_mentioned": 0, "citations": 0}
        monthly_data[month_key]["total"] += 1
        if run.extreme_mentioned:
            monthly_data[month_key]["extreme_mentioned"] += 1
        monthly_data[month_key]["citations"] += run.citation_count or 0
    
    # Calculate trends
    def calculate_trend(data_dict):
        sorted_periods = sorted(data_dict.keys())
        if len(sorted_periods) < 2:
            return {"trend": "insufficient_data", "change_pct": 0}
        
        first_period = sorted_periods[0]
        last_period = sorted_periods[-1]
        
        first_visibility = data_dict[first_period]["extreme_mentioned"] / data_dict[first_period]["total"] if data_dict[first_period]["total"] > 0 else 0
        last_visibility = data_dict[last_period]["extreme_mentioned"] / data_dict[last_period]["total"] if data_dict[last_period]["total"] > 0 else 0
        
        if first_visibility == 0:
            change_pct = 100 if last_visibility > 0 else 0
        else:
            change_pct = ((last_visibility - first_visibility) / first_visibility) * 100
        
        if change_pct > 5:
            trend = "increasing"
        elif change_pct < -5:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {"trend": trend, "change_pct": round(change_pct, 2)}
    
    weekly_trend = calculate_trend(weekly_data)
    monthly_trend = calculate_trend(monthly_data)
    
    return {
        "weekly": {
            "data": weekly_data,
            "trend": weekly_trend
        },
        "monthly": {
            "data": monthly_data,
            "trend": monthly_trend
        },
        "summary": {
            "overall_trend": "increasing" if weekly_trend["change_pct"] > 0 and monthly_trend["change_pct"] > 0 else "decreasing",
            "weekly_change_pct": weekly_trend["change_pct"],
            "monthly_change_pct": monthly_trend["change_pct"]
        }
    }

@router.get("/citation-analysis")
def get_citation_analysis(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    engine: Optional[str] = Query(None, description="Filter by engine"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get citation analysis including most cited sources and Extreme-related sources."""
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
    
    try:
        # Get all automated runs in the date range
        query = db.query(AutomatedRun).filter(
            and_(
                AutomatedRun.ts >= start,
                AutomatedRun.ts <= end + timedelta(days=1),  # Include end date
                AutomatedRun.status == "completed"
            )
        )
        
        if engine:
            query = query.filter(AutomatedRun.engine == engine)
        
        runs = query.all()
        
        # Analyze citations
        citation_analysis = _analyze_citations(runs)
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "filters": {"engine": engine},
            "total_runs_analyzed": len(runs),
            "citation_analysis": citation_analysis
        }
        
    except Exception as e:
        logging.error(f"Error in citation analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during citation analysis")


def _analyze_citations(runs: List[AutomatedRun]) -> Dict[str, Any]:
    """Analyze citations from runs to provide citation insights."""
    # Collect all citations and domains
    all_citations = []
    all_domains = []
    extreme_related_citations = []
    extreme_related_domains = []
    
    # Track detailed information for each domain
    domain_details = {}  # domain -> { queries: [str], urls: [str], runs: [int] }
    
    for run in runs:
        # Extract URLs from answer_text if links field is empty
        citations = []
        if run.links and isinstance(run.links, list):
            citations = [{"url": link, "query": run.query, "run_id": run.id} for link in run.links]
        elif run.answer_text:
            # Extract URLs from answer text using the extract_links function
            extracted_urls = extract_links(run.answer_text)
            citations = [{"url": url, "query": run.query, "run_id": run.id} for url in extracted_urls]
        
        all_citations.extend(citations)
        
        # Track domain details for all citations
        for citation in citations:
            url = citation['url']
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                if domain.startswith('www.'):
                    domain = domain[4:]
                
                # Combine Extreme domains
                if 'extremenetworks.com' in domain or 'een.extremenetworks.com' in domain:
                    domain = 'extremenetworks.com'
                
                if domain not in domain_details:
                    domain_details[domain] = {"queries": set(), "urls": set(), "runs": set()}
                
                domain_details[domain]["queries"].add(citation["query"])
                domain_details[domain]["urls"].add(url)
                domain_details[domain]["runs"].add(citation["run_id"])
            except Exception:
                continue
        
        if run.domains and isinstance(run.domains, list):
            all_domains.extend(run.domains)
        elif run.answer_text:
            # Extract domains from answer text if domains field is empty
            extracted_urls = extract_links(run.answer_text)
            extracted_domains = to_domains(extracted_urls)
            all_domains.extend(extracted_domains)
        
        # Check if this run mentions Extreme
        if run.extreme_mentioned:
            extreme_related_citations.extend(citations)
            if run.domains and isinstance(run.domains, list):
                extreme_related_domains.extend(run.domains)
            elif run.answer_text:
                extracted_urls = extract_links(run.answer_text)
                extracted_domains = to_domains(extracted_urls)
                extreme_related_domains.extend(extracted_domains)
    
    # Most cited sources (all citations) - use domain_details for counting with combination
    source_counts = {}
    for domain, details in domain_details.items():
        source_counts[domain] = len(details["urls"])
    
    # Sort by citation count and include detailed information
    most_cited_sources = []
    for domain, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
        source_info = {
            "domain": domain,
            "citation_count": count,
            "queries": list(domain_details[domain]["queries"]),
            "urls": list(domain_details[domain]["urls"]),
            "runs_count": len(domain_details[domain]["runs"])
        }
        most_cited_sources.append(source_info)
    
    # Extreme-related sources - filter from domain_details by extreme citations
    extreme_domain_details = {}
    for citation in extreme_related_citations:
        if isinstance(citation, dict) and 'url' in citation:
            url = citation['url']
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                if domain.startswith('www.'):
                    domain = domain[4:]
                
                # Combine Extreme domains
                if 'extremenetworks.com' in domain or 'een.extremenetworks.com' in domain:
                    domain = 'extremenetworks.com'
                
                if domain not in extreme_domain_details:
                    extreme_domain_details[domain] = {"queries": set(), "urls": set(), "runs": set()}
                
                extreme_domain_details[domain]["queries"].add(citation["query"])
                extreme_domain_details[domain]["urls"].add(url)
                extreme_domain_details[domain]["runs"].add(citation["run_id"])
            except Exception:
                continue
    
    # Sort by citation count and include detailed information
    extreme_sources = []
    extreme_source_counts = {domain: len(details["urls"]) for domain, details in extreme_domain_details.items()}
    for domain, count in sorted(extreme_source_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
        source_info = {
            "domain": domain,
            "citation_count": count,
            "queries": list(extreme_domain_details[domain]["queries"]),
            "urls": list(extreme_domain_details[domain]["urls"]),
            "runs_count": len(extreme_domain_details[domain]["runs"])
        }
        extreme_sources.append(source_info)
    
    # Domain analysis
    domain_counts = {}
    for domain in all_domains:
        if isinstance(domain, str):
            domain_lower = domain.lower()
            if domain_lower.startswith('www.'):
                domain_lower = domain_lower[4:]
            domain_counts[domain_lower] = domain_counts.get(domain_lower, 0) + 1
    
    most_cited_domains = sorted(
        [{"domain": domain, "mention_count": count} for domain, count in domain_counts.items()],
        key=lambda x: x["mention_count"],
        reverse=True
    )[:20]  # Top 20
    
    return {
        "most_cited_sources": {
            "total_unique_sources": len(source_counts),
            "top_sources": most_cited_sources
        },
        "extreme_related_sources": {
            "total_extreme_citations": len(extreme_related_citations),
            "total_unique_extreme_sources": len(extreme_source_counts),
            "top_extreme_sources": extreme_sources
        },
        "domain_analysis": {
            "total_unique_domains": len(domain_counts),
            "top_domains": most_cited_domains
        },
        "summary": {
            "total_citations": len(all_citations),
            "total_domains": len(all_domains),
            "extreme_mention_rate": len([r for r in runs if r.extreme_mentioned]) / len(runs) if runs else 0
        }
    }
