import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.agents.interfaces import AgentResponse
from backend.agents.rag_agent import RAGAgent


class TestRAGAgent:
    @pytest.fixture
    def agent(self):
        return RAGAgent(name="test_rag_agent")

    @pytest.fixture
    def mock_hybrid_client(self):
        with patch("backend.core.hybrid_llm_client.hybrid_llm_client") as mock:
            # Mock embed method
            mock.embed = AsyncMock(return_value=[0.1, 0.2, 0.3])
            # Mock chat method
            mock.chat = AsyncMock(
                return_value={"message": {"content": "Test response"}}
            )
            # Mock model_stats
            mock.model_stats = {"gemma3:12b": MagicMock(total_requests=0)}
            yield mock

    @pytest.fixture
    def mock_vector_store(self):
        with patch("backend.core.vector_store.vector_store") as mock:
            mock.similarity_search = AsyncMock(
                return_value=[{"content": "Test document"}]
            )
            mock.add_document = AsyncMock(return_value=["chunk_id_1"])
            yield mock

    def test_agent_initialization(self, agent):
        assert agent.name == "test_rag_agent"
        assert agent.initialized is False

    @pytest.mark.asyncio
    async def test_add_document(self, agent, mock_hybrid_client):
        with patch("backend.core.llm_client.llm_client.embed") as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3]

            with patch(
                "backend.core.vector_store.vector_store.add_document"
            ) as mock_add:
                mock_add.return_value = ["chunk_id_1"]

                result = await agent.add_document("test content", "test.txt")
                assert isinstance(result, list)
                assert len(result) > 0

    @pytest.mark.asyncio
    async def test_search(self, agent, mock_hybrid_client):
        with patch("backend.core.llm_client.llm_client.embed") as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3]

            with patch("backend.core.vector_store.vector_store.search") as mock_search:
                mock_search.return_value = [
                    {"content": "Test document", "metadata": {"source": "test.txt"}}
                ]

                results = await agent.search("vector databases", k=1)
                assert isinstance(results, list)
                assert len(results) > 0

    @pytest.mark.asyncio
    async def test_process_query(self, agent, mock_hybrid_client, mock_vector_store):
        """Test processing a query with RAG"""
        query = "What is the weather like?"

        with patch("backend.core.llm_client.llm_client.embed") as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3]

            # Zwróć kilka chunków, by agent miał kontekst
            with patch("backend.core.vector_store.vector_store.search") as mock_search:
                mock_search.return_value = [
                    {
                        "text": "Chunk 1: Weather is sunny.",
                        "metadata": {"source": "test.txt"},
                    },
                    {
                        "text": "Chunk 2: Temperature is 20C.",
                        "metadata": {"source": "test.txt"},
                    },
                ]

                with patch(
                    "backend.core.hybrid_llm_client.hybrid_llm_client.chat"
                ) as mock_chat:
                    mock_chat.return_value = {"message": {"content": "Test response"}}

                    response = await agent.process({"query": query})

                    assert isinstance(response, AgentResponse)
                    assert response.success is True
                    assert response.text is not None
                    assert len(response.text) > 0

    @pytest.mark.asyncio
    async def test_process_document(self, agent, mock_hybrid_client, mock_vector_store):
        """Test processing a document for indexing"""
        document = "This is a test document about weather."

        with patch("backend.core.llm_client.llm_client.embed") as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3]

            with patch("backend.core.vector_store.vector_store.search") as mock_search:
                mock_search.return_value = [
                    {"content": "Test document", "metadata": {"source": "test.txt"}}
                ]

                response = await agent.process(
                    {"query": "What is this document about?"}
                )

                assert isinstance(response, AgentResponse)
                assert response.success is True

    @pytest.mark.asyncio
    async def test_process_empty_query(self, agent):
        """Test processing empty query"""
        response = await agent.process({})

        assert isinstance(response, AgentResponse)
        assert response.success is False
        assert "No query provided" in response.text


if __name__ == "__main__":
    unittest.main()
