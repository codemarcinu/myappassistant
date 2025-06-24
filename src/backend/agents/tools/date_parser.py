from __future__ import annotations

import json
from datetime import date, timedelta

import ollama

from backend.core.utils import extract_json_from_text

# src/backend/agents/tools/date_parser.py


# Definiujemy dzisiejszą datę jako punkt odniesienia dla LLM
# W prawdziwej aplikacji moglibyśmy ją dynamicznie aktualizować.
TODAY = date(2025, 6, 15)

# Stworzymy bardziej zaawansowany prompt, który prosi o odpowiedź w formacie JSON.
# To ułatwi nam parsowanie wyniku.
PROMPT_TEMPLATE = f"""
Twoim zadaniem jest przeanalizować tekst użytkownika i wyodrębnić z niego zakres dat.
Odpowiedź zwróć ZAWSZE w formacie JSON, zawierającym klucze 'start_date' i 'end_date' w formacie RRRR-MM-DD.
Bazuj na dzisiejszej dacie, która to: {TODAY}.

Przykłady:
- Tekst: "w zeszłym tygodniu" -> start: Poniedziałek zeszłego tygodnia, end: Niedziela zeszłego tygodnia
- Tekst: "w maju" -> start: 2025-05-01, end: 2025-05-31
- Tekst: "wczoraj" -> start: {TODAY - timedelta(days=1)}, end: {TODAY - timedelta(days=1)}
- Tekst: "dzisiaj" -> start: {TODAY}, end: {TODAY}
- Tekst: "od początku miesiąca" -> start: {TODAY.replace(day=1)}, end: {TODAY}

Jeśli w tekście nie ma informacji o dacie, zwróć null dla obu wartości.

Tekst użytkownika do analizy:
"{{user_message}}"

Twój JSON:
"""


def parse_date_range_with_llm(text: str) -> dict | None:
    """
    Używa LLM do sparsowania tekstu w poszukiwaniu zakresu dat.
    """
    prompt = PROMPT_TEMPLATE.format(user_message=text)
    try:
        response = ollama.chat(
            model="mistral:latest",  # Możesz wybrać dowolny model, który dobrze radzi sobie z JSON-em
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.0},
        )
        content = response["message"]["content"]

        # Use extract_json_from_text to handle markdown and other formats
        json_str = extract_json_from_text(content)
        if json_str:
            date_range = json.loads(json_str)

            if date_range.get("start_date") and date_range.get("end_date"):
                return date_range
        else:
            print(f"No valid JSON found in date parsing response: {content}")
        return None

    except (json.JSONDecodeError, KeyError, Exception) as e:
        print(f"Błąd podczas parsowania daty z LLM: {e}")
        return None
