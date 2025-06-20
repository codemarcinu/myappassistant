"""
Authentication and authorization module for FoodSave AI
"""

import os

from .auth_middleware import AuthMiddleware
from .jwt_handler import JWTHandler
from .models import Role, User, UserRole
from .routes import auth_router
from .schemas import TokenResponse, UserCreate, UserLogin, UserResponse

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
