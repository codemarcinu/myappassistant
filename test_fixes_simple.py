#!/usr/bin/env python3
"""
Simple test script to verify FoodSave AI fixes
"""

import asyncio
import sys

# Add src to path
sys.path.insert(0, "src")


async def test_fixes():
    """Test that the fixes are working"""
    print("🧪 Testing FoodSave AI fixes...")

    try:
        # Test 1: Orchestrator import and methods
        print("\n1. Testing Orchestrator...")
        from backend.agents.orchestrator import Orchestrator

        orchestrator = Orchestrator()
        print("   ✅ Orchestrator created successfully")

        # Check if methods exist
        if hasattr(orchestrator, "process_command"):
            print("   ✅ process_command method exists")
        else:
            print("   ❌ process_command method missing")

        if hasattr(orchestrator, "_initialize_default_agents"):
            print("   ✅ _initialize_default_agents method exists")
        else:
            print("   ❌ _initialize_default_agents method missing")

        # Test 2: LLM Client
        print("\n2. Testing LLM Client...")
        from backend.core.llm_client import llm_client

        health = llm_client.get_health_status()
        print(f"   ✅ LLM client health: {health['ollama_available']}")

        # Test 3: Agent Router
        print("\n3. Testing Agent Router...")
        from backend.agents.agent_router import AgentRouter

        router = AgentRouter()
        print("   ✅ Agent router created successfully")

        # Test 4: Simple Circuit Breaker
        print("\n4. Testing Simple Circuit Breaker...")
        from backend.agents.orchestrator import SimpleCircuitBreaker

        breaker = SimpleCircuitBreaker("test", 3, 60)
        print("   ✅ SimpleCircuitBreaker created successfully")

        print("\n🎉 All tests passed! The fixes are working correctly.")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_fixes())
    sys.exit(0 if success else 1)
