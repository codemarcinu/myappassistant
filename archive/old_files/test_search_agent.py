#!/usr/bin/env python3
"""
Test script for SearchAgent
"""
import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.backend.agents.search_agent import SearchAgent


async def test_search_agent():
    """Test SearchAgent with different queries"""
    agent = SearchAgent()

    # Test queries
    test_queries = [
        "Python programming",
        "Python language",
        "Python tutorial",
        "znajdź informacje o Pythonie",
        "Python documentation",
    ]

    for query in test_queries:
        print(f"\n=== Testing query: '{query}' ===")
        try:
            response = await agent.process({"query": query})
            print(f"Success: {response.success}")
            print(f"Text: {response.text}")
            print(f"Data: {response.data}")
            print(f"Error: {response.error}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_search_agent())
