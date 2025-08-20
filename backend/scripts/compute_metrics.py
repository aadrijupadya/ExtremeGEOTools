#!/usr/bin/env python3
"""
Script to compute daily metrics for historical data.
Run this to populate the daily_metrics table with historical data.
"""

import sys
import os
from datetime import date, datetime, timedelta
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.database import SessionLocal
from app.services.metrics import MetricsService
from app.models.run import Run
from sqlalchemy import select, func


def get_date_range_with_data(db_session) -> tuple[date, date]:
    """Get the date range that has run data."""
    result = db_session.execute(
        select(func.min(Run.ts), func.max(Run.ts))
    ).one()
    
    min_date, max_date = result
    
    if not min_date or not max_date:
        print("No run data found in database")
        sys.exit(1)
    
    return min_date.date(), max_date.date()


def compute_metrics_for_date_range(start_date: date, end_date: date, engine: str = None):
    """Compute metrics for a range of dates."""
    db = SessionLocal()
    try:
        metrics_service = MetricsService(db)
        
        current_date = start_date
        total_metrics = 0
        
        while current_date <= end_date:
            print(f"Computing metrics for {current_date}...")
            
            try:
                metrics = metrics_service.compute_daily_metrics(current_date, engine)
                
                if metrics:
                    metrics_service.upsert_daily_metrics(metrics)
                    print(f"  ✓ Computed {len(metrics)} metrics")
                    total_metrics += len(metrics)
                else:
                    print(f"  - No runs found for {current_date}")
                
            except Exception as e:
                print(f"  ✗ Error computing metrics for {current_date}: {e}")
            
            current_date += timedelta(days=1)
        
        print(f"\nCompleted! Total metrics computed: {total_metrics}")
        
    finally:
        db.close()


def main():
    """Main function to compute metrics."""
    print("Daily Metrics Computation Script")
    print("=" * 40)
    
    # Get database session
    db = SessionLocal()
    try:
        # Get date range with data
        start_date, end_date = get_date_range_with_data(db)
        print(f"Found run data from {start_date} to {end_date}")
        
        # Ask user for date range
        print("\nEnter date range to compute metrics for:")
        print(f"Available range: {start_date} to {end_date}")
        
        try:
            start_input = input(f"Start date (YYYY-MM-DD) [default: {start_date}]: ").strip()
            start_date = datetime.strptime(start_input, "%Y-%m-%d").date() if start_input else start_date
            
            end_input = input(f"End date (YYYY-MM-DD) [default: {end_date}]: ").strip()
            end_date = datetime.strptime(end_input, "%Y-%m-%d").date() if end_input else end_date
            
        except ValueError:
            print("Invalid date format. Using full available range.")
        
        # Ask for engine filter
        engine_input = input("Engine filter (leave empty for all engines): ").strip()
        engine = engine_input if engine_input else None
        
        if engine:
            print(f"Filtering by engine: {engine}")
        
        # Confirm before proceeding
        print(f"\nAbout to compute metrics for {start_date} to {end_date}")
        if engine:
            print(f"Engine filter: {engine}")
        
        confirm = input("Proceed? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            return
        
        # Compute metrics
        print("\nStarting metrics computation...")
        compute_metrics_for_date_range(start_date, end_date, engine)
        
    finally:
        db.close()


if __name__ == "__main__":
    main()


