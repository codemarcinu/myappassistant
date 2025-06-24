"""
Testy dla ulepszonego OCR z preprocessingiem obrazów i obsługą polskich paragonów.
"""

import io
from unittest.mock import MagicMock, Mock, patch

import pytest
from PIL import Image, ImageEnhance

from backend.core.ocr import OCRProcessor, process_image_file, process_pdf_file


class TestOCREnhanced:
    """Testy dla ulepszonego OCR."""

    @pytest.fixture
    def ocr_processor(self):
        """Tworzy instancję OCRProcessor do testów."""
        return OCRProcessor()

    @pytest.fixture
    def sample_image(self):
        """Tworzy przykładowy obraz do testów."""
        # Tworzy prosty obraz testowy
        image = Image.new("RGB", (100, 100), color="white")
        return image

    @pytest.fixture
    def sample_image_bytes(self):
        """Tworzy bajty przykładowego obrazu."""
        image = Image.new("RGB", (100, 100), color="white")
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="PNG")
        return img_byte_arr.getvalue()

    def test_get_default_receipt_config(self, ocr_processor):
        """Test domyślnej konfiguracji dla paragonów."""
        config = ocr_processor._get_default_receipt_config()
        assert "--oem 3" in config
        assert "--psm 6" in config

    def test_get_tesseract_config_with_polish_chars(self, ocr_processor):
        """Test konfiguracji Tesseract z polskimi znakami."""
        config = ocr_processor._get_tesseract_config()

        # Sprawdź czy zawiera polskie znaki
        assert "ĄĆĘŁŃÓŚŹŻ" in config
        assert "ąćęłńóśźż" in config
        assert "-l pol" in config
        assert "--psm 6" in config

    def test_preprocess_receipt_image_grayscale_conversion(
        self, ocr_processor, sample_image
    ):
        """Test konwersji do skali szarości."""
        # Upewnij się że obraz jest RGB
        assert sample_image.mode == "RGB"

        processed = ocr_processor._preprocess_receipt_image(sample_image)
        assert processed.mode == "L"  # Skala szarości

    def test_preprocess_receipt_image_contrast_enhancement(
        self, ocr_processor, sample_image
    ):
        """Test zwiększenia kontrastu."""
        processed = ocr_processor._preprocess_receipt_image(sample_image)

        # Sprawdź czy obraz został przetworzony
        assert processed is not None
        assert processed.size == sample_image.size

    def test_preprocess_receipt_image_resize_small_image(self, ocr_processor):
        """Test zmiany rozmiaru małego obrazu."""
        # Tworzy mały obraz
        small_image = Image.new("RGB", (400, 300), color="white")

        processed = ocr_processor._preprocess_receipt_image(small_image)

        # Sprawdź czy obraz został powiększony
        assert processed.size[0] >= 800 or processed.size[1] >= 600

    def test_preprocess_receipt_image_error_handling(self, ocr_processor):
        """Test obsługi błędów podczas preprocessingu."""
        # Symuluj błąd podczas przetwarzania
        with patch.object(ImageEnhance, "Contrast") as mock_contrast:
            mock_contrast.side_effect = Exception("Test error")

            sample_image = Image.new("RGB", (100, 100), color="white")
            processed = ocr_processor._preprocess_receipt_image(sample_image)

            # Powinien zwrócić oryginalny obraz w przypadku błędu
            assert processed == sample_image

    @patch("backend.core.ocr.pytesseract")
    def test_process_image_with_preprocessing(
        self, mock_tesseract, ocr_processor, sample_image_bytes
    ):
        """Test przetwarzania obrazu z preprocessingiem."""
        # Mock odpowiedzi Tesseract
        mock_data = {"text": ["Test", "paragon", "tekst"], "conf": [90, 85, 80]}
        mock_tesseract.image_to_data.return_value = mock_data
        mock_tesseract.Output.DICT = "dict"

        result = ocr_processor.process_image(sample_image_bytes)

        assert result.text == "Test\nparagon\ntekst"
        assert result.confidence > 0
        assert result.metadata["preprocessing_applied"] is True

    @patch("backend.core.ocr.pytesseract")
    def test_process_image_error_handling(
        self, mock_tesseract, ocr_processor, sample_image_bytes
    ):
        """Test obsługi błędów podczas przetwarzania obrazu."""
        mock_tesseract.image_to_data.side_effect = Exception("OCR error")

        result = ocr_processor.process_image(sample_image_bytes)

        assert result.text == ""
        assert result.confidence == 0
        assert "error" in result.metadata

    @patch("backend.core.ocr.fitz")
    @patch("backend.core.ocr.pytesseract")
    def test_process_pdf_with_preprocessing(
        self, mock_tesseract, mock_fitz, ocr_processor
    ):
        """Test przetwarzania PDF z preprocessingiem."""
        # Mock PyMuPDF
        mock_doc = Mock()
        mock_page = Mock()
        mock_pix = Mock()
        mock_pix.width = 100
        mock_pix.height = 100
        mock_pix.samples = b"test_samples"

        mock_page.get_pixmap.return_value = mock_pix
        mock_doc.load_page.return_value = mock_page
        mock_doc.__len__ = Mock(return_value=1)

        mock_fitz.open.return_value = mock_doc

        # Mock Tesseract
        mock_data = {"text": ["PDF", "tekst"], "conf": [90, 85]}
        mock_tesseract.image_to_data.return_value = mock_data
        mock_tesseract.Output.DICT = "dict"

        pdf_bytes = b"fake_pdf_content"
        result = ocr_processor.process_pdf(pdf_bytes)

        assert "PDF" in result.text
        assert result.metadata["source"] == "pdf"
        assert result.metadata["pages"] == 1

    def test_process_images_batch_with_logging(self, ocr_processor):
        """Test batch processing obrazów z logowaniem."""
        images = [b"image1", b"image2", b"image3"]

        with patch.object(ocr_processor, "process_image") as mock_process:
            mock_process.return_value = Mock(text="test", confidence=90, metadata={})

            results = ocr_processor.process_images_batch(images)

            assert len(results) == 3
            mock_process.assert_called_count == 3

    def test_process_pdfs_batch_with_logging(self, ocr_processor):
        """Test batch processing PDF z logowaniem."""
        pdfs = [b"pdf1", b"pdf2"]

        with patch.object(ocr_processor, "process_pdf") as mock_process:
            mock_process.return_value = Mock(text="test", confidence=0, metadata={})

            results = ocr_processor.process_pdfs_batch(pdfs)

            assert len(results) == 2
            mock_process.assert_called_count == 2

    @patch("backend.core.ocr.pytesseract")
    def test_extract_text_from_image_obj_with_receipt_config(self, mock_tesseract):
        """Test wyciągania tekstu z obiektu obrazu z konfiguracją paragonów."""
        mock_tesseract.image_to_string.return_value = "Test paragon tekst"

        image = Image.new("RGB", (100, 100), color="white")
        text = process_image_file(image.tobytes())

        # Sprawdź czy użyto konfiguracji dla paragonów
        mock_tesseract.image_to_string.assert_called_once()
        call_args = mock_tesseract.image_to_string.call_args
        config = call_args[1]["config"]
        assert "--psm 6" in config
        assert "-l pol" in config
        assert "ĄĆĘŁŃÓŚŹŻ" in config

    @patch("backend.core.ocr.pytesseract")
    def test_process_image_file_with_preprocessing(self, mock_tesseract):
        """Test process_image_file z preprocessingiem."""
        mock_tesseract.image_to_string.return_value = "Przetworzony tekst"

        image = Image.new("RGB", (100, 100), color="white")
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="PNG")
        image_bytes = img_byte_arr.getvalue()

        text = process_image_file(image_bytes)

        assert text == "Przetworzony tekst"
        mock_tesseract.image_to_string.assert_called_once()

    @patch("backend.core.ocr.fitz")
    @patch("backend.core.ocr.pytesseract")
    def test_process_pdf_file_with_preprocessing(self, mock_tesseract, mock_fitz):
        """Test process_pdf_file z preprocessingiem."""
        mock_tesseract.image_to_string.return_value = "PDF tekst"

        # Mock PyMuPDF
        mock_doc = Mock()
        mock_page = Mock()
        mock_pix = Mock()
        mock_pix.width = 100
        mock_pix.height = 100
        mock_pix.samples = b"test_samples"

        mock_page.get_pixmap.return_value = mock_pix
        mock_doc.load_page.return_value = mock_page
        mock_doc.__len__ = Mock(return_value=1)

        mock_fitz.open.return_value = mock_doc

        pdf_bytes = b"fake_pdf_content"
        text = process_pdf_file(pdf_bytes)

        assert text == "PDF tekst"

    def test_ocr_processor_language_configuration(self):
        """Test konfiguracji języków OCR."""
        # Test z polskim i angielskim
        processor = OCRProcessor(languages=["pol", "eng"])
        config = processor._get_tesseract_config()
        assert "-l pol+eng" in config

        # Test tylko z polskim
        processor = OCRProcessor(languages=["pol"])
        config = processor._get_tesseract_config()
        assert "-l pol" in config

    def test_ocr_processor_custom_config(self):
        """Test niestandardowej konfiguracji OCR."""
        custom_config = "--oem 1 --psm 8"
        processor = OCRProcessor(tesseract_config=custom_config)

        config = processor._get_tesseract_config()
        assert custom_config in config

    @patch("backend.core.ocr.pytesseract")
    def test_ocr_confidence_calculation(
        self, mock_tesseract, ocr_processor, sample_image_bytes
    ):
        """Test obliczania confidence OCR."""
        # Mock odpowiedzi z różnymi poziomami confidence
        mock_data = {
            "text": ["Test", "paragon", "tekst"],
            "conf": [90, 85, 80],  # Średnia: 85
        }
        mock_tesseract.image_to_data.return_value = mock_data
        mock_tesseract.Output.DICT = "dict"

        result = ocr_processor.process_image(sample_image_bytes)

        assert result.confidence == 85.0

    @patch("backend.core.ocr.pytesseract")
    def test_ocr_confidence_with_zero_values(
        self, mock_tesseract, ocr_processor, sample_image_bytes
    ):
        """Test obliczania confidence z wartościami zerowymi."""
        mock_data = {"text": ["Test", "paragon"], "conf": [0, 0]}  # Wszystkie zera
        mock_tesseract.image_to_data.return_value = mock_data
        mock_tesseract.Output.DICT = "dict"

        result = ocr_processor.process_image(sample_image_bytes)

        assert result.confidence == 0

    def test_preprocessing_preserves_image_integrity(self, ocr_processor):
        """Test czy preprocessing zachowuje integralność obrazu."""
        # Tworzy obraz z określonymi wymiarami
        original_image = Image.new("RGB", (800, 600), color="white")

        processed = ocr_processor._preprocess_receipt_image(original_image)

        # Sprawdź czy obraz nie został uszkodzony
        assert processed is not None
        assert processed.size[0] > 0
        assert processed.size[1] > 0

    @patch("backend.core.ocr.pytesseract")
    def test_ocr_with_polish_receipt_text(
        self, mock_tesseract, ocr_processor, sample_image_bytes
    ):
        """Test OCR z polskim tekstem paragonu."""
        polish_text = "Lidl sp. z.o.o.\nMleko 3.2% 1L 4,99 PLN\nRAZEM 4,99 PLN"
        mock_data = {"text": polish_text.split("\n"), "conf": [95, 90, 85]}
        mock_tesseract.image_to_data.return_value = mock_data
        mock_tesseract.Output.DICT = "dict"

        result = ocr_processor.process_image(sample_image_bytes)

        assert "Lidl" in result.text
        assert "Mleko" in result.text
        assert "4,99" in result.text


if __name__ == "__main__":
    pytest.main(["-v", "test_ocr_enhanced.py"])
