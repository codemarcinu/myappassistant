"""
Testy integracyjne dla ulepszonych endpointów paragonów.
"""

from io import BytesIO
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from backend.agents.interfaces import AgentResponse
from backend.main import app


class TestReceiptEndpointsEnhanced:
    """Testy dla ulepszonych endpointów paragonów."""

    @pytest.fixture
    def client(self):
        """Tworzy klienta testowego."""
        return TestClient(app)

    @pytest.fixture
    def sample_image_bytes(self):
        """Tworzy przykładowe bajty obrazu."""
        # Symuluj bajty obrazu
        return b"fake_image_bytes"

    @pytest.fixture
    def mock_ocr_response(self):
        """Mock odpowiedzi OCR."""
        return AgentResponse(
            success=True,
            text="Lidl sp. z.o.o.\nMleko 3.2% 1L 4,99 PLN\nRAZEM 4,99 PLN",
            message="OCR successful",
            metadata={"confidence": 85.5, "preprocessing_applied": True},
        )

    @pytest.fixture
    def mock_analysis_response(self):
        """Mock odpowiedzi analizy paragonu."""
        return AgentResponse(
            success=True,
            data={
                "store_name": "Lidl",
                "date": "2024-01-15",
                "items": [
                    {
                        "name": "Mleko 3.2%",
                        "quantity": 1,
                        "unit_price": 4.99,
                        "total_price": 4.99,
                        "vat_rate": "A",
                    }
                ],
                "total_amount": 4.99,
            },
        )

    @patch("backend.agents.ocr_agent.OCRAgent.process")
    @patch("backend.agents.receipt_analysis_agent.ReceiptAnalysisAgent.process")
    async def test_process_receipt_complete_success(
        self,
        mock_analysis,
        mock_ocr,
        client,
        sample_image_bytes,
        mock_ocr_response,
        mock_analysis_response,
    ):
        """Test kompletnego przetwarzania paragonu."""
        mock_ocr.return_value = mock_ocr_response
        mock_analysis.return_value = mock_analysis_response

        # Przygotuj plik do wysłania
        files = {"file": ("receipt.jpg", sample_image_bytes, "image/jpeg")}

        response = client.post("/api/v2/receipts/process", files=files)

        assert response.status_code == 200
        data = response.json()

        assert data["status_code"] == 200
        assert "Receipt processed and analyzed successfully" in data["message"]
        assert "ocr_text" in data["data"]
        assert "analysis" in data["data"]
        assert data["data"]["analysis"]["store_name"] == "Lidl"

    @patch("backend.agents.ocr_agent.OCRAgent.process")
    async def test_process_receipt_ocr_failure(
        self, mock_ocr, client, sample_image_bytes
    ):
        """Test błędu OCR podczas przetwarzania."""
        mock_ocr.return_value = AgentResponse(
            success=False, error="OCR processing failed"
        )

        files = {"file": ("receipt.jpg", sample_image_bytes, "image/jpeg")}
        response = client.post("/api/v2/receipts/process", files=files)

        assert response.status_code == 422
        data = response.json()
        assert "OCR processing failed" in data["message"]

    @patch("backend.agents.ocr_agent.OCRAgent.process")
    @patch("backend.agents.receipt_analysis_agent.ReceiptAnalysisAgent.process")
    async def test_process_receipt_analysis_failure(
        self, mock_analysis, mock_ocr, client, sample_image_bytes, mock_ocr_response
    ):
        """Test błędu analizy podczas przetwarzania."""
        mock_ocr.return_value = mock_ocr_response
        mock_analysis.return_value = AgentResponse(
            success=False, error="Analysis failed"
        )

        files = {"file": ("receipt.jpg", sample_image_bytes, "image/jpeg")}
        response = client.post("/api/v2/receipts/process", files=files)

        assert response.status_code == 422
        data = response.json()
        assert "Receipt analysis failed" in data["message"]

    def test_process_receipt_file_too_large(self, client):
        """Test obsługi zbyt dużego pliku."""
        # Symuluj duży plik
        large_file_bytes = b"x" * (11 * 1024 * 1024)  # 11MB

        files = {"file": ("large_receipt.jpg", large_file_bytes, "image/jpeg")}
        response = client.post("/api/v2/receipts/process", files=files)

        assert response.status_code == 400
        data = response.json()
        assert "File too large" in data["message"]

    def test_process_receipt_unsupported_file_type(self, client, sample_image_bytes):
        """Test obsługi nieobsługiwanego typu pliku."""
        files = {"file": ("receipt.txt", sample_image_bytes, "text/plain")}
        response = client.post("/api/v2/receipts/process", files=files)

        assert response.status_code == 400
        data = response.json()
        assert "Unsupported file type" in data["message"]

    def test_process_receipt_missing_content_type(self, client, sample_image_bytes):
        """Test obsługi braku Content-Type."""
        files = {"file": ("receipt.jpg", sample_image_bytes, None)}
        response = client.post("/api/v2/receipts/process", files=files)

        assert response.status_code == 400
        data = response.json()
        assert "Missing content type header" in data["message"]

    @patch("backend.agents.ocr_agent.OCRAgent.process")
    async def test_upload_receipt_enhanced_success(
        self, mock_ocr, client, sample_image_bytes, mock_ocr_response
    ):
        """Test ulepszonego endpointu upload."""
        mock_ocr.return_value = mock_ocr_response

        files = {"file": ("receipt.jpg", sample_image_bytes, "image/jpeg")}
        response = client.post("/api/v2/receipts/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        assert data["status_code"] == 200
        assert "metadata" in data["data"]
        assert data["data"]["metadata"]["preprocessing_applied"] is True

    @patch("backend.agents.receipt_analysis_agent.ReceiptAnalysisAgent.process")
    async def test_analyze_receipt_enhanced_success(
        self, mock_analysis, client, mock_analysis_response
    ):
        """Test ulepszonego endpointu analyze."""
        mock_analysis.return_value = mock_analysis_response

        ocr_text = "Lidl sp. z.o.o.\nMleko 3.2% 1L 4,99 PLN"
        response = client.post("/api/v2/receipts/analyze", data={"ocr_text": ocr_text})

        assert response.status_code == 200
        data = response.json()

        assert data["status_code"] == 200
        assert data["data"]["store_name"] == "Lidl"

    def test_analyze_receipt_empty_text(self, client):
        """Test analizy pustego tekstu OCR."""
        response = client.post("/api/v2/receipts/analyze", data={"ocr_text": ""})

        assert response.status_code == 400
        data = response.json()
        assert "OCR text is required" in data["message"]

    def test_analyze_receipt_whitespace_only(self, client):
        """Test analizy tekstu zawierającego tylko białe znaki."""
        response = client.post(
            "/api/v2/receipts/analyze", data={"ocr_text": "   \n\t   "}
        )

        assert response.status_code == 400
        data = response.json()
        assert "OCR text is required" in data["message"]

    @patch("backend.agents.receipt_analysis_agent.ReceiptAnalysisAgent.process")
    async def test_analyze_receipt_analysis_failure(self, mock_analysis, client):
        """Test błędu analizy paragonu."""
        mock_analysis.return_value = AgentResponse(
            success=False, error="Analysis failed"
        )

        response = client.post(
            "/api/v2/receipts/analyze", data={"ocr_text": "Test receipt text"}
        )

        assert response.status_code == 422
        data = response.json()
        assert "Failed to analyze receipt data" in data["message"]

    @patch("backend.agents.ocr_agent.OCRAgent.process")
    async def test_upload_receipt_pdf_success(
        self, mock_ocr, client, mock_ocr_response
    ):
        """Test przetwarzania pliku PDF."""
        mock_ocr.return_value = mock_ocr_response

        # Symuluj plik PDF
        pdf_bytes = b"%PDF-1.4 fake pdf content"
        files = {"file": ("receipt.pdf", pdf_bytes, "application/pdf")}

        response = client.post("/api/v2/receipts/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["status_code"] == 200

    def test_process_receipt_pdf_success(self, client):
        """Test kompletnego przetwarzania pliku PDF."""
        pdf_bytes = b"%PDF-1.4 fake pdf content"
        files = {"file": ("receipt.pdf", pdf_bytes, "application/pdf")}

        with patch("backend.agents.ocr_agent.OCRAgent.process") as mock_ocr:
            mock_ocr.return_value = AgentResponse(
                success=True,
                text="PDF OCR text",
                metadata={"source": "pdf", "pages": 1},
            )

        with patch(
            "backend.agents.receipt_analysis_agent.ReceiptAnalysisAgent.process"
        ) as mock_analysis:
            mock_analysis.return_value = AgentResponse(
                success=True, data={"store_name": "Test Store", "total_amount": 10.0}
            )

            response = client.post("/api/v2/receipts/process", files=files)

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["metadata"]["file_type"] == "pdf"

    @patch("backend.agents.ocr_agent.OCRAgent.process")
    async def test_upload_receipt_ocr_failure_enhanced(
        self, mock_ocr, client, sample_image_bytes
    ):
        """Test ulepszonej obsługi błędu OCR."""
        mock_ocr.return_value = AgentResponse(
            success=False, error="OCR processing failed"
        )

        files = {"file": ("receipt.jpg", sample_image_bytes, "image/jpeg")}
        response = client.post("/api/v2/receipts/upload", files=files)

        assert response.status_code == 422
        data = response.json()
        assert "Failed to process receipt" in data["message"]
        assert "RECEIPT_PROCESSING_ERROR" in data["details"]["error_code"]

    def test_process_receipt_exception_handling(self, client, sample_image_bytes):
        """Test obsługi wyjątków podczas przetwarzania."""
        files = {"file": ("receipt.jpg", sample_image_bytes, "image/jpeg")}

        with patch("backend.agents.ocr_agent.OCRAgent.process") as mock_ocr:
            mock_ocr.side_effect = Exception("Unexpected error")

            response = client.post("/api/v2/receipts/process", files=files)

            assert response.status_code == 500
            data = response.json()
            assert "INTERNAL_SERVER_ERROR" in data["error_code"]

    @patch("backend.agents.ocr_agent.OCRAgent.process")
    async def test_upload_receipt_with_metadata(
        self, mock_ocr, client, sample_image_bytes, mock_ocr_response
    ):
        """Test endpointu upload z metadanymi."""
        mock_ocr.return_value = mock_ocr_response

        files = {"file": ("receipt.jpg", sample_image_bytes, "image/jpeg")}
        response = client.post("/api/v2/receipts/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        # Sprawdź czy metadane są zwracane
        assert "metadata" in data["data"]
        metadata = data["data"]["metadata"]
        assert "confidence" in metadata
        assert "preprocessing_applied" in metadata

    def test_process_receipt_workflow_steps(self, client):
        """Test kroków workflow przetwarzania paragonu."""
        pdf_bytes = b"%PDF-1.4 fake pdf content"
        files = {"file": ("receipt.pdf", pdf_bytes, "application/pdf")}

        with patch("backend.agents.ocr_agent.OCRAgent.process") as mock_ocr:
            mock_ocr.return_value = AgentResponse(
                success=True, text="OCR text", confidence=85.5
            )

        with patch(
            "backend.agents.receipt_analysis_agent.ReceiptAnalysisAgent.process"
        ) as mock_analysis:
            mock_analysis.return_value = AgentResponse(
                success=True, data={"store_name": "Test", "total_amount": 10.0}
            )

            response = client.post("/api/v2/receipts/process", files=files)

            assert response.status_code == 200
            data = response.json()

            # Sprawdź kroki przetwarzania
            processing_steps = data["data"]["metadata"]["processing_steps"]
            assert "ocr" in processing_steps
            assert "analysis" in processing_steps
            assert len(processing_steps) == 2


if __name__ == "__main__":
    pytest.main(["-v", "test_receipt_endpoints_enhanced.py"])
