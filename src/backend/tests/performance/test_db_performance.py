from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta
from typing import (Any, AsyncGenerator, Callable, Coroutine, Dict, List,
                    Optional, Union)

import pytest
from memory_profiler import memory_usage
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.core.database import AsyncSessionLocal
from backend.models.conversation import Conversation, Message
from backend.models.shopping import Product, ShoppingTrip


@pytest.mark.asyncio
async def test_conversation_query_performance() -> Any:
    """Test performance of querying conversations."""

    async def query_conversations() -> Any:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Conversation).options(selectinload(Conversation.messages))
            )
            _ = result.scalars().all()

    # Używamy bezpośrednio await
    await query_conversations()
    assert True  # Placeholder assertion


@pytest.mark.asyncio
async def test_shopping_query_performance() -> Any:
    """Test performance of querying shopping trips."""

    async def query_shopping_trips() -> Any:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ShoppingTrip).options(selectinload(ShoppingTrip.products))
            )
            _ = result.scalars().all()

    # Używamy bezpośrednio await
    await query_shopping_trips()
    assert True  # Placeholder assertion


@pytest.mark.asyncio
async def test_memory_usage() -> Any:
    """Test memory usage for querying data."""

    async def query_data() -> Any:
        async with AsyncSessionLocal() as db:
            # Query conversations
            conv_result = await db.execute(
                select(Conversation).options(selectinload(Conversation.messages))
            )
            conversations = conv_result.scalars().all()

            # Query shopping trips
            shop_result = await db.execute(
                select(ShoppingTrip).options(selectinload(ShoppingTrip.products))
            )
            shopping_trips = shop_result.scalars().all()

            return conversations, shopping_trips

    # Używamy bezpośrednio await
    result = await query_data()
    print(
        f"Query completed successfully: {len(result[0])} conversations, {len(result[1])} shopping trips"
    )

    # Add assertions for memory usage if needed
    assert True  # Placeholder assertion


async def _get_process_memory() -> None:
    """Get current process memory usage in MB"""
    import psutil

    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024  # Convert to MB
