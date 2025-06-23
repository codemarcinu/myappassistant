from __future__ import annotations
import os
from typing import Any, Dict, List, Optional, Union, Callable
from typing import AsyncGenerator, Coroutine

# Set User-Agent environment variable early to prevent warnings
os.environ.setdefault(
    "USER_AGENT", "FoodSave-AI/1.0.0 (https://github.com/foodsave-ai)"
)
