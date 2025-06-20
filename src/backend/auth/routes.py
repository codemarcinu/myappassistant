"""
Authentication routes for FastAPI
"""

import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .jwt_handler import jwt_handler
from .models import Role, User, UserRole
from .schemas import (
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm,
    RoleCreate,
    RoleResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserRoleAssign,
    UserUpdate,
)

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


# Dependency to get database session
def get_db():
    from ..infrastructure.database.database import AsyncSessionLocal

    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


@auth_router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user"""
    try:
        # Check if user already exists
        existing_user = (
            db.query(User)
            .filter(
                (User.email == user_data.email) | (User.username == user_data.username)
            )
            .first()
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists",
            )

        # Create new user
        hashed_password = jwt_handler.get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"New user registered: {user.email}")

        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            roles=[],
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user",
        )


@auth_router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user and return tokens"""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == user_data.email).first()

        if not user or not jwt_handler.verify_password(
            user_data.password, user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled",
            )

        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()

        # Get user roles
        roles = [role.name for role in user.roles]

        # Create tokens
        access_token = jwt_handler.create_access_token(
            data={"sub": str(user.id), "email": user.email, "roles": roles}
        )
        refresh_token = jwt_handler.create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )

        logger.info(f"User logged in: {user.email}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=jwt_handler.access_token_expire_minutes * 60,
            user=UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login=user.last_login,
                roles=roles,
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during login",
        )


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        payload = jwt_handler.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Get user roles
        roles = [role.name for role in user.roles]

        # Create new tokens
        access_token = jwt_handler.create_access_token(
            data={"sub": str(user.id), "email": user.email, "roles": roles}
        )
        new_refresh_token = jwt_handler.create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )

        logger.info(f"Token refreshed for user: {user.email}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=jwt_handler.access_token_expire_minutes * 60,
            user=UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login=user.last_login,
                roles=roles,
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refreshing token",
        )


@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(request: Request, db: Session = Depends(get_db)):
    """Get current user information"""
    try:
        user_id = request.state.user_id
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        roles = [role.name for role in user.roles]

        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            roles=roles,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting user information",
        )


@auth_router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate, request: Request, db: Session = Depends(get_db)
):
    """Update current user information"""
    try:
        user_id = request.state.user_id
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Update fields
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.username is not None:
            user.username = user_data.username
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        if user_data.is_active is not None:
            user.is_active = user_data.is_active

        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

        roles = [role.name for role in user.roles]

        logger.info(f"User updated: {user.email}")

        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            roles=roles,
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user",
        )


@auth_router.post("/change-password")
async def change_password(
    password_data: PasswordChange, request: Request, db: Session = Depends(get_db)
):
    """Change user password"""
    try:
        user_id = request.state.user_id
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Verify current password
        if not jwt_handler.verify_password(
            password_data.current_password, user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        # Update password
        user.hashed_password = jwt_handler.get_password_hash(password_data.new_password)
        user.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"Password changed for user: {user.email}")

        return {"message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error changing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error changing password",
        )
