import pytest
import pytest_asyncio

# Tutaj można dodać fixture specyficzne dla testów integracyjnych


@pytest_asyncio.fixture
async def db_session():
    """
    Async fixture dla sesji bazodanowej z cleanup.
    """
    from src.backend.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture
async def test_db():
    """
    Fixture dla testowej bazy danych z cleanup.
    """
    from src.backend.core.database import Base, engine

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
