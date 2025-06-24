import logging
import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select, update
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.conversation import Conversation, Message
from backend.models.shopping import Product, ShoppingTrip
from backend.models.user_profile import UserActivity, UserProfile

logger = logging.getLogger(__name__)

# Słownik do tłumaczenia polskich nazw miesięcy w dopełniaczu (np. 10 czerwca)
POLISH_MONTHS_GENITIVE = {
    "stycznia": 1,
    "lutego": 2,
    "marca": 3,
    "kwietnia": 4,
    "maja": 5,
    "czerwca": 6,
    "lipca": 7,
    "sierpnia": 8,
    "września": 9,
    "października": 10,
    "listopada": 11,
    "grudnia": 12,
}

# NOWOŚĆ: Słownik do tłumaczenia dni tygodnia
POLISH_WEEKDAYS = {
    "poniedziałek": 0,
    "wtorek": 1,
    "środa": 2,
    "czwartek": 3,
    "piątek": 4,
    "sobota": 5,
    "niedziela": 6,
}

# Słownik mapujący nazwy z LLM na nazwy atrybutów w modelach
FIELD_MAP = {
    "cena_jednostkowa": "unit_price",
    "ilosc": "quantity",
    "nazwa_artykulu": "name",
    "sklep": "store_name",
    "data_zakupow": "trip_date",
    "rabat": "discount",  # Dodajemy przyszłościowo, gdybyś dodał to pole do modelu
    "kwota_per_paragon": "total_amount",
    "kategoria": "category",  # New field for product category
}


def parse_human_date(date_string: str, today: Optional[date] = None) -> Optional[date]:
    """
    Tłumaczy "ludzki" opis daty na obiekt daty w Pythonie.
    WERSJA OSTATECZNA: Poprawiona i bardziej odporna.
    """
    if not date_string:
        return None

    if today is None:
        today = date.today()

    text = date_string.lower().strip()

    # Przypadek 1: Słowa relatywne (sprawdzamy zawieranie, a nie równość)
    if "dzisiaj" in text:
        return today
    if "wczoraj" in text:
        return today - timedelta(days=1)
    if "przedwczoraj" in text:
        return today - timedelta(days=2)

    # Przypadek 2: Dni tygodnia
    # Usuwamy słowa "ostatni", "zeszły", "w" dla uproszczenia
    day_text = (
        text.replace("ostatni", "").replace("zeszły", "").replace("w", "").strip()
    )
    if day_text in POLISH_WEEKDAYS:
        target_weekday = POLISH_WEEKDAYS[day_text]
        today_weekday = today.weekday()
        days_ago = (today_weekday - target_weekday + 7) % 7
        if days_ago == 0:  # Jeśli to ten sam dzień tygodnia, cofnij o 7 dni
            days_ago = 7
        return today - timedelta(days=days_ago)

    # Przypadek 3: Format "10 czerwca" (używamy re.search, aby znaleźć wzorzec w dowolnym miejscu)
    match = re.search(r"(\d{1,2})\s+([a-zżźćńółęąś]+)", text)
    if match:
        day, month_name = match.groups()
        month_num = POLISH_MONTHS_GENITIVE.get(month_name)
        if month_num:
            try:
                return date(today.year, month_num, int(day))
            except ValueError:
                return None

    return None


async def find_purchase_for_action(
    db: AsyncSession, entities: Dict[str, Any]
) -> List[ShoppingTrip]:
    """
    Wyszukuje w bazie danych paragony na podstawie "ludzkich" identyfikatorów. Zwraca listę!
    """
    paragon_query = select(ShoppingTrip)
    paragon_id_data = entities.get("paragon_identyfikator", {})

    if paragon_id_data:
        date_str = paragon_id_data.get("data")
        obliczona_data = parse_human_date(date_str)
        if obliczona_data:
            paragon_query = paragon_query.where(
                ShoppingTrip.trip_date == obliczona_data
            )

        if paragon_id_data.get("sklep"):
            paragon_query = paragon_query.where(
                ShoppingTrip.store_name.ilike(f"%{paragon_id_data['sklep']}%")
            )

        if paragon_id_data.get("kolejnosc") == "ostatni":
            paragon_query = paragon_query.order_by(ShoppingTrip.id.desc()).limit(1)

    result = await db.execute(paragon_query)
    znalezione_paragony = list(result.scalars().all())
    logger.info(f"Znaleziono {len(znalezione_paragony)} pasujących paragonów.")
    return znalezione_paragony


async def find_item_for_action(
    db: AsyncSession, entities: Dict[str, Any]
) -> List[Product]:
    """
    Wyszukuje w bazie danych artykuły na podstawie "ludzkich" identyfikatorów. Zwraca listę!
    """
    # Etap 1: Używamy naszej nowej funkcji do znalezienia paragonu
    znalezione_paragony = await find_purchase_for_action(db, entities)
    if not znalezione_paragony:
        # Komunikat o błędzie zostanie wypisany w find_purchase_for_action
        return []

    produkty: List[Product] = []
    produkt_id_data = entities.get("produkt_identyfikator", {})
    for paragon in znalezione_paragony:
        produkt_query = select(Product).where(Product.trip_id == paragon.id)
        if produkt_id_data and produkt_id_data.get("nazwa"):
            produkt_query = produkt_query.where(
                Product.name.ilike(f"%{produkt_id_data['nazwa']}%")
            )
        result = await db.execute(produkt_query)
        produkty.extend(result.scalars().all())
        logger.info(
            f"Znaleziono {len(produkty)} pasujących produktów na danym/danych paragonie."
        )
    return produkty


async def execute_action(
    db: AsyncSession,
    intent: str,
    target_object: Any,
    operations: Optional[List[Dict[str, Any]]] = None,
) -> bool:
    """
    Wykonuje finalną operację (UPDATE lub DELETE) na obiekcie z bazy danych.
    """
    if not target_object:
        logger.warning("Błąd wykonania akcji: Obiekt docelowy nie został znaleziony.")
        return False

    try:
        if intent in ["DELETE_ITEM", "DELETE_PURCHASE"]:
            logger.info(f"Wykonuję operację DELETE na obiekcie: {target_object}")
            await db.delete(target_object)
            await db.commit()
            logger.info("Operacja DELETE zakończona sukcesem.")
            return True

        elif intent in ["UPDATE_ITEM", "UPDATE_PURCHASE"]:
            if not operations:
                logger.warning(
                    "Błąd wykonania akcji: Brak zdefiniowanych operacji UPDATE."
                )
                return False

            logger.info(f"Wykonuję operację UPDATE na obiekcie: {target_object}")
            all_ops_successful = True
            for op in operations:
                human_field_name = op.get("pole_do_zmiany")
                updated_value = op.get("nowa_wartosc")

                # Używamy naszego słownika do tłumaczenia nazwy pola
                actual_field_name = FIELD_MAP.get(
                    str(human_field_name) if human_field_name is not None else ""
                )

                if not actual_field_name or not hasattr(
                    target_object, actual_field_name
                ):
                    logger.error(
                        f"Błąd: Nie można zmapować lub obiekt nie posiada pola dla "
                        f"'{human_field_name}'"
                    )
                    all_ops_successful = False
                    continue  # Przejdź do następnej operacji

                setattr(target_object, actual_field_name, updated_value)
                logger.info(
                    f"Zmieniono pole '{actual_field_name}' na wartość '{updated_value}'"
                )

            if all_ops_successful:
                await db.commit()
                logger.info("Operacja UPDATE zakończona sukcesem.")
                return True
            else:
                await db.rollback()
                logger.warning("Operacja UPDATE przerwana z powodu błędów.")
                return False

    except Exception as e:
        logger.error(f"Wystąpił krytyczny błąd podczas zapisu do bazy: {e}")
        await db.rollback()
        return False

    return False


async def create_shopping_trip(db: AsyncSession, data: Dict[str, Any]) -> ShoppingTrip:
    """
    Tworzy nowy wpis o zakupach wraz z listą produktów w jednej transakcji.
    WERSJA OSTATECZNA z mapowaniem pól.
    """
    try:
        paragon_info = data.get("paragon_info", {})
        lista_produktow = data.get("produkty", [])

        obliczona_data = parse_human_date(paragon_info.get("data", "dzisiaj"))
        kwota_calkowita = sum(p.get("cena_calkowita", 0) for p in lista_produktow)

        nowy_paragon = ShoppingTrip(
            trip_date=obliczona_data,
            store_name=paragon_info.get("sklep"),
            total_amount=kwota_calkowita,
        )
        db.add(nowy_paragon)
        await db.flush()

        for produkt_data in lista_produktow:
            # Tłumaczymy klucze z JSON-a na atrybuty modelu SQLAlchemy
            product_kwargs: Dict[str, Any] = {
                mapped_key: value
                for key, value in produkt_data.items()
                if (mapped_key := FIELD_MAP.get(key, key))
                and mapped_key in Product.__table__.columns
            }
            # Upewniamy się, że ID paragonu jest dodane
            product_kwargs["trip_id"] = nowy_paragon.id

            created_product = Product(**product_kwargs)
            db.add(created_product)

        await db.commit()
        await db.refresh(nowy_paragon)

        logger.info(
            f"Dodano nowy paragon (ID: {nowy_paragon.id}) z "
            f"{len(lista_produktow)} produktami"
        )
        return nowy_paragon

    except Exception as e:
        logger.error(f"Wystąpił błąd podczas tworzenia wpisu: {e}")
        await db.rollback()
        raise


async def get_summary(db: AsyncSession, query_params: Dict[str, Any]) -> List[Any]:
    """
    Na podstawie planu zapytania z LLM, dynamicznie buduje i wykonuje
    zapytanie analityczne SQLAlchemy. WERSJA FINALNA.
    """
    metryka = query_params.get("metryka")
    grupowanie = query_params.get("grupowanie", [])

    if metryka == "lista_wszystkiego":
        stmt = (
            select(ShoppingTrip)
            .options(selectinload(ShoppingTrip.products))
            .order_by(ShoppingTrip.trip_date.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    if metryka == "suma_wydatkow":
        selekcja = [func.sum(Product.unit_price * Product.quantity).label("value")]
        kolumny_grupujace_str = []
        kolumny_grupujace_sql = []

        for g in grupowanie:
            if g == "sklep":
                kolumna = ShoppingTrip.store_name.label("group")
                selekcja.append(kolumna)
                kolumny_grupujace_sql.append(kolumna)
                kolumny_grupujace_str.append("sklep")
            elif g == "kategoria":
                kolumna = Product.category.label("group")
                selekcja.append(kolumna)
                kolumny_grupujace_sql.append(kolumna)
                kolumny_grupujace_str.append("kategoria")

        if not selekcja:
            return []

        # Build base query
        stmt = select(*selekcja).select_from(Product).join(ShoppingTrip)

        # Add group by if needed
        if kolumny_grupujace_sql:
            stmt = stmt.group_by(*kolumny_grupujace_sql)

        result = await db.execute(stmt)
        return list(result.all())

    return []


async def get_all_products(db: AsyncSession) -> List[Product]:
    """Pobiera wszystkie produkty ze wszystkich zakupów."""
    query = select(Product).order_by(Product.id.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def add_products_to_trip(
    db: AsyncSession, shopping_trip_id: int, products_data: List[Dict[str, Any]]
) -> ShoppingTrip:
    """
    Dodaje wiele produktów do istniejącej listy zakupów w jednej transakcji.
    """
    try:
        # Pobierz istniejący paragon
        result = await db.execute(
            select(ShoppingTrip).where(ShoppingTrip.id == shopping_trip_id)
        )
        shopping_trip = result.scalar_one_or_none()

        if not shopping_trip:
            raise ValueError(f"Shopping trip with id {shopping_trip_id} not found.")

        for product_data in products_data:
            product_kwargs: Dict[str, Any] = {
                mapped_key: value
                for key, value in product_data.items()
                if (mapped_key := FIELD_MAP.get(key, key))
                and mapped_key in Product.__table__.columns
            }
            product_kwargs["trip_id"] = shopping_trip.id
            created_product = Product(**product_kwargs)
            db.add(created_product)

        # Opcjonalnie: Zaktualizuj sumę na paragonie
        total_products_price = sum(p.get("cena_calkowita", 0) for p in products_data)
        if shopping_trip.total_amount:
            shopping_trip.total_amount += total_products_price
        else:
            shopping_trip.total_amount = total_products_price

        await db.commit()
        await db.refresh(shopping_trip)

        logger.info(
            f"Dodano {len(products_data)} produktów do paragonu (ID: {shopping_trip.id})"
        )
        return shopping_trip

    except Exception as e:
        logger.error(f"Błąd podczas dodawania produktów do paragonu: {e}")
        await db.rollback()
        raise


async def get_trips_by_date_range(
    db: AsyncSession, start_date: date, end_date: date
) -> List[ShoppingTrip]:
    """Pobiera zakupy w podanym zakresie dat."""
    stmt = (
        select(ShoppingTrip)
        .where(ShoppingTrip.trip_date.between(start_date, end_date))
        .order_by(ShoppingTrip.trip_date.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_available_products(db: AsyncSession) -> List[Product]:
    """
    Gets all products that are not consumed and not expired.
    Returns list of Product objects.
    """
    today = date.today()
    stmt = (
        select(Product)
        .where(
            (Product.is_consumed.is_(False))
            & ((Product.expiration_date.is_(None)) | (Product.expiration_date >= today))
        )
        .order_by(Product.expiration_date.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def mark_products_consumed(db: AsyncSession, product_ids: List[int]) -> bool:
    """
    Marks multiple products as consumed by their IDs.
    Returns True if successful, False otherwise.
    """
    try:
        stmt = (
            update(Product).where(Product.id.in_(product_ids)).values(is_consumed=True)
        )
        await db.execute(stmt)
        await db.commit()
        return True
    except Exception as e:
        logger.error(f"Error marking products as consumed: {e}")
        await db.rollback()
        return False


async def get_shopping_trip_summary(
    db: AsyncSession, trip_id: int
) -> Optional[Dict[str, Any]]:
    """
    Calculates the summary for a specific shopping trip, including the total
    number of products and the sum of their costs.
    """
    stmt = (
        select(
            func.count(Product.id).label("total_products"),
            func.sum(Product.unit_price * Product.quantity).label("total_cost"),
        )
        .select_from(Product)
        .join(ShoppingTrip)
        .where(ShoppingTrip.id == trip_id)
        .group_by(ShoppingTrip.id)
    )

    result = await db.execute(stmt)
    summary = result.first()

    if summary:
        return {
            "total_products": summary.total_products,
            "total_cost": summary.total_cost or 0.0,
        }
    return None


async def get_conversation_by_session_id(
    db: AsyncSession, session_id: str
) -> Conversation | None:
    """
    Asynchronously retrieves a conversation from the database by session_id.
    """
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.session_id == session_id)
    )
    return result.scalars().one_or_none()


async def create_conversation(db: AsyncSession, session_id: str) -> Conversation:
    """
    Asynchronously creates a new conversation in the database.
    """
    conversation = Conversation(session_id=session_id)
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def add_message_to_conversation(
    db: AsyncSession, conversation_id: int, role: str, content: str
) -> Message:
    """
    Asynchronously adds a new message to a conversation in the database.
    """
    message = Message(conversation_id=conversation_id, role=role, content=content)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def create_user_profile(
    db: AsyncSession, user_id: str, session_id: str
) -> UserProfile:
    """
    Creates a new user profile with default preferences and schedule.
    Returns the created UserProfile object.
    """
    from backend.models.user_profile import UserPreferences, UserSchedule

    profile = UserProfile(
        user_id=user_id,
        session_id=session_id,
        preferences=UserPreferences().dict(),
        schedule=UserSchedule().dict(),
        topics_of_interest=[],
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def get_user_profile_by_session(
    db: AsyncSession, session_id: str
) -> Optional[UserProfile]:
    """
    Retrieves a user profile by session ID.
    Returns None if not found.
    """
    result = await db.execute(
        select(UserProfile).where(UserProfile.session_id == session_id)
    )
    return result.scalars().one_or_none()


async def update_user_preferences(
    db: AsyncSession, user_id: str, preferences: Dict[str, Any]
) -> bool:
    """
    Updates user preferences.
    Returns True if successful, False otherwise.
    """
    try:
        stmt = (
            update(UserProfile)
            .where(UserProfile.user_id == user_id)
            .values(preferences=preferences)
        )
        await db.execute(stmt)
        await db.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        await db.rollback()
        return False


async def update_user_schedule(
    db: AsyncSession, user_id: str, schedule: Dict[str, Any]
) -> bool:
    """
    Updates user schedule.
    Returns True if successful, False otherwise.
    """
    try:
        stmt = (
            update(UserProfile)
            .where(UserProfile.user_id == user_id)
            .values(schedule=schedule)
        )
        await db.execute(stmt)
        await db.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating user schedule: {e}")
        await db.rollback()
        return False


async def get_user_activities(
    db: AsyncSession, user_id: str, limit: int = 50
) -> List[UserActivity]:
    """
    Gets recent user activities.
    Returns list of UserActivity objects.
    """
    stmt = (
        select(UserActivity)
        .where(UserActivity.user_id == user_id)
        .order_by(UserActivity.timestamp.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_user_topics(db: AsyncSession, user_id: str, topics: List[str]) -> bool:
    """
    Updates user's topics of interest.
    Returns True if successful, False otherwise.
    """
    try:
        stmt = (
            update(UserProfile)
            .where(UserProfile.user_id == user_id)
            .values(topics_of_interest=topics)
        )
        await db.execute(stmt)
        await db.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating user topics: {e}")
        await db.rollback()
        return False


async def get_products_paginated(
    session: AsyncSession, limit: int = 100, offset: int = 0
) -> Result[Any]:
    stmt = select(Product).order_by(Product.id.desc()).limit(limit).offset(offset)
    return await session.execute(stmt)


async def get_shopping_trips_paginated(
    session: AsyncSession, limit: int = 100, offset: int = 0
) -> Result[Any]:
    stmt = (
        select(ShoppingTrip)
        .order_by(ShoppingTrip.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return await session.execute(stmt)


async def get_messages_paginated(
    session: AsyncSession, conversation_id: int, limit: int = 100, offset: int = 0
) -> Result[Any]:
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return await session.execute(stmt)
