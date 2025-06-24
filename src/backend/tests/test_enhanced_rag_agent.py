from __future__ import annotations

import asyncio
import unittest
from typing import (Any, AsyncGenerator, Callable, Coroutine, Dict, List,
                    Optional, Union)
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.agents.interfaces import AgentResponse
from backend.agents.rag_agent import RAGAgent
from backend.core.vector_store import DocumentChunk, VectorStore


@pytest.fixture
def mock_vector_store() -> Any:
    with patch("backend.agents.rag_agent.vector_store") as mock:
        mock.is_empty = AsyncMock(return_value=False)
        doc1 = DocumentChunk(
            id="doc1", content="Test document content", metadata={"source": "test.txt"}
        )
        doc2 = DocumentChunk(
            id="doc2", content="Another test document", metadata={"source": "test2.txt"}
        )
        mock.search = AsyncMock(return_value=[(doc1, 0.8), (doc2, 0.7)])
        yield mock


@pytest.fixture
def mock_hybrid_client() -> Any:
    with patch("backend.agents.rag_agent.hybrid_llm_client") as mock:
        mock.embed = AsyncMock(return_value=[0.1, 0.2, 0.3])
        mock.chat = AsyncMock(return_value={"message": {"content": "Test response"}})
        mock.model_stats = {"gemma3:12b": MagicMock(total_requests=0)}
        yield mock


@pytest.fixture
def mock_processor() -> Any:
    with patch("backend.agents.rag_agent.rag_document_processor") as mock:
        mock.process_document = AsyncMock(return_value=["chunk1", "chunk2"])
        mock.process_file = AsyncMock(
            return_value={"processed_chunks": 2, "source_id": "test.txt"}
        )
        mock.process_url = AsyncMock(
            return_value={"processed_chunks": 1, "source_id": "url"}
        )
        mock.process_directory = AsyncMock(
            return_value={"processed_chunks": 3, "source_id": "dir"}
        )
        yield mock


class TestRAGAgent:
    @pytest.fixture
    def agent(self) -> None:
        return RAGAgent(name="test_rag_agent")

    @pytest.mark.asyncio
    async def test_agent_initialization(
        self, agent, mock_vector_store, mock_hybrid_client, mock_processor
    ) -> Any:
        assert agent.name == "test_rag_agent"
        assert agent.initialized is False
        await agent.initialize()
        assert agent.initialized is True

    @pytest.mark.asyncio
    async def test_add_document(
        self, agent, mock_vector_store, mock_hybrid_client, mock_processor
    ) -> Any:
        agent.document_processor = AsyncMock()
        agent.document_processor.process_document = AsyncMock(
            return_value=["chunk1", "chunk2"]
        )

        result = await agent.add_document("test content", "test.txt")
        assert isinstance(result, dict)
        assert result["processed_chunks"] == 2
        assert result["source_id"] == "test.txt"

    @pytest.mark.asyncio
    async def test_search(
        self, agent, mock_vector_store, mock_hybrid_client, mock_processor
    ) -> Any:
        agent._get_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        from backend.core.vector_store import DocumentChunk

        doc1 = DocumentChunk(
            id="doc1", content="Test document content", metadata={"source": "test.txt"}
        )
        agent.vector_store = MagicMock()
        agent.vector_store.search = AsyncMock(return_value=[(doc1, 0.8)])
        agent.vector_store.is_empty = AsyncMock(return_value=False)
        agent.vector_store.get_all_documents = AsyncMock(return_value=[])
        results = await agent.search("vector databases", k=1)
        assert isinstance(results, list)
        assert len(results) > 0
        assert results[0]["text"] == "Test document content"
        assert results[0]["metadata"]["source"] == "test.txt"

    @pytest.mark.asyncio
    async def test_process_query(
        self, agent, mock_vector_store, mock_hybrid_client, mock_processor
    ) -> Any:
        query = "What is the weather like?"
        response = await agent.process({"query": query})
        assert isinstance(response, AgentResponse)
        assert response.success is True
        assert response.text is not None
        assert len(response.text) > 0

    @pytest.mark.asyncio
    async def test_process_document(
        self, agent, mock_vector_store, mock_hybrid_client, mock_processor
    ) -> Any:
        response = await agent.process({"query": "What is this document about?"})
        assert isinstance(response, AgentResponse)
        assert response.success is True

    @pytest.mark.asyncio
    async def test_process_empty_query(
        self, agent, mock_vector_store, mock_hybrid_client, mock_processor
    ) -> Any:
        response = await agent.process({})
        assert isinstance(response, AgentResponse)
        assert response.success is False
        assert "No query provided" in response.text


if __name__ == "__main__":
    unittest.main()
