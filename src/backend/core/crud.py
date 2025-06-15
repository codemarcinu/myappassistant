import logging
import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, TypeVar

from sqlalchemy import func, select, update

from ..models.shopping import Product, ShoppingTrip

# Define AsyncSession as a type variable to avoid import errors


# Define a type alias for AsyncSession if it can't be imported
AsyncSession = TypeVar("AsyncSession")

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
    db: Any, entities: Dict[str, Any]
) -> List[ShoppingTrip]:
    """
    Wyszukuje w bazie danych paragony na podstawie "ludzkich" identyfikatorów. Zwraca listę!
    """
    paragon_query = select([*ShoppingTrip.__table__.columns])
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


async def find_item_for_action(db: Any, entities: Dict[str, Any]) -> List[Product]:
    """
    Wyszukuje w bazie danych artykuły na podstawie "ludzkich" identyfikatorów. Zwraca listę!
    """
    # Etap 1: Używamy naszej nowej funkcji do znalezienia paragonu
    znalezione_paragony = await find_purchase_for_action(db, entities)
    if not znalezione_paragony:
        # Komunikat o błędzie zostanie wypisany w find_purchase_for_action
        return []

    produkty = []
    produkt_id_data = entities.get("produkt_identyfikator", {})
    for paragon in znalezione_paragony:
        produkt_query = select([*Product.__table__.columns]).where(
            Product.trip_id == paragon.id
        )
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
    db: Any,
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
                new_value = op.get("nowa_wartosc")

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

                setattr(target_object, actual_field_name, new_value)
                logger.info(
                    f"Zmieniono pole '{actual_field_name}' na wartość '{new_value}'"
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


async def create_shopping_trip(db: Any, data: Dict[str, Any]) -> ShoppingTrip:
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

            nowy_produkt = Product(**product_kwargs)
            db.add(nowy_produkt)

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


async def get_summary(db: Any, query_params: Dict[str, Any]) -> List[Any]:
    """
    Na podstawie planu zapytania z LLM, dynamicznie buduje i wykonuje
    zapytanie analityczne SQLAlchemy. WERSJA FINALNA.
    """
    metryka = query_params.get("metryka")
    grupowanie = query_params.get("grupowanie", [])

    if metryka == "lista_wszystkiego":
        stmt = (
            select([*ShoppingTrip.__table__.columns])
            .execution_options(populate_existing=True)
            .order_by(ShoppingTrip.trip_date.desc())
        )
        result = await db.execute(stmt)
        trips = list(result.scalars().all())

        # Load products separately
        for trip in trips:
            product_stmt = select([*Product.__table__.columns]).where(
                Product.trip_id == trip.id
            )
            product_result = await db.execute(product_stmt)
            trip.products = list(product_result.scalars().all())

        return trips

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
        stmt = select(*selekcja)

        # Add join
        stmt = stmt.select_from(
            Product.__table__.join(
                ShoppingTrip.__table__, Product.trip_id == ShoppingTrip.id
            )
        )

        # Add group by if needed
        if kolumny_grupujace_sql:
            # Fetch the raw SQL expression from the statement and execute with group by manually
            query = str(stmt.compile(compile_kwargs={"literal_binds": True}))
            query += " GROUP BY " + ", ".join(
                str(col.compile(compile_kwargs={"literal_binds": True}))
                for col in kolumny_grupujace_sql
            )
            result = await db.execute(query)
            return list(result)
        else:
            result = await db.execute(stmt)
            return list(result.all())

    return []


async def get_all_products(db: Any) -> List[Product]:
    """Pobiera wszystkie produkty ze wszystkich zakupów."""
    query = select([*Product.__table__.columns]).order_by(Product.id.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def add_products_to_trip(
    db: Any, shopping_trip_id: int, products_data: List[Dict[str, Any]]
) -> ShoppingTrip:
    """
    Dodaje wiele produktów do istniejącej listy zakupów w jednej transakcji.
    """
    try:
        # Pobierz istniejący paragon
        result = await db.execute(
            select([*ShoppingTrip.__table__.columns]).where(
                ShoppingTrip.id == shopping_trip_id
            )
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
            new_product = Product(**product_kwargs)
            db.add(new_product)

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
    db: Any, start_date: date, end_date: date
) -> List[ShoppingTrip]:
    """Pobiera zakupy w podanym zakresie dat."""
    stmt = (
        select([*ShoppingTrip.__table__.columns])
        .where(ShoppingTrip.trip_date.between(start_date, end_date))
        .order_by(ShoppingTrip.trip_date.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_available_products(db: Any) -> List[Product]:
    """
    Gets all products that are not consumed and not expired.
    Returns list of Product objects.
    """
    today = date.today()
    stmt = (
        select([*Product.__table__.columns])
        .where(
            (Product.is_consumed.is_(False))
            & ((Product.expiration_date.is_(None)) | (Product.expiration_date >= today))
        )
        .order_by(Product.expiration_date.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def mark_products_consumed(db: Any, product_ids: List[int]) -> bool:
    """
    Marks multiple products as consumed by their IDs.
    Returns True if successful, False otherwise.
    """
    try:
        stmt = (
            update(Product.__table__)
            .where(Product.id.in_(product_ids))
            .values(is_consumed=True)
        )
        await db.execute(stmt)
        await db.commit()
        return True
    except Exception as e:
        logger.error(f"Error marking products as consumed: {e}")
        await db.rollback()
        return False


async def get_shopping_trip_summary(db: Any, trip_id: int) -> Optional[Dict[str, Any]]:
    """
    Calculates the summary for a specific shopping trip, including the total
    number of products and the sum of their costs.
    """
    # Create base query
    stmt = select(
        func.count(Product.id).label("total_products"),
        func.sum(Product.unit_price * Product.quantity).label("total_cost"),
    )

    # Add join and filters
    stmt = stmt.select_from(
        Product.__table__.join(
            ShoppingTrip.__table__, Product.trip_id == ShoppingTrip.id
        )
    )

    # Execute with manual WHERE and GROUP BY clauses
    query = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    query += f" WHERE ShoppingTrip.id = {trip_id} GROUP BY ShoppingTrip.id"

    result = await db.execute(query)
    summary = result.first()

    if summary:
        return {
            "total_products": summary.total_products,
            "total_cost": summary.total_cost or 0.0,
        }
    return None
