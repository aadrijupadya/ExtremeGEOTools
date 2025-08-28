"""
Entity Associations API Routes

Provides endpoints for retrieving entity associations (products and keywords)
that AI engines associate with Extreme Networks.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException
from datetime import datetime

router = APIRouter(prefix="/entity-associations", tags=["entity-associations"])


def load_entity_associations() -> Dict[str, Any]:
    """Load entity associations from JSON file."""
    file_path = Path(__file__).parent.parent.parent.parent / "data" / "entity_associations.json"
    
    print(f"Loading entity associations from: {file_path}")
    print(f"File exists: {file_path.exists()}")
    
    if not file_path.exists():
        print("Entity associations file not found!")
        return {
            "version": "1.0",
            "description": "Entity associations extracted from AI responses about Extreme Networks",
            "associations": [],
            "last_updated": datetime.now().isoformat()
        }
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            print(f"Loaded {len(data.get('associations', []))} associations")
            return data
    except Exception as e:
        print(f"Error loading entity associations: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading entity associations: {str(e)}")


@router.get("/")
def get_entity_associations(
    engine: Optional[str] = Query(None, description="Filter by engine (openai, perplexity)"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of results to return")
) -> Dict[str, Any]:
    """Get entity associations with optional engine filtering."""
    
    print(f"get_entity_associations called with engine={engine}, limit={limit}")
    
    data = load_entity_associations()
    associations = data.get("associations", [])
    
    print(f"Found {len(associations)} total associations")
    
    # Filter by engine if specified
    if engine:
        if engine not in ["openai", "perplexity"]:
            raise HTTPException(status_code=400, detail="Engine must be 'openai' or 'perplexity'")
        
        associations = [a for a in associations if a.get("engine") == engine]
        print(f"After engine filtering: {len(associations)} associations")
    
    # Sort by timestamp (newest first) and limit results
    associations.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    associations = associations[:limit]
    
    print(f"Returning {len(associations)} associations")
    
    # Return the raw data structure that the frontend expects
    return {
        "associations": associations,
        "total_associations": len(associations),
        "filters": {"engine": engine},
        "last_updated": data.get("last_updated")
    }


@router.get("/products")
def get_product_associations(
    engine: Optional[str] = Query(None, description="Filter by engine (openai, perplexity)")
) -> Dict[str, Any]:
    """Get product associations with optional engine filtering."""
    
    data = load_entity_associations()
    associations = data.get("associations", [])
    
    # Filter by engine if specified
    if engine:
        if engine not in ["openai", "perplexity"]:
            raise HTTPException(status_code=400, detail="Engine must be 'openai' or 'perplexity'")
        
        associations = [a for a in associations if a.get("engine") == engine]
    
    # Aggregate products by engine
    product_counts = {}
    engine_products = {}
    
    for assoc in associations:
        engine_name = assoc.get("engine", "unknown")
        
        # Only process product queries
        if "product" in assoc.get("query", "").lower():
            products = assoc.get("products", [])
            
            if engine_name not in engine_products:
                engine_products[engine_name] = set()
            
            engine_products[engine_name].update(products)
            
            for product in products:
                if product not in product_counts:
                    product_counts[product] = {"count": 0, "engines": set()}
                
                product_counts[product]["count"] += 1
                product_counts[product]["engines"].add(engine_name)
    
    # Convert sets to lists for JSON serialization
    for product_data in product_counts.values():
        product_data["engines"] = list(product_data["engines"])
    
    for engine_name in engine_products:
        engine_products[engine_name] = list(engine_products[engine_name])
    
    return {
        "total_products": len(product_counts),
        "filters": {"engine": engine},
        "product_counts": product_counts,
        "by_engine": engine_products
    }


@router.get("/keywords")
def get_keyword_associations(
    engine: Optional[str] = Query(None, description="Filter by engine (openai, perplexity)")
) -> Dict[str, Any]:
    """Get keyword associations with optional engine filtering."""
    
    data = load_entity_associations()
    associations = data.get("associations", [])
    
    # Filter by engine if specified
    if engine:
        if engine not in ["openai", "perplexity"]:
            raise HTTPException(status_code=400, detail="Engine must be 'openai' or 'perplexity'")
        
        associations = [a for a in associations if a.get("engine") == engine]
    
    # Aggregate keywords by engine
    keyword_counts = {}
    engine_keywords = {}
    
    for assoc in associations:
        engine_name = assoc.get("engine", "unknown")
        
        # Only process keyword queries
        if "keyword" in assoc.get("query", "").lower():
            keywords = assoc.get("keywords", [])
            
            if engine_name not in engine_keywords:
                engine_keywords[engine_name] = set()
            
            engine_keywords[engine_name].update(keywords)
            
            for keyword in keywords:
                if keyword not in keyword_counts:
                    keyword_counts[keyword] = {"count": 0, "engines": set()}
                
                keyword_counts[keyword]["count"] += 1
                keyword_counts[keyword]["engines"].add(engine_name)
    
    # Convert sets to lists for JSON serialization
    for keyword_data in keyword_counts.values():
        keyword_data["engines"] = list(keyword_data["engines"])
    
    for engine_name in engine_keywords:
        engine_keywords[engine_name] = list(engine_keywords[engine_name])
    
    return {
        "total_keywords": len(keyword_counts),
        "filters": {"engine": engine},
        "keyword_counts": keyword_counts,
        "by_engine": engine_keywords
    }
