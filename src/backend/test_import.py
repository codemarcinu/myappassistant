#!/usr/bin/env python3

print("Testing imports...")

# Try importing the problematic module
from backend.agents.enhanced_orchestrator import EnhancedOrchestrator

print("Import successful! The circular dependency has been fixed.")

# Try creating an instance of EnhancedOrchestrator
from sqlalchemy.ext.asyncio import AsyncSession

print("Imports completed successfully.")