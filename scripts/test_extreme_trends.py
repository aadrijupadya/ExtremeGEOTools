#!/usr/bin/env python3
"""
Test script for the new extreme-trends endpoint.
"""

import requests
import json

def test_extreme_trends():
    """Test the new extreme-trends endpoint."""
    try:
        # Test the new endpoint
        url = "http://127.0.0.1:8000/metrics/extreme-trends?days=30"
        print(f"Testing endpoint: {url}")
        
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Endpoint working!")
            print(f"Focus: {data.get('focus', 'N/A')}")
            print(f"Trends found: {len(data.get('trends', []))}")
            print(f"Total runs: {data.get('summary', {}).get('total_runs', 0)}")
            print(f"Total Extreme citations: {data.get('summary', {}).get('total_extreme_citations', 0)}")
            
            if data.get('trends'):
                print("\nSample trend data:")
                for trend in data['trends'][:3]:  # Show first 3 trends
                    print(f"  {trend['date']}: {trend['extreme_mentions']} mentions, {trend['extreme_citations']} citations")
        else:
            print(f"❌ Endpoint failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Make sure it's running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"❌ Error testing endpoint: {str(e)}")

if __name__ == "__main__":
    test_extreme_trends()
