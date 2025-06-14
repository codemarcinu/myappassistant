import json
import re

def extract_json_from_text(text: str) -> str:
    """
    Wyszukuje i wyciąga pierwszy kompletny obiekt JSON z dłuższego tekstu.
    Obsługuje przypadki, gdy JSON jest otoczony dodatkowym tekstem lub znajduje się w blokach kodu.
    """
    # Najpierw próbujemy znaleźć JSON w blokach kodu
    json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    match = re.search(json_pattern, text, re.DOTALL)
    if match:
        return match.group(1)

    # Jeśli nie znaleziono w blokach kodu, szukamy samego obiektu JSON
    json_pattern = r'(\{.*\})'
    match = re.search(json_pattern, text, re.DOTALL)
    if match:
        try:
            # Sprawdzamy, czy to poprawny JSON
            json.loads(match.group(1))
            return match.group(1)
        except json.JSONDecodeError:
            pass

    return "" 