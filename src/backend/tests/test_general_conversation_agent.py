"""
Tests for GeneralConversationAgent

Tests the new agent that handles free-form conversations with RAG and internet search capabilities.
"""

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.backend.agents.general_conversation_agent import GeneralConversationAgent
from src.backend.agents.interfaces import AgentResponse


class TestGeneralConversationAgent:
    """Test suite for GeneralConversationAgent"""

    @pytest.fixture
    def agent(self):
        """Create a GeneralConversationAgent instance for testing"""
        return GeneralConversationAgent()

    @pytest.fixture
    def mock_input_data(self):
        """Mock input data for testing"""
        return {
            "query": "What is the weather like today?",
            "use_perplexity": False,
            "use_bielik": True,
            "session_id": "test_session_123",
        }

    @pytest.mark.asyncio
    async def test_process_with_valid_input(self, agent, mock_input_data):
        """Test processing with valid input data"""
        with patch.object(
            agent, "_needs_internet_search", return_value=True
        ), patch.object(
            agent, "_get_rag_context", return_value="RAG context"
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
    async def test_process_with_empty_query(self, agent):
        """Test processing with empty query"""
        input_data = {"query": "", "use_perplexity": False, "use_bielik": True}

        result = await agent.process(input_data)

        assert isinstance(result, AgentResponse)
        assert result.success is False
        assert "Query is required" in result.error

    @pytest.mark.asyncio
    async def test_needs_internet_search_with_time_keywords(self, agent):
        """Test internet search detection with time-related keywords"""
        queries_with_time = [
            "What's the weather like today?",
            "Show me the latest news",
            "What are the current prices?",
            "Tell me about recent events",
        ]

        for query in queries_with_time:
            result = await agent._needs_internet_search(query)
            assert result is True

    @pytest.mark.asyncio
    async def test_needs_internet_search_without_time_keywords(self, agent):
        """Test internet search detection without time-related keywords"""
        queries_without_time = [
            "What is a computer?",
            "Explain photosynthesis",
            "How does gravity work?",
            "What is the capital of France?",
        ]

        for query in queries_without_time:
            result = await agent._needs_internet_search(query)
            assert result is False

    @pytest.mark.asyncio
    async def test_get_rag_context_success(self, agent):
        """Test successful RAG context retrieval"""
        with patch(
            "src.backend.agents.general_conversation_agent.vector_store"
        ) as mock_vector_store, patch.object(
            agent, "rag_integration"
        ) as mock_rag_integration:

            # Mock async methods properly
            mock_vector_store.search = AsyncMock(
                return_value=[
                    {"content": "Document 1 content"},
                    {"content": "Document 2 content"},
                ]
            )
            mock_rag_integration.get_relevant_context = AsyncMock(
                return_value="Database context"
            )

            result = await agent._get_rag_context("test query")

            assert "Document 1 content" in result
            assert "Document 2 content" in result
            assert "Database context" in result

    @pytest.mark.asyncio
    async def test_get_rag_context_empty(self, agent):
        """Test RAG context retrieval when no documents found"""
        with patch(
            "src.backend.agents.general_conversation_agent.vector_store"
        ) as mock_vector_store, patch.object(
            agent, "rag_integration"
        ) as mock_rag_integration:

            # Mock async methods properly
            mock_vector_store.search = AsyncMock(return_value=[])
            mock_rag_integration.get_relevant_context = AsyncMock(return_value="")

            result = await agent._get_rag_context("test query")

            assert result == ""

    @pytest.mark.asyncio
    async def test_get_internet_context_with_perplexity(self, agent):
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
    async def test_get_internet_context_with_local_search(self, agent):
        """Test internet context retrieval using local search"""
        with patch(
            "src.backend.agents.search_agent.SearchAgent"
        ) as mock_search_agent_class:
            mock_search_agent = AsyncMock()
            mock_search_agent_class.return_value = mock_search_agent

            # Mock successful search response
            mock_search_agent.process.return_value = AgentResponse(
                success=True,
                text="Test search results",
                data={
                    "results": [
                        {"content": "Test result 1"},
                        {"content": "Test result 2"},
                    ]
                },
            )

            result = await agent._get_internet_context(
                "test query", use_perplexity=False
            )

            assert "Test result 1" in result
            assert "Test result 2" in result
            mock_search_agent.process.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_response_with_bielik(self, agent):
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
            mock_llm.chat.assert_called_once()
            call_args = mock_llm.chat.call_args
            assert call_args[1]["model"] == "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"

    @pytest.mark.asyncio
    async def test_generate_response_with_gemma(self, agent):
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
    async def test_generate_response_error_handling(self, agent):
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
    async def test_process_exception_handling(self, agent):
        """Test exception handling in process method"""
        with patch.object(
            agent, "_needs_internet_search", side_effect=Exception("Test error")
        ):
            result = await agent.process({"query": "test", "use_bielik": True})

            assert isinstance(result, AgentResponse)
            assert result.success is False
            assert "Błąd przetwarzania" in result.error
