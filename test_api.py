"""
Test script for Spike AI Backend.
Run test queries against the API to validate functionality.
"""

import requests
import json
import time


# Configuration
API_URL = "http://localhost:8080/query"
PROPERTY_ID = "516815205"  # Your GA4 property ID


def test_query(query: str, property_id: str = None, test_name: str = ""):
    """Execute a test query and print results."""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")
    print(f"Query: {query}")
    if property_id:
        print(f"Property ID: {property_id}")
    print()
    
    payload = {"query": query}
    if property_id:
        payload["propertyId"] = property_id
    
    try:
        start_time = time.time()
        response = requests.post(API_URL, json=payload)
        elapsed = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {elapsed:.2f}s")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("Response:")
            print(result.get("response", "No response"))
        else:
            print("Error:")
            print(response.text)
    
    except Exception as e:
        print(f"Error: {e}")
    
    print()


def main():
    """Run all test cases."""
    print("="*60)
    print("Spike AI Backend - Test Suite")
    print("="*60)
    
    # Check server health
    try:
        health = requests.get("http://localhost:8080/health")
        print(f"\n✓ Server is healthy: {health.json()}")
    except:
        print("\n✗ Server is not responding. Please start the server first.")
        return
    
    # Tier 1: Analytics Agent Tests
    print("\n" + "="*60)
    print("TIER 1: ANALYTICS AGENT TESTS")
    print("="*60)
    
    test_query(
        query="Give me a daily breakdown of page views, users, and sessions for the /pricing page over the last 14 days. Summarize any noticeable trends.",
        property_id=PROPERTY_ID,
        test_name="Daily Metrics Breakdown"
    )
    
    test_query(
        query="What are the top 5 traffic sources driving users to the pricing page in the last 30 days?",
        property_id=PROPERTY_ID,
        test_name="Traffic Source Analysis"
    )
    
    test_query(
        query="Calculate the average daily page views for the homepage over the last 30 days. Compare it to the previous 30-day period and explain whether traffic is increasing or decreasing.",
        property_id=PROPERTY_ID,
        test_name="Trend Analysis with Comparison"
    )
    
    test_query(
        query="Show me sessions by device category for the last 7 days",
        property_id=PROPERTY_ID,
        test_name="Device Breakdown"
    )
    
    test_query(
        query="Which countries have the most users this month?",
        property_id=PROPERTY_ID,
        test_name="Geographic Analysis"
    )
    
    # Tier 2: SEO Agent Tests
    print("\n" + "="*60)
    print("TIER 2: SEO AGENT TESTS")
    print("="*60)
    
    test_query(
        query="Which URLs do not use HTTPS and have title tags longer than 60 characters?",
        test_name="Conditional Filtering"
    )
    
    test_query(
        query="Group all pages by indexability status and provide a count for each group with a brief explanation.",
        test_name="Indexability Overview"
    )
    
    test_query(
        query="Calculate the percentage of indexable pages on the site. Based on this number, assess whether the site's technical SEO health is good, average, or poor.",
        test_name="SEO Health Assessment"
    )
    
    test_query(
        query="Find all pages with missing meta descriptions",
        test_name="Meta Description Analysis"
    )
    
    test_query(
        query="List all pages with duplicate title tags",
        test_name="Duplicate Title Detection"
    )
    
    # Tier 3: Multi-Agent Tests
    print("\n" + "="*60)
    print("TIER 3: MULTI-AGENT SYSTEM TESTS")
    print("="*60)
    
    test_query(
        query="What are the top 10 pages by page views in the last 14 days, and what are their corresponding title tags?",
        property_id=PROPERTY_ID,
        test_name="Analytics + SEO Fusion"
    )
    
    test_query(
        query="Which pages are in the top 20% by views but have missing or duplicate meta descriptions? Explain the SEO risk.",
        property_id=PROPERTY_ID,
        test_name="High Traffic Risk Analysis"
    )
    
    test_query(
        query="Return the top 5 pages by views along with their title tags and indexability status in JSON format.",
        property_id=PROPERTY_ID,
        test_name="Cross-Agent JSON Output"
    )
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETE")
    print("="*60)


if __name__ == "__main__":
    print("\n⚠️  NOTE: Update PROPERTY_ID variable with your GA4 property ID before running!")
    print("Current PROPERTY_ID:", PROPERTY_ID)
    
    if PROPERTY_ID == "YOUR_PROPERTY_ID":
        print("\n✗ Please set a valid PROPERTY_ID in the script.")
        exit(1)
    
    main()
