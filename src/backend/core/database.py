from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

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
