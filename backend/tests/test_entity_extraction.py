import asyncio
import json
import os
from typing import Any, List

import pytest

from backend.agents.prompts import get_entity_extraction_prompt
from backend.agents.tools import generate_clarification_question_text
from backend.agents.utils import extract_json_from_text
from backend.config import settings
from backend.core import crud
from backend.core.database import AsyncSessionLocal
from backend.core.llm_client import llm_client
from backend.models.shopping import Product, ShoppingTrip

# Ladowanie danych testowych bezposrednio z pliku JSON
TEST_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "tests", "fixtures", "test_data.json"
)
with open(TEST_DATA_PATH, "r") as f:
    TEST_DATA = json.load(f)

# --- NOWA FUNKCJA GENERUJĄCA PYTANIE ---
def generate_clarification_question(options: List[Any]) -> str:
    """
    Na podstawie listy potencjalnych obiektów, generuje pytanie do użytkownika.
    """
    if not options:
        return "Coś poszło nie tak, nie mam opcji do wyboru."

    # Krok 1: Stwórz czytelne opisy opcji
    formatted_options = []
    for i, obj in enumerate(options, 1):
        if isinstance(obj, ShoppingTrip):
            formatted_options.append(
                f"{i}. Paragon ze sklepu '{obj.store_name}' " f"z dnia {obj.trip_date}."
            )
        elif isinstance(obj, Product):
            formatted_options.append(
                f"{i}. Produkt '{obj.name}' w cenie {obj.unit_price} zł."
            )

    options_text = "\n".join(formatted_options)

    # Krok 2: Na razie, dla testów, zwracamy prosty, sformatowany tekst.
    # W przyszłości ten tekst można przekazać do LLM, aby ubrał go w ładniejsze zdanie.
    return f"ZNALEZIONO KILKA OPCJI. Proszę, wybierz jedną:\n{options_text}"


async def test_entity_extraction(intent: str, user_prompt: str) -> None:
    """
    Testuje pełny przepływ: ekstrakcję, wyszukiwanie i podejmowanie decyzji,
    w tym generowanie pytania doprecyzowującego.
    """
    print(f"\n--- Testuję polecenie: '{user_prompt}' (Intencja: {intent}) ---")

    try:
        # Krok 1: Ekstrakcja encji z LLM
        prompt = get_entity_extraction_prompt(user_prompt, intent)
        messages = [
            {
                "role": "system",
                "content": "Jesteś precyzyjnym systemem ekstrakcji encji. Zawsze zwracaj tylko JSON.",
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
        cleaned_json_string = extract_json_from_text(raw_response)

        if not cleaned_json_string:
            print("Błąd: Nie znaleziono obiektu JSON w odpowiedzi modelu.")
            return

        parsed_json = json.loads(cleaned_json_string)
        print("Krok 1: Ekstrakcja danych z LLM zakończona sukcesem.")
        print(json.dumps(parsed_json, indent=2, ensure_ascii=False))

        # Krok 2: Wyszukiwanie w bazie i logika decyzyjna
        print("\nKrok 2: Wyszukiwanie rekordów w bazie danych...")
        async with AsyncSessionLocal() as db:
            znalezione_obiekty = []
            # NOWA LOGIKA: Sprawdzamy, czy to intencja CZYTAJ_PODSUMOWANIE
            if intent == "CZYTAJ_PODSUMOWANIE":
                print("\nKrok 2: Wykonywanie zapytania analitycznego...")
                wyniki_analizy = await crud.get_summary(db, query_params=parsed_json)
                print("REZULTAT KOŃCOWY: Otrzymano wyniki analizy.")
                for row in wyniki_analizy:
                    print(f" - {row}")
            elif intent == "DODAJ_ZAKUPY":
                print("\nKrok 2: Tworzenie nowych rekordów w bazie danych...")
                nowy_paragon = await crud.create_shopping_trip(db, data=parsed_json)
                print(f"REZULTAT KOŃCOWY: UTWORZONO -> {nowy_paragon}")
            elif intent in ["UPDATE_ITEM", "DELETE_ITEM"]:
                znalezione_obiekty = await crud.find_item_for_action(
                    db, entities=parsed_json
                )
            elif intent in ["UPDATE_PURCHASE", "DELETE_PURCHASE"]:
                znalezione_obiekty = await crud.find_purchase_for_action(
                    db, entities=parsed_json
                )

            # Istniejąca logika decyzyjna dla pozostałych intencji
            if intent not in ["CZYTAJ_PODSUMOWANIE", "DODAJ_ZAKUPY"]:
                if len(znalezione_obiekty) == 1:
                    print(
                        f"REZULTAT WYSZUKIWANIA: Znaleziono 1 jednoznaczny obiekt: "
                        f"{znalezione_obiekty[0]}"
                    )
                    print("Akcja może zostać wykonana.")
                elif len(znalezione_obiekty) > 1:
                    print(
                        f"REZULTAT WYSZUKIWANIA: Znaleziono {len(znalezione_obiekty)} "
                        "pasujących obiektów. Wynik jest niejednoznaczny."
                    )
                    pytanie_do_uzytkownika = generate_clarification_question(
                        znalezione_obiekty
                    )
                    print("\n--- Agent zadałby teraz pytanie: ---")
                    print(pytanie_do_uzytkownika)
                    print("------------------------------------")
                else:
                    print(
                        "REZULTAT WYSZUKIWANIA: Nie znaleziono żadnych "
                        "pasujących obiektów."
                    )
                    print("Agent powinien poinformować użytkownika o niepowodzeniu.")

    except Exception as e:
        print(f"Wystąpił krytyczny błąd: {e}")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "intent, user_prompt",
    [(item["intent"], item["prompt"]) for item in TEST_DATA],
)
async def test_entity_extraction_parametrized(intent: str, user_prompt: str) -> None:
    """
    Testuje pełny przepływ: ekstrakcję, wyszukiwanie i podejmowanie decyzji,
    w tym generowanie pytania doprecyzowującego.
    """
    print(f"\n--- Testuję polecenie: '{user_prompt}' (Intencja: {intent}) ---")

    try:
        # Krok 1: Ekstrakcja encji z LLM
        prompt = get_entity_extraction_prompt(user_prompt, intent)
        messages = [
            {
                "role": "system",
                "content": "Jesteś precyzyjnym systemem ekstrakcji encji. Zawsze zwracaj tylko JSON.",
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
        cleaned_json_string = extract_json_from_text(raw_response)

        assert cleaned_json_string is not None, "Nie znaleziono JSON w odpowiedzi"
        parsed_json = json.loads(cleaned_json_string)
        print("Krok 1: Ekstrakcja danych z LLM zakończona sukcesem.")
        print(json.dumps(parsed_json, indent=2, ensure_ascii=False))

        # Krok 2: Wyszukiwanie w bazie i logika decyzyjna
        print("\nKrok 2: Wyszukiwanie rekordów w bazie danych...")
        async with AsyncSessionLocal() as db:
            znalezione_obiekty = []
            if intent == "CZYTAJ_PODSUMOWANIE":
                pass
            elif intent == "DODAJ_ZAKUPY":
                pass
            elif intent in ["UPDATE_ITEM", "DELETE_ITEM", "READ_ITEM"]:
                znalezione_obiekty = await crud.find_item_for_action(
                    db, entities=parsed_json
                )
            elif intent in ["UPDATE_PURCHASE", "DELETE_PURCHASE", "READ_PURCHASE"]:
                znalezione_obiekty = await crud.find_purchase_for_action(
                    db, entities=parsed_json
                )

            if intent not in ["CZYTAJ_PODSUMOWANIE", "DODAJ_ZAKUPY"]:
                if len(znalezione_obiekty) > 1:
                    pytanie = generate_clarification_question_text(znalezione_obiekty)
                    assert pytanie is not None

    except Exception as e:
        pytest.fail(f"Wystąpił krytyczny błąd: {e}")


async def run_tests():
    """
    Uruchamia serię testów ekstrakcji encji dla różnych intencji.
    """
    print("Uruchamiam testy ekstrakcji encji...")

    test_cases = [
        # --- Testy dla UPDATE_ITEM (już działające) ---
        ("UPDATE_ITEM", "zmień cenę mleka na 3.99 w ostatnim paragonie"),
        ("UPDATE_ITEM", "popraw ilość chleba na 2 w paragonie z Lidla"),
        ("UPDATE_ITEM", "W zakupach z wczoraj przy maśle zmień rabat na 1.50 zł."),
        # --- NOWE TESTY dla DELETE_ITEM ---
        ("DELETE_ITEM", "pozbądź się wpisu o chlebie z zakupów w Biedronce"),
        ("DELETE_ITEM", "wykreśl jajka z wczorajszego paragonu"),
        # --- NOWE TESTY dla DELETE_PURCHASE ---
        ("DELETE_PURCHASE", "usuń cały paragon z wtorku"),
        ("DELETE_PURCHASE", "skasuj zakupy z Lidla z 10 czerwca"),
        # --- NOWY TEST dla UPDATE_PURCHASE ---
        ("UPDATE_PURCHASE", "w zakupach z wczoraj pomyliłem sklep, to była Biedronka"),
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

    for intent, text in test_cases:
        await test_entity_extraction(intent, text)


if __name__ == "__main__":
    # Uruchamiamy testy
    asyncio.run(run_tests())
