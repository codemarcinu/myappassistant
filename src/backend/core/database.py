from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import declarative_base

# Adres URL do naszej bazy danych. Używamy SQLite, która zapisze bazę
# danych w pliku na dysku.
DATABASE_URL = "sqlite+aiosqlite:///./shopping.db"

# Tworzymy silnik SQLAlchemy, który będzie zarządzał połączeniami do bazy danych.
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,  # Ustaw na True, aby widzieć zapytania SQL
)

# Tworzymy fabrykę sesji, która będzie tworzyć nowe sesje bazy danych.
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

# Tworzymy bazową klasę dla modeli SQLAlchemy. Wszystkie nasze modele
# (reprezentujące tabele w bazie danych) będą po niej dziedziczyć.
Base = declarative_base()

# Osobny engine i sesja dla bazy danych testowej w pamięci
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
AsyncTestSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine, class_=AsyncSession
)


async def get_db() -> AsyncSession:
    """Dependency to get a database session."""
    async with AsyncSessionLocal() as session:
        yield session


async def get_test_db() -> AsyncSession:
    """Dependency to get a test database session."""
    async with AsyncTestSessionLocal() as session:
        # Tutaj można by w przyszłości zainicjować schemat bazy danych, jeśli potrzeba
        yield session
