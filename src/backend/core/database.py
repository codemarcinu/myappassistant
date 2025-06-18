from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from ..config import settings

# Adres URL do naszej bazy danych jest teraz wczytywany z centralnej konfiguracji.
# Używamy SQLite, która zapisze bazę danych w pliku na dysku.

# Tworzymy silnik SQLAlchemy, który będzie zarządzał połączeniami do bazy danych.
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=30,
    echo=False,
    connect_args={
        "timeout": 15,
        "check_same_thread": False,
        "isolation_level": None,  # Disable all isolation level handling
        "uri": True,  # Force URI mode to bypass SQLite PRAGMA queries
    },
    module=__import__("aiosqlite"),  # Force use of aiosqlite
    future=True,  # Enable SQLAlchemy 2.0 behavior
    execution_options={"isolation_level": "AUTOCOMMIT"},  # Explicit autocommit mode
)

# Tworzymy fabrykę sesji, która będzie tworzyć nowe sesje bazy danych.
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)


# Tworzymy bazową klasę dla modeli SQLAlchemy. Wszystkie nasze modele
# (reprezentujące tabele w bazie danych) będą po niej dziedziczyć.
class Base(DeclarativeBase):
    pass


# Osobny engine i sesja dla bazy danych testowej w pamięci
TEST_DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
AsyncTestSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine, class_=AsyncSession
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get a database session."""
    async with AsyncSessionLocal() as session:
        try:
            # Explicitly initialize connection
            await session.execute(text("SELECT 1"))
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"Database error: {str(e)}")
            raise
        finally:
            await session.close()


async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get a test database session."""
    async with AsyncTestSessionLocal() as session:
        try:
            # Explicitly initialize connection
            await session.execute(text("SELECT 1"))
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"Test database error: {str(e)}")
            raise
        finally:
            await session.close()
