import asyncio
import json
from typing import List, Any, Optional

from backend.core.llm_client import ollama_client
from backend.config import settings
from backend.core import crud
from backend.core.database import AsyncSessionLocal
from backend.models.shopping import ShoppingTrip, Product
from sqlalchemy.ext.asyncio import AsyncSession

# --- Klasa do zarządzania stanem konwersacji ---

class ConversationState:
    """Przechowuje stan bieżącej konwersacji."""
    def __init__(self):
        self.is_awaiting_clarification: bool = False
        self.original_intent: Optional[str] = None
        self.original_entities: Optional[dict] = None
        self.ambiguous_options: List[Any] = []

    def set_clarification_mode(self, intent: str, entities: dict, options: List[Any]):
        self.is_awaiting_clarification = True
        self.original_intent = intent
        self.original_entities = entities
        self.ambiguous_options = options
        print("--- AGENT: Zapisuję stan i przechodzę w tryb oczekiwania na doprecyzowanie. ---")

    def reset(self):
        self.is_awaiting_clarification = False
        self.original_intent = None
        self.original_entities = None
        self.ambiguous_options = []
        print("--- AGENT: Stan konwersacji zresetowany. ---")

# --- Funkcje pomocnicze ---
def extract_json_from_text(text: str) -> str:
    try:
        start_index = text.find('{')
        end_index = text.rfind('}')
        if start_index != -1 and end_index != -1 and end_index > start_index:
            return text[start_index:end_index+1]
        return ""
    except Exception: return ""

def generate_clarification_question(options: List[Any]) -> str:
    formatted_options = []
    for i, obj in enumerate(options, 1):
        if isinstance(obj, ShoppingTrip):
            formatted_options.append(f"{i}. Paragon ze sklepu '{obj.store_name}' z dnia {obj.trip_date}.")
        elif isinstance(obj, Product):
            formatted_options.append(f"{i}. Produkt '{obj.name}' w cenie {obj.unit_price} zł.")
    options_text = "\n".join(formatted_options)
    return f"Znalazłem kilka pasujących opcji. Proszę, wybierz jedną:\n{options_text}"

# --- GŁÓWNA LOGIKA AGENTA ---

async def process_user_command(user_command: str, state: ConversationState) -> str:
    """
    Główna funkcja przetwarzająca polecenie użytkownika, zarządzająca stanem.
    """
    db: AsyncSession = AsyncSessionLocal()
    try:
        # --- ŚCIEŻKA 2: Użytkownik odpowiada na pytanie agenta ---
        if state.is_awaiting_clarification:
            print("AGENT (myśli): Otrzymałem odpowiedź na moje pytanie. Próbuję ją zrozumieć...")
            options_text = generate_clarification_question(state.ambiguous_options)
            resolver_prompt = f"Twoim zadaniem jest analiza odpowiedzi użytkownika i dopasowanie jej do jednej z przedstawionych mu wcześniej opcji. Zwróć obiekt JSON z jednym kluczem: 'wybrany_indeks'. Indeks jest numerem opcji z listy (zaczynając od 1). Jeśli nie jesteś w stanie dopasować odpowiedzi, zwróć null.\n\n### Kontekst\nUżytkownik został poproszony o wybór jednej z opcji:\n{options_text}\n\n### Odpowiedź użytkownika do analizy\n\"{user_command}\""
            messages = [
                {'role': 'system', 'content': "Jesteś pomocnym asystentem AI. Zawsze zwracaj tylko JSON."},
                {'role': 'user', 'content': resolver_prompt}
            ]
            response = await ollama_client.chat(model=settings.DEFAULT_CHAT_MODEL, messages=messages, stream=False)
            json_string = extract_json_from_text(response['message']['content'])
            selected_index = json.loads(json_string).get('wybrany_indeks')
            if selected_index is not None and 1 <= selected_index <= len(state.ambiguous_options):
                final_target = state.ambiguous_options[selected_index - 1]
                print(f"AGENT (myśli): Użytkownik wybrał opcję {selected_index}. Cel: {final_target}. Wykonuję pierwotną akcję.")
                # Wykonanie pierwotnej akcji
                if state.original_intent is not None:
                    operations = state.original_entities.get('operacje') if state.original_entities else None
                    if isinstance(operations, list):
                        await crud.execute_action(db, state.original_intent, final_target, operations)
                    else:
                        await crud.execute_action(db, state.original_intent, final_target, None)
                state.reset()
                return "Gotowe, operacja została wykonana na wybranym przez Ciebie obiekcie."
            else:
                state.reset()
                return "Niestety, nie udało mi się zrozumieć Twojego wyboru. Zacznijmy od nowa."
        # --- ŚCIEŻKA 1: Normalny przepływ dla nowego polecenia ---
        else:
            print("AGENT (myśli): Otrzymałem nowe polecenie. Zaczynam analizę od zera.")
            # Krok A: Rozpoznanie intencji (symulujemy, bo to już mamy)
            intent = "DELETE_PURCHASE" # Na potrzeby tego testu
            print(f"AGENT (myśli): Rozpoznana intencja: {intent}")
            # Krok B: Ekstrakcja encji (symulujemy, bo to już mamy)
            entities = {'paragon_identyfikator': {'data': 'wtorek'}}
            print(f"AGENT (myśli): Wyekstrahowane encje: {entities}")
            # Krok C: Wyszukanie w bazie
            found_objects = await crud.find_purchase_for_action(db, entities)
            if len(found_objects) == 1:
                operations = entities.get('operacje')
                if isinstance(operations, list):
                    await crud.execute_action(db, intent, found_objects[0], operations)
                else:
                    await crud.execute_action(db, intent, found_objects[0], None)
                return "Operacja wykonana pomyślnie."
            elif len(found_objects) > 1:
                state.set_clarification_mode(intent, entities, found_objects)
                return generate_clarification_question(found_objects)
            else:
                return "Niestety, nie znalazłem niczego pasującego do Twojego opisu."
    finally:
        await db.close()

# --- SYMULACJA PEŁNEJ KONWERSACJI ---

async def main():
    conversation_state = ConversationState()
    user_input_1 = "usuń paragon z wtorku"
    print(f"Użytkownik: {user_input_1}\n")
    agent_response_1 = await process_user_command(user_input_1, conversation_state)
    print(f"\nAgent: {agent_response_1}\n")
    user_input_2 = "ten drugi proszę"
    print(f"Użytkownik: {user_input_2}\n")
    agent_response_2 = await process_user_command(user_input_2, conversation_state)
    print(f"\nAgent: {agent_response_2}\n")

if __name__ == "__main__":
    asyncio.run(main()) 