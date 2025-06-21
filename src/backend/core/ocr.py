import io
import logging
import tempfile
import tracemalloc
from typing import Any, Dict, List, Optional

import fitz  # Import biblioteki PyMuPDF
import pytesseract
from PIL import Image
from pydantic import BaseModel

from backend.core.decorators import handle_exceptions

logger = logging.getLogger(__name__)


class OCRResult(BaseModel):
    """Model wyniku OCR"""

    text: str
    confidence: float
    metadata: Dict[str, Any] = {}


class OCRProcessor:
    """Główna klasa do przetwarzania OCR"""

    def __init__(
        self, languages: List[str] = ["pol"], tesseract_config: Optional[str] = None
    ):
        self.languages = languages
        self.default_config = tesseract_config or r"--oem 3 --psm 4"

    def _get_tesseract_config(self) -> str:
        """Generuje konfigurację Tesseract z uwzględnieniem języków"""
        lang_part = f"-l {'+'.join(self.languages)}" if self.languages else ""
        return f"{self.default_config} {lang_part}"

    def process_image(
        self, image_bytes: bytes, config: Optional[str] = None
    ) -> OCRResult:
        """Przetwarza obraz na tekst z context managerem"""
        try:
            with Image.open(io.BytesIO(image_bytes)) as image:
                config = config or self._get_tesseract_config()
                data = pytesseract.image_to_data(
                    image, config=config, output_type=pytesseract.Output.DICT
                )

                text = "\n".join([line for line in data["text"] if line.strip()])
                avg_conf = (
                    sum(conf for conf in data["conf"] if conf > 0) / len(data["conf"])
                    if data["conf"]
                    else 0
                )

                return OCRResult(
                    text=text,
                    confidence=avg_conf,
                    metadata={
                        "source": "image",
                        "pages": 1,
                        "language": self.languages[0] if self.languages else "unknown",
                    },
                )
        except Exception as e:
            logger.error(f"OCR image processing error: {e}")
            return OCRResult(text="", confidence=0, metadata={"error": str(e)})

    def process_pdf(self, pdf_bytes: bytes, config: Optional[str] = None) -> OCRResult:
        """Przetwarza plik PDF na tekst z context managerem i cleanup"""
        try:
            full_text = []
            with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(pdf_bytes)
                tmp_pdf.flush()
                pdf_document = fitz.open(tmp_pdf.name)

                for page_num in range(len(pdf_document)):
                    page = pdf_document.load_page(page_num)
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    with Image.frombytes(
                        "RGB", (pix.width, pix.height), pix.samples
                    ) as image:
                        page_result = self.process_image(image.tobytes(), config=config)
                        full_text.append(page_result.text)

            return OCRResult(
                text="\n".join(full_text),
                confidence=0,  # PDF confidence calculation would be more complex
                metadata={
                    "source": "pdf",
                    "pages": len(full_text),
                    "language": self.languages[0] if self.languages else "unknown",
                },
            )
        except Exception as e:
            logger.error(f"OCR PDF processing error: {e}")
            return OCRResult(text="", confidence=0, metadata={"error": str(e)})

    def process_images_batch(
        self, images: List[bytes], config: Optional[str] = None
    ) -> List[OCRResult]:
        """Batch processing obrazów z monitoringiem pamięci"""
        tracemalloc.start()
        results = []
        for img_bytes in images:
            result = self.process_image(img_bytes, config=config)
            results.append(result)
        current, peak = tracemalloc.get_traced_memory()
        logger.info(
            f"OCR batch images: memory usage={current/1024/1024:.2f}MB, peak={peak/1024/1024:.2f}MB"
        )
        tracemalloc.stop()
        return results

    def process_pdfs_batch(
        self, pdfs: List[bytes], config: Optional[str] = None
    ) -> List[OCRResult]:
        """Batch processing PDF z monitoringiem pamięci"""
        tracemalloc.start()
        results = []
        for pdf_bytes in pdfs:
            result = self.process_pdf(pdf_bytes, config=config)
            results.append(result)
        current, peak = tracemalloc.get_traced_memory()
        logger.info(
            f"OCR batch PDFs: memory usage={current/1024/1024:.2f}MB, peak={peak/1024/1024:.2f}MB"
        )
        tracemalloc.stop()
        return results


@handle_exceptions(max_retries=1)
def _extract_text_from_image_obj(
    image: Image.Image, config: Optional[str] = None
) -> str:
    """
    Prywatna funkcja pomocnicza, która wykonuje OCR na obiekcie obrazu PIL.
    """
    custom_config = config or r"--oem 3 --psm 4 -l pol"
    return pytesseract.image_to_string(image, config=custom_config)


@handle_exceptions(max_retries=1, retry_delay=0.5)
def process_image_file(
    file_bytes: bytes, config: Optional[str] = None
) -> Optional[str]:
    """
    Przetwarza plik obrazu (jpg, png) i wyciąga z niego tekst.
    """
    try:
        logger.info("OCR: Rozpoczynam odczyt pliku obrazu...")
        with Image.open(io.BytesIO(file_bytes)) as image:
            text = _extract_text_from_image_obj(image, config=config)
        logger.info("OCR: Odczyt obrazu zakończony sukcesem.")
        return text
    except Exception as e:
        logger.error(f"Błąd podczas przetwarzania obrazu: {e}")
        return None


@handle_exceptions(max_retries=1, retry_delay=1.0)
def process_pdf_file(file_bytes: bytes, config: Optional[str] = None) -> Optional[str]:
    """
    Przetwarza plik PDF, konwertując każdą stronę na obraz i odczytując tekst.
    """
    try:
        logger.info("OCR: Rozpoczynam odczyt pliku PDF...")
        full_text = []
        with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as tmp_pdf:
            tmp_pdf.write(file_bytes)
            tmp_pdf.flush()
            pdf_document = fitz.open(tmp_pdf.name)

            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                with Image.frombytes(
                    "RGB", (pix.width, pix.height), pix.samples
                ) as image:
                    page_text = _extract_text_from_image_obj(image, config=config)
                    full_text.append(page_text)

        logger.info(
            f"OCR: Odczyt PDF (stron: {len(pdf_document)}) zakończony sukcesem."
        )
        return "\n".join(full_text)

    except Exception as e:
        logger.error(f"Błąd podczas przetwarzania PDF: {e}")
        return None
