import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.config import settings

logger = logging.getLogger(__name__)

# Database URL is now loaded from central configuration.
# We're using SQLite which will store the database in a file.

# Create async SQLAlchemy engine with optimized connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30,  # Connection timeout
        "isolation_level": "EXCLUSIVE",  # Better concurrency for SQLite
    },
    echo=False,  # Disable SQL logging in production
    poolclass=StaticPool,  # Use StaticPool for SQLite async engine
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
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
class Base(DeclarativeBase):
    pass


# Enhanced async context manager for database sessions
@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Enhanced async context manager for database sessions with proper error handling"""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        await session.close()


# Dependency to get an async database session (for FastAPI)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions"""
    async with get_db_session() as session:
        yield session


# Database performance monitoring with enhanced metrics
class DatabaseMetrics:
    """Enhanced database performance metrics with memory monitoring"""

    def __init__(self):
        self.query_count = 0
        self.slow_queries = []
        self.connection_errors = 0
        self.connection_pool_stats = {
            "checked_in": 0,
            "checked_out": 0,
            "overflow": 0,
            "invalid": 0,
        }

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

    def update_pool_stats(self, pool):
        """Update connection pool statistics"""
        if hasattr(pool, "_pool"):
            self.connection_pool_stats.update(
                {
                    "checked_in": pool._pool.qsize(),
                    "checked_out": pool.size() - pool._pool.qsize(),
                    "overflow": pool.overflow(),
                    "invalid": pool.invalid(),
                }
            )

    def get_stats(self) -> dict:
        """Get comprehensive database statistics"""
        return {
            "total_queries": self.query_count,
            "slow_queries_count": len(self.slow_queries),
            "connection_errors": self.connection_errors,
            "slow_queries": self.slow_queries[-10:],  # Last 10 slow queries
            "pool_stats": self.connection_pool_stats,
        }


# Global metrics instance
db_metrics = DatabaseMetrics()


# Health check function for database
async def check_database_health() -> dict:
    """Check database health and connection pool status"""
    try:
        async with get_db_session() as session:
            # Simple query to test connection
            await session.execute(text("SELECT 1"))

            # Update pool stats
            db_metrics.update_pool_stats(engine.pool)

            return {
                "status": "healthy",
                "pool_stats": db_metrics.connection_pool_stats,
                "total_queries": db_metrics.query_count,
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "pool_stats": db_metrics.connection_pool_stats,
        }
