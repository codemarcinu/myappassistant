from sqlalchemy import text

from .database import engine


async def run_migrations():
    """Run database migrations."""
    async with engine.begin() as conn:
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
