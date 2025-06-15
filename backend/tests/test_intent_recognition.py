import asyncio
import json
import os

import pytest

from backend.agents.prompts import get_intent_recognition_prompt
from backend.config import settings
from backend.core.llm_client import llm_client

# Prompt systemowy pozostaje ten sam - prosty i klarowny.
SYSTEM_PROMPT = (
    "Jesteś precyzyjnym systemem klasyfikacji intencji. Twoim zadaniem jest analiza "
    "polecenia użytkownika i zwrócenie TYLKO I WYŁĄCZNIE obiektu JSON z jednym "
    "kluczem 'intencja'.\n"
    "Dostępne wartości dla klucza 'intencja' to: DODAJ_ZAKUPY, CZYTAJ_PODSUMOWANIE, "
    "UPDATE_ITEM, DELETE_ITEM, UPDATE_PURCHASE, DELETE_PURCHASE, UNKNOWN.\n"
    "Nie dodawaj żadnego tekstu przed ani po obiekcie JSON. Twoja odpowiedź musi być "
    "wyłącznie poprawnym składniowo JSON-em.\n"
)

# Ladowanie danych testowych bezposrednio z pliku JSON
TEST_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "tests", "fixtures", "test_data.json"
)
with open(TEST_DATA_PATH, "r") as f:
    TEST_DATA = json.load(f)


async def test_intent_recognition(user_prompt: str) -> None:
    print(f"\n--- Testuję polecenie: '{user_prompt}' ---")

    try:
        # Używamy promptu z modułu prompts
        prompt = get_intent_recognition_prompt(user_prompt)
        messages = [
            {
                "role": "system",
                "content": (
                    "Jesteś precyzyjnym systemem klasyfikacji intencji. "
                    "Zawsze zwracaj tylko JSON."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        response = await llm_client.chat(
            model=settings.DEFAULT_CHAT_MODEL,
            messages=messages,
            stream=False,
            options={"temperature": 0.0},
        )

        raw_response = response["message"]["content"]
        print(f"Odpowiedź modelu: {raw_response}")

        try:
            parsed_json = json.loads(raw_response.strip())
            print(
                "Rozpoznana intencja: {0}".format(
                    parsed_json.get("intent", "BRAK INTENCJI")
                )
            )
        except json.JSONDecodeError as e:
            print("Błąd: Model nie zwrócił poprawnego JSON")
            print(f"Otrzymany tekst: {raw_response}")
            print(f"Szczegóły błędu: {e}")

    except Exception as e:
        print(f"Wystąpił błąd: {e}")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_prompt, expected_intent",
    [(item["prompt"], item["intent"]) for item in TEST_DATA],
)
async def test_intent_recognition_parametrized(
    user_prompt: str, expected_intent: str
) -> None:
    print(f"\n--- Testuję polecenie: '{user_prompt}' ---")

    try:
        prompt = get_intent_recognition_prompt(user_prompt)
        messages = [
            {
                "role": "system",
                "content": "Jesteś precyzyjnym systemem klasyfikacji intencji. Zawsze zwracaj tylko JSON.",
            },
            {"role": "user", "content": prompt},
        ]

        response = await llm_client.chat(
            model=settings.DEFAULT_CHAT_MODEL,
            messages=messages,
            stream=False,
            options={"temperature": 0.0},
        )

        raw_response = response["message"]["content"]
        print(f"Odpowiedź modelu: {raw_response}")

        parsed_json = json.loads(raw_response.strip())
        recognized_intent = parsed_json.get("intent")

        assert recognized_intent == expected_intent, (
            f"Oczekiwano intencji '{expected_intent}', "
            f"a otrzymano '{recognized_intent}'"
        )

    except Exception as e:
        pytest.fail(f"Test zakończony niepowodzeniem: {e}")


if __name__ == "__main__":
    asyncio.run(test_intent_recognition_parametrized())
