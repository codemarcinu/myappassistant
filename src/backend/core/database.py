from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from fastapi import HTTPException
import logging

from backend.config import settings
from typing import Any, Dict, List, Optional, Union, Callable
from typing import AsyncGenerator, Coroutine

DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False
)

# TODO MDC-AUDIT: brak retry mechanizmu i monitoringu poolingu – potencjalne connection leaks przy błędach DB


class Base(DeclarativeBase):
    pass


async def get_db() -> None:
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
                "error_code": "INTERNAL_SERVER_ERROR"
            }
        )
