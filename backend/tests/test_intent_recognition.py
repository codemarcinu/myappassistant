import asyncio
import json

from ..agents.prompts import get_intent_recognition_prompt
from ..config import settings
from ..core.llm_client import llm_client

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


async def run_tests():
    print("Uruchamiam testy rozpoznawania intencji...")
    test_cases = [
        # --- Testy dla UPDATE_ITEM (już działające) ---
        ("UPDATE_ITEM", "zmień cenę mleka na 3.99 w ostatnim paragonie"),
        ("UPDATE_ITEM", "popraw ilość chleba na 2 w paragonie z Lidla"),
        (
            "UPDATE_ITEM",
            "W zakupach z wczoraj przy maśle zmień rabat na 1.50 zł.",
        ),
        # --- NOWE TESTY dla DELETE_ITEM ---
        (
            "DELETE_ITEM",
            "pozbądź się wpisu o chlebie z zakupów w Biedronce",
        ),
        ("DELETE_ITEM", "wykreśl jajka z wczorajszego paragonu"),
        # --- NOWE TESTY dla DELETE_PURCHASE ---
        ("DELETE_PURCHASE", "usuń cały paragon z wtorku"),
        (
            "DELETE_PURCHASE",
            "skasuj zakupy z Lidla z 10 czerwca",
        ),
        # --- NOWY TEST dla UPDATE_PURCHASE ---
        (
            "UPDATE_PURCHASE",
            "w zakupach z wczoraj pomyliłem sklep, to była Biedronka",
        ),
        # --- NOWY TEST dla DODAJ_ZAKUPY ---
        (
            "DODAJ_ZAKUPY",
            "dodaj dzisiejszy paragon z Biedronki, kupiłem 2 mleka po 4.50 i jeden chleb za 5zł",
        ),
        # --- NOWY PRZYPADEK TESTOWY DLA ANALIZY ---
        (
            "CZYTAJ_PODSUMOWANIE",
            "ile wydałem w Biedronce w tym miesiącu, pokaż wyniki posortowane od największych",
        ),
    ]

    for test_case in test_cases:
        await test_intent_recognition(test_case[1])


if __name__ == "__main__":
    asyncio.run(run_tests())
