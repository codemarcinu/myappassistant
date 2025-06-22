import os
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.agents.interfaces import AgentResponse, BaseAgent
from backend.api.v2.exceptions import APIErrorCodes
from backend.main import app

client = TestClient(app)


class DummyAgent(BaseAgent):
    async def process(self, input_data):
        return AgentResponse(success=True, text="dummy")

    def get_metadata(self):
        return {}

    def get_dependencies(self):
        return []

    def is_healthy(self):
        return True


@pytest.fixture
def mock_ocr_agent():
    with patch("src.backend.agents.ocr_agent.OCRAgent") as mock:
        yield mock


def test_upload_receipt_success_image(mock_ocr_agent):
    """Test successful receipt upload with image"""
    mock_agent = DummyAgent()
    mock_agent.process.return_value = MagicMock(
        success=True, text="Test receipt text", message="Processed successfully"
    )
    mock_ocr_agent.return_value = mock_agent

    test_image = BytesIO(b"fake image data")
    response = client.post(
        "/api/v2/receipts/upload",
        files={"file": ("receipt.jpg", test_image, "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status_code": 200,
        "message": "Receipt processed successfully",
        "data": {"text": "Test receipt text", "message": "Processed successfully"},
    }


def test_upload_receipt_success_pdf(mock_ocr_agent):
    """Test successful receipt upload with PDF"""
    mock_agent = DummyAgent()
    mock_agent.process.return_value = MagicMock(
        success=True, text="Test PDF receipt", message="PDF processed"
    )
    mock_ocr_agent.return_value = mock_agent

    test_pdf = BytesIO(b"fake pdf data")
    response = client.post(
        "/api/v2/receipts/upload",
        files={"file": ("receipt.pdf", test_pdf, "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json()["data"]["text"] == "Test PDF receipt"


def test_upload_receipt_missing_content_type():
    """Test missing content type header"""
    response = client.post(
        "/api/v2/receipts/upload", files={"file": ("receipt.jpg", b"fake data")}
    )

    assert response.status_code == 400
    assert response.json() == {
        "status_code": 400,
        "error_code": APIErrorCodes.INVALID_INPUT,
        "message": "Missing content type header",
        "details": {"field": "file", "error": "Content-Type header is required"},
    }


def test_upload_receipt_unsupported_type():
    """Test unsupported file type"""
    test_file = BytesIO(b"fake data")
    response = client.post(
        "/api/v2/receipts/upload",
        files={"file": ("receipt.txt", test_file, "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == APIErrorCodes.INVALID_INPUT
    assert "Unsupported file type" in response.json()["message"]


def test_upload_receipt_processing_error(mock_ocr_agent):
    """Test receipt processing failure"""
    mock_agent = DummyAgent()
    mock_agent.process.return_value = MagicMock(
        success=False, error="OCR processing failed"
    )
    mock_ocr_agent.return_value = mock_agent

    test_image = BytesIO(b"fake image data")
    response = client.post(
        "/api/v2/receipts/upload",
        files={"file": ("receipt.jpg", test_image, "image/jpeg")},
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == APIErrorCodes.RECEIPT_PROCESSING_ERROR


def test_upload_receipt_internal_error(mock_ocr_agent):
    """Test unexpected internal error"""
    mock_agent = DummyAgent()
    mock_agent.process.side_effect = Exception("Unexpected error")
    mock_ocr_agent.return_value = mock_agent

    test_image = BytesIO(b"fake image data")
    response = client.post(
        "/api/v2/receipts/upload",
        files={"file": ("receipt.jpg", test_image, "image/jpeg")},
    )

    assert response.status_code == 500
    assert response.json()["error_code"] == APIErrorCodes.INTERNAL_ERROR


@pytest.mark.integration
def test_receipt_upload_ocr():
    fixture_path = "tests/fixtures/test_receipt.jpg"
    if not os.path.exists(fixture_path):
        pytest.skip("Brak pliku testowego paragonu.")
    with open(fixture_path, "rb") as f:
        response = client.post(
            "/api/v2/receipts/upload", files={"file": ("receipt.jpg", f, "image/jpeg")}
        )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data and "text" in data["data"]
    assert len(data["data"]["text"]) > 0


@pytest.mark.integration
def test_receipt_analyze():
    ocr_text = """LIDL 2024-06-01\nChleb 4.99\nMleko 3.49\nSUMA 8.48"""
    response = client.post("/api/v2/receipts/analyze", data={"ocr_text": ocr_text})
    assert response.status_code == 200
    data = response.json()
    assert "data" in data and "items" in data["data"]
    assert data["data"]["store_name"]
    assert data["data"]["total"] > 0


@pytest.mark.integration
def test_receipt_save():
    payload = {
        "trip_date": "2024-06-01",
        "store_name": "LIDL",
        "total_amount": 8.48,
        "products": [
            {
                "name": "Chleb",
                "quantity": 1,
                "unit": "szt.",
                "price": 4.99,
                "category": "pieczywo",
            },
            {
                "name": "Mleko",
                "quantity": 1,
                "unit": "l",
                "price": 3.49,
                "category": "nabiał",
            },
        ],
    }
    response = client.post("/api/v2/receipts/save", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["products_count"] == 2


@pytest.mark.integration
def test_receipt_full_flow():
    # 1. Upload OCR
    fixture_path = "tests/fixtures/test_receipt.jpg"
    if not os.path.exists(fixture_path):
        pytest.skip("Brak pliku testowego paragonu.")
    with open(fixture_path, "rb") as f:
        upload_resp = client.post(
            "/api/v2/receipts/upload", files={"file": ("receipt.jpg", f, "image/jpeg")}
        )
    assert upload_resp.status_code == 200
    ocr_text = upload_resp.json()["data"]["text"]
    # 2. Analiza
    analyze_resp = client.post("/api/v2/receipts/analyze", data={"ocr_text": ocr_text})
    assert analyze_resp.status_code == 200
    data = analyze_resp.json()["data"]
    # 3. Zapis
    payload = {
        "trip_date": data.get("date") or "2024-06-01",
        "store_name": data.get("store_name") or "LIDL",
        "total_amount": data.get("total") or 0,
        "products": [
            {
                "name": p["name"],
                "quantity": p.get("quantity", 1),
                "unit_price": p.get("price", 0),
                "category": p.get("category", "inne"),
            }
            for p in data.get("items", [])
        ],
    }
    save_resp = client.post("/api/v2/receipts/save", json=payload)
    assert save_resp.status_code == 200
    save_data = save_resp.json()["data"]
    assert save_data["products_count"] == len(payload["products"])
