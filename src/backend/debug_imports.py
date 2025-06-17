#!/usr/bin/env python3
import sys
import os

print("Python version:", sys.version)
print("PYTHONPATH:", sys.path)
print("Current directory:", os.getcwd())
print("Directory contents:", os.listdir("."))

try:
    print("Attempting imports...")
    
    # Try importing main first
    print("Importing backend module...")
    import backend
    print("Successfully imported backend module")
    
    print("Importing backend.main...")
    import backend.main
    print("Successfully imported backend.main")
    
    # If that works, try the problem modules
    print("Importing backend.agents.enhanced_orchestrator...")
    from backend.agents.enhanced_orchestrator import EnhancedOrchestrator
    print("Successfully imported EnhancedOrchestrator")
    
    print("Importing backend.agents.agent_factory...")
    from backend.agents.agent_factory import AgentFactory
    print("Successfully imported AgentFactory")
    
    print("All imports successful!")
except Exception as e:
    import traceback
    print(f"Import error: {e}")
    print("Traceback:")
    traceback.print_exc()