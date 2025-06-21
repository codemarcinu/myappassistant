"""
Database models for authentication
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


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

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    user_roles = relationship("UserRole", back_populates="user")


class Role(Base):
    """Role model"""

    __tablename__ = "roles"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    permissions = Column(String, nullable=True)  # JSON string of permissions
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    user_roles = relationship("UserRole", back_populates="role")


class UserRole(Base):
    """User-Role association model with additional metadata"""

    __tablename__ = "user_role_associations"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
