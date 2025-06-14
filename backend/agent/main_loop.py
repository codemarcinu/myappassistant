import json
from typing import Any, List, Optional

from ..core import crud
from ..core.database import AsyncSessionLocal
from ..models.shopping import ShoppingTrip, Product
from ..core.llm_client import llm_client
from ..config import settings
from .state import ConversationState
from .orchestrator import recognize_intent
from .prompts import get_entity_extraction_prompt, get_resolver_prompt
from .utils import extract_json_from_text

def generate_clarification_question(options: List[Any]) -> str:
    """
    Generuje pytanie doprecyzowujące na podstawie listy znalezionych elementów.
    """
    if not options:
        return "Nie znalazłem żadnych pasujących elementów. Czy możesz podać więcej szczegółów?"
    
    formatted_options = []
    for i, obj in enumerate(options, 1):
        if isinstance(obj, ShoppingTrip):
            formatted_options.append(f"{i}. Paragon ze sklepu '{obj.store_name}' z dnia {obj.trip_date}.")
        elif isinstance(obj, Product):
            formatted_options.append(f"{i}. Produkt '{obj.name}' w cenie {obj.unit_price} zł.")
    
    return f"Znalazłem kilka pasujących opcji. Proszę, wybierz jedną:\n" + "\n".join(formatted_options)

async def extract_entities(user_command: str, intent: str) -> dict:
    """
    Ekstrahuje encje z polecenia użytkownika na podstawie rozpoznanej intencji.
    """
    system_prompt = get_entity_extraction_prompt()
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': f"Intencja: {intent}\nPolecenie: {user_command}"}
    ]
    
    try:
        response = await llm_client.chat(
            model=settings.DEFAULT_CHAT_MODEL,
            messages=messages,
            stream=False,
            options={'temperature': 0.0}
        )
        raw_response = response['message']['content']
        json_string = extract_json_from_text(raw_response)
        
        if not json_string:
            return {}
            
        return json.loads(json_string)
    except Exception as e:
        print(f"Błąd w ekstrakcji encji: {e}")
        return {}

async def resolve_ambiguity(options: List[Any], user_reply: str) -> Optional[Any]:
    """
    Rozwiązuje niejednoznaczność na podstawie odpowiedzi użytkownika.
    """
    options_text = generate_clarification_question(options)
    resolver_prompt = get_resolver_prompt(options_text, user_reply)
    
    messages = [
        {'role': 'system', 'content': "Jesteś precyzyjnym systemem AI. Zawsze zwracaj tylko i wyłącznie obiekt JSON."},
        {'role': 'user', 'content': resolver_prompt}
    ]
    
    try:
        response = await llm_client.chat(
            model=settings.DEFAULT_CHAT_MODEL,
            messages=messages,
            stream=False,
            options={'temperature': 0.0}
        )
        raw_response = response['message']['content'].strip()
        
        if raw_response == "null":
            return None
            
        json_string = extract_json_from_text(raw_response)
        if not json_string:
            return None
            
        parsed_json = json.loads(json_string)
        selected_index = parsed_json.get('wybrany_indeks')
        
        if selected_index is not None and isinstance(selected_index, int) and 1 <= selected_index <= len(options):
            return options[selected_index - 1]
            
        return None
    except Exception as e:
        print(f"Błąd w rozwiązywaniu niejednoznaczności: {e}")
        return None

async def process_user_command(user_command: str, state: ConversationState) -> str:
    """
    Główna funkcja przetwarzająca polecenia użytkownika.
    """
    async with AsyncSessionLocal() as db:
        try:
            if state.is_awaiting_clarification:
                chosen_object = await resolve_ambiguity(state.ambiguous_options, user_command)
                if chosen_object and state.original_intent is not None:
                    operations = state.original_entities.get('operacje') if state.original_entities else None
                    await crud.execute_action(db, state.original_intent, chosen_object, operations)
                    state.reset()
                    return "Gotowe, operacja została wykonana na wybranym przez Ciebie obiekcie."
                else:
                    state.reset()
                    return "Niestety, nie udało mi się zrozumieć Twojego wyboru. Zacznijmy od nowa."
            else:
                intent = await recognize_intent(user_command)
                if intent == "UNKNOWN":
                    return "Przepraszam, nie potrafię pomóc w tej kwestii. Skupmy się na wydatkach."
                
                entities = await extract_entities(user_command, intent)
                
                if intent == "DODAJ_ZAKUPY":
                    result = await crud.create_shopping_trip(db, data=entities)
                    if result:
                        return "Pomyślnie dodałem nowy paragon i jego produkty."
                    return "Wystąpił błąd podczas dodawania paragonu."
                
                found_objects = []
                if intent in ["UPDATE_ITEM", "DELETE_ITEM"]:
                    found_objects = await crud.find_item_for_action(db, entities=entities)
                elif intent in ["UPDATE_PURCHASE", "DELETE_PURCHASE"]:
                    found_objects = await crud.find_purchase_for_action(db, entities=entities)
                
                if len(found_objects) == 1:
                    operations = entities.get('operacje')
                    await crud.execute_action(db, intent, found_objects[0], operations)
                    return "Gotowe, operacja wykonana."
                elif len(found_objects) > 1:
                    state.set_clarification_mode(intent, entities, found_objects)
                    return generate_clarification_question(found_objects)
                else:  # len == 0
                    return "Niestety, nie znalazłem niczego pasującego do Twojego opisu."
        except Exception as e:
            print(f"Wystąpił krytyczny błąd w pętli agenta: {e}")
            return "Coś poszło nie tak. Spróbuj ponownie." 