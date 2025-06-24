from __future__ import annotations

import os
from typing import (Any, AsyncGenerator, Callable, Coroutine, Dict, List,
                    Optional, Union)

# Set User-Agent environment variable early to prevent warnings
os.environ.setdefault(
    "USER_AGENT", "FoodSave-AI/1.0.0 (https://github.com/foodsave-ai)"
)
