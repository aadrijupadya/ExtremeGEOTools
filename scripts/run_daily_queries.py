#!/usr/bin/env python3
"""
CLI script to run daily queries manually.
Usage: python run_daily_queries.py [--date YYYY-MM-DD] [--dry-run] [--limit N]
"""

import sys
import argparse
from pathlib import Path
from datetime import date, datetime

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.query_scheduler import QueryScheduler, run_daily_queries


def parse_date(date_str: str) -> date:
    """Parse a date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Run daily competitive intelligence queries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run today's queries (dry run)
  python run_daily_queries.py --dry-run
  
  # Run queries for a specific date
  python run_daily_queries.py --date 2024-01-15
  
  # Run only first 5 queries for today
  python run_daily_queries.py --limit 5
  
  # Run real queries for yesterday
  python run_daily_queries.py --date 2024-01-14
        """
    )
    
    parser.add_argument(
        "--date", 
        type=parse_date,
        help="Target date (YYYY-MM-DD). Defaults to today."
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without executing real queries"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit the number of queries to execute"
    )
    
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Show the current scheduler configuration and exit"
    )
    
    args = parser.parse_args()
    
    # Show configuration if requested
    if args.show_config:
        scheduler = QueryScheduler()
        config = scheduler.get_schedule_info()
        
        print("📋 Query Scheduler Configuration")
        print("=" * 40)
        print(f"Schedule: {config.get('cadence')} at {config.get('morning_time')} and {config.get('evening_time')}")
        print(f"Total queries per day: {config.get('total_queries_per_day')}")
        print(f"Engine distribution: {config.get('engine_distribution')}")
        print(f"Competitor set: {', '.join(config.get('competitor_set', []))}")
        print(f"Query types: {config.get('query_types')}")
        return 0
    
    # Determine target date
    target_date = args.date or date.today()
    dry_run = args.dry_run
    
    print(f"🚀 Running daily queries for {target_date}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE EXECUTION'}")
    print("=" * 50)
    
    try:
        # Get the scheduler
        scheduler = QueryScheduler()
        
        # Get daily queries
        queries = scheduler.get_daily_queries(target_date)
        
        if not queries:
            print("❌ No queries found for the specified date")
            return 1
        
        print(f"📝 Found {len(queries)} queries to execute")
        
        # Apply limit if specified
        if args.limit:
            queries = queries[:args.limit]
            print(f"🔢 Limited to {len(queries)} queries")
        
        # Show query summary
        engine_counts = {}
        intent_counts = {}
        
        for query in queries:
            engine = query['engine']
            intent = query['intent']
            
            engine_counts[engine] = engine_counts.get(engine, 0) + 1
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        print(f"\n📊 Query Distribution:")
        print(f"  Engines: {engine_counts}")
        print(f"  Intents: {intent_counts}")
        
        # Confirm execution (unless dry run)
        if not dry_run:
            response = input(f"\n⚠️  Execute {len(queries)} LIVE queries? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("❌ Execution cancelled")
                return 0
        
        # Execute queries
        print(f"\n🔄 Executing queries...")
        results = scheduler.execute_daily_queries(target_date, dry_run=dry_run)
        
        # Show results summary
        print(f"\n✅ Execution completed!")
        print(f"Total queries: {len(results)}")
        
        status_counts = {}
        for result in results:
            status = result['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"Status distribution: {status_counts}")
        
        # Show sample results
        if results:
            print(f"\n📋 Sample results:")
            for i, result in enumerate(results[:3]):
                status_emoji = "✅" if result['status'] == 'completed' else "❌"
                print(f"  {i+1}. {status_emoji} {result['engine']}: {result['query'][:50]}... ({result['status']})")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n❌ Execution interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
