from datetime import date, timedelta
from ..models.shopping import ShoppingTrip, Product

# Example seed data for testing with fixed dates
SEED_DATA = [
    {
        "trip_date": date(2025, 6, 12),  # przedwczoraj
        "store_name": "Biedronka",
        "total_amount": 15.50,
        "products": [
            {
                "name": "masło",
                "quantity": 1.0,
                "unit_price": 7.50,
                "discount": 0.0,
                "category": "Nabiał"
            },
            {
                "name": "jajka",
                "quantity": 10.0,
                "unit_price": 0.80,
                "discount": 0.0,
                "category": "Nabiał"
            }
        ]
    },
    {
        "trip_date": date(2025, 6, 11),  # 3 dni temu
        "store_name": "Lidl",
        "total_amount": 5.00,
        "products": [
            {
                "name": "chleb",
                "quantity": 1.0,
                "unit_price": 5.00,
                "discount": 0.0,
                "category": "Pieczywo"
            }
        ]
    },
    {
        "trip_date": date(2025, 6, 13),  # wczoraj
        "store_name": "Żabka",
        "total_amount": 10.00,
        "products": [
            {
                "name": "mleko",
                "quantity": 2.0,
                "unit_price": 5.00,
                "discount": 0.0,
                "category": "Nabiał"
            }
        ]
    }
]

async def seed_database(db):
    """Seed the database with initial data."""
    for trip_data in SEED_DATA:
        # Create shopping trip
        trip = ShoppingTrip(
            trip_date=trip_data["trip_date"],
            store_name=trip_data["store_name"],
            total_amount=trip_data["total_amount"]
        )
        db.add(trip)
        await db.flush()

        # Create products for the trip
        for product_data in trip_data["products"]:
            product = Product(
                name=product_data["name"],
                quantity=product_data["quantity"],
                unit_price=product_data["unit_price"],
                discount=product_data["discount"],
                category=product_data["category"],
                trip_id=trip.id
            )
            db.add(product)

    await db.commit() 