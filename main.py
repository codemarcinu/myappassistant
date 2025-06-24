"""
Main application entry point.
"""

import os
import sys

from backend.app_factory import create_app

# Fix import paths
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the app from the backend module
app = create_app()

# This file is just a wrapper to help with imports
