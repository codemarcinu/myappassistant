import pytest
import pytest_asyncio

# Tutaj można dodać fixture specyficzne dla testów e2e


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
