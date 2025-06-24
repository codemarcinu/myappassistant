"""
Authentication middleware for FastAPI
"""

import logging
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

from .jwt_handler import jwt_handler

logger = logging.getLogger(__name__)

security = HTTPBearer()


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware"""

    def __init__(self, app, exclude_paths: Optional[list] = None) -> None:
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
            "/auth/register",
            "/auth/refresh",
            "/health",
            "/ready",
            "/api/v2/weather",  # Weather endpoint doesn't require authentication
        ]

    async def dispatch(self, request: Request, call_next) -> None:
        """Process request with authentication"""

        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Extract token from Authorization header
        token = self._extract_token(request)

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify token
        payload = jwt_handler.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Add user info to request state
        request.state.user = payload
        request.state.user_id = payload.get("sub")
        request.state.user_roles = payload.get("roles", [])

        logger.debug(f"Authenticated user {payload.get('sub')} for {request.url.path}")

        return await call_next(request)

    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request"""
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None

        if not auth_header.startswith("Bearer "):
            return None

        return auth_header.split(" ")[1]


def get_current_user(request: Request) -> dict:
    """Get current user from request state"""
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    return request.state.user


def get_current_user_id(request: Request) -> int:
    """Get current user ID from request state"""
    if not hasattr(request.state, "user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    return request.state.user_id


def require_roles(required_roles: list) -> None:
    """Decorator to require specific roles"""

    def decorator(func) -> None:
        async def wrapper(request: Request, *args, **kwargs) -> None:
            user_roles = getattr(request.state, "user_roles", [])

            if not any(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions",
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_permission(permission: str) -> None:
    """Decorator to require specific permission"""

    def decorator(func) -> None:
        async def wrapper(request: Request, *args, **kwargs) -> None:
            user_permissions = getattr(request.state, "user_permissions", [])

            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required",
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
