from __future__ import annotations
from typing import Dict, List, Any, Optional
from datetime import date, datetime, timedelta
from collections import defaultdict, Counter
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import Session

from ..models.run import Run
from ..models.metrics import DailyMetrics


class MetricsService:
    """Service for computing and managing daily metrics aggregates."""
    
    def __init__(self, db: Session):
        self.db = db
    #Daily metrics include 
    def compute_daily_metrics(self, target_date: date, engine: Optional[str] = None) -> List[DailyMetrics]:
        """Compute daily metrics for a specific date and optionally specific engine."""
        # Get all runs for the target date
        start_ts = datetime.combine(target_date, datetime.min.time())
        end_ts = datetime.combine(target_date, datetime.max.time())
        
        where_clause = and_(
            Run.ts >= start_ts,
            Run.ts < end_ts,
            Run.deleted.is_(False)
        )
        
        if engine:
            where_clause = and_(where_clause, Run.engine == engine)
        
        runs = self.db.execute(
            select(Run).where(where_clause)
        ).scalars().all()
        
        if not runs:
            return []
        
        # Group runs by engine
        runs_by_engine = defaultdict(list)
        for run in runs:
            runs_by_engine[run.engine].append(run)
        
        metrics = []
        
        for run_engine, engine_runs in runs_by_engine.items():
            # Compute overall metrics for this engine
            overall_metrics = self._compute_engine_metrics(engine_runs, "overall")
            metrics.append(overall_metrics)
            
            # Compute brand-specific metrics
            brand_metrics = self._compute_brand_metrics(engine_runs, "extreme_networks")
            if brand_metrics:
                metrics.append(brand_metrics)
            
            # Compute competitor metrics
            competitor_metrics = self._compute_competitor_metrics(engine_runs, "competitors")
            if competitor_metrics:
                metrics.append(competitor_metrics)
        
        return metrics
    #calculates citations costs, domains, runs
    def _compute_engine_metrics(self, runs: List[Run], context: str) -> DailyMetrics:
        """Compute overall metrics for a set of runs."""
        total_runs = len(runs)
        total_cost = sum(float(r.cost_usd or 0) for r in runs)
        
        # Aggregate citations and domains
        all_citations = []
        all_domains = set()
        domain_counts = Counter()
        
        for run in runs:
            citations = run.citations_enriched or []
            all_citations.extend(citations)
            
            for citation in citations:
                domain = citation.get('domain', '')
                if domain:
                    all_domains.add(domain)
                    domain_counts[domain] += 1
        
        # Calculate top domains with quality scores
        top_domains = self._calculate_top_domains(domain_counts, all_citations)
        
        # Calculate average visibility score
        visibility_scores = [self._calculate_citation_quality(c) for c in all_citations]
        avg_visibility = sum(visibility_scores) / len(visibility_scores) if visibility_scores else 0
        
        # Count high quality citations
        high_quality_count = sum(1 for score in visibility_scores if score > 0.7)
        
        return DailyMetrics(
            date=runs[0].ts.date(),
            engine=runs[0].engine,
            brand_context=context,
            total_runs=total_runs,
            total_cost_usd=total_cost,
            total_citations=len(all_citations),
            unique_domains=len(all_domains),
            top_domains=top_domains,
            brand_mentions=0,  # Will be computed in brand-specific metrics
            competitor_mentions=0,  # Will be computed in brand-specific metrics
            share_of_voice_pct=0,  # Will be computed in brand-specific metrics
            avg_visibility_score=round(avg_visibility, 2),
            high_quality_citations=high_quality_count,
            last_updated=datetime.utcnow().isoformat(),
            data_version="1.0"
        )
    #brand visibility metrics calculated here
    def _compute_brand_metrics(self, runs: List[Run], context: str) -> Optional[DailyMetrics]:
        """Compute metrics specifically for Extreme Networks brand mentions."""
        brand_runs = [r for r in runs if r.extreme_mentioned]
        
        if not brand_runs:
            return None
        
        # Get base metrics from overall computation
        base_metrics = self._compute_engine_metrics(runs, context)
        
        # Override with brand-specific data
        base_metrics.brand_mentions = len(brand_runs)
        base_metrics.competitor_mentions = len(runs) - len(brand_runs)
        
        # Calculate share of voice
        total_mentions = base_metrics.brand_mentions + base_metrics.competitor_mentions
        if total_mentions > 0:
            base_metrics.share_of_voice_pct = round(
                (base_metrics.brand_mentions / total_mentions) * 100, 2
            )
        
        return base_metrics
    #competitor metrics calculated here, like rank
    def _compute_competitor_metrics(self, runs: List[Run], context: str) -> Optional[DailyMetrics]:
        """Compute metrics for competitor mentions."""
        competitor_runs = [r for r in runs if not r.extreme_mentioned and r.entities_normalized]
        
        if not competitor_runs:
            return None
        
        # Get base metrics from overall computation
        base_metrics = self._compute_engine_metrics(runs, context)
        
        # Override with competitor-specific data
        base_metrics.brand_mentions = len([r for r in runs if r.extreme_mentioned])
        base_metrics.competitor_mentions = len(competitor_runs)
        
        # Calculate share of voice (inverse of brand share)
        total_mentions = base_metrics.brand_mentions + base_metrics.competitor_mentions
        if total_mentions > 0:
            base_metrics.share_of_voice_pct = round(
                (base_metrics.competitor_mentions / total_mentions) * 100, 2
            )
        
        return base_metrics
    
    def _calculate_top_domains(self, domain_counts: Counter, citations: List[Dict]) -> List[Dict]:
        """Calculate top domains with quality scores."""
        top_domains = []
        
        for domain, count in domain_counts.most_common(10):  # Top 10 domains
            # Find citations for this domain to calculate quality
            domain_citations = [c for c in citations if c.get('domain') == domain]
            quality_scores = [self._calculate_citation_quality(c) for c in domain_citations]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            top_domains.append({
                "domain": domain,
                "count": count,
                "quality_score": round(avg_quality, 2)
            })
        
        return top_domains
    #currently not using this because it doesn't work that well, could use Ahrefs API to get domain authority
    def _calculate_citation_quality(self, citation: Dict) -> float:
        """Calculate quality score for a citation (0.0 to 1.0)."""
        score = 0.0
        
        # Domain authority (basic heuristic - could be enhanced with external APIs)
        domain = citation.get('domain', '').lower()
        if domain:
            # Simple scoring based on domain characteristics
            if domain.endswith('.com') and len(domain.split('.')) == 2:
                score += 0.3  # Clean commercial domain
            elif domain.endswith('.org') or domain.endswith('.edu'):
                score += 0.4  # Educational/organizational domains
            elif 'news' in domain or 'media' in domain:
                score += 0.2  # News/media domains
        
        # Title quality
        title = citation.get('title', '')
        if title and len(title) > 10:
            score += 0.2  # Has meaningful title
        
        # URL structure
        url = citation.get('url', '')
        if url and 'utm_' not in url and 'gclid' not in url:
            score += 0.1  # Clean URL without tracking params
        
        # Rank bonus (earlier results get higher scores)
        rank = citation.get('rank', 999)
        if rank <= 5:
            score += 0.2
        elif rank <= 10:
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def upsert_daily_metrics(self, metrics: List[DailyMetrics]) -> None:
        """Upsert daily metrics to the database."""
        for metric in metrics:
            # Check if metric already exists
            existing = self.db.get(DailyMetrics, (
                metric.date, 
                metric.engine, 
                metric.brand_context
            ))
            
            if existing:
                # Update existing
                for key, value in metric.__dict__.items():
                    if not key.startswith('_'):
                        setattr(existing, key, value)
                existing.last_updated = datetime.utcnow().isoformat()
            else:
                # Insert new
                self.db.add(metric)
        
        self.db.commit()
    
    def get_daily_metrics(self, 
                         start_date: date, 
                         end_date: date, 
                         engine: Optional[str] = None,
                         brand_context: Optional[str] = None) -> List[DailyMetrics]:
        """Retrieve daily metrics for a date range."""
        where_clause = and_(
            DailyMetrics.date >= start_date,
            DailyMetrics.date <= end_date
        )
        
        if engine:
            where_clause = and_(where_clause, DailyMetrics.engine == engine)
        
        if brand_context:
            where_clause = and_(where_clause, DailyMetrics.brand_context == brand_context)
        
        return self.db.execute(
            select(DailyMetrics)
            .where(where_clause)
            .order_by(DailyMetrics.date, DailyMetrics.engine, DailyMetrics.brand_context)
        ).scalars().all()
    
    def get_metrics_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get summary metrics for the last N days."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        metrics = self.get_daily_metrics(start_date, end_date)
        
        if not metrics:
            return {}
        
        # Aggregate across the period
        summary = {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_runs": sum(m.total_runs for m in metrics),
            "total_cost_usd": float(sum(m.total_cost_usd for m in metrics)),
            "total_citations": sum(m.total_citations for m in metrics),
            "avg_visibility_score": 0,
            "brand_share_of_voice": 0,
            "top_domains": [],
            "by_engine": defaultdict(lambda: {
                "runs": 0, "cost": 0, "citations": 0
            })
        }
        
        # Calculate averages and engine breakdowns
        visibility_scores = [m.avg_visibility_score for m in metrics if m.avg_visibility_score > 0]
        if visibility_scores:
            summary["avg_visibility_score"] = round(sum(visibility_scores) / len(visibility_scores), 2)
        
        # Brand share of voice (from brand context metrics)
        brand_metrics = [m for m in metrics if m.brand_context == "extreme_networks"]
        if brand_metrics:
            total_share = sum(m.share_of_voice_pct for m in brand_metrics)
            summary["brand_share_of_voice"] = round(total_share / len(brand_metrics), 2)
        
        # Top domains across the period
        domain_totals = defaultdict(int)
        for metric in metrics:
            for domain_info in metric.top_domains:
                domain_totals[domain_info["domain"]] += domain_info["count"]
        
        summary["top_domains"] = [
            {"domain": domain, "count": count}
            for domain, count in sorted(domain_totals.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Engine breakdowns
        for metric in metrics:
            engine = metric.engine
            summary["by_engine"][engine]["runs"] += metric.total_runs
            summary["by_engine"][engine]["cost"] += float(metric.total_cost_usd)
            summary["by_engine"][engine]["citations"] += metric.total_citations
        
        # Convert defaultdict to regular dict
        summary["by_engine"] = dict(summary["by_engine"])
        
        return summary
