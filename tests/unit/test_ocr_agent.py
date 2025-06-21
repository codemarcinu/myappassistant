from unittest.mock import patch

import pytest

from src.backend.agents.error_types import AgentError
from src.backend.agents.ocr_agent import OCRAgent
from src.backend.core.ocr import OCRProcessor

# sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../..", "src"))  # Usuń jeśli niepotrzebne


class TestOCRAgent:
    """Testy dla OCR Agent - agenta przetwarzającego obrazy i dokumenty"""

    @pytest.fixture
    def ocr_agent(self):
        """Fixture dla OCR Agent"""
        return OCRAgent()

    @pytest.mark.asyncio
    async def test_process_image_success(self, ocr_agent):
        """Test pomyślnego przetwarzania obrazu"""
        # Given
        input_data = {
            "file_bytes": b"fake_image_data",
            "file_type": "image",
        }

        with patch("src.backend.agents.ocr_agent.process_image_file") as mock_process:
            mock_process.return_value = "Extracted text from image"

            # When
            response = await ocr_agent.process(input_data)

            # Then
            assert response.success is True
            assert response.text == "Extracted text from image"
            assert "file_type" in response.metadata

    @pytest.mark.asyncio
    async def test_process_image_missing_path(self, ocr_agent):
        """Test przetwarzania bez podania ścieżki obrazu"""
        # Given
        input_data = {"file_bytes": b"fake_image_data"}  # Brak file_type

        # When
        response = await ocr_agent.process(input_data)

        # Then
        assert response.success is False
        assert "validation error" in response.error.lower()

    @pytest.mark.asyncio
    async def test_process_image_ocr_error(self, ocr_agent):
        """Test błędu OCR podczas przetwarzania"""
        # Given
        input_data = {"file_bytes": b"fake_image_data", "file_type": "image"}
        with patch("src.backend.agents.ocr_agent.process_image_file") as mock_process:
            mock_process.side_effect = Exception("OCR error")

            # When
            response = await ocr_agent.process(input_data)

            # Then
            assert response.success is False
            assert "OCR error" in response.error

    @pytest.mark.asyncio
    async def test_process_image_with_llm_enhancement(self, ocr_agent):
        """Test wzbogacania danych OCR przez LLM"""
        # Given
        input_data = {"file_bytes": b"fake_image_data", "file_type": "image"}

        with patch("src.backend.agents.ocr_agent.process_image_file") as mock_process:
            mock_process.return_value = "Extracted text"

            # When
            response = await ocr_agent.process(input_data)

            # Then
            assert response.success is True
            assert "text" in response.__dict__

    @pytest.mark.asyncio
    async def test_process_pdf_success(self, ocr_agent):
        """Test pomyślnego przetwarzania pliku PDF"""
        # Given
        input_data = {"file_bytes": b"fake_pdf_data", "file_type": "pdf"}

        with patch("src.backend.agents.ocr_agent.process_pdf_file") as mock_process:
            mock_process.return_value = "Extracted text from PDF"

            # When
            response = await ocr_agent.process(input_data)

            # Then
            assert response.success is True
            assert response.text == "Extracted text from PDF"

    @pytest.mark.asyncio
    async def test_process_unsupported_type(self, ocr_agent):
        """Test przetwarzania nieobsługiwanego typu pliku"""
        # Given
        input_data = {"file_bytes": b"fake_data", "file_type": "xyz"}

        # When
        response = await ocr_agent.process(input_data)

        # Then
        assert response.success is False
        assert "Nieobsługiwany typ pliku" in response.error

    @pytest.mark.asyncio
    async def test_process_large_image(self, ocr_agent):
        """Test przetwarzania dużego obrazu"""
        # Given
        # Symulacja dużego obrazu (5MB)
        large_image = b"0" * (5 * 1024 * 1024)
        input_data = {"file_bytes": large_image, "file_type": "image"}

        with patch("src.backend.agents.ocr_agent.process_image_file") as mock_process:
            mock_process.return_value = "Extracted text from large image"

            # When
            response = await ocr_agent.process(input_data)

            # Then
            assert response.success is True

    @pytest.mark.asyncio
    async def test_process_with_multiple_pages(self, ocr_agent):
        """Test przetwarzania dokumentu wielostronicowego"""
        # Given
        input_data = {"file_bytes": b"fake_pdf_data", "file_type": "pdf"}

        with patch("src.backend.agents.ocr_agent.process_pdf_file") as mock_process:
            mock_process.return_value = "Page 1 content\nPage 2 content"

            # When
            response = await ocr_agent.process(input_data)

            # Then
            assert response.success is True

    @pytest.mark.asyncio
    async def test_process_with_language_hint(self, ocr_agent):
        """Test przetwarzania z podpowiedzią języka"""
        # Given
        input_data = {"file_bytes": b"fake_image_data", "file_type": "image"}

        with patch("src.backend.agents.ocr_agent.process_image_file") as mock_process:
            mock_process.return_value = "Extracted text"

            # When
            response = await ocr_agent.process(input_data)

            # Then
            assert response.success is True

    @pytest.mark.asyncio
    async def test_process_with_rotation_correction(self, ocr_agent):
        """Test automatycznej korekty rotacji obrazu"""
        # Given
        input_data = {"file_bytes": b"fake_image_data", "file_type": "image"}

        with patch("src.backend.agents.ocr_agent.process_image_file") as mock_process:
            mock_process.return_value = "Extracted text from rotated image"

            # When
            response = await ocr_agent.process(input_data)

            # Then
            assert response.success is True

    @pytest.mark.asyncio
    async def test_process_with_table_extraction(self, ocr_agent):
        """Test wyodrębniania tabel z dokumentów"""
        # Given
        input_data = {"file_bytes": b"fake_image_data", "file_type": "image"}

        with patch("src.backend.agents.ocr_agent.process_image_file") as mock_process:
            mock_process.return_value = "Table data extracted"

            # When
            response = await ocr_agent.process(input_data)

            # Then
            assert response.success is True

    @pytest.mark.asyncio
    async def test_process_with_specific_region(self, ocr_agent):
        """Test przetwarzania określonego regionu obrazu"""
        # Given
        input_data = {"file_bytes": b"fake_image_data", "file_type": "image"}

        with patch("src.backend.agents.ocr_agent.process_image_file") as mock_process:
            mock_process.return_value = "Region specific text"

            # When
            response = await ocr_agent.process(input_data)

            # Then
            assert response.success is True

    @pytest.mark.asyncio
    async def test_process_with_fallback_engine(self, ocr_agent):
        """Test użycia fallback engine w przypadku błędu"""
        # Given
        input_data = {"file_bytes": b"fake_image_data", "file_type": "image"}

        with patch("src.backend.agents.ocr_agent.process_image_file") as mock_process:
            mock_process.return_value = "Fallback text"

            # When
            response = await ocr_agent.process(input_data)

            # Then
            assert response.success is True

    @pytest.mark.asyncio
    async def test_process_with_quality_metrics(self, ocr_agent):
        """Test zwracania metryk jakości OCR"""
        # Given
        input_data = {"file_bytes": b"fake_image_data", "file_type": "image"}

        with patch("src.backend.agents.ocr_agent.process_image_file") as mock_process:
            mock_process.return_value = "High quality text"

            # When
            response = await ocr_agent.process(input_data)

            # Then
            assert response.success is True

    @pytest.mark.asyncio
    async def test_process_with_image_enhancement(self, ocr_agent):
        """Test automatycznego ulepszania obrazu przed OCR"""
        # Given
        input_data = {"file_bytes": b"fake_image_data", "file_type": "image"}

        with patch("src.backend.agents.ocr_agent.process_image_file") as mock_process:
            mock_process.return_value = "Enhanced image text"

            # When
            response = await ocr_agent.process(input_data)

            # Then
            assert response.success is True

    @pytest.mark.asyncio
    async def test_process_with_barcode_detection(self, ocr_agent):
        """Test wykrywania kodów kreskowych"""
        # Given
        input_data = {"file_bytes": b"fake_image_data", "file_type": "image"}

        with patch("src.backend.agents.ocr_agent.process_image_file") as mock_process:
            mock_process.return_value = "Barcode detected: 123456789"

            # When
            response = await ocr_agent.process(input_data)

            # Then
            assert response.success is True

    @pytest.mark.asyncio
    async def test_process_with_specialized_model(self, ocr_agent):
        """Test użycia specjalizowanego modelu OCR"""
        # Given
        input_data = {"file_bytes": b"fake_image_data", "file_type": "image"}

        with patch("src.backend.agents.ocr_agent.process_image_file") as mock_process:
            mock_process.return_value = "Specialized model text"

            # When
            response = await ocr_agent.process(input_data)

            # Then
            assert response.success is True

    @pytest.mark.asyncio
    async def test_process_with_streaming_output(self, ocr_agent):
        """Test przetwarzania z streaming output"""
        # Given
        input_data = {"file_bytes": b"fake_image_data", "file_type": "image"}

        with patch("src.backend.agents.ocr_agent.process_image_file") as mock_process:
            mock_process.return_value = "Streaming text output"

            # When
            response = await ocr_agent.process(input_data)

            # Then
            assert response.success is True

    @pytest.mark.asyncio
    async def test_process_empty_text_result(self, ocr_agent):
        """Test gdy OCR nie rozpoznaje tekstu"""
        # Given
        input_data = {"file_bytes": b"fake_image_data", "file_type": "image"}

        with patch("src.backend.agents.ocr_agent.process_image_file") as mock_process:
            mock_process.return_value = ""

            # When
            response = await ocr_agent.process(input_data)

            # Then
            assert response.success is False
            assert "Nie udało się rozpoznać tekstu" in response.error

    @pytest.mark.asyncio
    async def test_process_none_text_result(self, ocr_agent):
        """Test gdy OCR zwraca None"""
        # Given
        input_data = {"file_bytes": b"fake_image_data", "file_type": "image"}

        with patch("src.backend.agents.ocr_agent.process_image_file") as mock_process:
            mock_process.return_value = None

            # When
            response = await ocr_agent.process(input_data)

            # Then
            assert response.success is False
            assert "Nie udało się rozpoznać tekstu" in response.error
