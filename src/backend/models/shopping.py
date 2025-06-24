from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List

from sqlalchemy import (Date, DateTime, Float, ForeignKey, Index, Integer,
                        String, Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.core.database import Base


class ShoppingTrip(Base):
    __tablename__ = "shopping_trips"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trip_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    store_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    total_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Ta relacja tworzy połączenie z produktami.
    # Jeden paragon (ShoppingTrip) może mieć wiele produktów (Product).
    products: Mapped[List["Product"]] = relationship(
        f"{__name__}.Product",
        back_populates="trip",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje obiekt ShoppingTrip na słownik."""
        return {
            "id": self.id,
            "trip_date": self.trip_date.isoformat(),
            "store_name": self.store_name,
            "total_amount": self.total_amount,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "products": [product.to_dict() for product in self.products],
        }


class Product(Base):
    __tablename__ = "products"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    unit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String, nullable=True)
    expiration_date: Mapped[date | None] = mapped_column(
        Date, nullable=True, index=True
    )
    is_consumed: Mapped[int] = mapped_column(
        Integer, default=0, index=True
    )  # 0 = not consumed, 1 = consumed
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Klucz obcy - każdy produkt musi należeć do jakiegoś paragonu.
    trip_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("shopping_trips.id"), nullable=False, index=True
    )

    # Relacja zwrotna do paragonu.
    trip: Mapped["ShoppingTrip"] = relationship(
        f"{__name__}.ShoppingTrip",
        back_populates="products",
        lazy="selectin",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje obiekt Product na słownik."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "unit_price": self.unit_price,
            "quantity": self.quantity,
            "unit": self.unit,
            "expiration_date": (
                self.expiration_date.isoformat() if self.expiration_date else None
            ),
            "is_consumed": bool(self.is_consumed),
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "trip_id": self.trip_id,
        }


# Composite indexes for common product queries
Index("ix_product_trip_category", Product.trip_id, Product.category)
Index("ix_product_expiration", Product.expiration_date, Product.is_consumed)
Index("ix_product_name_category", Product.name, Product.category)
Index("ix_product_consumed_date", Product.is_consumed, Product.expiration_date)

# Index for shopping trips by date
Index("ix_trip_date", ShoppingTrip.trip_date)
Index("ix_trip_store_date", ShoppingTrip.store_name, ShoppingTrip.trip_date)
Index("ix_trip_created", ShoppingTrip.created_at)
