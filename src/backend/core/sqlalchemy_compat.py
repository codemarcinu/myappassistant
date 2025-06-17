"""
SQLAlchemy compatibility module for asyncio support.
This module provides fallbacks when sqlalchemy.ext.asyncio is not available.
"""

import logging

logger = logging.getLogger(__name__)

# Try to import AsyncSession from sqlalchemy.ext.asyncio
try:
    from sqlalchemy.ext.asyncio import AsyncSession

    HAS_ASYNC_SQLALCHEMY = True
    logger.info("Using native SQLAlchemy AsyncSession")
except ImportError:
    logger.warning("sqlalchemy.ext.asyncio not available, using compatibility class")
    HAS_ASYNC_SQLALCHEMY = False

    # Create a stub class for AsyncSession
    class AsyncSession:
        """
        Stub AsyncSession class for compatibility when SQLAlchemy async extension is not available.

        Note: This is only a stub for import compatibility.
        Please install SQLAlchemy with asyncio support:
        pip install sqlalchemy[asyncio]
        """

        def __init__(self, *args, **kwargs):
            logger.warning(
                "Using stub AsyncSession - SQLAlchemy async support not available"
            )
            self._args = args
            self._kwargs = kwargs

        async def commit(self):
            logger.warning(
                "Stub AsyncSession.commit() called - operation will not persist data"
            )
            pass

        async def close(self):
            logger.warning("Stub AsyncSession.close() called")
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            await self.close()
