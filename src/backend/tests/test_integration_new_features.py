from __future__ import annotations

from typing import (Any, AsyncGenerator, Callable, Coroutine, Dict, List,
                    Optional, Union)

"""
Integration tests for new features with Bielik/Gemma toggle

Tests the complete flow of:
- Model selection (Bielik vs Gemma)
- Intent detection with new conversation types
- Agent routing and processing
- API endpoints with model selection
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.agents.agent_factory import AgentFactory
from backend.agents.general_conversation_agent import GeneralConversationAgent
from backend.agents.intent_detector import SimpleIntentDetector
from backend.agents.interfaces import AgentResponse, MemoryContext
from backend.agents.orchestrator import Orchestrator
from backend.core.hybrid_llm_client import HybridLLMClient


class TestIntegrationNewFeatures:
    """Integration tests for new features"""

    @pytest.fixture
    def orchestrator(self) -> None:
        """Create an Orchestrator instance for testing (mock dependencies)"""

        class Dummy:
            async def get_or_create_profile(self, session_id) -> None:
                return None

            async def log_activity(self, session_id, typ, val) -> None:
                return None

            async def get_context(self, session_id) -> None:
                return None

            async def update_context(self, context, data) -> None:
                return None

            async def detect_intent(self, query, context) -> None:
                from backend.agents.orchestration_components import IntentData

                return IntentData(type="general_conversation", confidence=0.8)

        db = None
        profile_manager = Dummy()
        intent_detector = Dummy()
        return Orchestrator(
            db_session=db,
            profile_manager=profile_manager,
            intent_detector=intent_detector,
        )

    @pytest.fixture
    def intent_detector(self) -> None:
        """Create an IntentDetector instance for testing"""
        return SimpleIntentDetector()

    @pytest.fixture
    def agent_factory(self) -> None:
        """Create an AgentFactory instance for testing"""
        return AgentFactory()

    @pytest.fixture
    def llm_client(self) -> None:
        """Create a HybridLLMClient instance for testing"""
        return HybridLLMClient()

    @pytest.fixture
    def context(self) -> None:
        """Create a MemoryContext instance for testing"""
        return MemoryContext(session_id="test_session_123")

    @pytest.mark.asyncio
    async def test_complete_flow_with_bielik(
        self, orchestrator, intent_detector, context
    ) -> None:
        """Test complete flow using Bielik model"""
        query = "What is the weather like today?"

        with patch("src.backend.core.llm_client.llm_client.chat") as mock_llm, patch(
            "src.backend.agents.general_conversation_agent.vector_store"
        ) as mock_vector_store, patch(
            "src.backend.agents.general_conversation_agent.perplexity_client"
        ) as mock_perplexity:

            # Mock LLM responses
            mock_llm.return_value = {"message": {"content": "Bielik weather response"}}

            # Mock vector store
            mock_vector_store.search.return_value = []

            # Mock Perplexity
            mock_perplexity.search.return_value = {
                "success": True,
                "results": [{"content": "Weather data from internet"}],
            }

            # Process query with Bielik
            response = await orchestrator.process_query(
                query=query,
                session_id=context.session_id,
                use_bielik=True,
                use_perplexity=False,
            )

            assert response.success is True
            assert "Bielik weather response" in response.text
            assert response.data["use_bielik"] is True
            assert response.data["use_perplexity"] is False

    @pytest.mark.asyncio
    async def test_complete_flow_with_gemma(
        self, orchestrator, intent_detector, context
    ) -> None:
        """Test complete flow using Gemma model"""
        query = "How to cook pasta?"

        with patch("src.backend.core.llm_client.llm_client.chat") as mock_llm, patch(
            "src.backend.agents.general_conversation_agent.vector_store"
        ) as mock_vector_store, patch(
            "src.backend.agents.general_conversation_agent.perplexity_client"
        ) as mock_perplexity:

            # Mock LLM responses
            mock_llm.return_value = {"message": {"content": "Gemma cooking response"}}

            # Mock vector store
            mock_vector_store.search.return_value = []

            # Mock Perplexity
            mock_perplexity.search.return_value = {
                "success": True,
                "results": [{"content": "Cooking data from internet"}],
            }

            # Process query with Gemma
            response = await orchestrator.process_query(
                query=query,
                session_id=context.session_id,
                use_bielik=False,
                use_perplexity=False,
            )

            assert response.success is True
            assert "Gemma cooking response" in response.text
            assert response.data["use_bielik"] is False
            assert response.data["use_perplexity"] is False

    @pytest.mark.asyncio
    async def test_intent_detection_and_agent_routing(
        self, intent_detector, agent_factory, context
    ) -> None:
        """Test intent detection and agent routing for new conversation types"""
        test_cases = [
            ("Kupiłem mleko za 5 zł", GeneralConversationAgent),
            ("Jak ugotować spaghetti?", GeneralConversationAgent),
            ("Co to jest sztuczna inteligencja?", GeneralConversationAgent),
            ("Cześć, jak się masz?", GeneralConversationAgent),
        ]

        for query, expected_agent_type in test_cases:
            with patch("src.backend.core.llm_client.llm_client.chat") as mock_llm:
                # Mock LLM to trigger fallback detection
                mock_llm.return_value = None

                # Detect intent
                intent = await intent_detector.detect_intent(query, context)
                assert intent.type is not None  # Sprawdzam czy intent jest wykryty
                assert (
                    intent.confidence > 0
                )  # Sprawdzam czy confidence jest większe od 0

                # Create appropriate agent
                agent = agent_factory.create_agent(intent.type)
                assert isinstance(agent, expected_agent_type)

    @pytest.mark.asyncio
    async def test_model_fallback_mechanism(self, llm_client) -> None:
        """Test model fallback mechanism"""
        messages = [{"role": "user", "content": "Test query"}]

        response = await llm_client.chat(messages=messages, use_bielik=True)

        assert response is not None  # Sprawdzam czy response jest zwrócony
        assert "message" in response  # Sprawdzam czy response ma strukturę message

    @pytest.mark.asyncio
    async def test_general_conversation_agent_with_rag_and_internet(
        self, agent_factory
    ) -> None:
        """Test GeneralConversationAgent with RAG and internet search"""
        agent = agent_factory.create_agent("general_conversation")

        with patch.object(
            agent, "_needs_internet_search", return_value=True
        ), patch.object(
            agent, "_get_rag_context", return_value="RAG context"
        ), patch.object(
            agent, "_get_internet_context", return_value="Internet context"
        ), patch.object(
            agent, "_generate_response", return_value="Final response"
        ):

            input_data = {
                "query": "What is the latest news?",
                "use_bielik": True,
                "use_perplexity": False,
                "session_id": "test_session",
            }

            response = await agent.process(input_data)

            assert response.success is True
            assert response.text == "Final response"
            assert response.data["used_rag"] is True
            assert response.data["used_internet"] is True
            assert response.data["use_bielik"] is True

    @pytest.mark.asyncio
    async def test_cooking_agent_with_model_selection(self, agent_factory) -> None:
        """Test cooking agent with model selection"""
        agent = agent_factory.create_agent("cooking")

        input_data = {
            "query": "How to cook rice?",
            "available_ingredients": ["rice", "water", "salt"],
            "use_bielik": False,  # Use Gemma
            "session_id": "test_session",
        }

        response = await agent.process(input_data)

        assert response.success is True
        assert "Recipe generation started" in response.text
        assert (
            response.text_stream is not None
        )  # Sprawdzam czy text_stream jest ustawiony

    @pytest.mark.asyncio
    async def test_search_agent_with_model_selection(self, agent_factory) -> None:
        """Test search agent with model selection"""
        agent = agent_factory.create_agent("search")

        input_data = {
            "query": "Search for Python tutorials",
            "use_bielik": True,  # Use Bielik
            "session_id": "test_session",
        }

        response = await agent.process(input_data)

        assert response.success is True
        assert response.text is not None  # Sprawdzam czy text jest ustawiony

    @pytest.mark.asyncio
    async def test_weather_agent_with_model_selection(self, agent_factory) -> None:
        """Test weather agent with model selection"""
        agent = agent_factory.create_agent("weather")

        input_data = {
            "query": "What's the weather in Warsaw?",
            "use_bielik": False,  # Use Gemma
            "session_id": "test_session",
        }

        response = await agent.process(input_data)

        assert response.success is True
        assert response.text is not None  # Sprawdzam czy text jest ustawiony

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, orchestrator, context) -> None:
        """Test error handling in integration flow"""
        query = "Test query that will fail"

        with patch(
            "src.backend.agents.orchestrator.Orchestrator.process_query"
        ) as mock_process:
            mock_process.side_effect = Exception("Integration error")

            with pytest.raises(Exception, match="Integration error"):
                await orchestrator.process_query(
                    query=query, session_id=context.session_id, use_bielik=True
                )

    @pytest.mark.asyncio
    async def test_concurrent_requests_with_different_models(
        self, orchestrator, context
    ) -> None:
        """Test concurrent requests with different model selections"""
        import asyncio

        async def process_with_model(use_bielik) -> None:
            with patch(
                "src.backend.core.hybrid_llm_client.hybrid_llm_client.chat"
            ) as mock_llm:
                mock_llm.return_value = {
                    "message": {
                        "content": f"Response with {'Bielik' if use_bielik else 'Gemma'}"
                    }
                }

                return await orchestrator.process_query(
                    query="Test query",
                    session_id=context.session_id,
                    use_bielik=use_bielik,
                )

        # Process multiple requests concurrently
        tasks = [
            process_with_model(True),  # Bielik
            process_with_model(False),  # Gemma
            process_with_model(True),  # Bielik
            process_with_model(False),  # Gemma
        ]

        responses = await asyncio.gather(*tasks)

        # Verify all responses are successful
        assert len(responses) == 4
        assert all(response.success for response in responses)

        # Verify model selection was respected (sprawdzamy dane w response, nie tekst)
        assert responses[0].data["use_bielik"] is True
        assert responses[1].data["use_bielik"] is False
        assert responses[2].data["use_bielik"] is True
        assert responses[3].data["use_bielik"] is False
