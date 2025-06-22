import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from io import BytesIO

from backend.agents.interfaces import AgentResponse, BaseAgent
from backend.main import app

client = TestClient(app)

class MockOCRAgent(BaseAgent):
    """Mock OCR agent for testing receipt processing"""
    async def process(self, input_data):
        # Simulate OCR extraction
        if not input_data.get("file_content"):
            return AgentResponse(success=False, error="No file content provided")
            
        # Mock successful OCR processing with sample receipt data
        extracted_data = {
            "store_name": "LIDL",
            "date": "2023-06-20",
            "total": 156.78,
            "items": [
                {"name": "Chleb pszenny", "price": 4.99, "quantity": 1},
                {"name": "Mleko UHT 3.2%", "price": 3.49, "quantity": 2},
                {"name": "Jabłka", "price": 2.99, "quantity": 1.5},  # kg
                {"name": "Ser żółty", "price": 24.99, "quantity": 0.5},  # kg
            ]
        }
        
        return AgentResponse(
            success=True, 
            text="Receipt processed successfully", 
            data=extracted_data
        )

    def get_metadata(self):
        return {"name": "MockOCRAgent"}

    def get_dependencies(self):
        return []

    def is_healthy(self):
        return True

@pytest.fixture
def mock_ocr_agent():
    with patch("backend.agents.agent_factory.AgentFactory.get_agent") as mock_factory:
        mock_agent = MockOCRAgent()
        mock_factory.return_value = mock_agent
        yield mock_agent

def test_upload_receipt_image(mock_ocr_agent):
    """Test successful receipt upload with JPEG image"""
    fixture_path = os.path.join("tests", "fixtures", "test_receipt.jpg")
    
    # Ensure the test receipt exists
    if not os.path.exists(fixture_path):
        pytest.skip(f"Test receipt not found at {fixture_path}")
    
    with open(fixture_path, "rb") as f:
        file_content = f.read()
    
    response = client.post(
        "/api/v2/receipts/upload",
        files={"file": ("receipt.jpg", BytesIO(file_content), "image/jpeg")}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["status_code"] == 200
    assert data["message"] == "Receipt processed successfully"
    assert "data" in data
    
    # Check that we have the expected data structure
    receipt_data = data["data"]
    if isinstance(receipt_data, dict) and "data" in receipt_data:
        receipt_data = receipt_data["data"]
    
    assert "store_name" in receipt_data
    assert "items" in receipt_data
    assert len(receipt_data["items"]) > 0

def test_upload_receipt_invalid_format():
    """Test receipt upload with invalid format"""
    response = client.post(
        "/api/v2/receipts/upload",
        files={"file": ("receipt.txt", BytesIO(b"not an image"), "text/plain")}
    )
    
    # Verify response
    assert response.status_code == 400
    data = response.json()
    assert "error_code" in data
    assert "Unsupported file type" in data["message"]

def test_upload_receipt_empty_file(mock_ocr_agent):
    """Test receipt upload with empty file"""
    response = client.post(
        "/api/v2/receipts/upload",
        files={"file": ("receipt.jpg", BytesIO(b""), "image/jpeg")}
    )
    
    # Verify response is an error
    assert response.status_code in [400, 422]
    
@pytest.mark.asyncio
async def test_receipt_to_db_integration():
    """Test integration between OCR and database storage"""
    mock_db = MagicMock()
    mock_db.add = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    # Create a mock agent response with sample receipt data
    ocr_result = AgentResponse(
        success=True,
        text="Receipt processed",
        data={
            "store_name": "LIDL",
            "date": "2023-06-20",
            "total": 156.78,
            "items": [
                {"name": "Chleb pszenny", "price": 4.99, "quantity": 1},
                {"name": "Mleko UHT 3.2%", "price": 3.49, "quantity": 2},
                {"name": "Jabłka", "price": 2.99, "quantity": 1.5},
            ]
        }
    )
    
    # Mock the shopping service
    with patch("backend.services.shopping_service.add_receipt_to_db") as mock_add_receipt:
        mock_add_receipt.return_value = (True, 1, ["Chleb pszenny", "Mleko UHT 3.2%", "Jabłka"])
        
        # Mock the agent process
        with patch("backend.agents.agent_factory.AgentFactory.get_agent") as mock_factory:
            mock_agent = MagicMock()
            mock_agent.process = AsyncMock(return_value=ocr_result)
            mock_factory.return_value = mock_agent
            
            # Integration test would call the service here
            from backend.services.shopping_service import process_receipt_upload
            result = await process_receipt_upload(BytesIO(b"fake image data"), "image/jpeg", mock_db)
            
            # Verify the result
            assert result["success"] is True
            assert "receipt_id" in result
            assert "products" in result
            assert len(result["products"]) == 3

if __name__ == "__main__":
    pytest.main(["-v", "test_receipt_processing.py"]) 