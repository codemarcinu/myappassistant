import json
import re
from typing import Dict, Any

def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Próbuje wyodrębnić obiekt JSON z tekstu.
    Obsługuje przypadki, gdy JSON jest otoczony innym tekstem.
    """
    # Najpierw próbujemy znaleźć JSON w tekście
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    # Jeśli nie znaleźliśmy poprawnego JSON, zwracamy pusty słownik
    return {}

def format_price(price: float) -> str:
    """
    Formatuje cenę do wyświetlenia.
    """
    return f"{price:.2f} zł"

def format_date(date_str: str) -> str:
    """
    Formatuje datę do wyświetlenia.
    """
    try:
        from datetime import datetime
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return date.strftime("%d.%m.%Y")
    except:
        return date_str 