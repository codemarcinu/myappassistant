"""
✅ REQUIRED: Tests for critical fixes implemented according to cursorrules
This module tests the anti-pattern fixes and new implementations.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio

from backend.agents.agent_factory import AgentFactory
from backend.core.database import Base
from backend.core.exceptions import (
    AgentError,
    AuthenticationError,
    ConfigurationError,
    DatabaseError,
    ExternalAPIError,
    FoodSaveError,
    HealthCheckError,
    ProcessingError,
    RateLimitError,
    ValidationError,
)
from backend.core.monitoring import (
    PerformanceMetrics,
    monitor_agent,
    monitor_database_operation,
    monitor_external_api,
    monitor_processing,
    monitor_request,
    update_system_metrics,
)


class TestSQLAlchemyRegistryFixes:
    """Test SQLAlchemy registry conflict fixes"""

    def test_unified_base_class(self):
        """Test that all models use the same Base class"""
        from backend.core.database import Base as CoreBase
        from backend.models import Base as ModelsBase

        # ✅ ALWAYS: Use unified Base class
        assert ModelsBase is CoreBase
        # SQLAlchemy 2.x: DeclarativeBase is the correct base
        try:
            from sqlalchemy.orm import DeclarativeBase

            assert issubclass(ModelsBase, DeclarativeBase)
        except ImportError:
            from sqlalchemy.orm import DeclarativeMeta

            assert isinstance(ModelsBase, DeclarativeMeta)

    def test_model_imports_dont_conflict(self):
        """Test that model imports don't cause registry conflicts"""
        # Import all models to ensure no conflicts
        from backend.auth.models import Role, User, UserRole
        from backend.models.conversation import Conversation, Message
        from backend.models.shopping import Product, ShoppingTrip
        from backend.models.user_profile import UserActivity, UserProfile

        # All models should inherit from the same Base
        assert issubclass(Conversation, Base)
        assert issubclass(Message, Base)
        assert issubclass(ShoppingTrip, Base)
        assert issubclass(Product, Base)
        assert issubclass(UserProfile, Base)
        assert issubclass(UserActivity, Base)
        assert issubclass(User, Base)
        assert issubclass(Role, Base)
        assert issubclass(UserRole, Base)


class TestAgentFactoryFixes:
    """Test Agent Factory registration fixes"""

    def test_agent_factory_has_fallback(self):
        """Test that AgentFactory has proper fallback registration"""
        factory = AgentFactory()

        # ✅ ALWAYS: Proper agent registration with fallback
        assert "default" in factory.AGENT_REGISTRY
        assert factory.AGENT_REGISTRY["default"] is not None

    def test_unknown_agent_type_fallback(self):
        """Test that unknown agent types fallback to default"""
        factory = AgentFactory()

        # Test with unknown agent type
        agent = factory.create_agent("unknown_agent_type")

        # Should fallback to default agent
        assert agent is not None
        assert isinstance(agent, factory.AGENT_REGISTRY["default"])

    def test_agent_registry_completeness(self):
        """Test that all required agents are registered"""
        factory = AgentFactory()

        required_agents = [
            "general_conversation",
            "search",
            "weather",
            "rag",
            "ocr",
            "categorization",
            "meal_planning",
            "analytics",
        ]

        for agent_type in required_agents:
            assert (
                agent_type in factory.AGENT_REGISTRY
            ), f"Agent {agent_type} not registered"


class TestHealthCheckSystem:
    """Test comprehensive health check system"""

    @pytest.mark.asyncio
    async def test_database_health_check(self):
        """Test database health check functionality"""
        from backend.infrastructure.database.database import check_database_health

        # Test database health check
        status_details = await check_database_health()

        # Should return a dict with status information
        assert isinstance(status_details, dict)
        assert "status" in status_details
        assert "pool_stats" in status_details
        assert "last_check" in status_details

        # Status should be either healthy or unhealthy
        assert status_details["status"] in ["healthy", "unhealthy"]

        # Pool stats should be a dict
        assert isinstance(status_details["pool_stats"], dict)

    @pytest.mark.asyncio
    async def test_agents_health_check(self):
        """Test agents health check functionality"""
        from backend.api.monitoring import check_agents_health

        # Test agents health check
        agents_health = await check_agents_health()

        assert isinstance(agents_health, dict)
        assert "status" in agents_health
        assert "agents" in agents_health

    @pytest.mark.asyncio
    async def test_external_apis_health_check(self):
        """Test external APIs health check functionality"""
        from backend.api.monitoring import check_external_apis_health

        # Test external APIs health check
        apis_health = await check_external_apis_health()

        assert isinstance(apis_health, dict)
        assert "status" in apis_health
        assert "apis" in apis_health

    @pytest.mark.asyncio
    async def test_comprehensive_health_check(self):
        """Test comprehensive health check endpoint"""
        from backend.api.monitoring import health_check

        # Test health check endpoint
        response = await health_check()

        assert response.status_code in [200, 503]  # Healthy or unhealthy
        assert "status" in response.body.decode()
        assert "checks" in response.body.decode()
        assert "timestamp" in response.body.decode()


class TestErrorHandlingSystem:
    """Test comprehensive error handling system"""

    def test_exception_hierarchy(self):
        """Test that all exceptions inherit from FoodSaveError"""
        exceptions = [
            ProcessingError,
            AgentError,
            DatabaseError,
            ValidationError,
            AuthenticationError,
            ExternalAPIError,
            ConfigurationError,
            RateLimitError,
            HealthCheckError,
        ]

        for exception_class in exceptions:
            assert issubclass(exception_class, FoodSaveError)

    def test_exception_with_context(self):
        """Test exception creation with proper context"""
        error = ProcessingError(
            message="Test processing error",
            operation="test_operation",
            food_item_id="test_id",
        )

        assert error.message == "Test processing error"
        assert error.error_code == "PROCESSING_ERROR"
        assert error.details["operation"] == "test_operation"
        assert error.details["food_item_id"] == "test_id"
        assert error.severity == "high"
        assert isinstance(error.timestamp, datetime)

    def test_error_logging(self):
        """Test that errors are properly logged"""
        with patch("backend.core.exceptions.logger") as mock_logger:
            error = AgentError(message="Test agent error", agent_type="test_agent")

            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Test agent error" in call_args[0][0]
            assert "error_code" in call_args[1]["extra"]
            assert "severity" in call_args[1]["extra"]


class TestPerformanceMonitoring:
    """Test performance monitoring system"""

    def test_metrics_initialization(self):
        """Test that metrics are properly initialized"""
        metrics = PerformanceMetrics()

        # Check that all required metrics exist
        assert hasattr(metrics, "request_count")
        assert hasattr(metrics, "request_duration")
        assert hasattr(metrics, "agent_request_count")
        assert hasattr(metrics, "agent_response_time")
        assert hasattr(metrics, "active_agents")
        assert hasattr(metrics, "db_query_count")
        assert hasattr(metrics, "db_query_duration")
        assert hasattr(metrics, "external_api_calls")
        assert hasattr(metrics, "error_count")

    @pytest.mark.asyncio
    async def test_monitor_request_decorator(self):
        """Test request monitoring decorator"""

        @monitor_request("GET", "/test")
        async def test_endpoint():
            return {"status": "success"}

        # Test async function monitoring
        result = await test_endpoint()
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_monitor_agent_decorator(self):
        """Test agent monitoring decorator"""

        @monitor_agent("test_agent")
        async def test_agent():
            return {"response": "test"}

        # Test agent monitoring
        result = await test_agent()
        assert result["response"] == "test"

    @pytest.mark.asyncio
    async def test_monitor_database_operation(self):
        """Test database operation monitoring"""

        @monitor_database_operation("SELECT", "test_table")
        async def test_db_operation():
            return {"data": "test"}

        # Test database monitoring
        result = await test_db_operation()
        assert result["data"] == "test"

    @pytest.mark.asyncio
    async def test_monitor_external_api(self):
        """Test external API monitoring"""

        @monitor_external_api("test_api", "/test_endpoint")
        async def test_api_call():
            return {"api_response": "test"}

        # Test external API monitoring
        result = await test_api_call()
        assert result["api_response"] == "test"

    @pytest.mark.asyncio
    async def test_monitor_processing_context(self):
        """Test processing monitoring context manager"""
        async with monitor_processing("test_operation"):
            # Simulate processing
            await asyncio.sleep(0.01)

        # Context manager should complete without error


class TestAsyncTestConfiguration:
    """Test async test configuration"""

    @pytest.mark.asyncio
    async def test_async_fixture_works(self, db_session):
        """Test that async fixtures work correctly"""
        assert db_session is not None

        # Test basic database operation
        from sqlalchemy import text

        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    def test_mock_vector_store_has_required_attributes(self, mock_vector_store):
        """Test that mock vector store has required attributes"""
        # ✅ ALWAYS: Use spec parameter in mocks to prevent AttributeError
        assert hasattr(mock_vector_store, "is_empty")
        assert hasattr(mock_vector_store, "similarity_search")
        assert hasattr(mock_vector_store, "add_documents")
        assert hasattr(mock_vector_store, "delete")

        # Test that attributes work
        assert mock_vector_store.is_empty is False
        assert callable(mock_vector_store.similarity_search)
        assert callable(mock_vector_store.add_documents)
        assert callable(mock_vector_store.delete)

    def test_test_data_fixture(self, test_data):
        """Test test data fixture"""
        assert "user_query" in test_data
        assert "session_id" in test_data
        assert "agent_type" in test_data
        assert "test_food_items" in test_data
        assert len(test_data["test_food_items"]) > 0


class TestErrorHandlingUtilities:
    """Test error handling utilities"""

    def test_handle_exception_with_context(self):
        """Test exception handling with context"""
        from backend.core.exceptions import DatabaseError, handle_exception_with_context

        # Test with database error
        original_error = Exception("Database connection failed")
        context = {"operation": "test_operation", "user_id": "test_user"}

        foodsave_error = handle_exception_with_context(
            original_error, context, "test_operation"
        )

        assert isinstance(foodsave_error, DatabaseError)
        assert "Database connection failed" in foodsave_error.message
        assert foodsave_error.context["operation"] == "test_operation"
        assert foodsave_error.context["user_id"] == "test_user"

    def test_create_error_response(self):
        """Test error response creation"""
        from backend.core.exceptions import create_error_response

        error = ProcessingError(message="Test error", operation="test_operation")

        response = create_error_response(error, include_details=True)

        assert response["success"] is False
        assert response["error_code"] == "PROCESSING_ERROR"
        assert response["message"] == "Test error"
        assert "timestamp" in response
        assert "details" in response
        assert "context" in response


class TestSystemMetrics:
    """Test system metrics functionality"""

    def test_update_system_metrics(self):
        """Test system metrics update"""
        # This should not raise any exceptions
        update_system_metrics()

    def test_get_metrics_summary(self):
        """Test metrics summary"""
        from backend.core.monitoring import get_metrics_summary

        summary = get_metrics_summary()

        assert "timestamp" in summary
        assert "prometheus_available" in summary
        assert "metrics_collected" in summary
        assert "requests" in summary["metrics_collected"]
        assert "agents" in summary["metrics_collected"]
        assert "database" in summary["metrics_collected"]


# Integration tests
class TestIntegrationFixes:
    """Integration tests for the implemented fixes"""

    @pytest.mark.asyncio
    async def test_full_health_check_flow(self):
        """Test complete health check flow"""
        from backend.api.monitoring import health_check

        # Test health check endpoint
        response = await health_check()

        # Should return proper response structure
        assert response.status_code in [200, 503]
        response_data = response.body.decode()
        assert "status" in response_data
        assert "checks" in response_data

    @pytest.mark.asyncio
    async def test_agent_factory_with_health_checks(self):
        """Test agent factory with health checks"""
        factory = AgentFactory()

        # Test creating agents
        agent_types = ["general_conversation", "search", "weather"]

        for agent_type in agent_types:
            agent = factory.create_agent(agent_type)
            assert agent is not None

            # Test agent health check if available
            if hasattr(agent, "is_healthy"):
                health_status = agent.is_healthy()
                assert isinstance(health_status, bool)

    def test_error_handling_integration(self):
        """Test error handling integration"""
        from backend.core.exceptions import (
            create_error_response,
            handle_exception_with_context,
        )

        # Simulate a processing error
        try:
            raise ValueError("Invalid food item data")
        except Exception as e:
            context = {"operation": "food_processing", "user_id": "test_user"}
            foodsave_error = handle_exception_with_context(
                e, context, "food_processing"
            )

            # Create error response
            response = create_error_response(foodsave_error, include_details=True)

            assert response["success"] is False
            assert "Invalid food item data" in response["message"]
            assert response["context"]["operation"] == "food_processing"


# Performance tests
class TestPerformanceFixes:
    """Performance tests for the implemented fixes"""

    @pytest.mark.asyncio
    async def test_health_check_performance(self):
        """Test health check performance"""
        import time

        from backend.api.monitoring import health_check

        start_time = time.time()
        response = await health_check()
        duration = time.time() - start_time

        # Health check should complete within reasonable time
        assert duration < 5.0  # Should complete within 5 seconds
        assert response.status_code in [200, 503]

    def test_agent_factory_performance(self):
        """Test agent factory performance"""
        import time

        factory = AgentFactory()
        agent_types = ["general_conversation", "search", "weather", "rag"]

        start_time = time.time()
        for agent_type in agent_types:
            agent = factory.create_agent(agent_type)
            assert agent is not None
        duration = time.time() - start_time

        # Agent creation should be fast
        assert duration < 1.0  # Should complete within 1 second

    def test_error_handling_performance(self):
        """Test error handling performance"""
        import time

        from backend.core.exceptions import handle_exception_with_context

        start_time = time.time()
        for _ in range(100):
            try:
                raise ValueError("Test error")
            except Exception as e:
                context = {"operation": "test", "iteration": _}
                error = handle_exception_with_context(e, context, "test")
                assert error is not None
        duration = time.time() - start_time

        # Error handling should be fast
        assert duration < 1.0  # Should complete within 1 second
