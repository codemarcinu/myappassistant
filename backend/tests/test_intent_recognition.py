import asyncio
import json
from ..core.llm_client import llm_client
from ..config import settings
from ..agents.prompts import get_intent_recognition_prompt

# Prompt systemowy pozostaje ten sam - prosty i klarowny.
SYSTEM_PROMPT = """Jesteś precyzyjnym systemem klasyfikacji intencji. Twoim zadaniem jest analiza polecenia użytkownika i zwrócenie TYLKO I WYŁĄCZNIE obiektu JSON z jednym kluczem 'intencja'.
Dostępne wartości dla klucza 'intencja' to: DODAJ_ZAKUPY, CZYTAJ_PODSUMOWANIE, UPDATE_ITEM, DELETE_ITEM, UPDATE_PURCHASE, DELETE_PURCHASE, UNKNOWN.
Nie dodawaj żadnego tekstu przed ani po obiekcie JSON. Twoja odpowiedź musi być wyłącznie poprawnym składniowo JSON-em.
"""

async def test_intent_recognition(user_prompt: str) -> None:
    print(f"\n--- Testuję polecenie: '{user_prompt}' ---")
    
    try:
        # Używamy promptu z modułu prompts
        prompt = get_intent_recognition_prompt(user_prompt)
        messages = [
            {'role': 'system', 'content': "Jesteś precyzyjnym systemem klasyfikacji intencji. Zawsze zwracaj tylko JSON."},
            {'role': 'user', 'content': prompt}
        ]
        
        response = await llm_client.chat(
            model=settings.DEFAULT_CHAT_MODEL,
            messages=messages,
            stream=False,
            options={'temperature': 0.0}
        )
        
        raw_response = response['message']['content']
        print(f"Odpowiedź modelu: {raw_response}")
        
        try:
            parsed_json = json.loads(raw_response.strip())
            print(f"Rozpoznana intencja: {parsed_json.get('intent', 'BRAK INTENCJI')}")
        except json.JSONDecodeError as e:
            print(f"Błąd: Model nie zwrócił poprawnego JSON")
            print(f"Otrzymany tekst: {raw_response}")
            print(f"Szczegóły błędu: {e}")
        
    except Exception as e:
        print(f"Wystąpił błąd: {e}")

async def run_tests():
    print("Uruchamiam testy rozpoznawania intencji...")
    test_cases = [
        "chciałbym poprawić nazwę sera na paragonie z wczoraj",
        "wywal ten paragon za 150 zł",
        "pomyłka, te zakupy były w Żabce",
        "pozbądź się wpisu o maśle",
        "co u ciebie słychać?",
        "dodaj nowy paragon z Biedronki, kupiłem mleko i chleb",
        "ile wydałem w tym miesiącu na jedzenie?",
        "zmień cenę mleka na 3.99 w ostatnim paragonie",
        "usuń cały paragon z wczoraj",
        "popraw datę zakupów z Lidla na 15 czerwca"
    ]
    
    for test_case in test_cases:
        await test_intent_recognition(test_case)

if __name__ == "__main__":
    asyncio.run(run_tests()) 