#!/usr/bin/env python3
import os
import sys

print("Python version:", sys.version)
print("PYTHONPATH:", sys.path)
print("Current directory:", os.getcwd())
print("Directory contents:", os.listdir("."))

try:
    print("Attempting imports...")

    # Try importing main first
    print("Importing backend module...")

    print("Successfully imported backend module")

    print("Importing backend.main...")

    print("Successfully imported backend.main")

    # If that works, try the problem modules
    print("Importing backend.agents.orchestrator...")

    print("Successfully imported Orchestrator")

    print("Importing backend.agents.agent_factory...")

    print("Successfully imported AgentFactory")

    print("All imports successful!")
except Exception as e:
    import traceback

    print(f"Import error: {e}")
    print("Traceback:")
    traceback.print_exc()
