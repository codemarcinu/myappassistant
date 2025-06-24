from __future__ import annotations

from sqlalchemy import text

from backend.core.database import engine


async def run_migrations() -> None:
    """Run database migrations."""
    async with engine.begin() as conn:
        # Create products table if it doesn't exist
        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR NOT NULL,
                price FLOAT DEFAULT 0.0,
                unit VARCHAR,
                category VARCHAR,
                discount FLOAT DEFAULT 0.0,
                notes TEXT,
                created_at DATETIME,
                updated_at DATETIME
            )
        """
            )
        )
        print("Products table created/verified")

        # Create shopping_trips table if it doesn't exist
        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS shopping_trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_date DATETIME,
                store_name VARCHAR,
                total_amount FLOAT DEFAULT 0.0,
                created_at DATETIME,
                updated_at DATETIME
            )
        """
            )
        )
        print("Shopping_trips table created/verified")

        # Now add columns if they don't exist (safe operations)
        # Check if the discount column exists
        result = await conn.execute(
            text(
                """
            SELECT name FROM pragma_table_info('products')
            WHERE name='discount'
        """
            )
        )
        if not result.scalar():
            # Add the discount column if it doesn't exist
            await conn.execute(
                text(
                    """
                ALTER TABLE products
                ADD COLUMN discount FLOAT DEFAULT 0.0
            """
                )
            )
            print("Added discount column to products table")
        else:
            print("Discount column already exists")

        # Check if the category column exists
        result = await conn.execute(
            text(
                """
            SELECT name FROM pragma_table_info('products')
            WHERE name='category'
        """
            )
        )
        if not result.scalar():
            # Add the category column if it doesn't exist
            await conn.execute(
                text(
                    """
                ALTER TABLE products
                ADD COLUMN category VARCHAR
            """
                )
            )
            print("Added category column to products table")
        else:
            print("Category column already exists")

        # Check if created_at column exists in shopping_trips table
        result = await conn.execute(
            text(
                """
            SELECT name FROM pragma_table_info('shopping_trips')
            WHERE name='created_at'
        """
            )
        )
        if not result.scalar():
            # Add the created_at column if it doesn't exist
            await conn.execute(
                text(
                    """
                ALTER TABLE shopping_trips
                ADD COLUMN created_at DATETIME
            """
                )
            )
            print("Added created_at column to shopping_trips table")
        else:
            print("Created_at column already exists in shopping_trips")

        # Check if updated_at column exists in shopping_trips table
        result = await conn.execute(
            text(
                """
            SELECT name FROM pragma_table_info('shopping_trips')
            WHERE name='updated_at'
        """
            )
        )
        if not result.scalar():
            # Add the updated_at column if it doesn't exist
            await conn.execute(
                text(
                    """
                ALTER TABLE shopping_trips
                ADD COLUMN updated_at DATETIME
            """
                )
            )
            print("Added updated_at column to shopping_trips table")
        else:
            print("Updated_at column already exists in shopping_trips")

        # Check if created_at column exists in products table
        result = await conn.execute(
            text(
                """
            SELECT name FROM pragma_table_info('products')
            WHERE name='created_at'
        """
            )
        )
        if not result.scalar():
            # Add the created_at column if it doesn't exist
            await conn.execute(
                text(
                    """
                ALTER TABLE products
                ADD COLUMN created_at DATETIME
            """
                )
            )
            print("Added created_at column to products table")
        else:
            print("Created_at column already exists in products")

        # Check if updated_at column exists in products table
        result = await conn.execute(
            text(
                """
            SELECT name FROM pragma_table_info('products')
            WHERE name='updated_at'
        """
            )
        )
        if not result.scalar():
            # Add the updated_at column if it doesn't exist
            await conn.execute(
                text(
                    """
                ALTER TABLE products
                ADD COLUMN updated_at DATETIME
            """
                )
            )
            print("Added updated_at column to products table")
        else:
            print("Updated_at column already exists in products")

        # Check if price column exists in products table
        result = await conn.execute(
            text(
                """
            SELECT name FROM pragma_table_info('products')
            WHERE name='price'
        """
            )
        )
        if not result.scalar():
            # Add the price column if it doesn't exist
            await conn.execute(
                text(
                    """
                ALTER TABLE products
                ADD COLUMN price FLOAT DEFAULT 0.0
            """
                )
            )
            print("Added price column to products table")
        else:
            print("Price column already exists in products")

        # Check if unit column exists in products table
        result = await conn.execute(
            text(
                """
            SELECT name FROM pragma_table_info('products')
            WHERE name='unit'
        """
            )
        )
        if not result.scalar():
            # Add the unit column if it doesn't exist
            await conn.execute(
                text(
                    """
                ALTER TABLE products
                ADD COLUMN unit VARCHAR
            """
                )
            )
            print("Added unit column to products table")
        else:
            print("Unit column already exists in products")

        # Check if notes column exists in products table
        result = await conn.execute(
            text(
                """
            SELECT name FROM pragma_table_info('products')
            WHERE name='notes'
        """
            )
        )
        if not result.scalar():
            # Add the notes column if it doesn't exist
            await conn.execute(
                text(
                    """
                ALTER TABLE products
                ADD COLUMN notes TEXT
            """
                )
            )
            print("Added notes column to products table")
        else:
            print("Notes column already exists in products")

        print("Database migrations completed successfully")
