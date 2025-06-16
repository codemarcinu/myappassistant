import asyncio
import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from backend.agents.enhanced_rag_agent import EnhancedRAGAgent
from backend.core.rag_document_processor import RAGDocumentProcessor


class TestEnhancedRAGAgent(unittest.TestCase):
    """Tests for the EnhancedRAGAgent"""

    def setUp(self):
        """Set up the test environment"""
        self.agent = EnhancedRAGAgent("test-rag-agent")
        
        # Create a test document
        self.test_content = """
        # Test Document
        
        This is a test document for RAG. It contains information about vector databases.
        
        Vector databases like FAISS and Pinecone are used to store embeddings for RAG systems.
        They allow for efficient similarity search.
        """
        
        self.test_metadata = {
            "title": "Test Document",
            "category": "Test",
            "tags": ["test", "rag", "vector-db"]
        }

    def test_agent_initialization(self):
        """Test that the agent initializes correctly"""
        self.assertEqual(self.agent.name, "test-rag-agent")
        self.assertFalse(self.agent.initialized)
        self.assertIsNotNone(self.agent.document_processor)
        self.assertIsNotNone(self.agent.vector_store)

    @patch('backend.core.rag_document_processor.rag_document_processor.process_document')
    async def test_add_document(self, mock_process_document):
        """Test adding a document"""
        # Mock the process_document method
        mock_process_document.return_value = ["chunk1", "chunk2"]
        
        # Call add_document
        result = await self.agent.add_document(
            self.test_content,
            "test-doc-1",
            self.test_metadata
        )
        
        # Check that process_document was called correctly
        mock_process_document.assert_called_once_with(
            self.test_content,
            "test-doc-1",
            self.test_metadata
        )
        
        # Check the result
        self.assertEqual(result, ["chunk1", "chunk2"])

    @patch('backend.core.enhanced_vector_store.enhanced_vector_store.search')
    async def test_search(self, mock_search):
        """Test searching for documents"""
        # Mock the search method
        mock_results = [
            {
                "chunk_id": "test-chunk-1",
                "text": "Vector databases like FAISS and Pinecone",
                "metadata": self.test_metadata,
                "similarity": 0.85
            }
        ]
        mock_search.return_value = mock_results
        
        # Call search
        results = await self.agent.search("vector databases", k=1)
        
        # Check that search was called correctly
        mock_search.assert_called_once_with(
            query="vector databases",
            k=1,
            filter_metadata=None,
            min_similarity=0.65
        )
        
        # Check the results
        self.assertEqual(results, mock_results)

    @patch('backend.core.hybrid_llm_client.hybrid_llm_client.chat')
    @patch('backend.agents.enhanced_rag_agent.EnhancedRAGAgent.search')
    async def test_process(self, mock_search, mock_chat):
        """Test processing a query"""
        # Mock the search method
        mock_search.return_value = [
            {
                "chunk_id": "test-chunk-1",
                "text": "Vector databases like FAISS and Pinecone are used to store embeddings.",
                "metadata": {"source": "test-doc-1"},
                "similarity": 0.85
            }
        ]
        
        # Mock the chat method
        mock_chat.return_value = {
            "message": {
                "content": "Vector databases are specialized databases for storing embeddings."
            }
        }
        
        # Call process
        response = await self.agent.process({"query": "What are vector databases?"})
        
        # Check that search was called
        mock_search.assert_called_once()
        
        # Check that chat was called
        mock_chat.assert_called_once()
        
        # Check the response
        self.assertTrue(response.success)
        self.assertIn("Vector databases", response.text)
        self.assertIn("test-doc-1", response.text)  # Source should be included


def async_test(coro):
    """Decorator for async test methods"""
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper


# Add the async_test decorator to async test methods
TestEnhancedRAGAgent.test_add_document = async_test(TestEnhancedRAGAgent.test_add_document)
TestEnhancedRAGAgent.test_search = async_test(TestEnhancedRAGAgent.test_search)
TestEnhancedRAGAgent.test_process = async_test(TestEnhancedRAGAgent.test_process)


if __name__ == "__main__":
    unittest.main()