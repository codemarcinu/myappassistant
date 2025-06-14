import asyncio
import json
from typing import List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.llm_client import ollama_client
from ..config import settings
from ..core import crud
from ..core.database import AsyncSessionLocal
from ..models.shopping import ShoppingTrip, Product

# --- Funkcje pomocnicze, które już znamy ---

def extract_json_from_text(text: str) -> str:
    try:
        start_index = text.find('{')
        end_index = text.rfind('}')
        if start_index != -1 and end_index != -1 and end_index > start_index:
            return text[start_index:end_index+1]
        return ""
    except Exception:
        return ""

def generate_clarification_question(options: List[Any]) -> str:
    if not options:
        return "Coś poszło nie tak, nie mam opcji do wyboru."
    formatted_options = []
    for i, obj in enumerate(options, 1):
        if isinstance(obj, ShoppingTrip):
            formatted_options.append(f"{i}. Paragon ze sklepu '{obj.store_name}' z dnia {obj.trip_date}.")
        elif isinstance(obj, Product):
            formatted_options.append(f"{i}. Produkt '{obj.name}' w cenie {obj.unit_price} zł.")
    return "\n".join(formatted_options)

# --- NOWA FUNKCJA Z INTELIGENCJĄ DO ROZUMIENIA ODPOWIEDZI ---

async def resolve_ambiguity(options: List[Any], user_reply: str) -> Optional[Any]:
    """
    Na podstawie listy opcji i odpowiedzi użytkownika, prosi LLM o wybranie właściwego obiektu.
    """
    print("\n--- Krok 3: Rozwiązywanie niejednoznaczności ---")
    
    options_text = generate_clarification_question(options)
    
    resolver_prompt = f"""Twoim zadaniem jest analiza odpowiedzi użytkownika i dopasowanie jej do jednej z przedstawionych mu wcześniej opcji. Zwróć obiekt JSON z jednym kluczem: 'wybrany_indeks'. Indeks jest numerem opcji z listy (zaczynając od 1). Jeśli nie jesteś w stanie jednoznacznie dopasować odpowiedzi do żadnej z opcji, zwróć null.

### Kontekst
Użytkownik został poproszony o wybór jednej z poniższych opcji:
{options_text}

### Odpowiedź użytkownika do analizy
"{user_reply}"
"""
    try:
        messages = [{'role': 'system', 'content': "Jesteś pomocnym asystentem AI. Zawsze zwracaj tylko i wyłącznie obiekt JSON."}, {'role': 'user', 'content': resolver_prompt}]
        
        response = await ollama_client.chat(
            model=settings.DEFAULT_CHAT_MODEL, messages=messages, stream=False, options={'temperature': 0.0}
        )
        
        raw_response = response['message']['content']
        print(f"Odpowiedź LLM (resolver): {raw_response}")
        
        json_string = extract_json_from_text(raw_response)
        parsed_json = json.loads(json_string)
        selected_index = parsed_json.get('wybrany_indeks')

        if selected_index is not None and isinstance(selected_index, int) and 1 <= selected_index <= len(options):
            chosen_object = options[selected_index - 1]
            print(f"Sukces! Agent zinterpretował odpowiedź i wybrał opcję nr {selected_index}.")
            return chosen_object
        else:
            print("Agent nie był w stanie zinterpretować odpowiedzi.")
            return None
    except Exception as e:
        print(f"Wystąpił krytyczny błąd podczas rozwiązywania niejednoznaczności: {e}")
        return None

# --- GŁÓWNA FUNKCJA SYMULUJĄCA DIALOG ---

async def run_dialogue_simulation():
    """
    Symuluje pełną, dwuetapową konwersację z agentem.
    """
    print("--- SCENARIUSZ: Użytkownik chce usunąć paragon, ale jego polecenie jest niejednoznaczne ---")
    
    # Etap 1: Niejednoznaczne polecenie użytkownika
    user_input_1 = "usuń cały paragon z wtorku"
    intent = "DELETE_PURCHASE"
    print(f"\nUżytkownik: '{user_input_1}'")
    
    async with AsyncSessionLocal() as db:
        try:
            # Agent próbuje znaleźć cel
            znalezione_obiekty = await crud.find_purchase_for_action(db, entities={'paragon_identyfikator': {'data': 'wtorek'}})
            
            if len(znalezione_obiekty) > 1:
                print(f"Agent (myśli): Znalazłem {len(znalezione_obiekty)} pasujących obiektów. Muszę dopytać.")
                
                # Etap 2: Agent zadaje pytanie doprecyzowujące
                pytanie_agenta = generate_clarification_question(znalezione_obiekty)
                print(f"\nAgent (pyta): Znalazłem kilka opcji, proszę wybierz jedną:\n{pytanie_agenta}")
                
                # Etap 3: Użytkownik odpowiada, doprecyzowując
                user_input_2 = "ten z Lidla poproszę"
                print(f"\nUżytkownik (odpowiada): '{user_input_2}'")
                
                # Etap 4: Agent próbuje zrozumieć odpowiedź
                finalny_cel = await resolve_ambiguity(znalezione_obiekty, user_input_2)
                
                if finalny_cel:
                    print("\n--- FINAŁ SYMULACJI ---")
                    print(f"Agent poprawnie zidentyfikował ostateczny cel: {finalny_cel}")
                    print("Teraz można bezpiecznie wykonać na nim operację DELETE.")
                    print("--- ZWYCIĘSTWO! ---")
                else:
                    print("\n--- FINAŁ SYMULACJI ---")
                    print("Agentowi nie udało się zrozumieć odpowiedzi. Konwersacja wymaga dalszego prowadzenia.")
            
            else:
                print("Coś poszło nie tak, test nie wygenerował niejednoznaczności.")

        except Exception as e:
            print(f"Wystąpił krytyczny błąd: {e}")

if __name__ == "__main__":
    asyncio.run(run_dialogue_simulation()) 