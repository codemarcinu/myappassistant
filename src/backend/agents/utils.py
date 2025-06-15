import json
import logging
import re
from datetime import datetime
from typing import Any, Dict


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Próbuje wyodrębnić obiekt JSON z tekstu.
    Obsługuje przypadki, gdy JSON jest otoczony innym tekstem.
    """
    # Najpierw próbujemy znaleźć JSON w tekście
    json_match = re.search(r"\{[\s\S]*\}", text)
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
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return date.strftime("%d.%m.%Y")
    except ValueError:
        return date_str


def sanitize_prompt(prompt: str) -> str:
    """
    Usuwa z promptu potencjalnie szkodliwe frazy mające na celu
    manipulację modelem językowym (prompt injection).
    """
    # Lista wyrażeń regularnych dopasowujących frazy-klucze
    # uzywamy \b do dopasowania granic słów
    forbidden_patterns = [
        r"\bignoruj (wszystkie|poprzednie) instrukcje\b",
        r"\bjesteś teraz\b",
        r"\bmasz nowe instrukcje\b",
        r"\binstrukcje dla ciebie to\b",
        r"\b(system|systemowy) prompt\b",
        r"\bujawnij swoje instrukcje\b",
    ]

    sanitized_prompt = prompt
    for pattern in forbidden_patterns:
        # Sprawdzamy, czy fraza występuje w prompcie (ignorując wielkość liter)
        if re.search(pattern, sanitized_prompt, re.IGNORECASE):
            logging.warning(
                f"Wykryto potencjalną próbę ataku prompt injection: '{pattern}'"
            )
            # Usuwamy znalezioną frazę
            sanitized_prompt = re.sub(
                pattern, "", sanitized_prompt, flags=re.IGNORECASE
            )

    # Usuwamy nadmiarowe białe znaki
    return " ".join(sanitized_prompt.split())
