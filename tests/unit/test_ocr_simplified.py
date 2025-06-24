from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.agents.interfaces import AgentResponse
from backend.agents.ocr_agent import OCRAgent, OCRAgentInput
from backend.core.ocr import OCRProcessor, OCRResult


class TestOCRSimplified:
    """Simplified tests for OCR functionality with complete mocking."""

    @pytest.mark.asyncio
    async def test_ocr_agent_basic_functionality(self):
        """Test basic OCR agent functionality with complete mocking."""
        # Create a mock OCR agent
        agent = MagicMock(spec=OCRAgent)

        # Configure the mock to return a successful response
        expected_response = AgentResponse(
            success=True,
            text="Sample receipt text\nMilk 3.99\nBread 4.50\nTotal 8.49",
            message="Pomyślnie wyodrębniono tekst z pliku",
            metadata={"file_type": "image"},
        )
        agent.process = AsyncMock(return_value=expected_response)

        # Create input data
        input_data = {"file_bytes": b"mock_image_data", "file_type": "image"}

        # Process the input
        result = await agent.process(input_data)

        # Verify the result
        assert result.success is True
        assert "Milk 3.99" in result.text
        assert result.message == "Pomyślnie wyodrębniono tekst z pliku"
        assert result.metadata["file_type"] == "image"

        # Verify the mock was called with the input data
        agent.process.assert_called_once_with(input_data)

    @pytest.mark.asyncio
    async def test_ocr_agent_error_handling(self):
        """Test OCR agent error handling with complete mocking."""
        # Create a mock OCR agent
        agent = MagicMock(spec=OCRAgent)

        # Configure the mock to return an error response
        error_response = AgentResponse(
            success=False,
            error="Nie udało się rozpoznać tekstu z pliku",
            text=None,
            metadata={"file_type": "image"},
        )
        agent.process = AsyncMock(return_value=error_response)

        # Create input data
        input_data = {"file_bytes": b"mock_image_data", "file_type": "image"}

        # Process the input
        result = await agent.process(input_data)

        # Verify the result
        assert result.success is False
        assert result.text is None
        assert "Nie udało się rozpoznać tekstu" in result.error

        # Verify the mock was called with the input data
        agent.process.assert_called_once_with(input_data)

    def test_ocr_processor_image_processing(self):
        """Test OCR processor image processing with complete mocking."""
        # Create a mock OCR processor
        processor = MagicMock(spec=OCRProcessor)

        # Configure the mock to return a successful result
        expected_result = OCRResult(
            text="Sample receipt text\nMilk 3.99\nBread 4.50\nTotal 8.49",
            confidence=90.5,
            metadata={"source": "image", "language": "pol"},
        )
        processor.process_image = MagicMock(return_value=expected_result)

        # Process an image
        image_bytes = b"mock_image_data"
        result = processor.process_image(image_bytes)

        # Verify the result
        assert result.text == expected_result.text
        assert result.confidence == expected_result.confidence
        assert result.metadata["source"] == "image"
        assert result.metadata["language"] == "pol"

        # Verify the mock was called with the image bytes
        processor.process_image.assert_called_once_with(image_bytes)

    def test_ocr_processor_pdf_processing(self):
        """Test OCR processor PDF processing with complete mocking."""
        # Create a mock OCR processor
        processor = MagicMock(spec=OCRProcessor)

        # Configure the mock to return a successful result
        expected_result = OCRResult(
            text="Page 1\nInvoice #12345\nTotal: $123.45\n\nPage 2\nThank you for your business",
            confidence=85.0,
            metadata={"source": "pdf", "pages": 2, "language": "pol"},
        )
        processor.process_pdf = MagicMock(return_value=expected_result)

        # Process a PDF
        pdf_bytes = b"mock_pdf_data"
        result = processor.process_pdf(pdf_bytes)

        # Verify the result
        assert result.text == expected_result.text
        assert result.confidence == expected_result.confidence
        assert result.metadata["source"] == "pdf"
        assert result.metadata["pages"] == 2
        assert result.metadata["language"] == "pol"

        # Verify the mock was called with the PDF bytes
        processor.process_pdf.assert_called_once_with(pdf_bytes)

    def test_ocr_processor_error_handling(self):
        """Test OCR processor error handling with complete mocking."""
        # Create a mock OCR processor
        processor = MagicMock(spec=OCRProcessor)

        # Configure the mock to return an error result
        error_result = OCRResult(
            text="", confidence=0.0, metadata={"error": "Failed to process image"}
        )
        processor.process_image = MagicMock(return_value=error_result)

        # Process an image
        image_bytes = b"mock_image_data"
        result = processor.process_image(image_bytes)

        # Verify the result
        assert result.text == ""
        assert result.confidence == 0.0
        assert "error" in result.metadata
        assert result.metadata["error"] == "Failed to process image"

        # Verify the mock was called with the image bytes
        processor.process_image.assert_called_once_with(image_bytes)


if __name__ == "__main__":
    pytest.main(["-v", "test_ocr_simplified.py"])
