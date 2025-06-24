from __future__ import annotations

"""
Database models for authentication
"""
from datetime import datetime
from typing import List

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String,
                        Table)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base

# Association table for many-to-many relationship between users and roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
)


class User(Base):
    """User model"""

    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    roles: Mapped[List[Role]] = relationship(
        secondary=user_roles, back_populates="users"
    )
    user_roles: Mapped[List[UserRole]] = relationship(
        "backend.auth.models.UserRole",
        back_populates="user",
        foreign_keys="backend.auth.models.UserRole.user_id",
    )


class Role(Base):
    """Role model"""

    __tablename__ = "roles"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    permissions: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # JSON string of permissions
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    users: Mapped[List[User]] = relationship(
        secondary=user_roles, back_populates="roles"
    )
    user_roles: Mapped[List[UserRole]] = relationship(
        "backend.auth.models.UserRole",
        back_populates="role",
        foreign_keys="backend.auth.models.UserRole.role_id",
    )


class UserRole(Base):
    """User-Role association model with additional metadata"""

    __tablename__ = "user_role_associations"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id"), nullable=False
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    assigned_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    user: Mapped[User] = relationship(
        "backend.auth.models.User", back_populates="user_roles", foreign_keys=[user_id]
    )
    role: Mapped[Role] = relationship(
        "backend.auth.models.Role", back_populates="user_roles"
    )
