from typing import Dict, List

from fastapi import APIRouter

router = APIRouter()

# Przykładowe dane
DUMMY_PRODUCTS = [
    {"id": 1, "name": "Mleko Łaciate", "unified_category": "Nabiał"},
    {"id": 2, "name": "Chleb", "unified_category": "Pieczywo"},
]


@router.get("/pantry/products", response_model=List[Dict])
async def get_pantry_products() -> None:
    return DUMMY_PRODUCTS
