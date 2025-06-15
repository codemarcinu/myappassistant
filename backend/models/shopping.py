# w pliku backend/models/shopping.py
from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..core.database import Base  # Importujemy naszą klasę bazową z kroku 2


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
    unit_price = Column(Float, nullable=True)
    discount = Column(Float, default=0.0)
    category = Column(String, nullable=True)  # New field for product category

    # Klucz obcy - każdy produkt musi należeć do jakiegoś paragonu.
    trip_id = Column(Integer, ForeignKey("shopping_trips.id"), nullable=False)

    # Relacja zwrotna do paragonu.
    trip = relationship("ShoppingTrip", back_populates="products")
