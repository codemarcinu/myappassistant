from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from backend.agents.interfaces import AgentResponse

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


@pytest.fixture(autouse=True)
def mock_ocr_agent_process():
    with patch(
        "backend.agents.ocr_agent.OCRAgent.process", new_callable=AsyncMock
    ) as mock_process:
        mock_process.return_value = AgentResponse(
            success=True,
            text="BIEDRONKA\nData: 2024-06-23\nMleko 4.50zł\nChleb 3.20zł\nRazem: 7.70zł",
            message="Pomyślnie wyodrębniono tekst z pliku",
            metadata={"file_type": "image"},
        )
        yield mock_process


@pytest_asyncio.fixture
async def client():
    """
    Async HTTP client dla FastAPI (httpx.AsyncClient)
    """
    import httpx

    from src.backend.main import app

    async with httpx.AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac
