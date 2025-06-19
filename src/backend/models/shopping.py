from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import deferred, relationship

from ..core.database import Base


class ShoppingTrip(Base):
    __tablename__ = "shopping_trips"

    id = Column(Integer, primary_key=True, index=True)
    trip_date = Column(Date, nullable=False)
    store_name = Column(String, index=True)
    total_amount = Column(Float, nullable=True)

    # Ta relacja tworzy połączenie z produktami.
    # Jeden paragon (ShoppingTrip) może mieć wiele produktów (Product).
    products = relationship(
        "Product", back_populates="trip", cascade="all, delete-orphan"
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    quantity = Column(Float, default=1.0)
    unit_price = deferred(Column(Float, nullable=True))  # Defer loading unless needed
    discount = Column(Float, default=0.0)
    category = Column(String, index=True, nullable=True)  # Index for category queries
    expiration_date = Column(
        Date, index=True, nullable=True
    )  # Index for expiration queries
    is_consumed = Column(Boolean, default=False, nullable=False, index=True)

    # Klucz obcy - każdy produkt musi należeć do jakiegoś paragonu.
    trip_id = Column(Integer, ForeignKey("shopping_trips.id"), nullable=False)

    # Relacja zwrotna do paragonu.
    trip = relationship("ShoppingTrip", back_populates="products", lazy="selectin")


# Composite indexes for common product queries
Index("ix_product_trip_category", Product.trip_id, Product.category)
Index("ix_product_expiration", Product.expiration_date, Product.is_consumed)

# Index for shopping trips by date
Index("ix_trip_date", ShoppingTrip.trip_date)
