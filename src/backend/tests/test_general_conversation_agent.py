from __future__ import annotations

from typing import (Any, AsyncGenerator, Callable, Coroutine, Dict, List,
                    Optional, Union)

"""
Tests for GeneralConversationAgent

Tests the new agent that handles free-form conversations with RAG and internet search capabilities.
"""

from unittest.mock import AsyncMock, patch

import pytest

from backend.agents.general_conversation_agent import (
    AgentResponse, GeneralConversationAgent)


class TestGeneralConversationAgent:
    """Test suite for GeneralConversationAgent"""

    @pytest.fixture
    def agent(self) -> Any:
        """Create a GeneralConversationAgent instance for testing"""
        return GeneralConversationAgent()

    @pytest.fixture
    def mock_input_data(self) -> Any:
        """Mock input data for testing"""
        return {
            "query": "What is the weather like today?",
            "use_perplexity": False,
            "use_bielik": True,
            "session_id": "test_session_123",
        }

    @pytest.mark.asyncio
    async def test_process_with_valid_input(self, agent, mock_input_data) -> None:
        """Test processing with valid input data"""
        with patch.object(
            agent, "_get_rag_context", return_value=("RAG context", 0.8)
        ), patch.object(
            agent, "_get_internet_context", return_value="Internet context"
        ), patch.object(
            agent, "_generate_response", return_value="Generated response"
        ):

            result = await agent.process(mock_input_data)

            assert isinstance(result, AgentResponse)
            assert result.success is True
            assert result.text == "Generated response"
            assert result.data["query"] == "What is the weather like today?"
            assert result.data["used_rag"] is True
            assert result.data["used_internet"] is True
            assert result.data["use_perplexity"] is False
            assert result.data["use_bielik"] is True

    @pytest.mark.asyncio
    async def test_process_with_empty_query(self, agent) -> None:
        """Test processing with empty query"""
        input_data = {"query": "", "use_perplexity": False, "use_bielik": True}

        result = await agent.process(input_data)

        assert isinstance(result, AgentResponse)
        assert result.success is False
        assert "No query provided" in result.error

    @pytest.mark.asyncio
    async def test_get_rag_context_success(self, agent) -> None:
        """Test successful RAG context retrieval"""
        with patch(
            "src.backend.agents.general_conversation_agent.mmlw_client"
        ) as mock_mmlw, patch(
            "src.backend.agents.general_conversation_agent.vector_store"
        ) as mock_vector_store:

            # Mock async methods properly
            mock_mmlw.embed_text = AsyncMock(return_value=[0.1, 0.2, 0.3])
            mock_vector_store.search = AsyncMock(
                return_value=[
                    (
                        type(
                            "obj",
                            (object,),
                            {
                                "content": "Document 1 content",
                                "metadata": {"filename": "test.txt"},
                            },
                        )(),
                        0.8,
                    ),
                    (
                        type(
                            "obj",
                            (object,),
                            {
                                "content": "Document 2 content",
                                "metadata": {"filename": "test2.txt"},
                            },
                        )(),
                        0.7,
                    ),
                ]
            )

            result, confidence = await agent._get_rag_context("test query")

            assert "Document 1 content" in result
            assert "Document 2 content" in result
            assert confidence > 0.0

    @pytest.mark.asyncio
    async def test_get_rag_context_empty(self, agent) -> None:
        """Test RAG context retrieval when no documents found"""
        with patch(
            "src.backend.agents.general_conversation_agent.mmlw_client"
        ) as mock_mmlw, patch(
            "src.backend.agents.general_conversation_agent.vector_store"
        ) as mock_vector_store:

            # Mock async methods properly
            mock_mmlw.embed_text = AsyncMock(return_value=[0.1, 0.2, 0.3])
            mock_vector_store.search = AsyncMock(return_value=[])

            result, confidence = await agent._get_rag_context("test query")

            assert result == ""
            assert confidence == 0.0

    @pytest.mark.asyncio
    async def test_get_internet_context_with_perplexity(self, agent) -> None:
        """Test internet context retrieval using Perplexity"""
        with patch(
            "src.backend.agents.general_conversation_agent.perplexity_client"
        ) as mock_perplexity:
            # Mock async method properly
            mock_perplexity.search = AsyncMock(
                return_value={
                    "success": True,
                    "results": [
                        {"content": "Perplexity result 1"},
                        {"content": "Perplexity result 2"},
                    ],
                }
            )

            result = await agent._get_internet_context(
                "test query", use_perplexity=True
            )

            assert "Perplexity result 1" in result
            assert "Perplexity result 2" in result
            assert "Informacje z internetu:" in result

    @pytest.mark.asyncio
    async def test_get_internet_context_with_local_search(self, agent) -> None:
        """Test internet context retrieval using local search"""
        with patch(
            "src.backend.agents.general_conversation_agent.web_search"
        ) as mock_web_search:
            # Mock successful search response
            mock_web_search.search = AsyncMock(
                return_value=[
                    {"content": "Test result 1"},
                    {"content": "Test result 2"},
                ]
            )

            result = await agent._get_internet_context(
                "test query", use_perplexity=False
            )

            assert "Test result 1" in result
            assert "Test result 2" in result

    @pytest.mark.asyncio
    async def test_generate_response_with_bielik(self, agent) -> None:
        """Test response generation using Bielik model"""
        with patch(
            "src.backend.agents.general_conversation_agent.hybrid_llm_client"
        ) as mock_llm:
            # Mock async method properly
            mock_llm.chat = AsyncMock(
                return_value={"message": {"content": "Bielik response"}}
            )

            result = await agent._generate_response(
                "test query",
                "rag context",
                "internet context",
                use_perplexity=False,
                use_bielik=True,
            )

            assert result == "Bielik response"

    @pytest.mark.asyncio
    async def test_generate_response_with_gemma(self, agent) -> None:
        """Test response generation using Gemma model"""
        with patch(
            "src.backend.agents.general_conversation_agent.hybrid_llm_client"
        ) as mock_llm:
            # Mock async method properly
            mock_llm.chat = AsyncMock(
                return_value={"message": {"content": "Gemma response"}}
            )

            result = await agent._generate_response(
                "test query",
                "rag context",
                "internet context",
                use_perplexity=False,
                use_bielik=False,
            )

            assert result == "Gemma response"
            mock_llm.chat.assert_called_once()
            call_args = mock_llm.chat.call_args
            assert call_args[1]["model"] == "gemma3:12b"

    @pytest.mark.asyncio
    async def test_generate_response_error_handling(self, agent) -> None:
        """Test error handling in response generation"""
        with patch(
            "src.backend.agents.general_conversation_agent.hybrid_llm_client"
        ) as mock_llm:
            # Mock async method properly
            mock_llm.chat = AsyncMock(side_effect=Exception("LLM error"))

            result = await agent._generate_response(
                "test query",
                "rag context",
                "internet context",
                use_perplexity=False,
                use_bielik=True,
            )

            assert "Przepraszam, wystąpił błąd podczas generowania odpowiedzi" in result

    @pytest.mark.asyncio
    async def test_process_exception_handling(self, agent) -> None:
        """Test exception handling in process method"""
        with patch.object(
            agent, "_needs_internet_search", side_effect=Exception("Test error")
        ):
            result = await agent.process({"query": "test", "use_bielik": True})

            assert isinstance(result, AgentResponse)
            assert result.success is False
            assert "Błąd przetwarzania" in result.error
