import logging
from typing import Any, Dict, List

from backend.core.vector_store import VectorStore
from backend.infrastructure.llm_api.llm_client import LLMClient

logger = logging.getLogger(__name__)


class EnhancedVectorStoreImpl:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.vector_store = VectorStore()

    async def add_documents(self, documents: List[str]) -> None:
        """Add documents to vector store"""
        try:
            for i, document in enumerate(documents):
                metadata = {"source": f"document_{i}", "type": "text", "index": i}
                await self.vector_store.add_document(
                    text=document, metadata=metadata, auto_embed=True
                )
            logger.info(f"Added {len(documents)} documents to vector store")
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise

    async def similarity_search(self, query: str, k: int = 4) -> List[str]:
        """Search for similar documents"""
        try:
            # Generate query embedding
            query_embedding = await self.llm_client.embed(query)
            if not query_embedding:
                return []

            # Search vector store
            results = await self.vector_store.search(
                query_embedding=query_embedding, k=k
            )

            # Extract text from results
            documents = [result["text"] for result in results if result.get("text")]
            return documents
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []

    async def get_relevant_documents(self, query: str) -> List[str]:
        """Get relevant documents for query"""
        try:
            # Use similarity search with default k=4
            return await self.similarity_search(query, k=4)
        except Exception as e:
            logger.error(f"Error getting relevant documents: {e}")
            return []
