import time
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from backend.core.database import AsyncSessionLocal, Base, engine
from backend.models.conversation import Conversation, Message
from backend.models.shopping import Product, ShoppingTrip


@pytest.fixture
def unique_session_id():
    return f"perf_test_{str(hash(time.time()))[-8:]}"


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """Inicjalizacja bazy danych dla testów"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup po testach
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_conversation_query_performance(unique_session_id):
    """Test performance of optimized conversation queries"""
    async with AsyncSessionLocal() as session:
        # Create test data
        conv = Conversation(session_id=unique_session_id)
        session.add(conv)
        await session.commit()

        # Add 100 test messages
        for i in range(100):
            msg = Message(
                content=f"Test message {i}",
                role="user",
                conversation_id=conv.id,
                created_at=datetime.now() - timedelta(minutes=i),
            )
            session.add(msg)
        await session.commit()

        # Benchmark query with composite index
        start = time.time()
        result = await session.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
            .limit(10)
        )
        elapsed = time.time() - start
        assert elapsed < 0.1  # Should be much faster with index
        assert len(result.scalars().all()) == 10


@pytest.mark.asyncio
async def test_shopping_query_performance():
    """Test performance of optimized shopping queries"""
    async with AsyncSessionLocal() as session:
        # Create test trip with unique name
        trip = ShoppingTrip(
            trip_date=datetime.now().date(),
            store_name=f"PerfTest_{str(hash(time.time()))[-8:]}",
        )
        session.add(trip)
        await session.flush()  # Ensure ID is available

        # Add 50 test products using bulk insert
        products = [
            Product(
                name=f"Product {i}",
                category="test" if i % 2 else "other",
                expiration_date=datetime.now().date() + timedelta(days=i),
                trip_id=trip.id,
            )
            for i in range(50)
        ]
        session.add_all(products)
        await session.commit()

        # Benchmark category query
        start = time.time()
        result = await session.execute(
            select(Product)
            .where(Product.trip_id == trip.id)
            .where(Product.category == "test")
        )
        elapsed = time.time() - start
        assert elapsed < 0.1  # Should be fast with composite index
        assert len(result.scalars().all()) == 25


@pytest.mark.asyncio
async def test_memory_usage():
    """Test memory usage of database operations"""

    async def _memory_test_operations():
        async with AsyncSessionLocal() as session:
            for i in range(100):
                conv = Conversation(
                    session_id=f"mem_test_{i}_{int(time.time() * 1000)}"
                )
                session.add(conv)
                await session.flush()  # Ensure conv.id is available

                for j in range(10):
                    msg = Message(
                        content=f"Msg {j}", role="user", conversation_id=conv.id
                    )
                    session.add(msg)
            await session.commit()

    # Get baseline memory usage
    baseline = await _get_process_memory()

    # Run operations
    await _memory_test_operations()

    # Get memory after operations
    after = await _get_process_memory()

    # Check memory difference is reasonable
    assert (after - baseline) < 50  # MB


async def _get_process_memory():
    """Get current process memory usage in MB"""
    import psutil

    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024  # Convert to MB
