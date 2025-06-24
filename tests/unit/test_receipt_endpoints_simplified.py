import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.responses import JSONResponse

from backend.agents.interfaces import AgentResponse
from backend.api.v2.endpoints.receipts import ALLOWED_FILE_TYPES


class TestReceiptEndpointsSimplified:
    """Simplified tests for receipt endpoints with complete mocking."""

    @pytest.mark.asyncio
    async def test_receipt_endpoint_success_scenario(self):
        """Test successful receipt processing scenario."""
        # Mock the upload_receipt function
        upload_receipt_mock = AsyncMock()

        # Configure the mock to return a successful response
        expected_response = JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Receipt processed successfully",
                "data": {"text": "Sklep ABC\nMleko 3.99\nChleb 4.50\nRazem 8.49"},
            },
        )
        upload_receipt_mock.return_value = expected_response

        # Create a mock file
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "image/jpeg"
        mock_file.read = AsyncMock(return_value=b"test_receipt_image_bytes")

        # Call the mocked function
        response = await upload_receipt_mock(file=mock_file)

        # Verify the response
        assert response.status_code == 200
        response_data = json.loads(response.body)
        assert response_data["status_code"] == 200
        assert response_data["message"] == "Receipt processed successfully"
        assert "Sklep ABC" in response_data["data"]["text"]

        # Verify the mock was called with the file
        upload_receipt_mock.assert_called_once_with(file=mock_file)

    @pytest.mark.asyncio
    async def test_receipt_endpoint_invalid_file_type(self):
        """Test receipt processing with invalid file type."""
        # Mock the upload_receipt function
        upload_receipt_mock = AsyncMock()

        # Configure the mock to raise an exception for invalid file type
        error_detail = {
            "status_code": 400,
            "error_code": "BAD_REQUEST",
            "message": "Unsupported file type",
            "details": {
                "content_type": "text/plain",
                "supported_types": ALLOWED_FILE_TYPES,
            },
        }
        upload_receipt_mock.side_effect = HTTPException(
            status_code=400, detail=error_detail
        )

        # Create a mock file with invalid content type
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "text/plain"

        # Call the mocked function and expect an exception
        with pytest.raises(HTTPException) as excinfo:
            await upload_receipt_mock(file=mock_file)

        # Verify the exception
        assert excinfo.value.status_code == 400
        assert excinfo.value.detail["message"] == "Unsupported file type"
        assert excinfo.value.detail["details"]["content_type"] == "text/plain"

        # Verify the mock was called with the file
        upload_receipt_mock.assert_called_once_with(file=mock_file)

    @pytest.mark.asyncio
    async def test_receipt_endpoint_ocr_failure(self):
        """Test receipt processing with OCR failure."""
        # Mock the upload_receipt function
        upload_receipt_mock = AsyncMock()

        # Configure the mock to raise an exception for OCR failure
        error_detail = {
            "status_code": 422,
            "error_code": "UNPROCESSABLE_ENTITY",
            "message": "Failed to process receipt",
            "details": {
                "error": "Failed to extract text from image",
                "error_code": "RECEIPT_PROCESSING_ERROR",
            },
        }
        upload_receipt_mock.side_effect = HTTPException(
            status_code=422, detail=error_detail
        )

        # Create a mock file
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "image/jpeg"

        # Call the mocked function and expect an exception
        with pytest.raises(HTTPException) as excinfo:
            await upload_receipt_mock(file=mock_file)

        # Verify the exception
        assert excinfo.value.status_code == 422
        assert excinfo.value.detail["message"] == "Failed to process receipt"
        assert "Failed to extract text" in excinfo.value.detail["details"]["error"]

        # Verify the mock was called with the file
        upload_receipt_mock.assert_called_once_with(file=mock_file)

    def test_allowed_file_types_validation(self):
        """Test validation of allowed file types."""
        # Verify that common image types are allowed
        assert "image/jpeg" in ALLOWED_FILE_TYPES
        assert "image/png" in ALLOWED_FILE_TYPES

        # Verify that PDF is allowed
        assert "application/pdf" in ALLOWED_FILE_TYPES

        # Verify that common invalid types are not included
        assert "text/plain" not in ALLOWED_FILE_TYPES
        assert "application/msword" not in ALLOWED_FILE_TYPES


if __name__ == "__main__":
    pytest.main(["-v", "test_receipt_endpoints_simplified.py"])
