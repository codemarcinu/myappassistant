from PIL import Image
import pytesseract
import io
from typing import Optional

def extract_text_from_image(image_bytes: bytes) -> Optional[str]:
    """
    Używa Tesseract OCR do wyciągnięcia tekstu z obrazu.
    
    Args:
        image_bytes: Obraz w formie bajtów (otrzymany z file_uploader'a).

    Returns:
        Odczytany tekst lub None w przypadku błędu.
    """
    try:
        print("OCR: Rozpoczynam odczyt obrazu...")
        # Otwieramy obraz z bajtów przekazanych przez Streamlit
        image = Image.open(io.BytesIO(image_bytes))
        
        # Używamy Tesseracta do odczytania tekstu w języku polskim
        # Konfiguracja '--psm 4' pomaga w traktowaniu obrazu jako pojedynczej kolumny tekstu
        custom_config = r'--oem 3 --psm 4 -l pol'
        text = pytesseract.image_to_string(image, config=custom_config)
        
        print("OCR: Odczyt zakończony sukcesem.")
        return text
    except Exception as e:
        print(f"Błąd podczas przetwarzania OCR: {e}")
        return None 