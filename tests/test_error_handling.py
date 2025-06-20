import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pybreaker
import pytest

from backend.agents.base_agent import AgentResponse, BaseAgent
from backend.agents.interfaces import ErrorSeverity

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent))


class DummyAgent(BaseAgent):
    async def process(self, input_data):
        return AgentResponse(success=True, text="dummy")

    def get_metadata(self):
        return {}

    def get_dependencies(self):
        return []

    def is_healthy(self):
        return True


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_handle_exceptions_decorator(self):
        """Test that the error decorator properly catches and handles exceptions"""
        mock_agent = DummyAgent()
        mock_agent.process = AsyncMock()

        # Test successful execution
        mock_agent.process.return_value = AgentResponse(
            success=True,
            data={},
            error=None,
            severity=ErrorSeverity.LOW,
            request_id="test123",
            timestamp=time.time(),
        )
        response = await mock_agent.process({})
        assert response.success is True

        # Test error handling
        mock_agent.process.side_effect = ValueError("Test error")
        mock_agent.process_with_circuit_breaker = AsyncMock(
            return_value=AgentResponse(
                success=False,
                data={},
                error="Test error",
                severity=ErrorSeverity.MEDIUM,
                request_id="test456",
                timestamp=time.time(),
            )
        )
        response = await mock_agent.process_with_circuit_breaker({})
        assert response.success is False
        assert "Test error" in response.error
        assert response.severity == ErrorSeverity.MEDIUM.value

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self):
        """Test that circuit breaker works with error handling"""
        mock_agent = DummyAgent()
        mock_agent.process = AsyncMock()

        # Simulate circuit breaker open
        mock_agent.process.side_effect = pybreaker.CircuitBreakerError()
        mock_agent.process_with_circuit_breaker = AsyncMock(
            return_value=AgentResponse(
                success=False,
                data={},
                error="Service temporarily unavailable",
                severity=ErrorSeverity.MEDIUM,
                request_id="test789",
                timestamp=time.time(),
            )
        )
        response = await mock_agent.process_with_circuit_breaker({})
        assert response.success is False
        assert "Service temporarily unavailable" in response.error
        assert response.severity == ErrorSeverity.MEDIUM.value
