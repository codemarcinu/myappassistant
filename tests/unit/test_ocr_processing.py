import io
import pytest
from unittest.mock import MagicMock, patch

from PIL import Image
import pytesseract
import fitz  # PyMuPDF

from backend.core.ocr import (
    OCRProcessor, 
    OCRResult,
    process_image_file,
    process_pdf_file,
    _extract_text_from_image_obj
)


class TestOCRProcessing:
    """Unit tests for OCR processing functions with mocked image processing libraries."""

    @pytest.fixture
    def mock_image(self):
        """Create a mock PIL Image object."""
        mock_img = MagicMock(spec=Image.Image)
        mock_img.size = (100, 100)
        return mock_img

    @pytest.fixture
    def mock_tesseract_data(self):
        """Create mock tesseract output data."""
        return {
            "text": ["Sample", "receipt", "text", "Milk", "3.99", "Bread", "4.50", "Total", "8.49"],
            "conf": [90.5, 85.2, 88.7, 92.1, 87.6, 91.3, 86.8, 93.2, 89.5]
        }

    def test_extract_text_from_image_obj(self, mock_image):
        """Test the _extract_text_from_image_obj function with mocked pytesseract."""
        expected_text = "Sample receipt text\nMilk 3.99\nBread 4.50\nTotal 8.49"
        
        with patch('pytesseract.image_to_string', return_value=expected_text) as mock_image_to_string:
            result = _extract_text_from_image_obj(mock_image)
            
            # Verify the function was called with correct parameters
            mock_image_to_string.assert_called_once_with(mock_image, config=r"--oem 3 --psm 4 -l pol")
            assert result == expected_text

    def test_process_image_file(self):
        """Test the process_image_file function with mocked PIL and pytesseract."""
        sample_bytes = b"mock_image_data"
        expected_text = "Sample receipt text\nMilk 3.99\nBread 4.50\nTotal 8.49"
        
        mock_image = MagicMock()
        
        with patch('PIL.Image.open') as mock_open, \
             patch('backend.core.ocr._extract_text_from_image_obj', return_value=expected_text) as mock_extract:
            
            mock_open.return_value.__enter__.return_value = mock_image
            
            result = process_image_file(sample_bytes)
            
            # Verify the function calls
            mock_open.assert_called_once()
            mock_extract.assert_called_once_with(mock_image, config=None)
            assert result == expected_text

    def test_process_pdf_file(self):
        """Test the process_pdf_file function with mocked PyMuPDF and PIL."""
        sample_bytes = b"mock_pdf_data"
        page_text = "Page content with receipt data"
        
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_pixmap = MagicMock()
        mock_image = MagicMock()
        
        # Setup mocks for PyMuPDF objects
        mock_pdf.load_page.return_value = mock_page
        mock_page.get_pixmap.return_value = mock_pixmap
        mock_pixmap.width = 100
        mock_pixmap.height = 100
        mock_pixmap.samples = b"mock_image_data"
        
        # Set the PDF to have 2 pages
        mock_pdf.__len__ = lambda _: 2
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp, \
             patch('fitz.open', return_value=mock_pdf) as mock_open, \
             patch('PIL.Image.frombytes') as mock_frombytes, \
             patch('backend.core.ocr._extract_text_from_image_obj', return_value=page_text) as mock_extract:
            
            # Setup the context manager returns
            mock_temp.return_value.__enter__.return_value.name = "temp.pdf"
            mock_frombytes.return_value.__enter__.return_value = mock_image
            
            result = process_pdf_file(sample_bytes)
            
            # Verify function calls
            assert mock_open.called
            assert mock_pdf.load_page.call_count == 2  # Called once per page
            assert mock_page.get_pixmap.call_count == 2
            assert mock_frombytes.call_count == 2
            assert mock_extract.call_count == 2
            
            # Verify the result combines text from all pages
            assert result == f"{page_text}\n{page_text}"

    def test_ocr_processor_process_image(self, mock_tesseract_data):
        """Test OCRProcessor.process_image with mocked pytesseract."""
        sample_bytes = b"mock_image_data"
        processor = OCRProcessor(languages=["pol"])
        
        with patch('PIL.Image.open') as mock_open, \
             patch('pytesseract.image_to_data', return_value=mock_tesseract_data) as mock_image_to_data:
            
            mock_image = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_image
            
            result = processor.process_image(sample_bytes)
            
            # Verify function calls
            mock_open.assert_called_once()
            mock_image_to_data.assert_called_once()
            
            # Verify result
            assert isinstance(result, OCRResult)
            assert result.text == "\n".join(mock_tesseract_data["text"])
            # Calculate expected confidence
            expected_confidence = sum(mock_tesseract_data["conf"]) / len(mock_tesseract_data["conf"])
            assert result.confidence == expected_confidence
            assert result.metadata["source"] == "image"
            assert result.metadata["language"] == "pol"

    def test_ocr_processor_process_image_error_handling(self):
        """Test error handling in OCRProcessor.process_image."""
        sample_bytes = b"mock_image_data"
        processor = OCRProcessor()
        
        with patch('PIL.Image.open', side_effect=Exception("Mock error")):
            result = processor.process_image(sample_bytes)
            
            # Verify error handling
            assert isinstance(result, OCRResult)
            assert result.text == ""
            assert result.confidence == 0
            assert "error" in result.metadata
            assert result.metadata["error"] == "Mock error"

    def test_ocr_processor_process_pdf(self):
        """Test OCRProcessor.process_pdf with mocked PyMuPDF and PIL."""
        sample_bytes = b"mock_pdf_data"
        processor = OCRProcessor(languages=["pol"])
        
        # Create a mock for process_image that returns a known result
        mock_result = OCRResult(text="Page content", confidence=90.0, metadata={"source": "image"})
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp, \
             patch('fitz.open') as mock_open, \
             patch.object(processor, 'process_image', return_value=mock_result) as mock_process_image:
            
            # Setup mock PDF with 2 pages
            mock_pdf = MagicMock()
            mock_open.return_value = mock_pdf
            
            # Setup page mocks
            mock_page = MagicMock()
            mock_pixmap = MagicMock()
            mock_pdf.load_page.return_value = mock_page
            mock_page.get_pixmap.return_value = mock_pixmap
            mock_pixmap.width = 100
            mock_pixmap.height = 100
            mock_pixmap.samples = b"mock_image_data"
            
            # Set the PDF to have 2 pages
            mock_pdf.__len__ = lambda _: 2
            
            # Create a list of pages for iteration
            mock_pdf.__iter__ = lambda _: iter(range(2))
            
            result = processor.process_pdf(sample_bytes)
            
            # Verify function calls
            assert mock_open.called
            assert mock_pdf.load_page.call_count == 2
            assert mock_process_image.call_count == 2
            
            # Verify result
            assert isinstance(result, OCRResult)
            assert result.text == f"{mock_result.text}\n{mock_result.text}"
            assert result.metadata["source"] == "pdf"
            assert result.metadata["pages"] == 2
            assert result.metadata["language"] == "pol"

    def test_ocr_processor_process_pdf_error_handling(self):
        """Test error handling in OCRProcessor.process_pdf."""
        sample_bytes = b"mock_pdf_data"
        processor = OCRProcessor()
        
        with patch('tempfile.NamedTemporaryFile', side_effect=Exception("Mock PDF error")):
            result = processor.process_pdf(sample_bytes)
            
            # Verify error handling
            assert isinstance(result, OCRResult)
            assert result.text == ""
            assert result.confidence == 0
            assert "error" in result.metadata
            assert result.metadata["error"] == "Mock PDF error"

    def test_ocr_processor_process_images_batch(self):
        """Test OCRProcessor.process_images_batch with mocked process_image."""
        sample_bytes1 = b"mock_image_data1"
        sample_bytes2 = b"mock_image_data2"
        processor = OCRProcessor()
        
        # Create mock results
        mock_result1 = OCRResult(text="Image 1 content", confidence=91.0, metadata={"source": "image"})
        mock_result2 = OCRResult(text="Image 2 content", confidence=88.5, metadata={"source": "image"})
        
        with patch.object(processor, 'process_image', side_effect=[mock_result1, mock_result2]) as mock_process:
            results = processor.process_images_batch([sample_bytes1, sample_bytes2])
            
            # Verify function calls
            assert mock_process.call_count == 2
            assert len(results) == 2
            
            # Verify results
            assert results[0] == mock_result1
            assert results[1] == mock_result2


if __name__ == "__main__":
    pytest.main(["-v", "test_ocr_processing.py"]) 