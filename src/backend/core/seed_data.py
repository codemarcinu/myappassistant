import datetime
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.shopping import Product, ShoppingTrip

# Sample seed data
SEED_DATA: Dict[str, List[Dict]] = {
    "shopping_trips": [
        {
            "store_name": "Biedronka",
            "trip_date": datetime.date.today() - datetime.timedelta(days=2),
            "total_amount": 45.67,
            "products": [
                {
                    "name": "Mleko",
                    "quantity": 1,
                    "unit_price": 4.50,
                    "category": "Nabiał",
                },
                {
                    "name": "Chleb",
                    "quantity": 1,
                    "unit_price": 3.20,
                    "category": "Pieczywo",
                },
                {
                    "name": "Masło",
                    "quantity": 1,
                    "unit_price": 6.80,
                    "category": "Nabiał",
                },
                {
                    "name": "Jabłka",
                    "quantity": 1.5,
                    "unit_price": 3.99,
                    "category": "Owoce",
                },
                {
                    "name": "Ser żółty",
                    "quantity": 0.25,
                    "unit_price": 29.99,
                    "category": "Nabiał",
                },
            ],
        },
        {
            "store_name": "Lidl",
            "trip_date": datetime.date.today() - datetime.timedelta(days=5),
            "total_amount": 62.35,
            "products": [
                {
                    "name": "Kurczak",
                    "quantity": 1.2,
                    "unit_price": 16.99,
                    "category": "Mięso",
                },
                {
                    "name": "Ziemniaki",
                    "quantity": 2,
                    "unit_price": 2.49,
                    "category": "Warzywa",
                },
                {
                    "name": "Jogurt",
                    "quantity": 4,
                    "unit_price": 1.49,
                    "category": "Nabiał",
                },
                {
                    "name": "Makaron",
                    "quantity": 2,
                    "unit_price": 4.99,
                    "category": "Suche",
                },
                {
                    "name": "Sos pomidorowy",
                    "quantity": 1,
                    "unit_price": 5.99,
                    "category": "Sosy",
                },
            ],
        },
        {
            "store_name": "Auchan",
            "trip_date": datetime.date.today() - datetime.timedelta(days=10),
            "total_amount": 127.89,
            "products": [
                {
                    "name": "Wino",
                    "quantity": 2,
                    "unit_price": 25.99,
                    "category": "Alkohol",
                },
                {
                    "name": "Ser pleśniowy",
                    "quantity": 0.3,
                    "unit_price": 59.99,
                    "category": "Nabiał",
                },
                {
                    "name": "Oliwa z oliwek",
                    "quantity": 1,
                    "unit_price": 29.99,
                    "category": "Oleje",
                },
                {
                    "name": "Czekolada",
                    "quantity": 3,
                    "unit_price": 4.99,
                    "category": "Słodycze",
                },
                {
                    "name": "Kawa",
                    "quantity": 1,
                    "unit_price": 24.99,
                    "category": "Napoje",
                },
            ],
        },
    ]
}


async def seed_database(db: Optional[AsyncSession] = None) -> None:
    """
    Seeds the database with initial data.
    This function should be called during application initialization.

    Args:
        db: Optional database session
    """
    if db is None:
        return

    # Check if database is already seeded
    result = await db.execute(select(ShoppingTrip).limit(1))
    existing_trip = result.scalars().first()

    if existing_trip:
        print("Database already has data, skipping seeding")
        return

    print("Seeding database with initial shopping data...")

    # Insert shopping trips and their products
    for trip_data in SEED_DATA["shopping_trips"]:
        products_data = trip_data.pop("products")
        trip = ShoppingTrip(**trip_data)
        db.add(trip)
        await db.flush()  # Get the trip ID

        for product_data in products_data:
            product = Product(trip_id=trip.id, **product_data)
            db.add(product)

    await db.commit()
    print(
        f"Successfully seeded database with {len(SEED_DATA['shopping_trips'])} shopping trips"
    )
