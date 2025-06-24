import datetime
import json
import logging
import os
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.shopping import Product, ShoppingTrip

logger = logging.getLogger(__name__)


def load_seed_data() -> Dict[str, List[Dict[str, Any]]]:
    """Loads seed data from a JSON file."""
    path = os.path.join(os.path.dirname(__file__), "seed_data.json")
    with open(path, "r", encoding="utf-8") as f:
        data: Dict[str, List[Dict[str, Any]]] = json.load(f)
    # Convert date strings to date objects
    for trip in data["shopping_trips"]:
        trip["trip_date"] = datetime.date.fromisoformat(trip["trip_date"])
    return data


async def seed_database(db: Optional[AsyncSession] = None) -> None:
    """
    Seeds the database with initial data.
    This function should be called during application initialization.

    Args:
        db: Optional database session
    """
    if db is None:
        return

    try:
        # Check if database is already seeded
        result = await db.execute(select(ShoppingTrip).limit(1))
        existing_trip = result.scalars().first()

        if existing_trip:
            logger.info("Database already has data, skipping seeding.")
            return

        logger.info("Seeding database with initial shopping data...")

        seed_data = load_seed_data()
        # Insert shopping trips and their products
        for trip_data in seed_data["shopping_trips"]:
            products_data = trip_data.pop("products")
            trip = ShoppingTrip(**trip_data)
            db.add(trip)
            await db.flush()  # Get the trip ID

            for product_data in products_data:
                product = Product(trip_id=trip.id, **product_data)
                db.add(product)

        await db.commit()
        logger.info(
            f"Successfully seeded database with {len(seed_data['shopping_trips'])} shopping trips."
        )
    except SQLAlchemyError as e:
        logger.error(f"Database seeding failed: {e}")
        await db.rollback()
    except Exception as e:
        logger.error(f"An unexpected error occurred during database seeding: {e}")
        await db.rollback()
