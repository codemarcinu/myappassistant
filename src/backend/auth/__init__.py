from __future__ import annotations

"""
Authentication and authorization module for FoodSave AI
"""

import os

from backend.auth.auth_middleware import AuthMiddleware
from backend.auth.jwt_handler import JWTHandler
from backend.auth.models import Role, User, UserRole
from backend.auth.routes import auth_router
from backend.auth.schemas import (TokenResponse, UserCreate, UserLogin,
                                  UserResponse)

# Set User-Agent environment variable early to prevent warnings
os.environ.setdefault(
    "USER_AGENT", "FoodSave-AI/1.0.0 (https://github.com/foodsave-ai)"
)

__all__ = [
    "JWTHandler",
    "AuthMiddleware",
    "User",
    "Role",
    "UserRole",
    "UserCreate",
    "UserLogin",
    "TokenResponse",
    "UserResponse",
    "auth_router",
]
