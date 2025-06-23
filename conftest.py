"""
✅ REQUIRED: pytest configuration with proper async test setup
This file provides fixtures and configuration for all tests in the FoodSave AI project.
"""

import asyncio
from datetime import datetime
from typing import Any, AsyncGenerator, Dict
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio

# Import test dependencies
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.agents.agent_factory import AgentFactory
from backend.agents.base_agent import BaseAgent

# Import application components
from backend.core.database import Base


# ✅ ALWAYS: Use @pytest_asyncio.fixture for async fixtures
@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """✅ REQUIRED: Proper fixtures with cleanup"""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", echo=False, poolclass=None
    )
    TestSessionLocal = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    await test_engine.dispose()


@pytest.fixture
def mock_vector_store():
    """✅ ALWAYS: Use spec parameter in mocks to prevent AttributeError"""
    mock = Mock(spec=object)  # Generic spec to avoid AttributeError
    # Ensure required attributes exist
    mock.is_empty = False
    mock.similarity_search = AsyncMock(return_value=[])
    mock.add_documents = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing"""
    mock = Mock()
    mock.generate = AsyncMock(return_value={"text": "Test response"})
    mock.health_check = AsyncMock(return_value={"status": "healthy"})
    return mock


@pytest.fixture
def mock_agent_factory():
    """Mock agent factory for testing"""
    factory = Mock(spec=AgentFactory)
    factory.AGENT_REGISTRY = {
        "test_agent": Mock(spec=BaseAgent),
        "default": Mock(spec=BaseAgent),
    }
    factory.create_agent = Mock(return_value=Mock(spec=BaseAgent))
    return factory


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        "database_url": "sqlite+aiosqlite:///:memory:",
        "ollama_url": "http://localhost:11434",
        "model_name": "test-model",
        "max_retries": 3,
        "timeout": 30,
    }


@pytest.fixture
def test_data():
    """Sample test data for various tests"""
    return {
        "user_query": "What's the weather like today?",
        "session_id": "test-session-123",
        "agent_type": "weather",
        "expected_response": "The weather is sunny today.",
        "test_food_items": [
            {
                "name": "Apple",
                "category": "produce",
                "expiration_date": "2024-12-25",
                "quantity": 5,
            },
            {
                "name": "Milk",
                "category": "dairy",
                "expiration_date": "2024-12-20",
                "quantity": 1,
            },
        ],
    }


@pytest.fixture
def mock_health_check_response():
    """Mock health check response data"""
    return {
        "status": "healthy",
        "checks": {
            "database": {
                "status": "healthy",
                "pool_stats": {"checked_in": 5, "checked_out": 2},
                "total_queries": 100,
            },
            "agents": {
                "status": "healthy",
                "agents": {
                    "weather": {"status": "healthy"},
                    "search": {"status": "healthy"},
                },
            },
            "external_apis": {
                "status": "healthy",
                "apis": {
                    "perplexity": {"status": "healthy"},
                    "mmlw": {"status": "healthy"},
                },
            },
        },
        "response_time": 0.123,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }


# ✅ ALWAYS: Use @pytest.mark.asyncio for async tests
@pytest.mark.asyncio
async def test_async_fixture_works(db_session):
    """Test that async fixtures work correctly"""
    assert db_session is not None
    # Test basic database operation
    from sqlalchemy import text

    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


# Performance test fixtures
@pytest.fixture
def performance_test_config():
    """Configuration for performance tests"""
    return {
        "iterations": 100,
        "timeout": 30,
        "memory_limit_mb": 512,
        "cpu_limit_percent": 80,
    }


# Integration test fixtures
@pytest.fixture
def integration_test_session():
    """Session for integration tests"""
    return {
        "session_id": "integration-test-123",
        "user_id": "test-user-456",
        "start_time": datetime.now(),
    }


# Error handling test fixtures
@pytest.fixture
def error_test_cases():
    """Test cases for error handling"""
    return [
        {
            "name": "database_connection_error",
            "error_type": "ConnectionError",
            "expected_status_code": 503,
            "expected_message": "Database connection failed",
        },
        {
            "name": "agent_not_found",
            "error_type": "ValueError",
            "expected_status_code": 400,
            "expected_message": "Unknown agent type",
        },
        {
            "name": "external_api_timeout",
            "error_type": "TimeoutError",
            "expected_status_code": 504,
            "expected_message": "External API timeout",
        },
    ]


# Logging test fixtures
@pytest.fixture
def log_capture():
    """Capture logs for testing"""
    import logging
    from io import StringIO

    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.DEBUG)

    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)

    yield log_stream

    # Cleanup
    root_logger.removeHandler(handler)


# Rate limiting test fixtures
@pytest.fixture
def rate_limit_config():
    """Configuration for rate limiting tests"""
    return {"requests_per_minute": 60, "burst_size": 10, "window_size": 60}


# Security test fixtures
@pytest.fixture
def security_test_data():
    """Test data for security tests"""
    return {
        "malicious_inputs": [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "{{7*7}}",
            "admin' OR '1'='1",
        ],
        "valid_inputs": [
            "normal query",
            "weather in Warsaw",
            "recipe for pasta",
            "shopping list",
        ],
    }


# Cleanup fixture for all tests
@pytest_asyncio.fixture(autouse=True)
async def cleanup_after_test():
    """Automatic cleanup after each test"""
    yield
    # Clean up any test-specific resources
    await asyncio.sleep(0.01)  # Allow async operations to complete


# Test markers configuration
def pytest_configure(config):
    """Configure custom test markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "security: marks tests as security tests")


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add default markers"""
    for item in items:
        # Add unit marker to tests that don't have any marker
        if not any(item.iter_markers()):
            item.add_marker(pytest.mark.unit)

        # Add asyncio marker to async tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
