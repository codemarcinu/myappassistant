from __future__ import annotations

from typing import (Any, AsyncGenerator, Callable, Coroutine, Dict, List,
                    Optional, Union)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.repositories import FoodItemRepository, UserRepository
from backend.models.shopping import Product
from backend.models.user_profile import UserProfile


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: int) -> Dict[str, Any] | None:
        result = await self.session.execute(
            select(UserProfile).where(UserProfile.id == user_id)
        )
        user = result.scalars().first()
        if user:
            return {
                "user_id": user.user_id,
                "session_id": user.session_id,
                "created_at": user.created_at.isoformat(),
                "last_active": user.last_active.isoformat(),
                "preferences": user.preferences,
                "schedule": user.schedule,
                "topics_of_interest": user.topics_of_interest,
                "activities": [activity.to_dict() for activity in user.activities],
            }
        return None

    async def create(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        user = UserProfile(**user_data)
        self.session.add(user)
        await self.session.commit()
        return {
            "user_id": user.user_id,
            "session_id": user.session_id,
            "created_at": user.created_at.isoformat(),
            "last_active": user.last_active.isoformat(),
            "preferences": user.preferences,
            "schedule": user.schedule,
            "topics_of_interest": user.topics_of_interest,
            "activities": [activity.to_dict() for activity in user.activities],
        }


class SQLAlchemyFoodItemRepository(FoodItemRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, item_id: int) -> Dict[str, Any] | None:
        result = await self.session.execute(
            select(Product).where(Product.id == item_id)
        )
        item = result.scalars().first()
        if item:
            return {
                "id": item.id,
                "name": item.name,
                "category": item.category,
                "unit_price": item.unit_price,
                "quantity": item.quantity,
                "unit": item.unit,
                "expiration_date": (
                    item.expiration_date.isoformat() if item.expiration_date else None
                ),
                "is_consumed": bool(item.is_consumed),
                "notes": item.notes,
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat(),
                "trip_id": item.trip_id,
            }
        return None

    async def create(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        item = Product(**item_data)
        self.session.add(item)
        await self.session.commit()
        return {
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "unit_price": item.unit_price,
            "quantity": item.quantity,
            "unit": item.unit,
            "expiration_date": (
                item.expiration_date.isoformat() if item.expiration_date else None
            ),
            "is_consumed": bool(item.is_consumed),
            "notes": item.notes,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
            "trip_id": item.trip_id,
        }

    async def search(self, query: str) -> List[Dict[str, Any]]:
        result = await self.session.execute(
            select(Product).where(Product.name.ilike(f"%{query}%"))
        )
        return [
            {
                "id": item.id,
                "name": item.name,
                "category": item.category,
                "unit_price": item.unit_price,
                "quantity": item.quantity,
                "unit": item.unit,
                "expiration_date": (
                    item.expiration_date.isoformat() if item.expiration_date else None
                ),
                "is_consumed": bool(item.is_consumed),
                "notes": item.notes,
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat(),
                "trip_id": item.trip_id,
            }
            for item in result.scalars().all()
        ]
