# w pliku backend/schemas/shopping_schemas.py
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

# --- Schematy dla Produktu ---


# Pola wspólne dla tworzenia i odczytu
class ProductBase(BaseModel):
    name: str
    quantity: float = 1.0
    unit_price: Optional[float] = None
    expiration_date: Optional[date] = None
    is_consumed: bool = False


# Schemat używany przy tworzeniu nowego produktu (nie znamy jeszcze jego ID)
class ProductCreate(ProductBase):
    pass


# Schemat używany przy aktualizacji produktu
class ProductUpdate(BaseModel):
    """
    Model Pydantic dla aktualizacji istniejącego produktu.
    Wszystkie pola są opcjonalne.
    """

    name: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


# Schemat używany przy odczytywaniu produktu z bazy danych
class ProductSchema(ProductBase):
    id: int
    trip_id: int

    # Konfiguracja pozwalająca tworzyć schemat z obiektu SQLAlchemy
    model_config = ConfigDict(from_attributes=True)


# --- Schematy dla Paragonu (ShoppingTrip) ---


class ShoppingTripBase(BaseModel):
    trip_date: date
    store_name: str
    total_amount: Optional[float] = None


# Schemat do tworzenia nowego paragonu - zawiera listę produktów do stworzenia
class ShoppingTripCreate(ShoppingTripBase):
    products: List[ProductCreate] = []


# Schemat do aktualizacji paragonu
class ShoppingTripUpdate(BaseModel):
    """
    Model Pydantic dla aktualizacji istniejącego paragonu.
    Wszystkie pola są opcjonalne.
    """

    trip_date: Optional[date] = None
    store_name: Optional[str] = None
    total_amount: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


# Schemat do odczytu paragonu z bazy - zawiera listę wczytanych produktów
class ShoppingTrip(ShoppingTripBase):
    id: int
    products: List[ProductSchema] = []

    model_config = ConfigDict(from_attributes=True)


class ShoppingTripSummary(BaseModel):
    """
    Schema for the summary of a shopping trip.
    """

    total_products: int
    total_cost: float

    model_config = ConfigDict(from_attributes=True)
