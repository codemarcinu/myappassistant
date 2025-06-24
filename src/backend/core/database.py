from __future__ import annotations

import logging
from typing import AsyncGenerator

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from backend.config import settings

DATABASE_URL = settings.DATABASE_URL

# Create async SQLAlchemy engine with optimized connection pooling
engine = create_async_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30,  # Connection timeout
        "isolation_level": "EXCLUSIVE",  # Better concurrency for SQLite
    },
    echo=False,  # Disable SQL logging in production
    poolclass=StaticPool,  # Use StaticPool for SQLite async engine
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

# TODO MDC-AUDIT: brak retry mechanizmu i monitoringu poolingu – potencjalne connection leaks przy błędach DB


class Base(DeclarativeBase):
    """Unified Base class for all SQLAlchemy models"""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_db_with_error_handling() -> AsyncGenerator[AsyncSession, None]:
    """Database dependency with proper error handling"""
    try:
        async for session in get_db():
            yield session
    except Exception as e:
        logging.error(f"Database connection failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Database connection failed",
                "error_code": "INTERNAL_SERVER_ERROR",
            },
        )
