#!/usr/bin/env python3
"""
Test script for the query scheduler.
This script tests the query distribution and can run a few sample queries.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.query_scheduler import QueryScheduler, run_daily_queries
from datetime import date


def test_scheduler_config():
    """Test the scheduler configuration loading."""
    print("=== Testing Scheduler Configuration ===")
    
    scheduler = QueryScheduler()
    config = scheduler.get_schedule_info()
    
    print(f"Schedule Info:")
    print(f"  Cadence: {config.get('cadence')}")
    print(f"  Runs per day: {config.get('runs_per_day')}")
    print(f"  Morning time: {config.get('morning_time')}")
    print(f"  Evening time: {config.get('evening_time')}")
    print(f"  Total queries per day: {config.get('total_queries_per_day')}")
    print(f"  Engine distribution: {config.get('engine_distribution')}")
    print(f"  Competitor set: {config.get('competitor_set')}")
    print(f"  Query types: {config.get('query_types')}")
    
    return config


def test_daily_query_generation():
    """Test the daily query generation."""
    print("\n=== Testing Daily Query Generation ===")
    
    scheduler = QueryScheduler()
    today = date.today()
    
    queries = scheduler.get_daily_queries(today)
    print(f"Generated {len(queries)} queries for {today}")
    
    # Count by engine
    engine_counts = {}
    intent_counts = {}
    
    for query in queries:
        engine = query['engine']
        intent = query['intent']
        
        engine_counts[engine] = engine_counts.get(engine, 0) + 1
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
    
    print(f"Engine distribution: {engine_counts}")
    print(f"Intent distribution: {intent_counts}")
    
    # Show a few sample queries
    print("\nSample queries:")
    for i, query in enumerate(queries[:5]):
        print(f"  {i+1}. {query['engine']}: {query['query'][:60]}... ({query['intent']})")
    
    return queries


def test_dry_run():
    """Test a dry run of the query execution."""
    print("\n=== Testing Dry Run ===")
    
    today = date.today()
    results = run_daily_queries(today, dry_run=True)
    
    print(f"Dry run completed for {len(results)} queries")
    
    # Show results summary
    status_counts = {}
    for result in results:
        status = result['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"Status distribution: {status_counts}")
    
    return results


def test_single_query():
    """Test executing a single real query (optional)."""
    print("\n=== Testing Single Query Execution ===")
    
    # Check if we have API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")
    
    if not openai_key:
        print("❌ OPENAI_API_KEY not set - skipping real query test")
        return None
    
    if not perplexity_key:
        print("❌ PERPLEXITY_API_KEY not set - skipping real query test")
        return None
    
    print("✅ API keys found - testing single query execution")
    
    try:
        from app.services.engines import call_engine
        
        # Test a simple query
        test_query = "top enterprise Wi-Fi 7 solutions"
        print(f"Testing query: {test_query}")
        
        result = call_engine(
            engine="gpt-4o-mini-search-preview",
            prompt=test_query,
            temperature=0.2
        )
        
        print(f"✅ Query executed successfully!")
        print(f"  Model: {result.get('model')}")
        print(f"  Tokens: {result.get('input_tokens', 0)} in, {result.get('output_tokens', 0)} out")
        
        cost = result.get('cost_usd')
        if cost is not None:
            print(f"  Cost: ${cost:.6f}")
        else:
            print(f"  Cost: Not available")
            
        print(f"  Latency: {result.get('latency_ms', 0)}ms")
        print(f"  Text length: {len(result.get('text', ''))}")
        
        # Show first 200 characters of response
        text = result.get('text', '')
        if text:
            print(f"  Response preview: {text[:200]}...")
        
        return result
        
    except Exception as e:
        print(f"❌ Error executing query: {e}")
        return None


def main():
    """Main test function."""
    print("🚀 Testing Query Scheduler")
    print("=" * 50)
    
    try:
        # Test 1: Configuration
        config = test_scheduler_config()
        
        # Test 2: Query generation
        queries = test_daily_query_generation()
        
        # Test 3: Dry run
        dry_run_results = test_dry_run()
        
        # Test 4: Single real query (if API keys available)
        real_result = test_single_query()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        
        if real_result:
            print("🎉 Real query execution successful!")
        else:
            print("⚠️  Real query execution skipped (check API keys)")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
