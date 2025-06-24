import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import AsyncSessionLocal, engine

logger = logging.getLogger(__name__)


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

    def __init__(self) -> None:
        self.query_count: int = 0
        self.slow_queries: List[Dict[str, Any]] = []
        self.connection_errors: int = 0
        self.connection_pool_stats: Dict[str, int] = {
            "checked_in": 0,
            "checked_out": 0,
            "overflow": 0,
            "invalid": 0,
        }

    def record_query(self, query_time: float, query: str) -> None:
        """Record query performance"""
        self.query_count += 1
        if query_time > 1.0:  # Queries taking more than 1 second
            self.slow_queries.append(
                {"query": query, "time": query_time, "timestamp": "now"}
            )

    def record_connection_error(self) -> None:
        """Record connection error"""
        self.connection_errors += 1

    def update_pool_stats(self, pool: Any) -> None:
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
    """✅ REQUIRED: Check database health and connection pool status

    Returns:
        dict: Status details with health information
    """
    try:
        async with get_db_session() as session:
            # Simple query to test connection
            await session.execute(text("SELECT 1"))

            # Update pool stats
            db_metrics.update_pool_stats(engine.pool)

            status_details = {
                "status": "healthy",
                "pool_stats": db_metrics.connection_pool_stats,
                "total_queries": db_metrics.query_count,
                "last_check": "now",
            }

            return status_details

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        status_details = {
            "status": "unhealthy",
            "error": str(e),
            "pool_stats": db_metrics.connection_pool_stats,
            "last_check": "now",
        }
        return status_details
