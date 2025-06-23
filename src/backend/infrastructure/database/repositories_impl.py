from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.repositories import FoodItemRepository, UserRepository
from backend.models.shopping import Product
from backend.models.user_profile import UserProfile
from typing import Any, Dict, List, Optional, Union, Callable
from typing import AsyncGenerator, Coroutine


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: int) -> dict | None:
        result = await self.session.execute(
            select(UserProfile).where(UserProfile.id == user_id)
        )
        user = result.scalars().first()
        return user.to_dict() if user else None

    async def create(self, user_data: dict) -> dict:
        user = UserProfile(**user_data)
        self.session.add(user)
        await self.session.commit()
        return user.to_dict()


class SQLAlchemyFoodItemRepository(FoodItemRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, item_id: int) -> dict | None:
        result = await self.session.execute(
            select(Product).where(Product.id == item_id)
        )
        item = result.scalars().first()
        return item.to_dict() if item else None

    async def create(self, item_data: dict) -> dict:
        item = Product(**item_data)
        self.session.add(item)
        await self.session.commit()
        return item.to_dict()

    async def search(self, query: str) -> list[dict]:
        result = await self.session.execute(
            select(Product).where(Product.name.ilike(f"%{query}%"))
        )
        return [item.to_dict() for item in result.scalars().all()]
