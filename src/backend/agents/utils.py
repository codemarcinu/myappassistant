import json
import logging
import re
from datetime import datetime
from typing import Any, Dict


def extract_json_from_text(text: str) -> str | None:
    """
    Próbuje wyodrębnić obiekt JSON z tekstu.
    Obsługuje przypadki, gdy JSON jest otoczony innym tekstem.
    Zwraca string JSON lub None jeśli nie znaleziono poprawnego JSON.
    """
    if not text:
        return None

    # First try to find JSON in markdown code blocks
    match = re.search(r"```json\s*({.*?})\s*```", text, re.DOTALL)
    if not match:
        match = re.search(r"```\s*({.*?})\s*```", text, re.DOTALL)

    if match:
        json_candidate = match.group(1)
        # Use the helper function to find complete JSON
        json_str = _find_complete_json(json_candidate)
        if json_str:
            try:
                json.loads(json_str)
                return json_str
            except Exception:
                pass

    # If no markdown block found or invalid, search for JSON in the entire text
    # Find the first opening brace
    start_pos = text.find("{")
    if start_pos == -1:
        return None

    # Use the helper function to find complete JSON starting from the first brace
    json_str = _find_complete_json(text[start_pos:])
    if json_str:
        try:
            json.loads(json_str)
            return json_str
        except Exception:
            pass

    return None


def _find_complete_json(text: str) -> str | None:
    """
    Znajduje kompletny JSON w tekście, obsługując zagnieżdżone struktury.
    """
    if not text or not text.strip().startswith("{"):
        return None

    brace_count = 0
    in_string = False
    escape_next = False
    start_pos = text.find("{")

    for i, char in enumerate(text[start_pos:], start_pos):
        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if not in_string:
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    # Znaleziono kompletny JSON
                    return text[start_pos : i + 1]

    return None


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
