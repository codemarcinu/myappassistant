from __future__ import annotations
from typing import Any, Dict, List, Optional, Union, Callable
from typing import AsyncGenerator, Coroutine
"""
Test package for the backend application.
"""

import os

# Set User-Agent environment variable early to prevent warnings
os.environ.setdefault(
    "USER_AGENT", "FoodSave-AI/1.0.0 (https://github.com/foodsave-ai)"
)
