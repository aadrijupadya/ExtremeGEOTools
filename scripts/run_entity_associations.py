#!/usr/bin/env python3
"""
Entity Association Runner

This script runs the two entity association queries:
1. "What products do you associate with Extreme Networks?"
2. "What keywords do you associate with Extreme Networks?"

It runs these queries on both OpenAI and Perplexity engines and stores the results
in a JSON file with parsing of products and keywords.
"""

import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path

# Add the backend directory to the path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.services.engines import call_engine
import uuid


def extract_products_from_response(response_text):
    """Extract product names from the AI response."""
    products = []
    
    # Clean up the response text
    response_text = response_text.replace('**', '').replace('*', '')
    
    # Parse structured format: "Product Name - Brief description"
    lines = response_text.split('\n')
    for line in lines:
        line = line.strip()
        if '-' in line and len(line) > 5:
            # Split by first dash to get product name
            parts = line.split('-', 1)
            if len(parts) == 2:
                product_name = parts[0].strip()
                description = parts[1].strip()
                
                # Clean up the product name
                product_name = clean_product_name(product_name)
                if product_name:
                    # Store as "Product Name - Description"
                    products.append(f"{product_name} - {description}")
    
    # Fallback: if no structured format found, try old method
    if not products:
        for line in lines:
            line = line.strip()
            if any(indicator in line.lower() for indicator in ['product', 'solution', 'platform', 'system', 'switch', 'access point', 'router', 'wi-fi', 'wireless']):
                if ':' in line:
                    product = line.split(':', 1)[1].strip()
                    if product and len(product) > 2:
                        product = clean_product_name(product)
                        if product:
                            products.append(product)
    
    return list(set(products))[:10]  # Remove duplicates and limit to top 10


def clean_product_name(product):
    """Clean up product names by removing URLs, markdown, and other artifacts."""
    if not product:
        return None
    
    # Remove URLs
    if 'http' in product or 'www.' in product:
        return None
    
    # Remove markdown formatting
    product = product.replace('**', '').replace('*', '').replace('`', '')
    
    # Remove brackets and parentheses content
    product = re.sub(r'\[.*?\]', '', product)
    product = re.sub(r'\(.*?\)', '', product)
    
    # Remove common artifacts
    product = product.replace('//', '').replace('https://', '').replace('http://', '')
    
    # Clean up whitespace and punctuation
    product = product.strip(' .[](){}')
    
    # Skip if too short or contains obvious artifacts
    if len(product) < 3 or any(artifact in product.lower() for artifact in ['http', 'www', '//', '[']):
        return None
    
    # Capitalize properly (first letter of each word)
    words = product.split()
    cleaned_words = []
    for word in words:
        if word.lower() in ['ai', 'sd-wan', 'sase', 'wifi', 'iot']:
            cleaned_words.append(word.upper())
        else:
            cleaned_words.append(word.capitalize())
    
    return ' '.join(cleaned_words)


def extract_keywords_from_response(response_text):
    """Extract keywords from the AI response."""
    keywords = []
    
    # Clean up the response text
    response_text = response_text.replace('**', '').replace('*', '')
    
    # Parse structured format: "Keyword - Brief definition"
    lines = response_text.split('\n')
    for line in lines:
        line = line.strip()
        if '-' in line and len(line) > 5:
            # Split by first dash to get keyword and definition
            parts = line.split('-', 1)
            if len(parts) == 2:
                keyword = parts[0].strip()
                definition = parts[1].strip()
                
                # Clean up the keyword
                keyword = clean_keyword_name(keyword)
                if keyword:
                    # Store as "Keyword - Definition"
                    keywords.append(f"{keyword} - {definition}")
    
    # Fallback: if no structured format found, try old method
    if not keywords:
        for line in lines:
            line = line.strip()
            if any(indicator in line.lower() for indicator in ['keyword', 'term', 'concept', 'technology', 'feature']):
                if ':' in line:
                    keyword_part = line.split(':', 1)[1].strip()
                    # Split by commas, semicolons, or "and"
                    for keyword in keyword_part.replace(' and ', ',').replace(';', ',').split(','):
                        keyword = keyword.strip()
                        if keyword and len(keyword) > 2:
                            clean_keyword = clean_keyword_name(keyword)
                            if clean_keyword:
                                keywords.append(clean_keyword)
    
    # If still no keywords, try to find technical terms
    if not keywords:
        technical_terms = ['aiops', 'sd-wan', 'sase', 'wifi', 'ethernet', 'automation', 'analytics', 'cloud', 'security', 'networking', 'ai', 'platform', 'fabric', 'wireless', 'switching', 'routing']
        for term in technical_terms:
            if term in response_text.lower():
                clean_term = clean_keyword_name(term)
                if clean_term:
                    keywords.append(clean_term.upper() if term in ['aiops', 'sd-wan', 'sase', 'wifi'] else clean_term.title())
    
    return list(set(keywords))[:10]  # Remove duplicates and limit to top 10


def clean_keyword_name(keyword):
    """Clean up keyword names by removing URLs, markdown, and other artifacts."""
    if not keyword:
        return None
    
    # Remove URLs
    if 'http' in keyword or 'www.' in keyword:
        return None
    
    # Remove markdown formatting
    keyword = keyword.replace('**', '').replace('*', '').replace('`', '')
    
    # Remove brackets and parentheses content
    keyword = re.sub(r'\[.*?\]', '', keyword)
    keyword = re.sub(r'\(.*?\)', '', keyword)
    
    # Remove common artifacts
    keyword = keyword.replace('//', '').replace('https://', '').replace('http://', '')
    
    # Clean up whitespace and punctuation
    keyword = keyword.strip(' .[](){}')
    
    # Skip if too short or contains obvious artifacts
    if len(keyword) < 3 or any(artifact in keyword.lower() for artifact in ['http', 'www', '//', '[']):
        return None
    
    # Capitalize properly (first letter of each word)
    words = keyword.split()
    cleaned_words = []
    for word in words:
        if word.lower() in ['ai', 'sd-wan', 'sase', 'wifi', 'iot', 'aiops']:
            cleaned_words.append(word.upper())
        else:
            cleaned_words.append(word.capitalize())
    
    return ' '.join(cleaned_words)


def run_entity_association_queries():
    """Run the entity association queries on both engines."""
    
    queries = [
        "List the TOP 10 product names that you associate with Extreme Networks. For each product, provide ONLY the product name in this exact format: 'Product Name - Brief one-line description'. Example: 'ExtremeCloud IQ - Cloud-based network management platform'. Do not include URLs, markdown, or additional text. Just list each product on a new line. Limit to exactly 10 products.",
        "List the TOP 10 keywords and technical terms that you associate with Extreme Networks. For each keyword, provide ONLY the keyword in this exact format: 'Keyword - Brief one-line definition'. Example: 'SD-WAN - Software-defined wide area networking'. Do not include URLs, markdown, or additional text. Just list each keyword on a new line. Limit to exactly 10 keywords."
    ]
    
    engines = ["openai", "perplexity"]
    results = []
    
    for engine in engines:
        for query in queries:
            print(f"Running query on {engine}: {query}")
            
            try:
                # Run the query using call_engine
                model = "gpt-4o-mini" if engine == "openai" else "sonar"
                response = call_engine(
                    engine=engine,
                    prompt=query,
                    temperature=0.7,
                    model=model
                )
                
                # Extract only the relevant data based on query type
                if "product" in query.lower():
                    # This is a product query - only extract products
                    products = extract_products_from_response(response.get('text', ''))
                    keywords = []  # Empty for product queries
                else:
                    # This is a keyword query - only extract keywords  
                    keywords = extract_keywords_from_response(response.get('text', ''))
                    products = []  # Empty for keyword queries
                
                # Store the result
                result = {
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat(),
                    "engine": engine,
                    "query": query,
                    "response": response.get('text', ''),
                    "products": products,
                    "keywords": keywords,
                    "model": response.get('model', ''),
                    "cost_usd": response.get('cost_usd', 0.0),
                    "latency_ms": response.get('latency_ms', 0)
                }
                
                results.append(result)
                print(f"  Extracted {len(products)} products and {len(keywords)} keywords")
                
            except Exception as e:
                print(f"  Error running query on {engine}: {e}")
                continue
    
    return results


def update_entity_associations_file(new_results):
    """Update the entity associations JSON file."""
    file_path = Path(__file__).parent.parent / "data" / "entity_associations.json"
    
    # Load existing data
    if file_path.exists():
        with open(file_path, 'r') as f:
            data = json.load(f)
    else:
        data = {
            "version": "1.0",
            "description": "Entity associations extracted from AI responses about Extreme Networks",
            "associations": []
        }
    
    # Add new results
    data["associations"].extend(new_results)
    data["last_updated"] = datetime.now().isoformat()
    
    # Keep only last 50 results to avoid file bloat
    if len(data["associations"]) > 50:
        data["associations"] = data["associations"][-50:]
    
    # Save updated data
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Updated {file_path} with {len(new_results)} new results")


def main():
    """Main function to run entity association queries."""
    print("Starting Entity Association Queries...")
    
    # Run the queries
    results = run_entity_association_queries()
    
    if results:
        # Update the storage file
        update_entity_associations_file(results)
        print(f"Successfully processed {len(results)} queries")
    else:
        print("No results to process")


if __name__ == "__main__":
    main()
