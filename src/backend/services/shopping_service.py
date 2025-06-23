# w pliku backend/services/shopping_service.py
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload  # <--- Kluczowy import!

from backend.models.shopping import Product, ShoppingTrip
from backend.schemas import shopping_schemas


async def create_shopping_trip(
    db: AsyncSession, trip: shopping_schemas.ShoppingTripCreate
) -> ShoppingTrip:
    """
    Tworzy w bazie danych nowy paragon (ShoppingTrip) wraz z powiązanymi produktami.
    """
    db_trip = ShoppingTrip(
        trip_date=trip.trip_date,
        store_name=trip.store_name,
        total_amount=trip.total_amount,
    )
    db.add(db_trip)
    await db.flush()

    for product_data in trip.products:
        db_product = Product(**product_data.model_dump(), trip_id=db_trip.id)
        db.add(db_product)

    await db.commit()

    # Zamiast odświeżać, pobieramy świeżo utworzony obiekt jeszcze raz,
    # ale tym razem z instrukcją, aby od razu załadował produkty.
    # To jest właśnie "eager loading".
    query = (
        select(ShoppingTrip)
        .where(ShoppingTrip.id == db_trip.id)
        .options(selectinload(ShoppingTrip.products))  # <--- TA LINIA JEST KLUCZOWA
    )
    result = await db.execute(query)
    created_trip = (
        result.scalar_one()
    )  # Używamy scalar_one, bo wiemy, że obiekt istnieje

    return created_trip


async def get_shopping_trips(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> list[ShoppingTrip]:
    """
    Pobiera listę wszystkich paragonów z bazy danych wraz z ich produktami.
    """
    query = (
        select(ShoppingTrip)
        .offset(skip)
        .limit(limit)
        .order_by(ShoppingTrip.trip_date.desc())  # Sortuj od najnowszych
        .options(
            selectinload(ShoppingTrip.products)
        )  # Eager loading jest tu równie kluczowy!
    )
    result = await db.execute(query)
    shopping_trips: list[ShoppingTrip] = list(result.scalars().all())
    return shopping_trips


async def update_shopping_trip(
    db: AsyncSession, trip_id: int, trip_update: shopping_schemas.ShoppingTripUpdate
) -> Optional[ShoppingTrip]:
    """
    Aktualizuje dane paragonu w bazie danych.
    Zwraca zaktualizowany obiekt lub None, jeśli nie znaleziono.
    """
    # 1. Pobierz obiekt z bazy
    query = (
        select(ShoppingTrip)
        .where(ShoppingTrip.id == trip_id)
        .options(selectinload(ShoppingTrip.products))
    )
    result = await db.execute(query)
    db_trip = result.scalar_one_or_none()

    if not db_trip:
        return None

    # 2. Pobierz dane do aktualizacji z modelu Pydantic
    update_data = trip_update.model_dump(exclude_unset=True)

    # 3. Zaktualizuj pola obiektu bazodanowego
    for key, value in update_data.items():
        setattr(db_trip, key, value)

    # 4. Zapisz zmiany w bazie
    await db.commit()
    await db.refresh(db_trip)

    return db_trip


async def update_product(
    db: AsyncSession, product_id: int, product_update: shopping_schemas.ProductUpdate
) -> Optional[Product]:
    """
    Aktualizuje dane produktu w bazie danych.
    Zwraca zaktualizowany obiekt lub None, jeśli nie znaleziono.
    """
    # 1. Pobierz obiekt z bazy
    query = select(Product).where(Product.id == product_id)
    result = await db.execute(query)
    db_product: Optional[Product] = result.scalar_one_or_none()

    if not db_product:
        return None

    # 2. Pobierz dane do aktualizacji z modelu Pydantic
    update_data = product_update.model_dump(exclude_unset=True)

    # 3. Zaktualizuj pola obiektu bazodanowego
    for key, value in update_data.items():
        setattr(db_product, key, value)

    # 4. Zapisz zmiany w bazie
    await db.commit()
    await db.refresh(db_product)

    return db_product


async def delete_shopping_trip(db: AsyncSession, trip_id: int) -> bool:
    """Usuwa paragon z bazy danych na podstawie jego ID.

    Produkty powiązane z paragonem są automatycznie usuwane dzięki konfiguracji
    cascade w modelu.

    Returns:
        bool: True jeśli obiekt został znaleziony i usunięty, False jeśli nie znaleziono
    """
    # 1. Znajdź obiekt w bazie
    query = select(ShoppingTrip).where(ShoppingTrip.id == trip_id)
    result = await db.execute(query)
    db_trip = result.scalar_one_or_none()

    if not db_trip:
        return False  # Paragonu nie znaleziono

    # 2. Usuń paragon (produkty zostaną usunięte automatycznie dzięki cascade)
    await db.delete(db_trip)
    await db.commit()

    return True


async def delete_product(db: AsyncSession, product_id: int) -> bool:
    """
    Usuwa produkt z bazy danych na podstawie jego ID.
    Zwraca True, jeśli obiekt został znaleziony i usunięty.
    Zwraca False, jeśli obiekt nie został znaleziony.
    """
    # 1. Znajdź obiekt w bazie
    query = select(Product).where(Product.id == product_id)
    result = await db.execute(query)
    db_product = result.scalar_one_or_none()

    if not db_product:
        return False  # Produktu nie znaleziono

    # 2. Usuń obiekt i zapisz zmiany
    await db.delete(db_product)
    await db.commit()

    return True
