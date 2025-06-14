import asyncio
import json
from typing import List, Any
from ..core.llm_client import ollama_client
from ..config import settings
from ..core import crud
from ..core.database import AsyncSessionLocal
from ..models.shopping import ShoppingTrip, Product

def extract_json_from_text(text: str) -> str:
    """
    Wyszukuje i wyciąga pierwszy kompletny obiekt JSON z dłuższego tekstu.
    """
    try:
        # Znajdź pierwszą klamrę otwierającą
        start_index = text.find('{')
        # Znajdź ostatnią klamrę zamykającą
        end_index = text.rfind('}')
        
        if start_index != -1 and end_index != -1 and end_index > start_index:
            # Wytnij tekst od pierwszej do ostatniej klamry włącznie
            return text[start_index:end_index+1]
        else:
            # Zwróć pusty string, jeśli nie znaleziono JSONa
            return ""
    except Exception:
        return ""

# Nasz "Super-Prompt" dla Agenta Ekstrakcji Danych
ENTITY_EXTRACTION_PROMPT = """Jesteś precyzyjnym agentem do ekstrakcji danych (encji) w systemie zarządzania budżetem. Twoim zadaniem jest analiza polecenia użytkownika oraz jego intencji i zwrócenie obiektu JSON z wyekstrahowanymi parametrami. Zawsze zwracaj tylko i wyłącznie obiekt JSON. Jeśli jakiejś informacji nie ma w poleceniu, użyj wartości `null`.

### Schemat Obiektu JSON do zwrotu

Twoja odpowiedź MUSI pasować do poniższego schematu, w zależności od otrzymanej intencji.

#### 1. Dla intencji: UPDATE_ITEM
```json
{
  "produkt_identyfikator": {
    "nazwa": "mleko",
    "kolejnosc": null,
    "kryterium_dodatkowe": null
  },
  "paragon_identyfikator": {
    "data": "wczoraj",
    "sklep": null,
    "kolejnosc": "ostatni"
  },
  "operacje": [
    {
      "pole_do_zmiany": "cena_jednostkowa",
      "nowa_wartosc": 3.99
    }
  ]
}
```

#### 2. Dla intencji: DELETE_ITEM
```json
{
  "produkt_identyfikator": {
    "nazwa": "masło",
    "kolejnosc": null
  },
  "paragon_identyfikator": {
    "data": null,
    "sklep": "Lidl",
    "kolejnosc": null
  }
}
```

#### 3. Dla intencji: UPDATE_PURCHASE
```json
{
  "paragon_identyfikator": {
    "data": "wczoraj",
    "sklep": null,
    "kolejnosc": "ostatni"
  },
  "operacje": [
    {
      "pole_do_zmiany": "sklep",
      "nowa_wartosc": "Biedronka"
    }
  ]
}
```

#### 4. Dla intencji: DELETE_PURCHASE
```json
{
  "paragon_identyfikator": {
    "data": "10 czerwca",
    "sklep": "Lidl",
    "kolejnosc": null
  }
}
```

#### 5. Dla intencji: DODAJ_ZAKUPY
```json
{
  "paragon_info": {
    "sklep": "Biedronka",
    "data": "dzisiaj"
  },
  "produkty": [
    {
      "nazwa_artykulu": "mleko",
      "ilosc": 2,
      "cena_jednostkowa": 4.50,
      "cena_calkowita": 9.00
    },
    {
      "nazwa_artykulu": "chleb",
      "ilosc": 1,
      "cena_jednostkowa": 5.00,
      "cena_calkowita": 5.00
    }
  ]
}
```

#### 6. Dla intencji: CZYTAJ_PODSUMOWANIE
```json
{
  "metryka": "suma_wydatkow", 
  "grupowanie": ["sklep"],
  "filtry": [
    {
      "pole": "data",
      "operator": "w_tym_miesiacu"
    },
    {
      "pole": "sklep",
      "operator": "rowna_sie",
      "wartosc": "Biedronka"
    }
  ],
  "sortowanie": {
    "pole": "suma_wydatkow",
    "kierunek": "malejaco"
  }
}
```

### Wyjaśnienie Schematu 'CZYTAJ_PODSUMOWANIE'
- `metryka`: Co liczymy? Dostępne wartości: `suma_wydatkow`, `liczba_produktow`, `srednia_cena`.
- `grupowanie`: Jak grupujemy wyniki? Jest to lista pól, np. `["sklep"]`, `["kategoria_produktu"]`.
- `filtry`: Jak zawężamy dane? Lista warunków WHERE.
  - `pole`: Nazwa pola do filtrowania (np. `data`, `sklep`, `nazwa_artykulu`).
  - `operator`: Jak filtrujemy? Np. `rowna_sie`, `zawiera`, `wieksze_niz`, `w_tym_miesiacu`, `w_zeszlym_roku`.
  - `wartosc`: Wartość dla filtra.
- `sortowanie`: Jak sortujemy wyniki?
  - `pole`: Pole do sortowania.
  - `kierunek`: `rosnaco` lub `malejaco`.

### Przykład działania
"""

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
            formatted_options.append(f"{i}. Paragon ze sklepu '{obj.store_name}' z dnia {obj.trip_date}.")
        elif isinstance(obj, Product):
            formatted_options.append(f"{i}. Produkt '{obj.name}' w cenie {obj.unit_price} zł.")
    
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
        # Krok 1: Ekstrakcja encji z LLM (pozostaje bez zmian)
        final_user_content = f"Otrzymałem polecenie od użytkownika z intencją '{intent}'. Przeanalizuj poniższe polecenie i zwróć obiekt JSON z wyekstrahowanymi encjami.\n\nPolecenie: \"{user_prompt}\""
        messages = [{'role': 'system', 'content': ENTITY_EXTRACTION_PROMPT}, {'role': 'user', 'content': final_user_content}]
        
        response = await ollama_client.chat(
            model=settings.DEFAULT_CHAT_MODEL, messages=messages, stream=False, options={'temperature': 0.0}
        )
        
        raw_response = response['message']['content']
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
                znalezione_obiekty = await crud.find_item_for_action(db, entities=parsed_json)
            elif intent in ["UPDATE_PURCHASE", "DELETE_PURCHASE"]:
                znalezione_obiekty = await crud.find_purchase_for_action(db, entities=parsed_json)

            # Istniejąca logika decyzyjna dla pozostałych intencji
            if intent not in ["CZYTAJ_PODSUMOWANIE", "DODAJ_ZAKUPY"]:
                if len(znalezione_obiekty) == 1:
                    print(f"REZULTAT WYSZUKIWANIA: Znaleziono 1 jednoznaczny obiekt: {znalezione_obiekty[0]}")
                    print("Akcja może zostać wykonana.")
                elif len(znalezione_obiekty) > 1:
                    print(f"REZULTAT WYSZUKIWANIA: Znaleziono {len(znalezione_obiekty)} pasujących obiektów. Wynik jest niejednoznaczny.")
                    pytanie_do_uzytkownika = generate_clarification_question(znalezione_obiekty)
                    print("\n--- Agent zadałby teraz pytanie: ---")
                    print(pytanie_do_uzytkownika)
                    print("------------------------------------")
                else:
                    print("REZULTAT WYSZUKIWANIA: Nie znaleziono żadnych pasujących obiektów.")
                    print("Agent powinien poinformować użytkownika o niepowodzeniu.")

    except Exception as e:
        print(f"Wystąpił krytyczny błąd: {e}")

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
        ("DODAJ_ZAKUPY", "dodaj dzisiejszy paragon z Biedronki, kupiłem 2 mleka po 4.50 i jeden chleb za 5zł"),

        # --- NOWY PRZYPADEK TESTOWY DLA ANALIZY ---
        ("CZYTAJ_PODSUMOWANIE", "ile wydałem w Biedronce w tym miesiącu, pokaż wyniki posortowane od największych")
    ]
    
    for intent, user_prompt in test_cases:
        await test_entity_extraction(intent, user_prompt)

if __name__ == "__main__":
    # Uruchamiamy testy
    asyncio.run(run_tests()) 