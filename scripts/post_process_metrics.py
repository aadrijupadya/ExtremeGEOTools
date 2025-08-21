#!/usr/bin/env python3
"""
Post-Processing Pipeline for Automated Queries
This script runs after automated queries complete to:
1. Compute daily metrics
2. Update dashboard data
3. Generate insights and reports
"""

import sys
import logging
import json
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.metrics import MetricsService
from app.services.database import get_db
from app.models.run import Run
from app.models.metrics import DailyMetrics


class PostProcessPipeline:
    """Post-processing pipeline for automated query results."""
    
    def __init__(self):
        self.setup_logging()
        self.db = next(get_db())
        self.metrics_service = MetricsService(self.db)
        
    def setup_logging(self):
        """Setup logging."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"post_process_{date.today().isoformat()}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def get_recent_automated_runs(self, days_back: int = 3) -> List[Run]:
        """Get recent automated runs for processing."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # For now, get all recent runs since source column may not exist yet
        # TODO: Once source column is added, filter by source="automated"
        runs = self.db.query(Run).filter(
            Run.deleted == False,
            Run.ts >= cutoff_date
        ).order_by(Run.ts.desc()).all()
        
        self.logger.info(f"Found {len(runs)} total runs in the last {days_back} days")
        self.logger.info("Note: Not filtering by source yet (source column may not exist)")
        
        return runs
    
    def compute_daily_metrics(self, target_date: date) -> List[DailyMetrics]:
        """Compute daily metrics for a specific date."""
        self.logger.info(f"Computing daily metrics for {target_date}")
        
        try:
            metrics = self.metrics_service.compute_daily_metrics(target_date)
            self.logger.info(f"Generated {len(metrics)} metric records")
            return metrics
        except Exception as e:
            self.logger.error(f"Error computing metrics for {target_date}: {e}")
            return []
    
    def compute_share_of_voice_metrics(self, runs: List[Run]) -> Dict[str, Any]:
        """Compute share of voice metrics from recent runs."""
        if not runs:
            return {}
        
        # Group runs by date
        runs_by_date = {}
        for run in runs:
            run_date = run.ts.date()
            if run_date not in runs_by_date:
                runs_by_date[run_date] = []
            runs_by_date[run_date].append(run)
        
        share_of_voice_data = {}
        
        for run_date, date_runs in runs_by_date.items():
            # Count brand mentions
            extreme_mentions = sum(1 for run in date_runs if run.extreme_mentioned)
            total_runs = len(date_runs)
            
            # Calculate share of voice
            share_of_voice = (extreme_mentions / total_runs * 100) if total_runs > 0 else 0
            
            share_of_voice_data[run_date.isoformat()] = {
                "date": run_date.isoformat(),
                "total_runs": total_runs,
                "extreme_mentions": extreme_mentions,
                "share_of_voice_pct": round(share_of_voice, 2),
                "competitor_mentions": total_runs - extreme_mentions
            }
        
        return share_of_voice_data
    
    def compute_cost_metrics(self, runs: List[Run]) -> Dict[str, Any]:
        """Compute cost metrics from recent runs."""
        if not runs:
            return {}
        
        total_cost = sum(float(run.cost_usd or 0) for run in runs)
        total_tokens = sum(run.input_tokens + run.output_tokens for run in runs)
        
        # Cost by engine
        cost_by_engine = {}
        for run in runs:
            engine = run.engine
            if engine not in cost_by_engine:
                cost_by_engine[engine] = {"cost": 0, "runs": 0}
            cost_by_engine[engine]["cost"] += float(run.cost_usd or 0)
            cost_by_engine[engine]["runs"] += 1
        
        return {
            "total_cost_usd": round(total_cost, 6),
            "total_tokens": total_tokens,
            "avg_cost_per_run": round(total_cost / len(runs), 6) if runs else 0,
            "cost_by_engine": cost_by_engine
        }
    
    def compute_competitor_insights(self, runs: List[Run]) -> Dict[str, Any]:
        """Compute competitor insights from recent runs."""
        if not runs:
            return {}
        
        # Extract all entities mentioned
        all_entities = []
        competitor_detection_analysis = {
            "total_runs_analyzed": len(runs),
            "runs_with_entities": 0,
            "runs_without_entities": 0,
            "entity_extraction_issues": [],
            "competitor_mentions_by_run": {},
            "extreme_networks_analysis": {
                "total_mentions": 0,
                "runs_mentioned": 0,
                "ranking_analysis": [],
                "context_analysis": []
            }
        }
        
        for run in runs:
            try:
                entities = run.entities_normalized
                if entities is None:
                    competitor_detection_analysis["runs_without_entities"] += 1
                    competitor_detection_analysis["entity_extraction_issues"].append({
                        "run_id": run.id,
                        "issue": "entities_normalized is None",
                        "query": run.query
                    })
                    continue
                
                # Handle different data types
                if isinstance(entities, str):
                    # If it's a string, try to parse as JSON
                    try:
                        import json
                        entities = json.loads(entities)
                    except:
                        competitor_detection_analysis["entity_extraction_issues"].append({
                            "run_id": run.id,
                            "issue": f"Could not parse entities as JSON: {entities[:100]}",
                            "query": run.query
                        })
                        continue
                
                if isinstance(entities, list):
                    competitor_detection_analysis["runs_with_entities"] += 1
                    
                    # Track what was found in each run
                    entities_found = []
                    extreme_networks_rank = None
                    
                    for i, entity in enumerate(entities):
                        if isinstance(entity, dict):
                            name = entity.get("name", "Unknown")
                            first_pos = entity.get("first_pos", 0)
                        else:
                            name = str(entity)
                            first_pos = i
                        
                        # Create processed entity with rank information
                        processed_entity = {
                            "name": name,
                            "rank": i + 1,
                            "first_pos": first_pos
                        }
                        
                        entities_found.append(processed_entity)
                        all_entities.append(processed_entity)  # Add processed entity to all_entities
                        
                        # Check for Extreme Networks mentions
                        if name.lower() in ["extreme networks", "extremenetworks"]:
                            extreme_networks_rank = i + 1
                            competitor_detection_analysis["extreme_networks_analysis"]["total_mentions"] += 1
                            
                            # Track ranking analysis
                            competitor_detection_analysis["extreme_networks_analysis"]["ranking_analysis"].append({
                                "run_id": run.id,
                                "query": run.query,
                                "rank": i + 1,
                                "total_entities_in_run": len(entities),
                                "engine": run.engine,
                                "date": run.ts.date().isoformat()
                            })
                    
                    # Track if Extreme Networks was mentioned in this run
                    if extreme_networks_rank:
                        competitor_detection_analysis["extreme_networks_analysis"]["runs_mentioned"] += 1
                    
                    competitor_detection_analysis["competitor_mentions_by_run"][run.id] = {
                        "query": run.query,
                        "entities_found": entities_found,
                        "extreme_mentioned": run.extreme_mentioned,
                        "extreme_networks_rank": extreme_networks_rank,
                        "engine": run.engine,
                        "total_entities": len(entities)
                    }
                else:
                    competitor_detection_analysis["entity_extraction_issues"].append({
                        "run_id": run.id,
                        "issue": f"Unexpected entities type: {type(entities)}",
                        "query": run.query
                    })
                    
            except Exception as e:
                competitor_detection_analysis["entity_extraction_issues"].append({
                    "run_id": run.id,
                    "issue": f"Error processing entities: {str(e)}",
                    "query": run.query
                })
                continue
        
        # Count entity mentions
        entity_counts = {}
        entity_ranking_analysis = {}
        
        # Debug: Log what we're processing
        self.logger.info(f"Processing {len(all_entities)} entities for ranking analysis")
        
        for entity in all_entities:
            try:
                if isinstance(entity, dict):
                    name = entity.get("name", "Unknown")
                    # Since entities from database don't have rank, we'll use the order they appear
                    # This gives us a simple ranking based on entity extraction order
                    rank = None  # We'll calculate this differently
                elif isinstance(entity, str):
                    name = entity
                    rank = None
                else:
                    name = str(entity)
                    rank = None
                
                if name not in entity_counts:
                    entity_counts[name] = 0
                    entity_ranking_analysis[name] = []
                
                entity_counts[name] += 1
                
            except Exception as e:
                self.logger.warning(f"Error processing entity {entity}: {e}")
                continue
        
        # Now calculate rankings based on entity order in the original extraction
        # We'll go through each run and assign rankings based on entity order
        for run in runs:
            try:
                entities = run.entities_normalized
                if not entities or not isinstance(entities, list):
                    continue
                
                # Assign rankings based on order in the entity list
                for i, entity in enumerate(entities):
                    if isinstance(entity, dict):
                        name = entity.get("name", "Unknown")
                    else:
                        name = str(entity)
                    
                    if name in entity_ranking_analysis:
                        # Add the ranking position (1-based) for this entity in this run
                        entity_ranking_analysis[name].append(i + 1)
                        self.logger.debug(f"Added rank {i + 1} for {name} in run {run.id}")
                
            except Exception as e:
                self.logger.warning(f"Error processing run {run.id} for ranking: {e}")
                continue
        
        # Debug: Log ranking analysis results
        self.logger.info(f"Ranking analysis results: {entity_ranking_analysis}")
        
        # Top competitors with ranking analysis
        top_competitors = []
        for name, count in sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            ranking_data = entity_ranking_analysis.get(name, [])
            avg_rank = sum(ranking_data) / len(ranking_data) if ranking_data else 0
            
            self.logger.info(f"Competitor {name}: {count} mentions, ranking_data: {ranking_data}, avg_rank: {avg_rank}")
            
            top_competitors.append({
                "name": name,
                "mentions": count,
                "avg_rank": round(avg_rank, 2) if avg_rank > 0 else "N/A",
                "ranking_positions": sorted(ranking_data) if ranking_data else []
            })
        
        # Analyze competitor detection effectiveness
        detection_effectiveness = {
            "entity_extraction_rate": round(
                competitor_detection_analysis["runs_with_entities"] / 
                competitor_detection_analysis["total_runs_analyzed"] * 100, 2
            ) if competitor_detection_analysis["total_runs_analyzed"] > 0 else 0,
            "avg_entities_per_run": round(
                len(all_entities) / competitor_detection_analysis["runs_with_entities"], 2
            ) if competitor_detection_analysis["runs_with_entities"] > 0 else 0,
            "extreme_networks_detection_rate": round(
                competitor_detection_analysis["extreme_networks_analysis"]["runs_mentioned"] / 
                len(runs) * 100, 2
            ) if runs else 0,
            "extreme_networks_mention_rate": round(
                competitor_detection_analysis["extreme_networks_analysis"]["total_mentions"] / 
                len(all_entities) * 100, 2
            ) if all_entities else 0
        }
        
        return {
            "total_entity_mentions": len(all_entities),
            "unique_entities": len(entity_counts),
            "top_competitors": top_competitors,
            "detection_effectiveness": detection_effectiveness,
            "competitor_detection_analysis": competitor_detection_analysis,
            "extreme_networks_detailed_analysis": competitor_detection_analysis["extreme_networks_analysis"]
        }
    
    def compute_citation_analysis(self, runs: List[Run]) -> Dict[str, Any]:
        """Compute simplified citation analysis focusing on domain frequency."""
        if not runs:
            return {}
        
        domain_counts = {}
        all_citations = []
        
        for run in runs:
            try:
                # Extract links and domains
                links = run.links or []
                domains = run.domains or []
                
                # Count domain mentions
                for i, link in enumerate(links):
                    domain = domains[i] if i < len(domains) else ""
                    
                    # Skip invalid domains (empty, single characters, etc.)
                    if not domain or len(domain) < 3 or domain in ['"', '.', 'w', 'e', '[', ']']:
                        continue
                    
                    if domain not in domain_counts:
                        domain_counts[domain] = {
                            "count": 0,
                            "total_mentions": 0,
                            "urls": [],
                            "mentions_by_date": {},
                            "avg_rank": 0,
                            "runs_mentioned": set()
                        }
                    
                    domain_counts[domain]["count"] += 1
                    domain_counts[domain]["total_mentions"] += 1
                    domain_counts[domain]["urls"].append(link)
                    domain_counts[domain]["runs_mentioned"].add(run.id)
                    
                    # Track mentions by date
                    date_key = run.ts.date().isoformat()
                    if date_key not in domain_counts[domain]["mentions_by_date"]:
                        domain_counts[domain]["mentions_by_date"][date_key] = 0
                    domain_counts[domain]["mentions_by_date"][date_key] += 1
                    
                    citation_data = {
                        "url": link,
                        "domain": domain,
                        "rank": i + 1,
                        "run_id": run.id,
                        "query": run.query,
                        "engine": run.engine,
                        "date": run.ts.date().isoformat()
                    }
                    all_citations.append(citation_data)
                    
            except Exception as e:
                self.logger.warning(f"Error processing citations for run {run.id}: {e}")
                continue
        
        # Calculate domain averages and convert sets to counts
        for domain, stats in domain_counts.items():
            if stats["count"] > 0:
                # Calculate average rank
                ranks = [c["rank"] for c in all_citations if c["domain"] == domain]
                stats["avg_rank"] = round(sum(ranks) / len(ranks), 2) if ranks else 0
                stats["runs_mentioned"] = len(stats["runs_mentioned"])
        
        # Top 5 domains by frequency (total mentions)
        top_domains_by_frequency = sorted(
            domain_counts.items(),
            key=lambda x: x[1]["total_mentions"],
            reverse=True
        )[:5]
        
        # Top domains by count (unique URLs)
        top_domains_by_count = sorted(
            domain_counts.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:10]
        
        return {
            "total_citations": len(all_citations),
            "unique_domains": len(domain_counts),
            "top_5_domains_by_frequency": [
                {
                    "domain": domain,
                    "total_mentions": stats["total_mentions"],
                    "unique_urls": stats["count"],
                    "avg_rank": stats["avg_rank"],
                    "runs_mentioned": stats["runs_mentioned"],
                    "mentions_by_date": stats["mentions_by_date"],
                    "sample_urls": stats["urls"][:3]  # Show first 3 URLs
                }
                for domain, stats in top_domains_by_frequency
            ],
            "top_domains_by_count": [
                {
                    "domain": domain,
                    "count": stats["count"],
                    "total_mentions": stats["total_mentions"],
                    "avg_rank": stats["avg_rank"],
                    "runs_mentioned": stats["runs_mentioned"]
                }
                for domain, stats in top_domains_by_count
            ],
            "domain_breakdown": {
                "total_domains_found": len(domain_counts),
                "domains_with_multiple_mentions": len([d for d in domain_counts.values() if d["total_mentions"] > 1]),
                "most_frequent_domain": top_domains_by_frequency[0][0] if top_domains_by_frequency else "None"
            }
        }
    
    def _calculate_citation_quality(self, url: str, domain: str, rank: int) -> float:
        """Calculate quality score for a citation (0.0 to 1.0)."""
        score = 0.0
        
        # Domain authority scoring
        if domain:
            domain_lower = domain.lower()
            
            # High authority domains
            if any(auth in domain_lower for auth in ["cisco.com", "juniper.net", "hpe.com", "aruba.com", "dell.com"]):
                score += 0.4  # Official vendor sites
            elif any(auth in domain_lower for auth in ["gartner.com", "forrester.com", "idc.com", "techradar.com"]):
                score += 0.35  # Industry analysts
            elif any(auth in domain_lower for auth in ["zdnet.com", "techcrunch.com", "venturebeat.com", "crn.com"]):
                score += 0.3  # Tech news sites
            elif domain_lower.endswith(".edu"):
                score += 0.25  # Educational institutions
            elif domain_lower.endswith(".org"):
                score += 0.2  # Organizations
            elif domain_lower.endswith(".com") and len(domain_lower.split(".")) == 2:
                score += 0.15  # Clean commercial domains
            else:
                score += 0.1  # Other domains
        
        # URL structure quality
        if url:
            # Penalize tracking parameters
            if any(param in url.lower() for param in ["utm_", "gclid", "fbclid", "ref="]):
                score -= 0.1
            
            # Bonus for clean URLs
            if not any(char in url for char in ["?", "&", "#"]):
                score += 0.1
        
        # Rank bonus (earlier results get higher scores)
        if rank <= 3:
            score += 0.2
        elif rank <= 5:
            score += 0.15
        elif rank <= 10:
            score += 0.1
        
        return max(0.0, min(score, 1.0))  # Cap between 0.0 and 1.0
    
    def generate_dashboard_summary(self, runs: List[Run]) -> Dict[str, Any]:
        """Generate a comprehensive dashboard summary."""
        if not runs:
            return {}
        
        # Get date range
        dates = [run.ts.date() for run in runs]
        start_date = min(dates)
        end_date = max(dates)
        
        # Compute all metrics
        share_of_voice = self.compute_share_of_voice_metrics(runs)
        cost_metrics = self.compute_cost_metrics(runs)
        competitor_insights = self.compute_competitor_insights(runs)
        citation_analysis = self.compute_citation_analysis(runs)
        
        # Generate summary
        summary = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days + 1
            },
            "execution_summary": {
                "total_runs": len(runs),
                "successful_runs": len([run for run in runs if run.status == "completed"]),
                "failed_runs": len([run for run in runs if run.status != "completed"]),
                "total_cost_usd": cost_metrics.get("total_cost_usd", 0)
            },
            "share_of_voice": share_of_voice,
            "cost_analysis": cost_metrics,
            "competitor_insights": competitor_insights,
            "citation_analysis": citation_analysis,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return summary
    
    def save_dashboard_summary(self, summary: Dict[str, Any]) -> bool:
        """Save dashboard summary to a JSON file for frontend consumption."""
        try:
            dashboard_dir = Path("data/dashboard")
            dashboard_dir.mkdir(exist_ok=True)
            
            summary_file = dashboard_dir / "latest_summary.json"
            
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            self.logger.info(f"Dashboard summary saved to {summary_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving dashboard summary: {e}")
            return False
    
    def run_post_processing(self, target_date: Optional[date] = None) -> bool:
        """Run the complete post-processing pipeline."""
        try:
            self.logger.info("Starting post-processing pipeline")
            
            # Use target date or default to today
            if target_date is None:
                target_date = date.today()
            
            # Get recent automated runs
            runs = self.get_recent_automated_runs(days_back=7)  # Look back 7 days
            
            if not runs:
                self.logger.warning("No automated runs found for post-processing")
                return False
            
            # Compute daily metrics
            metrics = self.compute_daily_metrics(target_date)
            if metrics:
                self.metrics_service.upsert_daily_metrics(metrics)
                self.logger.info("Daily metrics computed and saved")
            
            # Generate dashboard summary
            summary = self.generate_dashboard_summary(runs)
            if summary:
                self.save_dashboard_summary(summary)
                self.logger.info("Dashboard summary generated and saved")
            
            # Log completion
            self.logger.info("Post-processing pipeline completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in post-processing pipeline: {e}")
            return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Post-Processing Pipeline for Automated Queries")
    parser.add_argument("--date", type=str, help="Target date (YYYY-MM-DD). Defaults to today.")
    parser.add_argument("--force", action="store_true", help="Force processing even if no recent runs")
    
    args = parser.parse_args()
    
    # Parse target date
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
            return 1
    
    # Run pipeline
    pipeline = PostProcessPipeline()
    success = pipeline.run_post_processing(target_date)
    
    if success:
        print("✅ Post-processing pipeline completed successfully")
        return 0
    else:
        print("❌ Post-processing pipeline failed")
        return 1


if __name__ == "__main__":
    exit(main())
