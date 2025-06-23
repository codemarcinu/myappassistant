import pytest
import pytest_asyncio

# Tutaj można dodać fixture specyficzne dla testów e2e


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


@pytest.fixture
def mock_ocr_success(mocker):
    """
    Fixture do mockowania sukcesu OCR (obraz).
    """
    return mocker.patch(
        "backend.agents.ocr_agent.process_image_file", return_value="Test receipt text"
    )


@pytest.fixture
def mock_ocr_pdf_success(mocker):
    """
    Fixture do mockowania sukcesu OCR (PDF).
    """
    return mocker.patch(
        "backend.agents.ocr_agent.process_pdf_file", return_value="Test PDF receipt"
    )


@pytest.fixture
def mock_ocr_failure(mocker):
    """
    Fixture do mockowania błędu OCR (obraz).
    """
    return mocker.patch(
        "backend.agents.ocr_agent.process_image_file", return_value=None
    )


@pytest.fixture
def mock_ocr_exception(mocker):
    """
    Fixture do mockowania wyjątku OCR (obraz).
    """
    return mocker.patch(
        "backend.agents.ocr_agent.process_image_file",
        side_effect=Exception("Unexpected error"),
    )
