import logging
from typing import Any, Dict, List

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore

from backend.config import settings
from backend.core import crud
from backend.core.llm_client import llm_client
from backend.models.shopping import Product, ShoppingTrip

logger = logging.getLogger(__name__)


async def recognize_intent(prompt: str) -> str:
    """
    Narzędzie, które rozpoznaje intencję użytkownika na podstawie promptu.
    """
    try:
        response = await llm_client.chat(
            model=settings.DEFAULT_CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Jesteś precyzyjnym systemem klasyfikacji intencji. Zawsze zwracaj tylko JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            stream=False,
            options={"temperature": 0.0},
        )
        if response and response.get("message"):
            return response["message"]["content"]
        return '{"intent": "UNKNOWN"}'
    except Exception as e:
        logger.error(f"Błąd podczas rozpoznawania intencji: {e}")
        return '{"intent": "UNKNOWN"}'


async def extract_entities(prompt: str) -> str:
    """
    Narzędzie, które ekstrahuje encje z promptu.
    """
    try:
        response = await llm_client.chat(
            model=settings.DEFAULT_CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Jesteś precyzyjnym systemem ekstrakcji encji. Zawsze zwracaj tylko JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            stream=False,
            options={"temperature": 0.0},
        )
        if response and response.get("message"):
            return response["message"]["content"]
        return "{}"
    except Exception as e:
        logger.error(f"Błąd podczas ekstrakcji encji: {e}")
        return "{}"


async def find_database_object(
    db: AsyncSession, intent: str, entities: Dict
) -> List[Any]:
    """
    Narzędzie, które na podstawie intencji i encji wyszukuje obiekty w bazie danych.
    Zwraca listę znalezionych obiektów.
    """
    match intent:
        case "UPDATE_ITEM" | "DELETE_ITEM":
            return await crud.find_item_for_action(db, entities=entities)
        case "UPDATE_PURCHASE" | "DELETE_PURCHASE" | "ADD_PRODUCTS_TO_TRIP":
            return await crud.find_purchase_for_action(db, entities=entities)
        case "CZYTAJ_PODSUMOWANIE":
            return await crud.get_summary(db, query_params=entities)
        case _:
            return []


async def execute_database_action(
    db: AsyncSession, intent: str, target_object: Any, entities: Dict
) -> Any:
    """
    Narzędzie, które wykonuje operację zapisu (UPDATE/DELETE/CREATE) lub analizy w bazie.
    """
    try:
        if intent in ["DODAJ_ZAKUPY", "CREATE_ITEM", "CREATE_PURCHASE"]:
            from backend.agents.agent_factory import AgentFactory

            agent_factory = AgentFactory()
            categorization_agent = agent_factory.create_agent("categorization")

            for product in entities.get("produkty", []):
                if not product.get("kategoria"):
                    response = await categorization_agent.process(
                        {"product_name": product["nazwa"]}
                    )
                    if response.success and response.data:
                        product["kategoria"] = response.data.get("category")

            await crud.create_shopping_trip(db, data=entities)
            return True
        elif intent == "ADD_PRODUCTS_TO_TRIP":
            if not target_object or not isinstance(target_object, ShoppingTrip):
                logger.error("Nie znaleziono paragonu do którego można dodać produkty.")
                return False
            products_data = entities.get("produkty", [])
            if not products_data:
                logger.error("Brak danych o produktach do dodania.")
                return False
            await crud.add_products_to_trip(
                db, shopping_trip_id=target_object.id, products_data=products_data
            )
            return True
        elif intent == "ANALYZE":
            return await crud.get_summary(db, query_params=entities)
        else:  # Dla UPDATE i DELETE
            operations = entities.get("operacje")
            return await crud.execute_action(db, intent, target_object, operations)
    except SQLAlchemyError as e:
        logger.error(f"Błąd podczas wykonywania akcji w bazie danych: {e}")
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
            formatted_options.append(
                f"{i}. Paragon ze sklepu '{obj.store_name}' " f"z dnia {obj.trip_date}."
            )
        elif isinstance(obj, Product):
            formatted_options.append(
                f"{i}. Produkt '{obj.name}' w cenie {obj.unit_price} zł."
            )
        else:  # Dla wyników z get_summary
            formatted_options.append(f"{i}. {obj}")

    return "Znalazłem kilka pasujących opcji. Proszę, wybierz jedną:\n" + "\n".join(
        formatted_options
    )


async def get_available_products_from_pantry(db: AsyncSession) -> List[Product]:
    """
    Gets all available products from pantry (not consumed and not expired).
    Returns list of Product objects.
    """
    try:
        return await crud.get_available_products(db)
    except SQLAlchemyError as e:
        logger.error(f"Error getting available products: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error getting available products: {e}")
        return []


async def mark_products_as_consumed(db: AsyncSession, product_ids: List[int]) -> bool:
    """
    Marks specified products as consumed.
    Returns True if successful, False otherwise.
    """
    try:
        return await crud.mark_products_consumed(db, product_ids)
    except SQLAlchemyError as e:
        logger.error(f"Error marking products as consumed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error marking products as consumed: {e}")
        return False
