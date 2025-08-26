#!/usr/bin/env python3
"""
Extract Extreme Networks focused trend data from automated runs.
Focuses on neutral queries and Extreme-related metrics only.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.automated_run import AutomatedRun

def get_db_session():
    """Get database session."""
    # Update these with your actual database credentials
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/extreme_geo"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def extract_extreme_trends(days=30):
    """Extract Extreme-focused trend data from automated runs."""
    session = get_db_session()
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query only non-branded (neutral) queries with Extreme mentions
        query = session.query(AutomatedRun).filter(
            AutomatedRun.ts >= start_date,
            AutomatedRun.is_branded == False,  # Only neutral queries
            AutomatedRun.extreme_mentioned == True  # Must mention Extreme
        )
        
        runs = query.order_by(AutomatedRun.ts.asc()).all()
        
        print(f"Found {len(runs)} neutral queries mentioning Extreme Networks from {start_date.date()} to {end_date.date()}")
        
        if not runs:
            return {
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "trends": [],
                "message": "No neutral queries mentioning Extreme Networks found"
            }
        
        # Group runs by date for daily trends
        trends_by_date = {}
        
        for run in runs:
            date_key = run.ts.date().isoformat()
            
            if date_key not in trends_by_date:
                trends_by_date[date_key] = {
                    "date": date_key,
                    "extreme_mentions": 0,
                    "extreme_citations": 0,
                    "total_citations": 0,
                    "avg_rank": 0,
                    "runs_count": 0,
                    "total_cost": 0.0
                }
            
            trends_by_date[date_key]["runs_count"] += 1
            trends_by_date[date_key]["total_cost"] += float(run.cost_usd or 0)
            
            # Count Extreme mentions (if available)
            if hasattr(run, 'extreme_mentioned') and run.extreme_mentioned:
                trends_by_date[date_key]["extreme_mentions"] += 1
            
            # Count Extreme-related citations from links
            if run.links:
                try:
                    links = json.loads(run.links) if isinstance(run.links, str) else run.links
                    if isinstance(links, list):
                        for link in links:
                            if isinstance(link, dict) and 'url' in link:
                                url = link['url'].lower()
                                if 'extremenetworks.com' in url or 'een.extremenetworks.com' in url:
                                    trends_by_date[date_key]["extreme_citations"] += 1
                            elif isinstance(link, str):
                                url = link.lower()
                                if 'extremenetworks.com' in url or 'een.extremenetworks.com' in url:
                                    trends_by_date[date_key]["extreme_citations"] += 1
                except (json.JSONDecodeError, AttributeError):
                    pass
            
            # Count total citations
            if run.links:
                try:
                    links = json.loads(run.links) if isinstance(run.links, str) else run.links
                    if isinstance(links, list):
                        trends_by_date[date_key]["total_citations"] += len(links)
                except (json.JSONDecodeError, AttributeError):
                    pass
            
            # Calculate average rank (placeholder for now)
            # This would need to be implemented based on your ranking logic
            trends_by_date[date_key]["avg_rank"] = 1.0  # Placeholder
        
        # Convert to sorted list
        trends = list(trends_by_date.values())
        trends.sort(key=lambda x: x["date"])
        
        # Calculate summary statistics
        summary = {
            "total_runs": len(runs),
            "total_extreme_mentions": sum(t["extreme_mentions"] for t in trends),
            "total_extreme_citations": sum(t["extreme_citations"] for t in trends),
            "total_citations": sum(t["total_citations"] for t in trends),
            "total_cost": sum(t["total_cost"] for t in trends),
            "avg_cost_per_run": sum(t["total_cost"] for t in trends) / len(runs) if runs else 0
        }
        
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "focus": "extreme_networks_neutral_queries",
            "trends": trends,
            "summary": summary
        }
        
    except Exception as e:
        print(f"Error extracting Extreme trends: {str(e)}")
        return None
    finally:
        session.close()

def save_trends_to_file(trends_data, output_file="data/extreme_trends.json"):
    """Save trends data to JSON file."""
    try:
        # Ensure data directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Add timestamp
        trends_data["extracted_at"] = datetime.now().isoformat()
        
        with open(output_path, 'w') as f:
            json.dump(trends_data, f, indent=2)
        
        print(f"Extreme trends data saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error saving trends data: {str(e)}")
        return False

def main():
    """Main function to extract and save Extreme trends."""
    print("Extracting Extreme Networks focused trend data...")
    
    # Extract trends for last 30 days
    trends_data = extract_extreme_trends(days=30)
    
    if trends_data and trends_data["trends"]:
        print(f"Extracted {len(trends_data['trends'])} trend data points")
        print(f"Total runs: {trends_data['summary']['total_runs']}")
        print(f"Total Extreme citations: {trends_data['summary']['total_extreme_citations']}")
        print(f"Total cost: ${trends_data['summary']['total_cost']:.4f}")
        
        # Save to file
        if save_trends_to_file(trends_data):
            print("✅ Extreme trends extraction completed successfully!")
        else:
            print("❌ Failed to save trends data")
    else:
        print("❌ No trend data extracted")

if __name__ == "__main__":
    main()
