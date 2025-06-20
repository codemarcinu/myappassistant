#!/usr/bin/env python3
"""
Test script for SearchAgent
"""
import asyncio
import os
import sys

# Dodaj src/backend do PYTHONPATH dla importów absolutnych
backend_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/backend")
)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from backend.agents.search_agent import SearchAgent


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
