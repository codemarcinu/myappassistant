from datetime import date
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Upewnij się, że importujesz swoje modele poprawnie
from .models.shopping import ShoppingTrip


async def get_trips_by_date_range(
    db: AsyncSession, start_date: date, end_date: date
) -> Sequence[ShoppingTrip]:
    """
    Asynchronously retrieves shopping trips from the database within a given date range.
    """
    query = (
        select(ShoppingTrip)
        .where(ShoppingTrip.trip_date >= start_date)
        .where(ShoppingTrip.trip_date <= end_date)
        .order_by(ShoppingTrip.trip_date.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()
