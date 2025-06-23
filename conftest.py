"""
Pytest configuration file to set up the test environment.
This file ensures that the src directory is in the Python path for all tests.
"""

import sys
from pathlib import Path

import pytest

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))


# Configure pytest markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "memory: marks tests as memory profiling tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow")


@pytest.fixture
def client():
    """
    Fixture do tworzenia TestClient dla FastAPI aplikacji.
    """
    from fastapi.testclient import TestClient

    from src.backend.main import app

    return TestClient(app)


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
