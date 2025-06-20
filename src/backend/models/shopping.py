from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import deferred, relationship
from sqlalchemy.sql import func

from ..core.database import Base


class ShoppingTrip(Base):
    __tablename__ = "shopping_trips"

    id = Column(Integer, primary_key=True, index=True)
    trip_date = Column(Date, nullable=False, index=True)
    store_name = Column(String, nullable=False, index=True)
    total_amount = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Ta relacja tworzy połączenie z produktami.
    # Jeden paragon (ShoppingTrip) może mieć wiele produktów (Product).
    products = relationship(
        "Product", back_populates="trip", cascade="all, delete-orphan"
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=True, index=True)
    price = Column(Float, nullable=True)
    quantity = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    expiration_date = Column(Date, nullable=True, index=True)
    is_consumed = Column(
        Integer, default=0, index=True
    )  # 0 = not consumed, 1 = consumed
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Klucz obcy - każdy produkt musi należeć do jakiegoś paragonu.
    trip_id = Column(
        Integer, ForeignKey("shopping_trips.id"), nullable=False, index=True
    )

    # Relacja zwrotna do paragonu.
    trip = relationship("ShoppingTrip", back_populates="products", lazy="selectin")


# Composite indexes for common product queries
Index("ix_product_trip_category", Product.trip_id, Product.category)
Index("ix_product_expiration", Product.expiration_date, Product.is_consumed)
Index("ix_product_name_category", Product.name, Product.category)
Index("ix_product_consumed_date", Product.is_consumed, Product.expiration_date)

# Index for shopping trips by date
Index("ix_trip_date", ShoppingTrip.trip_date)
Index("ix_trip_store_date", ShoppingTrip.store_name, ShoppingTrip.trip_date)
Index("ix_trip_created", ShoppingTrip.created_at)
