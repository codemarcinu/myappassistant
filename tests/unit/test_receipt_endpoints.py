import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.responses import JSONResponse

from backend.agents.interfaces import AgentResponse
from backend.api.v2.endpoints.receipts import ALLOWED_FILE_TYPES, upload_receipt
from backend.api.v2.exceptions import BadRequestError, UnprocessableEntityError


class TestReceiptEndpoints:
    """Unit tests for receipt endpoints with mocked dependencies."""

    @pytest.fixture
    def mock_file(self):
        """Create a mock UploadFile for testing."""
        mock = MagicMock(spec=UploadFile)
        mock.content_type = "image/jpeg"
        mock.read = AsyncMock(return_value=b"test_receipt_image_bytes")
        return mock

    @pytest.mark.asyncio
    async def test_upload_receipt_success(self, mock_file):
        """Test successful receipt upload and processing."""
        # Mock OCR agent response
        mock_ocr_response = AgentResponse(
            success=True,
            text="Sklep ABC\nMleko 3.99\nChleb 4.50\nRazem 8.49",
            message="Receipt processed successfully",
            metadata={"file_type": "image"},
        )

        # Mock the OCR agent
        with patch(
            "backend.agents.ocr_agent.OCRAgent.process", return_value=mock_ocr_response
        ):
            # Call the endpoint
            response = await upload_receipt(file=mock_file)

            # Verify the response
            assert isinstance(response, JSONResponse)
            assert response.status_code == 200

            # Parse the JSON response
            response_data = json.loads(response.body)

            # Verify the response content
            assert response_data["status_code"] == 200
            assert response_data["message"] == "Receipt processed successfully"
            assert (
                response_data["data"]["text"]
                == "Sklep ABC\nMleko 3.99\nChleb 4.50\nRazem 8.49"
            )

    @pytest.mark.asyncio
    async def test_upload_receipt_missing_content_type(self):
        """Test upload with missing content type."""
        # Create a mock file with no content_type
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = None

        # Call the endpoint and expect an exception
        with pytest.raises(HTTPException) as excinfo:
            await upload_receipt(file=mock_file)

        # Verify the exception
        assert excinfo.value.status_code == 400
        assert "Missing content type" in str(excinfo.value.detail)

    @pytest.mark.asyncio
    async def test_upload_receipt_invalid_file_type(self):
        """Test upload with invalid file type."""
        # Create a mock file with invalid content_type
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "text/plain"

        # Call the endpoint and expect an exception
        with pytest.raises(HTTPException) as excinfo:
            await upload_receipt(file=mock_file)

        # Verify the exception
        assert excinfo.value.status_code == 400
        assert "Unsupported file type" in str(excinfo.value.detail["message"])

    @pytest.mark.asyncio
    async def test_upload_receipt_ocr_failure(self, mock_file):
        """Test receipt upload with OCR processing failure."""
        # Mock OCR agent failure response
        mock_ocr_response = AgentResponse(
            success=False,
            error="Failed to process image",
            text=None,
            metadata={"file_type": "image"},
        )

        # Mock the OCR agent
        with patch(
            "backend.agents.ocr_agent.OCRAgent.process", return_value=mock_ocr_response
        ):
            # Call the endpoint and expect an exception
            with pytest.raises(HTTPException) as excinfo:
                await upload_receipt(file=mock_file)

            # Verify the exception
            assert excinfo.value.status_code == 422
            assert "Failed to process receipt" in str(excinfo.value.detail["message"])

    @pytest.mark.asyncio
    async def test_upload_receipt_unexpected_error(self, mock_file):
        """Test receipt upload with unexpected error during processing."""
        # Mock the OCR agent to raise an exception
        with patch(
            "backend.agents.ocr_agent.OCRAgent.process",
            side_effect=Exception("Unexpected test error"),
        ):
            # Call the endpoint
            response = await upload_receipt(file=mock_file)

            # Verify the response
            assert isinstance(response, JSONResponse)
            assert response.status_code == 500

            # Parse the JSON response
            response_data = json.loads(response.body)

            # Verify the response content
            assert response_data["status_code"] == 500
            assert response_data["error_code"] == "INTERNAL_SERVER_ERROR"
            assert "Unexpected error" in response_data["message"]
            assert "Unexpected test error" in response_data["details"]["error"]

    @pytest.mark.asyncio
    async def test_upload_receipt_pdf_file(self):
        """Test upload with PDF file type."""
        # Create a mock PDF file
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"test_pdf_bytes")

        # Mock OCR agent response
        mock_ocr_response = AgentResponse(
            success=True,
            text="PDF Receipt Content",
            message="PDF processed successfully",
            metadata={"file_type": "pdf"},
        )

        # Mock the OCR agent
        with patch(
            "backend.agents.ocr_agent.OCRAgent.process", return_value=mock_ocr_response
        ):
            # Call the endpoint
            response = await upload_receipt(file=mock_file)

            # Verify the response
            assert isinstance(response, JSONResponse)
            assert response.status_code == 200

            # Parse the JSON response
            response_data = json.loads(response.body)

            # Verify the response content
            assert response_data["status_code"] == 200
            assert response_data["message"] == "Receipt processed successfully"
            assert response_data["data"]["text"] == "PDF Receipt Content"

    def test_allowed_file_types(self):
        """Test the ALLOWED_FILE_TYPES constant."""
        # Verify that the constant contains expected file types
        assert "image/jpeg" in ALLOWED_FILE_TYPES
        assert "image/png" in ALLOWED_FILE_TYPES
        assert "application/pdf" in ALLOWED_FILE_TYPES

        # Verify that common invalid types are not included
        assert "text/plain" not in ALLOWED_FILE_TYPES
        assert "application/msword" not in ALLOWED_FILE_TYPES


if __name__ == "__main__":
    pytest.main(["-v", "test_receipt_endpoints.py"])
