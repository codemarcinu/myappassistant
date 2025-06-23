from __future__ import annotations
import time
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select

from backend.core.database import AsyncSessionLocal
from backend.models.conversation import Conversation, Message
from backend.models.shopping import Product, ShoppingTrip
from typing import Any, Dict, List, Optional, Union, Callable
from typing import AsyncGenerator, Coroutine
from memory_profiler import memory_usage


@pytest.fixture
def unique_session_id() -> None:
    return f"perf_test_{str(hash(time.time()))[-8:]}"


@pytest.fixture(scope="module")
async def setup_database():
    """Set up the database with test data."""
    async with AsyncSessionLocal() as db:
        # Clear existing data
        await db.execute(delete(Conversation))
        await db.execute(delete(Message))
        await db.execute(delete(ShoppingTrip))
        await db.execute(delete(Product))

        # Create test data
        conversation = Conversation(
            session_id=unique_session_id,
            messages=[
                Message(content="Hello", role="user"),
                Message(content="Hi", role="assistant"),
            ]
        )
        shopping_trip = ShoppingTrip(
            store_name="Test Store",
            products=[
                Product(name="Test Product 1", price=10.0, quantity=1),
                Product(name="Test Product 2", price=20.0, quantity=2),
            ],
        )
        db.add(conversation)
        db.add(shopping_trip)
        await db.commit()
    yield
    # Teardown is not strictly necessary for in-memory db, but good practice
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Conversation))
        await db.execute(delete(Message))
        await db.execute(delete(ShoppingTrip))
        await db.execute(delete(Product))
        await db.commit()


@pytest.mark.asyncio
async def test_conversation_query_performance(benchmark, setup_database):
    """Test performance of querying conversations."""

    async def query_conversations():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Conversation).options(selectinload(Conversation.messages)))
            _ = result.scalars().all()

    benchmark(asyncio.run, query_conversations())


@pytest.mark.asyncio
async def test_shopping_query_performance(benchmark, setup_database):
    """Test performance of querying shopping trips."""

    async def query_shopping_trips():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(ShoppingTrip).options(selectinload(ShoppingTrip.products)))
            _ = result.scalars().all()

    benchmark(asyncio.run, query_shopping_trips())


@pytest.mark.asyncio
async def test_memory_usage(setup_database):
    """Test memory usage for querying data."""

    async def query_data():
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

    # Measure memory usage
    mem_usage = memory_usage((asyncio.run, (query_data(),)), max_usage=True)
    print(f"Peak memory usage: {mem_usage} MiB")

    # Add assertions for memory usage if needed
    assert mem_usage < 100  # Example threshold: 100 MiB


async def _get_process_memory() -> None:
    """Get current process memory usage in MB"""
    import psutil

    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024  # Convert to MB
