#!/usr/bin/env python3
"""
Migration script to copy runs from local database to production database.

This script:
1. Connects to local database
2. Extracts runs (optionally filtered by date range or source)
3. Connects to production database
4. Inserts runs with conflict handling (skips duplicates)

Usage:
    python scripts/migrate_runs_to_prod.py [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD] [--source automated|manual] [--dry-run]
"""

import os
import sys
import argparse
import time
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, OperationalError

# Add backend to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.models.run import Run
from app.models.automated_run import AutomatedRun
from dotenv import load_dotenv

load_dotenv()


def get_local_db_session():
    """Get database session for local database."""
    # Default local database URL
    local_db_url = os.getenv(
        "LOCAL_DATABASE_URL",
        "postgresql+psycopg://eguser:egpass@localhost:5432/egtools"
    )
    engine = create_engine(local_db_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def get_prod_db_session():
    """Get database session for production database."""
    # Production database URL from environment, with fallback to default
    prod_db_url = os.getenv(
        "PROD_DATABASE_URL",
        "postgresql+psycopg://eguser:OLempgRdvHsu7Cxv6VraAWzu4X8LRhdJ@dpg-d2oc40er433s738lj4v0-a.oregon-postgres.render.com:5432/egtools?sslmode=require"
    )
    
    # Convert postgresql:// to postgresql+psycopg:// if needed
    if prod_db_url.startswith("postgresql://") and "psycopg" not in prod_db_url:
        prod_db_url = prod_db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    
    # Add SSL parameters and connection pool settings for better reliability
    engine = create_engine(
        prod_db_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600,  # Recycle connections after 1 hour
        connect_args={
            "sslmode": "require",  # Require SSL
            "connect_timeout": 10,  # 10 second connection timeout
        }
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def extract_runs_from_local(
    local_db,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    source: Optional[str] = None
) -> List[Run]:
    """
    Extract runs from local database with optional filters.
    Checks both 'runs' and 'automated_runs' tables.
    
    Args:
        local_db: Local database session
        start_date: Optional start date filter
        end_date: Optional end date filter
        source: Optional source filter (e.g., 'automated', 'manual')
    
    Returns:
        List of Run objects
    """
    all_runs = []
    
    # First, check the 'runs' table
    query = local_db.query(Run)
    
    # Apply filters
    if start_date:
        query = query.filter(Run.ts >= datetime.combine(start_date, datetime.min.time()))
    
    if end_date:
        query = query.filter(Run.ts <= datetime.combine(end_date, datetime.max.time()))
    
    if source:
        query = query.filter(Run.source == source)
    
    runs = query.order_by(Run.ts).all()
    all_runs.extend(runs)
    
    # Also check 'automated_runs' table if source is 'automated' or not specified
    if source is None or source == 'automated':
        auto_query = local_db.query(AutomatedRun)
        
        if start_date:
            auto_query = auto_query.filter(AutomatedRun.ts >= datetime.combine(start_date, datetime.min.time()))
        
        if end_date:
            auto_query = auto_query.filter(AutomatedRun.ts <= datetime.combine(end_date, datetime.max.time()))
        
        automated_runs = auto_query.order_by(AutomatedRun.ts).all()
        
        # Convert AutomatedRun to Run format
        for auto_run in automated_runs:
            # Determine is_branded using heuristic
            q_lower = (auto_run.query or "").lower()
            intent = (auto_run.intent_category or "").lower()
            branded_terms = ["extreme", "cisco", "juniper", "aruba", "vs", "versus", "compare", "comparison"]
            is_branded = intent in ("brand_focused", "comparison") or any(t in q_lower for t in branded_terms)
            
            # Convert AutomatedRun to Run object
            run = Run(
                id=auto_run.id,
                ts=auto_run.ts,
                engine=auto_run.engine,
                model=auto_run.model,
                prompt_version=None,
                intent=auto_run.intent_category,
                query=auto_run.query,
                status=auto_run.status or "completed",
                latency_ms=auto_run.latency_ms or 0,
                input_tokens=auto_run.input_tokens or 0,
                output_tokens=auto_run.output_tokens or 0,
                cost_usd=float(auto_run.cost_usd or 0.0),
                raw_excerpt=auto_run.answer_text[:1000] if auto_run.answer_text else None,
                vendors=[],
                links=auto_run.links or [],
                domains=auto_run.domains or [],
                citations_enriched=[],
                entities_normalized=auto_run.entities_normalized or [],
                extreme_mentioned=auto_run.extreme_mentioned or False,
                extreme_rank=None,  # Not available in AutomatedRun
                is_branded=is_branded,
                deleted=False,
                source="automated"
            )
            all_runs.append(run)
    
    return all_runs


def migrate_runs(
    runs: List[Run],
    prod_db_session_factory,
    dry_run: bool = False
) -> dict:
    """
    Migrate runs to production database.
    
    Args:
        runs: List of Run objects to migrate
        prod_db: Production database session
        dry_run: If True, don't actually insert, just report what would be done
    
    Returns:
        Dictionary with migration statistics
    """
    stats = {
        "total": len(runs),
        "inserted": 0,
        "skipped": 0,
        "errors": 0,
        "error_details": []
    }
    
    if dry_run:
        print(f"\n🔍 DRY RUN MODE - Would migrate {len(runs)} runs")
        return stats
    
    print(f"\n💾 Migrating {len(runs)} runs to production database...")
    print("📦 Using batch processing with connection refresh every 10 runs...")
    
    batch_size = 10
    max_retries = 3
    
    for batch_start in range(0, len(runs), batch_size):
        batch_end = min(batch_start + batch_size, len(runs))
        batch_runs = runs[batch_start:batch_end]
        
        # Create a fresh session for each batch
        prod_db = prod_db_session_factory()
        
        try:
            for i, run in enumerate(batch_runs, 1):
                global_index = batch_start + i
                retry_delay = 2  # seconds
                
                for attempt in range(max_retries):
                    try:
                        # Refresh session if we're retrying
                        if attempt > 0:
                            prod_db.close()
                            prod_db = prod_db_session_factory()
                        
                        # Check if run already exists
                        existing = prod_db.query(Run).filter(Run.id == run.id).first()
                        if existing:
                            print(f"⏭️  [{global_index}/{len(runs)}] Skipping existing run: {run.id}")
                            stats["skipped"] += 1
                            break
                        
                        # Create new run object for production database
                        prod_run = Run(
                            id=run.id,
                            ts=run.ts,
                            engine=run.engine,
                            model=run.model,
                            prompt_version=run.prompt_version,
                            intent=run.intent,
                            query=run.query,
                            status=run.status,
                            latency_ms=run.latency_ms,
                            input_tokens=run.input_tokens,
                            output_tokens=run.output_tokens,
                            cost_usd=run.cost_usd,
                            raw_excerpt=run.raw_excerpt,
                            vendors=run.vendors,
                            links=run.links,
                            domains=run.domains,
                            citations_enriched=run.citations_enriched,
                            entities_normalized=run.entities_normalized,
                            extreme_mentioned=run.extreme_mentioned,
                            extreme_rank=run.extreme_rank,
                            is_branded=run.is_branded,
                            deleted=run.deleted,
                            source=run.source
                        )
                        
                        prod_db.add(prod_run)
                        prod_db.commit()
                        
                        print(f"✅ [{global_index}/{len(runs)}] Migrated run: {run.id} ({run.query[:50]}...)")
                        stats["inserted"] += 1
                        break  # Success, exit retry loop
                        
                    except IntegrityError as e:
                        prod_db.rollback()
                        print(f"⚠️  [{global_index}/{len(runs)}] Integrity error for run {run.id}: {str(e)}")
                        stats["skipped"] += 1
                        stats["errors"] += 1
                        stats["error_details"].append(f"Run {run.id}: {str(e)}")
                        break  # Don't retry integrity errors
                        
                    except (OperationalError, Exception) as e:
                        prod_db.rollback()
                        
                        # Check if it's a connection error that we should retry
                        error_str = str(e).lower()
                        is_connection_error = any(term in error_str for term in [
                            "ssl connection", "connection closed", "connection failed",
                            "server closed", "timeout", "network"
                        ])
                        
                        if is_connection_error and attempt < max_retries - 1:
                            print(f"🔄 [{global_index}/{len(runs)}] Connection error (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                            continue
                        else:
                            print(f"❌ [{global_index}/{len(runs)}] Error migrating run {run.id}: {str(e)}")
                            stats["errors"] += 1
                            stats["error_details"].append(f"Run {run.id}: {str(e)}")
                            break  # Give up after max retries
            
            # Small delay between batches to avoid overwhelming the connection
            if batch_end < len(runs):
                time.sleep(0.5)
                
        finally:
            prod_db.close()
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Migrate runs from local database to production database"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date filter (YYYY-MM-DD). Only migrate runs on or after this date."
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date filter (YYYY-MM-DD). Only migrate runs on or before this date."
    )
    parser.add_argument(
        "--source",
        type=str,
        choices=["automated", "manual"],
        help="Filter by source type (automated or manual)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode - don't actually insert, just report what would be done"
    )
    
    args = parser.parse_args()
    
    # Parse date filters
    start_date = None
    end_date = None
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
    
    print("=" * 60)
    print("🚀 Run Migration Script")
    print("=" * 60)
    print(f"Start Date: {start_date or 'None'}")
    print(f"End Date: {end_date or 'None'}")
    print(f"Source Filter: {args.source or 'None'}")
    print(f"Dry Run: {args.dry_run}")
    print("=" * 60)
    
    # Get database sessions
    try:
        print("\n📡 Connecting to local database...")
        local_db = get_local_db_session()
        print("✅ Connected to local database")
        
        print("\n📡 Connecting to production database...")
        prod_db_session_factory = get_prod_db_session
        # Test the connection
        test_session = prod_db_session_factory()
        test_session.close()
        print("✅ Connected to production database")
        
        # Extract runs from local database
        print("\n📥 Extracting runs from local database...")
        runs = extract_runs_from_local(
            local_db,
            start_date=start_date,
            end_date=end_date,
            source=args.source
        )
        print(f"✅ Found {len(runs)} runs to migrate")
        
        if len(runs) == 0:
            print("\n⚠️  No runs found matching the criteria. Exiting.")
            return
        
        # Show sample of runs
        print("\n📋 Sample of runs to migrate:")
        for i, run in enumerate(runs[:5], 1):
            print(f"  {i}. {run.id} - {run.query[:60]}... ({run.ts})")
        if len(runs) > 5:
            print(f"  ... and {len(runs) - 5} more")
        
        # Migrate runs (pass prod_db session factory)
        stats = migrate_runs(runs, prod_db_session_factory, dry_run=args.dry_run)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 Migration Summary")
        print("=" * 60)
        print(f"Total runs found: {stats['total']}")
        print(f"Successfully inserted: {stats['inserted']}")
        print(f"Skipped (duplicates): {stats['skipped']}")
        print(f"Errors: {stats['errors']}")
        
        if stats['error_details']:
            print("\n⚠️  Error Details:")
            for detail in stats['error_details'][:10]:  # Show first 10 errors
                print(f"  - {detail}")
            if len(stats['error_details']) > 10:
                print(f"  ... and {len(stats['error_details']) - 10} more errors")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        if 'local_db' in locals():
            local_db.close()
        if 'prod_db' in locals():
            prod_db.close()


if __name__ == "__main__":
    main()

