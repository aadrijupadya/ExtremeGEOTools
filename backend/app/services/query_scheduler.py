from __future__ import annotations
import json
import random
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid

from .engines import call_engine
from .extract import extract_competitors, extract_links, to_domains
from ..models.run import Run
from ..services.database import get_db


class QueryScheduler:
    """Manages automated query execution according to the defined schedule and distribution."""
    
    def __init__(self):
        self.queries_path = Path("data/queries/system_queries.json")
        self.queries_config = self._load_queries_config()
    
    def _load_queries_config(self) -> Dict[str, Any]:
        """Load the system queries configuration."""
        try:
            with open(self.queries_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading queries config: {e}")
            return {}
    
    def get_daily_queries(self, target_date: date) -> List[Dict[str, Any]]:
        """Get the queries to run for a specific date."""
        if not self.queries_config:
            return []
        
        # Get all query sets
        generic_queries = self.queries_config.get("query_sets", {}).get("generic_intent", [])
        brand_queries = self.queries_config.get("query_sets", {}).get("brand_focused", [])
        comparison_queries = self.queries_config.get("query_sets", {}).get("comparison", [])
        
        # Get engine distribution
        engine_dist = self.queries_config.get("engine_distribution", {})
        gpt_queries = engine_dist.get("gpt-4o-mini-search-preview", 15)
        perplexity_queries = engine_dist.get("perplexity-online", 15)
        
        # Create daily query plan
        daily_queries = []
        
        # Distribute generic intent queries
        generic_gpt = generic_queries[:gpt_queries//3]
        generic_perplexity = generic_queries[gpt_queries//3:gpt_queries//3*2]
        
        # Distribute brand-focused queries
        brand_gpt = brand_queries[:gpt_queries//3]
        brand_perplexity = brand_queries[gpt_queries//3:gpt_queries//3*2]
        
        # Distribute comparison queries
        comp_gpt = comparison_queries[:gpt_queries//3]
        comp_perplexity = comparison_queries[gpt_queries//3:gpt_queries//3*2]
        
        # Add GPT queries
        for query in generic_gpt + brand_gpt + comp_gpt:
            daily_queries.append({
                "query": query,
                "engine": "gpt-4o-mini-search-preview",
                "intent": self._classify_intent(query),
                "priority": "high"
            })
        
        # Add Perplexity queries
        for query in generic_perplexity + brand_perplexity + comp_perplexity:
            daily_queries.append({
                "query": query,
                "engine": "perplexity",
                "intent": self._classify_intent(query),
                "priority": "high"
            })
        
        # Shuffle to avoid predictable patterns
        random.shuffle(daily_queries)
        
        return daily_queries
    
    def _classify_intent(self, query: str) -> str:
        """Classify the intent of a query."""
        query_lower = query.lower()
        if any(word in query_lower for word in ["vs", "versus", "compare", "comparison"]):
            return "comparison"
        elif any(brand in query_lower for brand in ["extreme", "cisco", "juniper", "aruba"]):
            return "brand_focused"
        else:
            return "generic_intent"
    
    def execute_daily_queries(self, target_date: date, dry_run: bool = False) -> List[Dict[str, Any]]:
        """Execute all daily queries for a specific date."""
        queries = self.get_daily_queries(target_date)
        results = []
        
        print(f"Executing {len(queries)} queries for {target_date}")
        
        # Get database session
        db = next(get_db())
        
        for i, query_info in enumerate(queries):
            print(f"Query {i+1}/{len(queries)}: {query_info['query'][:50]}...")
            
            if dry_run:
                results.append({
                    "query": query_info["query"],
                    "engine": query_info["engine"],
                    "intent": query_info["intent"],
                    "status": "dry_run",
                    "result": None
                })
                continue
            
            try:
                # Execute query
                result = call_engine(
                    engine=query_info["engine"],
                    prompt=query_info["query"],
                    temperature=0.2
                )
                
                # Extract entities and citations
                entities = extract_competitors(result.get("text", ""))
                links = extract_links(result.get("text", ""))
                domains = to_domains(links)
                
                # Check if Extreme Networks is mentioned
                extreme_mentioned = any(
                    entity.name.lower() == "extreme networks" 
                    for entity in entities
                )
                
                # Create run record
                run_id = str(uuid.uuid4())
                # Heuristic for branded queries: brand names or comparison terms
                q_lower = (query_info["query"] or "").lower()
                branded_terms = [
                    "extreme", "cisco", "juniper", "aruba", "meraki", "fortinet", "palo alto",
                    "ruckus", "ubiquiti", "netgear", "tp-link", "d-link", "huawei", "arista",
                    "vs", "versus", "compare", "comparison"
                ]
                is_branded = (query_info.get("intent") in ("brand_focused", "comparison")) or any(t in q_lower for t in branded_terms)
                run_data = {
                    "id": run_id,
                    "ts": datetime.utcnow(),
                    "query": query_info["query"],
                    "engine": query_info["engine"],
                    "model": result.get("model"),
                    "intent": query_info["intent"],
                    "is_branded": is_branded,
                    "status": "completed",
                    "latency_ms": result.get("latency_ms", 0),
                    "input_tokens": result.get("input_tokens", 0),
                    "output_tokens": result.get("output_tokens", 0),
                    "cost_usd": result.get("cost_usd", 0),
                    "raw_excerpt": result.get("text", "")[:1000],  # Truncate for storage
                    "links": links,
                    "domains": domains,
                    "extreme_mentioned": extreme_mentioned,
                    "entities_normalized": [
                        {
                            "name": entity.name,
                            "first_pos": entity.first_pos,
                            "type": "competitor"
                        }
                        for entity in entities
                    ],
                    "citations_enriched": [],  # Will be populated later
                    "vendors": [],  # Will be populated later
                    "deleted": False,
                    "source": "automated"  # Mark as automated query
                }
                
                # Save to database
                db_run = Run(**run_data)
                db.add(db_run)
                db.commit()
                
                print(f"✅ Saved run {run_id} to database")
                
                results.append({
                    "run_id": run_id,
                    "query": query_info["query"],
                    "engine": query_info["engine"],
                    "intent": query_info["intent"],
                    "status": "completed",
                    "result": run_data
                })
                
                # Add small delay between queries
                import time
                time.sleep(1)
                
            except Exception as e:
                print(f"Error executing query: {e}")
                results.append({
                    "query": query_info["query"],
                    "engine": query_info["engine"],
                    "intent": query_info["intent"],
                    "status": "error",
                    "error": str(e),
                    "result": None
                })
        
        return results
    
    def get_schedule_info(self) -> Dict[str, Any]:
        """Get information about the current schedule."""
        if not self.queries_config:
            return {}
        
        schedule = self.queries_config.get("schedule", {})
        engine_dist = self.queries_config.get("engine_distribution", {})
        competitor_set = self.queries_config.get("competitor_set", [])
        
        return {
            "cadence": schedule.get("cadence"),
            "runs_per_day": schedule.get("runs_per_day"),
            "morning_time": schedule.get("morning_time"),
            "evening_time": schedule.get("evening_time"),
            "total_queries_per_day": sum(engine_dist.values()),
            "engine_distribution": engine_dist,
            "competitor_set": competitor_set,
            "query_types": {
                "generic_intent": len(self.queries_config.get("query_sets", {}).get("generic_intent", [])),
                "brand_focused": len(self.queries_config.get("query_sets", {}).get("brand_focused", [])),
                "comparison": len(self.queries_config.get("query_sets", {}).get("comparison", []))
            }
        }


# Convenience function for manual execution
def run_daily_queries(target_date: Optional[date] = None, dry_run: bool = False) -> List[Dict[str, Any]]:
    """Run daily queries for a specific date (defaults to today)."""
    if target_date is None:
        target_date = date.today()
    
    scheduler = QueryScheduler()
    return scheduler.execute_daily_queries(target_date, dry_run=dry_run)


if __name__ == "__main__":
    # Test the scheduler
    scheduler = QueryScheduler()
    print("Schedule Info:", scheduler.get_schedule_info())
    
    # Test with today's date
    today = date.today()
    print(f"\nExecuting queries for {today} (dry run)")
    results = run_daily_queries(today, dry_run=True)
    
    print(f"\nExecuted {len(results)} queries:")
    for result in results[:5]:  # Show first 5
        print(f"- {result['engine']}: {result['query'][:50]}... ({result['status']})")
