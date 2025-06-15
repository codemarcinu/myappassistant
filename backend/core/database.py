from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

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
