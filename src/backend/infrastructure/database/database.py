from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.config import settings

# Database URL is now loaded from central configuration.
# We're using SQLite which will store the database in a file.

# Create async SQLAlchemy engine with connection pooling and optimizations
engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30,  # Connection timeout
        "isolation_level": "EXCLUSIVE",  # Better concurrency for SQLite
    },
    echo=False,  # Disable SQL logging in production
    poolclass=StaticPool,  # Use static pool for SQLite
    pool_pre_ping=True,  # Verify connections before use
)

# Create async session factory with optimizations
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects loaded after commit
)

# Create base class for SQLAlchemy models
Base = declarative_base()


# Dependency to get an async database session
async def get_db() -> AsyncGenerator:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Database performance monitoring
class DatabaseMetrics:
    """Database performance metrics"""

    def __init__(self):
        self.query_count = 0
        self.slow_queries = []
        self.connection_errors = 0

    def record_query(self, query_time: float, query: str):
        """Record query performance"""
        self.query_count += 1
        if query_time > 1.0:  # Queries taking more than 1 second
            self.slow_queries.append(
                {"query": query, "time": query_time, "timestamp": "now"}
            )

    def record_connection_error(self):
        """Record connection error"""
        self.connection_errors += 1

    def get_stats(self) -> dict:
        """Get database statistics"""
        return {
            "total_queries": self.query_count,
            "slow_queries_count": len(self.slow_queries),
            "connection_errors": self.connection_errors,
            "slow_queries": self.slow_queries[-10:],  # Last 10 slow queries
        }


# Global metrics instance
db_metrics = DatabaseMetrics()
