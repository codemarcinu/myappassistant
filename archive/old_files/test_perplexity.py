#!/usr/bin/env python3
"""
Test script for Perplexity API integration
"""

import asyncio
import os
import sys
from typing import Any, Dict

import httpx

# Add src to path
sys.path.append("src")


async def test_perplexity_status():
    """Test Perplexity API status"""
    print("🔍 Testing Perplexity API status...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8000/api/agents/perplexity/status"
            )
            response.raise_for_status()
            data = response.json()

            print(f"✅ Status: {data}")
            return data.get("configured", False)
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return False


async def test_perplexity_search(query: str):
    """Test Perplexity API search"""
    print(f"🔍 Testing Perplexity search: '{query}'")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/agents/perplexity/test",
                data={"query": query},
            )
            response.raise_for_status()
            data = response.json()

            print(f"✅ Search successful: {data}")
            return True
    except Exception as e:
        print(f"❌ Error testing search: {e}")
        return False


async def test_search_agent_with_perplexity(query: str):
    """Test SearchAgent with Perplexity fallback"""
    print(f"🔍 Testing SearchAgent with Perplexity fallback: '{query}'")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/agents/agents/execute", json={"task": query}
            )
            response.raise_for_status()
            data = response.json()

            print(f"✅ SearchAgent response: {data}")
            return True
    except Exception as e:
        print(f"❌ Error testing SearchAgent: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 Starting Perplexity API tests...")

    # Check if backend is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            response.raise_for_status()
            print("✅ Backend is running")
    except Exception as e:
        print(f"❌ Backend not running: {e}")
        print("Please start the backend first: uvicorn src.backend.main:app --reload")
        return

    # Test 1: Check Perplexity status
    configured = await test_perplexity_status()

    if not configured:
        print("❌ Perplexity API not configured")
        print("Please add PERPLEXITY_API_KEY to your .env file")
        return

    # Test 2: Test Perplexity search
    test_queries = [
        "What are the latest trends in plant-based cooking?",
        "Jakie są najnowsze trendy w kuchni roślinnej?",
        "What is the weather like in Warsaw today?",
        "Kto to jest Karol Nawrocki?",
    ]

    for query in test_queries:
        await test_perplexity_search(query)
        await asyncio.sleep(1)  # Rate limiting

    # Test 3: Test SearchAgent with Perplexity fallback
    print("\n🔍 Testing SearchAgent with Perplexity fallback...")
    await test_search_agent_with_perplexity(
        "What are the health benefits of Mediterranean diet?"
    )

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
