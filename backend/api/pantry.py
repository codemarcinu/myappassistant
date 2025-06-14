from fastapi import APIRouter
from typing import List, Dict

router = APIRouter()

# Przykładowe dane
DUMMY_PRODUCTS = [
    {"id": 1, "name": "Mleko Łaciate", "unified_category": "Nabiał"},
    {"id": 2, "name": "Chleb", "unified_category": "Pieczywo"},
]

@router.get("/pantry/products", response_model=List[Dict])
async def get_pantry_products():
    return DUMMY_PRODUCTS 