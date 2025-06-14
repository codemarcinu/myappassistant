from typing import Any, List, Dict, Optional
from ..core import crud
from ..core.database import AsyncSessionLocal
from ..models.shopping import ShoppingTrip, Product

async def find_database_object(intent: str, entities: Dict) -> List[Any]:
    """
    Narzędzie, które na podstawie intencji i encji wyszukuje obiekty w bazie danych.
    Zwraca listę znalezionych obiektów.
    """
    async with AsyncSessionLocal() as db:
        if intent in ["UPDATE_ITEM", "DELETE_ITEM"]:
            return await crud.find_item_for_action(db, entities=entities)
        elif intent in ["UPDATE_PURCHASE", "DELETE_PURCHASE"]:
            return await crud.find_purchase_for_action(db, entities=entities)
        elif intent == "CZYTAJ_PODSUMOWANIE":
            return await crud.get_summary(db, query_params=entities)
    return []

async def execute_database_action(intent: str, target_object: Any, entities: Dict) -> bool:
    """
    Narzędzie, które wykonuje operację zapisu (UPDATE/DELETE/CREATE) w bazie.
    """
    async with AsyncSessionLocal() as db:
        try:
            if intent == "DODAJ_ZAKUPY":
                await crud.create_shopping_trip(db, data=entities)
                return True
            else: # Dla UPDATE i DELETE
                operations = entities.get('operacje')
                return await crud.execute_action(db, intent, target_object, operations)
        except Exception as e:
            print(f"Błąd podczas wykonywania akcji w bazie danych: {e}")
            return False

def generate_clarification_question_text(options: List[Any]) -> str:
    """
    Narzędzie, które formatuje listę opcji na czytelne pytanie dla użytkownika.
    """
    if not options:
        return "Coś poszło nie tak, nie mam opcji do wyboru."
    formatted_options = []
    for i, obj in enumerate(options, 1):
        if isinstance(obj, ShoppingTrip):
            formatted_options.append(f"{i}. Paragon ze sklepu '{obj.store_name}' z dnia {obj.trip_date}.")
        elif isinstance(obj, Product):
            formatted_options.append(f"{i}. Produkt '{obj.name}' w cenie {obj.unit_price} zł.")
        else: # Dla wyników z get_summary
            formatted_options.append(f"{i}. {obj}")

    return f"Znalazłem kilka pasujących opcji. Proszę, wybierz jedną:\n" + "\n".join(formatted_options) 