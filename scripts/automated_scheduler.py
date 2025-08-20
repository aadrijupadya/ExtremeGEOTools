#!/usr/bin/env python3
"""
Automated Query Scheduler
This script is designed to be run by cron to automatically execute daily queries.
It handles logging, error reporting, and ensures only one instance runs at a time.
"""

import sys
import os
import logging
import json
import time
from pathlib import Path
from datetime import date, datetime
from typing import Optional

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.query_scheduler import QueryScheduler
from app.services.database import get_db
from app.models.run import Run


class AutomatedScheduler:
    """Automated scheduler that can be run by cron or systemd."""
    
    def __init__(self):
        self.setup_logging()
        self.scheduler = QueryScheduler()
        self.lock_file = Path("/tmp/extreme_geo_scheduler.lock")
        
    def setup_logging(self):
        """Setup logging to both file and console."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"scheduler_{date.today().isoformat()}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def acquire_lock(self) -> bool:
        """Acquire a lock to prevent multiple instances from running."""
        try:
            if self.lock_file.exists():
                # Check if the lock is stale (older than 1 hour)
                lock_age = time.time() - self.lock_file.stat().st_mtime
                if lock_age > 3600:  # 1 hour
                    self.logger.warning(f"Removing stale lock file (age: {lock_age:.0f}s)")
                    self.lock_file.unlink()
                else:
                    self.logger.error("Another scheduler instance is already running")
                    return False
            
            # Create lock file with current PID
            with open(self.lock_file, 'w') as f:
                f.write(str(os.getpid()))
            
            self.logger.info(f"Lock acquired (PID: {os.getpid()})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to acquire lock: {e}")
            return False
    
    def release_lock(self):
        """Release the lock file."""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
                self.logger.info("Lock released")
        except Exception as e:
            self.logger.error(f"Failed to release lock: {e}")
    
    def should_run_queries(self, force_run: bool = False) -> bool:
        """Determine if we should run queries based on current time and schedule."""
        # If force_run is True, bypass time checks (for testing)
        if force_run:
            self.logger.info("Force run mode enabled - bypassing time checks")
            return True
            
        now = datetime.now()
        current_time = now.time()
        
        # Get schedule from config
        config = self.scheduler.get_schedule_info()
        morning_time = config.get("morning_time", "09:00")
        cadence = config.get("cadence", "every_3_days")
        
        try:
            morning = datetime.strptime(morning_time, "%H:%M").time()
            
            # Check if current time is within 15 minutes of scheduled time
            morning_start = (datetime.combine(date.today(), morning) - 
                           datetime.timedelta(minutes=15)).time()
            morning_end = (datetime.combine(date.today(), morning) + 
                          datetime.timedelta(minutes=15)).time()
            
            # Check if we're within the time window
            if not (morning_start <= current_time <= morning_end):
                self.logger.info(f"Outside execution window. Current: {current_time}, Window: {morning_time}")
                return False
            
            # For 3-day cadence, check if it's been 3 days since last execution
            if cadence == "every_3_days":
                last_execution = self.get_last_execution_date()
                if last_execution:
                    days_since_last = (date.today() - last_execution).days
                    if days_since_last < 3:
                        self.logger.info(f"Only {days_since_last} days since last execution. Waiting for 3 days.")
                        return False
                    else:
                        self.logger.info(f"3 days have passed since last execution. Proceeding.")
                        return True
                else:
                    self.logger.info("No previous execution found. Proceeding with first run.")
                    return True
            
            # Default to daily if cadence not specified
            self.logger.info(f"Within execution window for {morning_time}")
            return True
                
        except Exception as e:
            self.logger.error(f"Error parsing schedule times: {e}")
            # Default to running if we can't parse the schedule
            return True
    
    def get_last_execution_date(self) -> Optional[date]:
        """Get the date of the last successful execution."""
        try:
            db = next(get_db())
            
            # Try to filter by source first
            try:
                last_run = db.query(Run).filter(
                    Run.source == "automated",
                    Run.deleted == False
                ).order_by(Run.ts.desc()).first()
            except Exception:
                # Fallback: get last run without source filtering
                self.logger.warning("Source column not available, checking all recent runs")
                last_run = db.query(Run).filter(
                    Run.deleted == False
                ).order_by(Run.ts.desc()).first()
            
            if last_run:
                return last_run.ts.date()
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting last execution date: {e}")
            return None
    
    def check_recent_execution(self) -> bool:
        """Check if queries were already executed recently (within last 2 hours)."""
        try:
            db = next(get_db())
            two_hours_ago = datetime.utcnow() - datetime.timedelta(hours=2)
            
            recent_runs = db.query(Run).filter(
                Run.ts >= two_hours_ago,
                Run.deleted.is_(False)
            ).count()
            
            if recent_runs > 0:
                self.logger.info(f"Found {recent_runs} recent runs in the last 2 hours")
                return True
            else:
                self.logger.info("No recent runs found, proceeding with execution")
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking recent execution: {e}")
            # If we can't check, assume we should run
            return False
    
    def execute_daily_queries(self) -> bool:
        """Execute the daily queries."""
        try:
            today = date.today()
            self.logger.info(f"Starting daily query execution for {today}")
            
            # Get today's queries
            queries = self.scheduler.get_daily_queries(today)
            if not queries:
                self.logger.error("No queries found for today")
                return False
            
            self.logger.info(f"Executing {len(queries)} queries")
            
            # Execute queries (not dry run)
            start_time = time.time()
            results = self.scheduler.execute_daily_queries(today, dry_run=False)
            execution_time = time.time() - start_time
            
            # Log results
            status_counts = {}
            for result in results:
                status = result['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            self.logger.info(f"Execution completed in {execution_time:.2f}s")
            self.logger.info(f"Status distribution: {status_counts}")
            
            # Check for errors
            error_count = status_counts.get('error', 0)
            if error_count > 0:
                self.logger.warning(f"Completed with {error_count} errors")
                return False
            
            # Trigger post-processing pipeline
            self.logger.info("Triggering post-processing pipeline...")
            self.trigger_post_processing()
            
            self.logger.info("Daily query execution completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during query execution: {e}")
            return False
    
    def trigger_post_processing(self):
        """Trigger the post-processing pipeline."""
        try:
            import subprocess
            import os
            
            # Get the path to the post-processing script
            script_dir = Path(__file__).parent
            post_process_script = script_dir / "post_process_metrics.py"
            
            if not post_process_script.exists():
                self.logger.error(f"Post-processing script not found: {post_process_script}")
                return
            
            # Run post-processing in background
            self.logger.info("Starting post-processing pipeline...")
            
            # Use subprocess to run the post-processing script
            result = subprocess.run([
                sys.executable, str(post_process_script)
            ], capture_output=True, text=True, cwd=script_dir.parent)
            
            if result.returncode == 0:
                self.logger.info("Post-processing pipeline completed successfully")
                if result.stdout:
                    self.logger.info(f"Output: {result.stdout}")
            else:
                self.logger.error(f"Post-processing pipeline failed: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"Error triggering post-processing: {e}")
    
    def run(self, force_run: bool = False) -> int:
        """Main execution method."""
        if not self.acquire_lock():
            return 1
        
        try:
            self.logger.info("Automated scheduler started")
            
            # Check if we should run queries
            if not self.should_run_queries(force_run=force_run):
                self.logger.info("Outside execution windows, exiting")
                return 0
            
            # Check if queries were already run recently
            if self.check_recent_execution():
                self.logger.info("Queries already executed recently, skipping")
                return 0
            
            # Execute queries
            success = self.execute_daily_queries()
            return 0 if success else 1
            
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return 1
        finally:
            self.release_lock()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated Query Scheduler")
    parser.add_argument("--test", action="store_true", help="Force run mode for testing (bypasses time checks)")
    parser.add_argument("--limit", type=int, help="Limit number of queries to execute")
    
    args = parser.parse_args()
    
    scheduler = AutomatedScheduler()
    
    # If test mode, also limit queries if specified
    if args.test and args.limit:
        # Override the scheduler to limit queries for testing
        original_get_daily_queries = scheduler.scheduler.get_daily_queries
        def limited_get_daily_queries(target_date):
            queries = original_get_daily_queries(target_date)
            return queries[:args.limit]
        scheduler.scheduler.get_daily_queries = limited_get_daily_queries
    
    exit_code = scheduler.run(force_run=args.test)
    
    if exit_code == 0:
        print("✅ Automated scheduler completed successfully")
    else:
        print("❌ Automated scheduler failed")
    
    return exit_code


if __name__ == "__main__":
    exit(main())
