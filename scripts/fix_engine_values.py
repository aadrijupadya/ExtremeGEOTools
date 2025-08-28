#!/usr/bin/env python3
"""
Script to fix existing database records where engine is set to 'gpt-4o-mini-search-preview' 
instead of 'openai'. This script updates both the 'runs' and 'automated_runs' tables.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine, text
from app.services.database import get_db, DATABASE_URL

def fix_engine_values():
    """Fix engine values in the database."""
    print("🔧 Fixing engine values in database...")
    
    # Create a direct database connection for this script
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Fix runs table
            print("📊 Fixing 'runs' table...")
            result = conn.execute(text("""
                UPDATE runs 
                SET engine = 'openai' 
                WHERE engine = 'gpt-4o-mini-search-preview'
            """))
            runs_updated = result.rowcount
            print(f"   Updated {runs_updated} records in 'runs' table")
            
            # Fix automated_runs table
            print("🤖 Fixing 'automated_runs' table...")
            result = conn.execute(text("""
                UPDATE automated_runs 
                SET engine = 'openai' 
                WHERE engine = 'gpt-4o-mini-search-preview'
            """))
            automated_runs_updated = result.rowcount
            print(f"   Updated {automated_runs_updated} records in 'automated_runs' table")
            
            # Commit the changes
            conn.commit()
            
            total_updated = runs_updated + automated_runs_updated
            print(f"\n✅ Successfully updated {total_updated} records")
            print(f"   - Runs table: {runs_updated} records")
            print(f"   - Automated runs table: {automated_runs_updated} records")
            
            if total_updated > 0:
                print("\n🔍 Verifying the fix...")
                
                # Check runs table
                result = conn.execute(text("SELECT COUNT(*) FROM runs WHERE engine = 'gpt-4o-mini-search-preview'"))
                remaining_runs = result.scalar()
                
                # Check automated_runs table
                result = conn.execute(text("SELECT COUNT(*) FROM automated_runs WHERE engine = 'gpt-4o-mini-search-preview'"))
                remaining_automated = result.scalar()
                
                if remaining_runs == 0 and remaining_automated == 0:
                    print("✅ All engine values have been successfully fixed!")
                else:
                    print(f"⚠️  Warning: {remaining_runs + remaining_automated} records still have incorrect engine values")
            else:
                print("ℹ️  No records needed fixing - engine values were already correct")
                
    except Exception as e:
        print(f"❌ Error fixing engine values: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting engine value fix script...")
    success = fix_engine_values()
    
    if success:
        print("\n🎉 Script completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Script failed!")
        sys.exit(1)
