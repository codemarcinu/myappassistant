from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from backend.config import settings

# Adres URL do naszej bazy danych. Używamy SQLite, która zapisze bazę
# do pliku o nazwie 'foodsave.db' w głównym katalogu projektu.
DATABASE_URL = "sqlite+aiosqlite:///./foodsave.db"

# Tworzymy 'silnik' bazy danych z poolingiem.
engine = create_async_engine(
    DATABASE_URL, echo=True, pool_size=10, max_overflow=20, future=True
)

# Tworzymy 'fabrykę' sesji. Sesja to nasz główny punkt kontaktu z bazą danych.
AsyncSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, autoflush=False, class_=AsyncSession
)

# Tworzymy bazową klasę dla naszych modeli. Wszystkie nasze modele
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
