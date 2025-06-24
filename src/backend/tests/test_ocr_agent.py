from __future__ import annotations

from typing import (Any, AsyncGenerator, Callable, Coroutine, Dict, List,
                    Optional, Union)
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.agents.interfaces import AgentResponse
from backend.agents.ocr_agent import OCRAgent


@pytest.mark.asyncio
async def test_ocr_agent_success_image() -> None:
    agent = OCRAgent()
    mock_input = {"file_bytes": b"test_image_bytes", "file_type": "image"}

    with patch("backend.agents.ocr_agent.process_image_file") as mock_process:
        mock_process.return_value = "Rozpoznany tekst z obrazu"

        response = await agent.process(mock_input)
        assert isinstance(response, AgentResponse)
        assert response.success is True
        assert "Rozpoznany tekst z obrazu" in response.text


@pytest.mark.asyncio
async def test_ocr_agent_success_pdf() -> None:
    agent = OCRAgent()
    mock_input = {"file_bytes": b"test_pdf_bytes", "file_type": "pdf"}

    with patch("backend.agents.ocr_agent.process_pdf_file") as mock_process:
        mock_process.return_value = "Rozpoznany tekst z PDF"

        response = await agent.process(mock_input)
        assert isinstance(response, AgentResponse)
        assert response.success is True
        assert "Rozpoznany tekst z PDF" in response.text


@pytest.mark.asyncio
async def test_ocr_agent_input_validation() -> None:
    agent = OCRAgent()

    # Test with invalid input (missing required fields)
    response = await agent.process({"invalid_field": "test"})
    assert response.success is False
    assert "validation error" in response.error.lower()


@pytest.mark.asyncio
async def test_ocr_agent_unsupported_file_type() -> None:
    agent = OCRAgent()
    mock_input = {"file_bytes": b"test", "file_type": "docx"}

    response = await agent.process(mock_input)
    assert not response.success
    assert "Nieobsługiwany typ pliku" in response.error


@pytest.mark.asyncio
async def test_ocr_agent_empty_result() -> None:
    agent = OCRAgent()
    mock_input = {"file_bytes": b"test", "file_type": "image"}

    with patch("backend.agents.ocr_agent.process_image_file") as mock_process:
        mock_process.return_value = ""

        response = await agent.process(mock_input)
        assert not response.success
        assert "Nie udało się rozpoznać tekstu" in response.error


@pytest.mark.asyncio
async def test_ocr_agent_processing_error() -> None:
    agent = OCRAgent()
    mock_input = {"file_bytes": b"test", "file_type": "image"}

    with patch("backend.agents.ocr_agent.process_image_file") as mock_process:
        mock_process.side_effect = Exception("OCR processing error")

        response = await agent.process(mock_input)
        assert not response.success
        assert "Wystąpił błąd podczas przetwarzania pliku" in response.error
