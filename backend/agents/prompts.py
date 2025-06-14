def get_intent_recognition_prompt(user_command: str) -> str:
    """
    Generuje prompt do rozpoznawania intencji z polecenia użytkownika.
    """
    return f"""Przeanalizuj poniższe polecenie użytkownika i określ jego intencję.
Dostępne intencje:
- DODAJ_ZAKUPY: dodawanie nowego paragonu/zakupów
- CZYTAJ_PODSUMOWANIE: wyświetlanie podsumowania/zestawienia
- UPDATE_ITEM: aktualizacja produktu
- DELETE_ITEM: usuwanie produktu
- UPDATE_PURCHASE: aktualizacja paragonu
- DELETE_PURCHASE: usuwanie paragonu
- UNKNOWN: nieznana intencja

Polecenie użytkownika: "{user_command}"

Odpowiedz w formacie JSON:
{{
    "intent": "WYBRANA_INTENCJA",
    "confidence": 0.95  // pewność rozpoznania (0-1)
}}
"""

def get_entity_extraction_prompt(user_command: str, intent: str) -> str:
    """
    Generuje prompt do ekstrakcji encji z polecenia użytkownika.
    WERSJA FINALNA z rozbudowanymi przykładami (few-shot).
    """
    return f"""Jesteś precyzyjnym agentem do ekstrakcji danych (encji) w systemie zarządzania budżetem. Twoim zadaniem jest analiza polecenia użytkownika oraz jego intencji i zwrócenie obiektu JSON z wyekstrahowanymi parametrami. Zawsze zwracaj tylko i wyłącznie obiekt JSON. Jeśli jakiejś informacji nie ma w poleceniu, użyj wartości `null`.

### Schemat Obiektu JSON do zwrotu

Dla DODAJ_ZAKUPY:
```json
{{
  "paragon_info": {{ "sklep": "Biedronka", "data": "dzisiaj" }},
  "produkty": [
    {{ "nazwa_artykulu": "mleko 3,2%", "ilosc": 2, "cena_jednostkowa": 4.50, "cena_calkowita": 9.00, "kategoria": "Nabiał" }},
    {{ "nazwa_artykulu": "chleb wiejski", "ilosc": 1, "cena_jednostkowa": 5.00, "cena_calkowita": 5.00, "kategoria": "Pieczywo" }}
  ]
}}
```

Dla UPDATE_ITEM/DELETE_ITEM:
```json
{{
    "nazwa_artykulu": "nazwa produktu",
    "sklep": "nazwa sklepu (opcjonalnie)",
    "data_zakupow": "YYYY-MM-DD (opcjonalnie)"
}}
```

Dla UPDATE_PURCHASE/DELETE_PURCHASE:
```json
{{
    "sklep": "nazwa sklepu",
    "data_zakupow": "YYYY-MM-DD"
}}
```

Dla CZYTAJ_PODSUMOWANIE:
```json
{{
    "metryka": "suma_wydatkow",
    "filtry": [],
    "grupowanie": ["sklep", "kategoria"],
    "sortowanie": null
}}
```

---
### PRZYKŁADY EKSTRAKCJI DLA `DODAJ_ZAKUPY`

Poniżej znajdują się przykłady, jak należy przetwarzać polecenia użytkownika dla intencji `DODAJ_ZAKUPY`.

**Przykład 1:**
POLECENIE: "wczoraj w Lidlu kupiłem 3 wody po 1.50 i chipsy za 7zł"
JSON:
```json
{{
  "paragon_info": {{ "sklep": "Lidl", "data": "wczoraj" }},
  "produkty": [
    {{ "nazwa_artykulu": "woda", "ilosc": 3, "cena_jednostkowa": 1.50, "cena_calkowita": 4.50, "kategoria": "Napoje" }},
    {{ "nazwa_artykulu": "chipsy", "ilosc": 1, "cena_jednostkowa": 7.00, "cena_calkowita": 7.00, "kategoria": "Przekąski" }}
  ]
}}
```

**Przykład 2:**
POLECENIE: "nowy paragon z Żabki: 2x cola zero, 1x kanapka"
JSON:
```json
{{
  "paragon_info": {{ "sklep": "Żabka", "data": "dzisiaj" }},
  "produkty": [
    {{ "nazwa_artykulu": "cola zero", "ilosc": 2, "cena_jednostkowa": null, "cena_calkowita": null, "kategoria": "Napoje" }},
    {{ "nazwa_artykulu": "kanapka", "ilosc": 1, "cena_jednostkowa": null, "cena_calkowita": null, "kategoria": "Gotowe dania" }}
  ]
}}
```

**Przykład 3:**
POLECENIE: "dodaj zakupy: jajka 10 sztuk, 12 zł"
JSON:
```json
{{
  "paragon_info": {{ "sklep": null, "data": "dzisiaj" }},
  "produkty": [
    {{ "nazwa_artykulu": "jajka", "ilosc": 10, "cena_jednostkowa": 1.20, "cena_calkowita": 12.00, "kategoria": "Nabiał" }}
  ]
}}
```

**Przykład 4:**
POLECENIE: "pokaż wszystkie moje zakupy"
JSON:
```json
{{
  "metryka": "lista_wszystkiego",
  "filtry": [],
  "grupowanie": [],
  "sortowanie": null
}}
```

---
### TWOJE ZADANIE

Przeanalizuj poniższe polecenie użytkownika i zwróć odpowiedni obiekt JSON zgodnie z powyższymi przykładami.

Intencja: {intent}
Polecenie użytkownika: "{user_command}"
"""

def get_resolver_prompt(options: list, user_reply: str) -> str:
    """
    Generuje prompt do rozwiązywania niejednoznaczności w wyborze użytkownika.
    """
    options_text = "\n".join([f"{i+1}. {str(opt)}" for i, opt in enumerate(options)])
    
    return f"""Przeanalizuj odpowiedź użytkownika i określ, którą opcję wybrał.
Dostępne opcje:
{options_text}

Odpowiedź użytkownika: "{user_reply}"

Odpowiedz w formacie JSON:
{{
    "choice": numer_wybranej_opcji,  // liczba od 1 do {len(options)}
    "confidence": 0.95  // pewność wyboru (0-1)
}}
""" 