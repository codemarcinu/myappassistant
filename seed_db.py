import asyncio
from backend.core.database import engine, Base
from backend.core.migrations import run_migrations
from backend.core.seed_data import seed_database
from backend.core.database import AsyncSessionLocal

async def init_db():
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # Drop all tables first
        await conn.run_sync(Base.metadata.create_all)  # Create tables with new schema
    
    print("Running migrations...")
    await run_migrations()
    
    print("Seeding database with initial data...")
    async with AsyncSessionLocal() as session:
        await seed_database(session)
    
    print("Database initialization completed successfully!")

if __name__ == "__main__":
    asyncio.run(init_db()) 