from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Adres URL do naszej bazy danych. Używamy SQLite, która zapisze bazę
# do pliku o nazwie 'foodsave.db' w głównym katalogu projektu.
DATABASE_URL = "sqlite+aiosqlite:///./foodsave.db"

# Tworzymy 'silnik' bazy danych. 'echo=True' sprawi, że w konsoli
# będziemy widzieć wszystkie wykonywane zapytania SQL - bardzo przydatne do debugowania.
engine = create_async_engine(DATABASE_URL, echo=True)

# Tworzymy 'fabrykę' sesji. Sesja to nasz główny punkt kontaktu z bazą danych.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    class_=AsyncSession
)

# Tworzymy bazową klasę dla naszych modeli. Wszystkie nasze modele
# (reprezentujące tabele w bazie danych) będą po niej dziedziczyć.
Base = declarative_base()