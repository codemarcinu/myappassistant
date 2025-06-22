import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.ocr_agent import OCRAgent
from backend.agents.interfaces import AgentResponse
from backend.api.v2.endpoints.receipts import upload_receipt
from backend.models.shopping import Product, ShoppingTrip
from backend.services.shopping_service import create_shopping_trip


@pytest.mark.asyncio
async def test_ocr_agent_receipt_processing():
    """Test OCR agent's ability to process receipt images"""
    # Create OCR agent
    agent = OCRAgent()
    
    # Mock input data with receipt image
    mock_input = {
        "file_bytes": b"test_receipt_image_bytes",
        "file_type": "image"
    }
    
    # Sample receipt text that would be extracted from an image
    receipt_text = """SKLEP ABC
ul. Główna 123
00-001 Warszawa
NIP: 123-456-78-90

PARAGON FISKALNY
--------------------------------
Mleko 3.2%        1 x 3.99 = 3.99
Chleb pszenny     1 x 4.50 = 4.50
Masło extra      1 x 6.99 = 6.99
Ser żółty       0.25 x 39.96 = 9.99
Jabłka          1.5 x 2.99 = 4.50
--------------------------------
SUMA: 28.97
--------------------------------
Data: 15-12-2023
Godzina: 15:30
"""
    
    # Mock the OCR processing
    with patch('backend.core.ocr.process_image_file', return_value=receipt_text):
        # Process the receipt
        result = await agent.process(mock_input)
        
        # Verify the result
        assert result.success is True
        assert "SKLEP ABC" in result.text
        assert "Mleko 3.2%" in result.text
        assert "SUMA: 28.97" in result.text
        assert result.metadata["file_type"] == "image"


@pytest.mark.asyncio
async def test_upload_receipt_endpoint():
    """Test upload receipt endpoint"""
    # Create a mock UploadFile
    mock_file = MagicMock()
    mock_file.content_type = "image/jpeg"
    mock_file.read = AsyncMock(return_value=b"test_receipt_image_bytes")
    
    # Mock OCR agent response
    mock_ocr_response = AgentResponse(
        success=True,
        text="Mocked receipt text",
        message="Receipt processed successfully",
        metadata={"file_type": "image"}
    )
    
    # Mock the OCR agent
    with patch('backend.agents.ocr_agent.OCRAgent.process', return_value=mock_ocr_response):
        # Call the endpoint
        response = await upload_receipt(file=mock_file)
        
        # Verify the response
        assert response.status_code == 200
        assert response.body
        
        # Parse the JSON response
        import json
        response_data = json.loads(response.body)
        
        # Verify the response content
        assert response_data["status_code"] == 200
        assert response_data["message"] == "Receipt processed successfully"
        assert response_data["data"]["text"] == "Mocked receipt text"


@pytest.mark.asyncio
async def test_upload_receipt_invalid_file_type():
    """Test upload receipt endpoint with invalid file type"""
    # Create a mock UploadFile with invalid content type
    mock_file = MagicMock()
    mock_file.content_type = "text/plain"  # Nieprawidłowy typ pliku
    mock_file.read = AsyncMock(return_value=b"test_receipt_text_bytes")
    
    # Wywołanie endpointu powinno zgłosić wyjątek BadRequestError
    from backend.api.v2.exceptions import BadRequestError
    
    with pytest.raises(BadRequestError) as exc_info:
        await upload_receipt(file=mock_file)
    
    # Sprawdzenie szczegółów wyjątku
    assert "Unsupported file type" in str(exc_info.value)
    assert exc_info.value.details["content_type"] == "text/plain"
    assert "image/jpeg" in exc_info.value.details["supported_types"]
    assert "image/png" in exc_info.value.details["supported_types"]
    assert "application/pdf" in exc_info.value.details["supported_types"]


@pytest.mark.asyncio
async def test_create_shopping_trip_service():
    """Test creating shopping trip from receipt data"""
    # Sample receipt data
    receipt_data = {
        "store_name": "SKLEP ABC",
        "date": "2023-12-15",
        "total_amount": 28.97,
        "products": [
            {"name": "Mleko 3.2%", "quantity": 1, "unit_price": 3.99, "category": "nabiał"},
            {"name": "Chleb pszenny", "quantity": 1, "unit_price": 4.50, "category": "pieczywo"},
            {"name": "Masło extra", "quantity": 1, "unit_price": 6.99, "category": "nabiał"},
            {"name": "Ser żółty", "quantity": 0.25, "unit_price": 39.96, "category": "nabiał"},
            {"name": "Jabłka", "quantity": 1.5, "unit_price": 2.99, "category": "owoce"}
        ]
    }
    
    # Mock database session
    mock_db = MagicMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    # Create shopping trip
    result = await create_shopping_trip(receipt_data, mock_db)
    
    # Verify the result
    assert result is not None
    assert result.store_name == "SKLEP ABC"
    assert result.trip_date == "2023-12-15"
    assert result.total_amount == 28.97
    assert len(result.products) == 5
    
    # Verify database operations
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


if __name__ == "__main__":
    pytest.main(["-v", "test_receipt_processing_fixed.py"]) 