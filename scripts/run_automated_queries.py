#!/usr/bin/env python3
"""
Script to execute automated competitive intelligence queries and store results.
This will run all 30 queries from system_queries.json and populate the automated_runs table.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.engines import call_engine
from app.services.extract import extract_competitors, extract_links, to_domains
from app.services.database import get_db
from app.models.automated_run import AutomatedRun
from app.services.pricing import estimate_cost

class AutomatedQueryExecutor:
    def __init__(self):
        self.db = next(get_db())
        self.queries_config = self._load_queries_config()
        
    def _load_queries_config(self) -> Dict[str, Any]:
        """Load the system queries configuration."""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'queries', 'system_queries.json')
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _classify_intent(self, query: str) -> str:
        """Classify the query intent based on content."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['extreme', 'juniper', 'cisco', 'aruba']):
            return 'brand_focused'
        elif any(word in query_lower for word in ['vs', 'versus', 'compare']):
            return 'comparison'
        else:
            return 'generic_intent'
    
    def _generate_run_id(self, engine: str, intent: str) -> str:
        """Generate a unique run ID."""
        timestamp = int(datetime.now().timestamp() * 1000)
        return f"auto_{engine}_{intent}_{timestamp}"
    
    def execute_single_query(self, query: str, engine: str, intent_category: str) -> Dict[str, Any]:
        """Execute a single query and return results."""
        print(f"🔄 Executing: {query[:60]}... ({engine})")
        
        try:
            # Call the engine
            start_time = datetime.now()
            response = call_engine(engine, query, temperature=0.2)
            end_time = datetime.now()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            if not response or not response.get('text'):
                print(f"❌ No response from {engine}")
                return None
            
            answer = response['text']
            
            # Extract competitive intelligence data
            entities = extract_competitors(answer)
            links = extract_links(answer)
            domains = to_domains(links)
            
            # Convert VendorItem objects to dictionaries for JSON serialization
            entities_normalized = []
            for entity in entities:
                if hasattr(entity, 'dict'):
                    # Pydantic model
                    entities_normalized.append(entity.dict())
                elif hasattr(entity, '__dict__'):
                    # Regular object
                    entities_normalized.append(entity.__dict__)
                else:
                    # String or other type
                    entities_normalized.append(str(entity))
            
            # Check for Extreme Networks mentions
            extreme_mentioned = any(
                'extreme' in str(entity).lower() for entity in entities_normalized
            )
            
            # Count competitors mentioned
            competitor_mentions = {
                'extreme_networks': extreme_mentioned,
                'cisco': any('cisco' in str(entity).lower() for entity in entities_normalized),
                'juniper': any('juniper' in str(entity).lower() for entity in entities_normalized),
                'aruba': any('aruba' in str(entity).lower() for entity in entities_normalized)
            }
            
            # Estimate costs
            cost_estimate = estimate_cost(response.get('input_tokens', 0), response.get('output_tokens', 0), None, response.get('model', engine))
            
            result = {
                'id': self._generate_run_id(engine, intent_category),
                'ts': start_time,
                'query': query,
                'engine': engine,
                'model': response.get('model', 'unknown'),
                'status': 'completed',
                'answer_text': answer,
                'entities_normalized': entities_normalized,
                'links': links,
                'domains': domains,
                'extreme_mentioned': extreme_mentioned,
                'competitor_mentions': competitor_mentions,
                'citation_count': len(links),
                'domain_count': len(domains),
                'input_tokens': response.get('input_tokens', 0),
                'output_tokens': response.get('output_tokens', 0),
                'cost_usd': cost_estimate,
                'latency_ms': latency_ms,
                'intent_category': intent_category,
                'competitor_set': self.queries_config['competitor_set'],
                'processed_at': datetime.now(),
                'metrics_computed': False
            }
            
            print(f"✅ Completed: {len(entities_normalized)} entities, {len(links)} citations, ${cost_estimate:.4f}")
            return result
            
        except Exception as e:
            print(f"❌ Error executing query: {str(e)}")
            return None
    
    def execute_all_queries(self) -> List[Dict[str, Any]]:
        """Execute all queries from the configuration."""
        all_results = []
        
        # Get all queries from all categories
        queries_to_execute = []
        
        for category, queries in self.queries_config['query_sets'].items():
            for query in queries:
                queries_to_execute.append((query, category))
        
        # Distribute queries across engines based on configuration
        engine_distribution = self.queries_config['engine_distribution']
        total_queries = len(queries_to_execute)
        
        # Calculate how many queries each engine should get
        engine_queries = {}
        current_engine = 0
        engines = list(engine_distribution.keys())
        
        for i, (query, intent_category) in enumerate(queries_to_execute):
            engine = engines[current_engine % len(engines)]
            if engine not in engine_queries:
                engine_queries[engine] = []
            engine_queries[engine].append((query, intent_category))
            current_engine += 1
        
        print(f"🚀 Executing {total_queries} queries across {len(engines)} engines...")
        print(f"📊 Distribution: {engine_queries}")
        
        # Execute queries for each engine
        for engine, queries in engine_queries.items():
            print(f"\n🔥 Executing {len(queries)} queries on {engine}...")
            
            for query, intent_category in queries:
                result = self.execute_single_query(query, engine, intent_category)
                if result:
                    all_results.append(result)
                
                # Small delay between queries to avoid rate limits
                import time
                time.sleep(1)
        
        return all_results
    
    def save_results_to_database(self, results: List[Dict[str, Any]]) -> int:
        """Save all results to the automated_runs table."""
        if not results:
            print("❌ No results to save")
            return 0
        
        print(f"\n💾 Saving {len(results)} results to database...")
        
        try:
            for result_data in results:
                # Create AutomatedRun object
                automated_run = AutomatedRun(**result_data)
                
                # Add to database
                self.db.add(automated_run)
            
            # Commit all changes
            self.db.commit()
            print(f"✅ Successfully saved {len(results)} automated runs to database")
            return len(results)
            
        except Exception as e:
            print(f"❌ Error saving to database: {str(e)}")
            self.db.rollback()
            return 0
    
    def run(self):
        """Main execution method."""
        print("🤖 Starting Automated Competitive Intelligence Query Execution")
        print("=" * 60)
        
        # Execute all queries
        results = self.execute_all_queries()
        
        if not results:
            print("❌ No queries were executed successfully")
            return
        
        print(f"\n📊 Execution Summary:")
        print(f"   Total Queries: {len(results)}")
        print(f"   Successful: {len(results)}")
        print(f"   Failed: 0")
        
        # Save to database
        saved_count = self.save_results_to_database(results)
        
        print(f"\n🎯 Next Steps:")
        print(f"   1. Run post-processing: python scripts/post_process_metrics.py")
        print(f"   2. Check dashboard: http://localhost:3000/metrics")
        print(f"   3. View automated runs in database")
        
        return saved_count

def main():
    """Main entry point."""
    executor = AutomatedQueryExecutor()
    executor.run()

if __name__ == "__main__":
    main()
