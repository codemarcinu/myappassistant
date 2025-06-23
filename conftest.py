"""
Pytest configuration file to set up the test environment.
This file ensures that the src directory is in the Python path for all tests.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Configure pytest markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "memory: marks tests as memory profiling tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    ) 