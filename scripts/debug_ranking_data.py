#!/usr/bin/env python3
"""
Helper Debug script to check the current state of entities and ranking data
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.database import get_db
from app.models.automated_run import AutomatedRun
from sqlalchemy.orm import Session

def debug_entities_and_ranking():
    """Debug the current state of entities and ranking data"""
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get a few runs with entities_normalized data
        runs = db.query(AutomatedRun).filter(
            AutomatedRun.entities_normalized.isnot(None),
            AutomatedRun.entities_normalized != []
        ).limit(3).all()
        
        print(f"Found {len(runs)} runs with entities")
        
        for i, run in enumerate(runs):
            print(f"\n=== Run {i+1} ===")
            print(f"ID: {run.id}")
            print(f"Query: {run.query[:100]}...")
            print(f"Entities: {type(run.entities_normalized)}")
            
            if isinstance(run.entities_normalized, list):
                print(f"Entity count: {len(run.entities_normalized)}")
                for j, entity in enumerate(run.entities_normalized[:3]):  # Show first 3
                    print(f"  Entity {j+1}: {type(entity)} - {entity}")
            else:
                print(f"Raw entities data: {run.entities_normalized}")
        
        # Now test the post-processing logic
        print("\n=== Testing Post-Processing Logic ===")
        
        all_entities = []
        entity_counts = {}
        entity_ranking_analysis = {}
        
        for run in runs:
            entities = run.entities_normalized
            if isinstance(entities, list):
                all_entities.extend(entities)
                
                # Count entities
                for entity in entities:
                    if isinstance(entity, dict):
                        name = entity.get("name", "Unknown")
                    else:
                        name = str(entity)
                    
                    if name not in entity_counts:
                        entity_counts[name] = 0
                        entity_ranking_analysis[name] = []
                    
                    entity_counts[name] += 1
                
                # Calculate rankings based on order
                for i, entity in enumerate(entities):
                    if isinstance(entity, dict):
                        name = entity.get("name", "Unknown")
                    else:
                        name = str(entity)
                    
                    if name in entity_ranking_analysis:
                        entity_ranking_analysis[name].append(i + 1)
        
        print(f"Total entities processed: {len(all_entities)}")
        print(f"Entity counts: {entity_counts}")
        print(f"Ranking analysis: {entity_ranking_analysis}")
        
        # Calculate average ranks
        for name, count in entity_counts.items():
            ranking_data = entity_ranking_analysis.get(name, [])
            avg_rank = sum(ranking_data) / len(ranking_data) if ranking_data else 0
            print(f"{name}: {count} mentions, rankings: {ranking_data}, avg: {avg_rank:.2f}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_entities_and_ranking()
