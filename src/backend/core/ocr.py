import io
import logging
from typing import Optional, Tuple, cast

import fitz  # Import biblioteki PyMuPDF
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


def _extract_text_from_image_obj(image: Image.Image) -> str:
    """
    Prywatna funkcja pomocnicza, która wykonuje OCR na obiekcie obrazu PIL.
    """
    custom_config = r"--oem 3 --psm 4 -l pol"
    return pytesseract.image_to_string(image, config=custom_config)


def process_image_file(file_bytes: bytes) -> Optional[str]:
    """
    Przetwarza plik obrazu (jpg, png) i wyciąga z niego tekst.
    """
    try:
        logger.info("OCR: Rozpoczynam odczyt pliku obrazu...")
        image = Image.open(io.BytesIO(file_bytes))
        text = _extract_text_from_image_obj(image)
        logger.info("OCR: Odczyt obrazu zakończony sukcesem.")
        return text
    except Exception as e:
        logger.error(f"Błąd podczas przetwarzania obrazu: {e}")
        return None


def process_pdf_file(file_bytes: bytes) -> Optional[str]:
    """
    Przetwarza plik PDF, konwertując każdą stronę na obraz i odczytując tekst.
    """
    try:
        logger.info("OCR: Rozpoczynam odczyt pliku PDF...")
        full_text = []
        # Otwieramy dokument PDF z bajtów
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")

        # Iterujemy po każdej stronie dokumentu
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            # Konwertujemy stronę na obraz (pixmap)
            pix = page.get_pixmap(matrix=cast(fitz.Matrix, fitz.Matrix(2, 2)))
            # Tworzymy obiekt obrazu PIL z pixmapa
            img_size: Tuple[int, int] = (pix.width, pix.height)
            image = Image.frombytes("RGB", img_size, pix.samples)

            # Używamy naszej funkcji do odczytu tekstu z obrazu strony
            page_text = _extract_text_from_image_obj(image)
            full_text.append(page_text)

        logger.info(
            f"OCR: Odczyt PDF (stron: {len(pdf_document)}) zakończony sukcesem."
        )
        return "\n".join(full_text)

    except Exception as e:
        logger.error(f"Błąd podczas przetwarzania PDF: {e}")
        return None
