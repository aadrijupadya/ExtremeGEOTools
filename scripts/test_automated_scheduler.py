#!/usr/bin/env python3
"""
Quick test script for the automated scheduler.
This bypasses all time checks and runs immediately for testing purposes.
"""

import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.query_scheduler import QueryScheduler
from datetime import date


def test_scheduler_immediately():
    """Test the scheduler by running it immediately."""
    print("🧪 Testing Automated Scheduler (Immediate Mode)")
    print("=" * 50)
    
    try:
        # Create scheduler
        scheduler = QueryScheduler()
        
        # Get today's queries
        today = date.today()
        queries = scheduler.get_daily_queries(today)
        
        print(f"📅 Date: {today}")
        print(f"📝 Total queries: {len(queries)}")
        
        # Show distribution
        engine_counts = {}
        intent_counts = {}
        
        for query in queries:
            engine = query['engine']
            intent = query['intent']
            
            engine_counts[engine] = engine_counts.get(engine, 0) + 1
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        print(f"🔧 Engine distribution: {engine_counts}")
        print(f"🎯 Intent distribution: {intent_counts}")
        
        # Test with just 2 queries first
        print(f"\n🚀 Testing execution with 2 queries...")
        test_queries = queries[:2]
        
        for i, query_info in enumerate(test_queries):
            print(f"  {i+1}. {query_info['engine']}: {query_info['query'][:50]}...")
        
        # Execute test queries
        results = scheduler.execute_daily_queries(today, dry_run=False)
        
        print(f"\n✅ Execution completed!")
        print(f"Results: {len(results)} queries processed")
        
        # Show results
        for i, result in enumerate(results):
            status_emoji = "✅" if result['status'] == 'completed' else "❌"
            run_id = result.get('run_id', 'N/A')
            print(f"  {i+1}. {status_emoji} {result['engine']}: {result['query'][:50]}... ({result['status']})")
            if run_id != 'N/A':
                print(f"     Run ID: {run_id}")
        
        print(f"\n💾 Results have been saved to the database!")
        print(f"   - Check the 'runs' table in your PostgreSQL database")
        print(f"   - Use the API endpoint: GET /runs to view all runs")
        print(f"   - Use the API endpoint: GET /runs/{run_id} to view specific runs")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_scheduler_immediately()
    exit(0 if success else 1)
