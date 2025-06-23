"""
RAG Agent

This agent implements advanced Retrieval-Augmented Generation capabilities:
- Supports multiple document types and sources
- Uses enhanced vector storage and retrieval
- Handles document chunking and embedding
- Provides source tracking and attribution
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

from ..core.hybrid_llm_client import ModelComplexity, hybrid_llm_client
from ..core.rag_document_processor import rag_document_processor
from ..core.vector_store import vector_store
from .base_agent import BaseAgent
from .interfaces import AgentResponse

logger = logging.getLogger(__name__)


class RAGAgent(BaseAgent):
    """
    Retrieval-Augmented Generation Agent

    Features:
    - Document processing with smart chunking
    - Efficient vector storage and retrieval
    - Support for various document formats
    - Source tracking and attribution
    """

    def __init__(
        self,
        name: str = "RAGAgent",
        error_handler: Any = None,
        fallback_manager: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            name=name, error_handler=error_handler, fallback_manager=fallback_manager
        )
        self.initialized = False
        self.document_processor = rag_document_processor
        self.vector_store = vector_store

    async def initialize(self) -> None:
        """Initialize the agent by ensuring vector store is populated"""
        if not self.initialized:
            # Check if vector store has documents
            if await self.vector_store.is_empty():
                # Try to process documents in the data/docs directory
                docs_dir = Path("data/docs")
                if docs_dir.exists() and docs_dir.is_dir():
                    logger.info(
                        f"Initializing RAG agent with documents from {docs_dir}"
                    )
                    await self.document_processor.process_directory(
                        docs_dir,
                        file_extensions=[".txt", ".pdf", ".docx", ".md", ".html"],
                        recursive=True,
                    )

            self.initialized = True
            count = len(await self.vector_store.get_all_documents()) if hasattr(self.vector_store, 'get_all_documents') else 0
            logger.info(
                f"RAG agent initialized with {count} chunks"
            )

    async def add_document(
        self, content: str, source_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a document to the knowledge base

        Args:
            content: Document text content
            source_id: Source identifier
            metadata: Optional metadata about the document

        Returns:
            Processing result information
        """
        results = await self.document_processor.process_document(
            content, source_id, metadata
        )
        return {"processed_chunks": len(results), "source_id": source_id}

    async def add_file(
        self, file_path: Union[str, Path], metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a document file to the knowledge base

        Args:
            file_path: Path to the document file
            metadata: Optional metadata about the document

        Returns:
            Processing result information
        """
        return await self.document_processor.process_file(file_path, metadata)

    async def add_url(
        self, url: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add content from a URL to the knowledge base

        Args:
            url: URL to fetch content from
            metadata: Optional metadata about the content

        Returns:
            Processing result information
        """
        return await self.document_processor.process_url(url, metadata)

    async def add_directory(
        self,
        directory_path: Union[str, Path],
        file_extensions: Optional[List[str]] = None,
        recursive: bool = True,
    ) -> Dict[str, Any]:
        """
        Add all documents in a directory to the knowledge base

        Args:
            directory_path: Path to the directory
            file_extensions: List of file extensions to include
            recursive: Whether to process subdirectories

        Returns:
            Processing result information
        """
        if file_extensions is None:
            file_extensions = [".txt", ".pdf", ".docx", ".md", ".html"]

        return await self.document_processor.process_directory(
            directory_path, file_extensions=file_extensions, recursive=recursive
        )

    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using the LLM client"""
        try:
            return await hybrid_llm_client.embed(text)
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            return []

    async def search(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.65,
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks

        Args:
            query: Search query
            k: Number of results to return
            filter_metadata: Optional metadata filter
            min_similarity: Minimum similarity threshold

        Returns:
            List of relevant document chunks with metadata
        """
        await self.initialize()
        query_embedding_list = await self._get_embedding(query)
        if not query_embedding_list:
            return []

        query_embedding = np.array(query_embedding_list, dtype=np.float32)

        search_results = await self.vector_store.search(
            query_embedding=query_embedding,
            k=k
        )
        # Format results to match the expected return type
        return [
            {
                "text": chunk.content,
                "metadata": chunk.metadata,
                "similarity": score,
            }
            for chunk, score in search_results
        ]

    async def process(self, context: Dict[str, Any]) -> AgentResponse:
        """
        Process a query using RAG

        Args:
            context: Request context with query

        Returns:
            AgentResponse with answer
        """
        await self.initialize()

        query = context.get("query", "")
        if not query:
            return AgentResponse(text="No query provided.", data={}, success=False)

        # Sprawdź flagę use_bielik
        use_bielik = context.get("use_bielik", True)
        model = (
            "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M" if use_bielik else "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
        )

        # Get query embedding and search for relevant chunks
        retrieved_docs = await self.search(query, k=5)

        if not retrieved_docs:
            return AgentResponse(
                text="Przepraszam, nie mogę odpowiedzieć na to pytanie. Spróbuj inaczej sformułować zapytanie lub zadaj inne pytanie.",
                data={},
                success=True,
            )

        # Format context from retrieved documents
        context_chunks = []
        sources = []

        for i, doc in enumerate(retrieved_docs):
            chunk_text = doc["text"]
            source = doc["metadata"].get("source", "unknown")

            # Add to context
            context_chunks.append(f"[Chunk {i+1}] {chunk_text}")

            # Track source if not already included
            if source not in sources:
                sources.append(source)

        # Build prompt with context
        context_text = "\n\n".join(context_chunks)
        prompt = f"""Based on the following context, answer the user's question. If the context doesn't contain enough information to answer the question, say so.

Context:
{context_text}

Question: {query}

Answer:"""

        # Generate response using LLM with selected model
        try:
            response = await hybrid_llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                force_complexity=ModelComplexity.STANDARD,
            )

            # Check if response is an error response
            if isinstance(response, dict) and "error" in response:
                logger.error(f"LLM returned error: {response['error']}")
                return AgentResponse(
                    text="Przepraszam, wystąpił błąd podczas generowania odpowiedzi. Spróbuj ponownie później.",
                    data={"error": response["error"]},
                    success=False,
                )

            answer = response.get("message", {}).get(
                "content", "No response generated."
            )

            # Check if the answer indicates an error
            if (
                "Error processing request" in answer
                or "Error during streaming" in answer
            ):
                logger.error(f"LLM returned error in content: {answer}")
                return AgentResponse(
                    text="Przepraszam, wystąpił błąd podczas generowania odpowiedzi. Spróbuj ponownie później.",
                    data={"error": answer},
                    success=False,
                )

            # Format response with sources
            if sources:
                answer += f"\n\nSources: {', '.join(sources)}"

            return AgentResponse(
                text=answer,
                data={
                    "sources": sources,
                    "chunks_used": len(retrieved_docs),
                    "query": query,
                },
                success=True,
            )

        except Exception as e:
            logger.error(f"Error generating RAG response: {str(e)}")
            return AgentResponse(
                text="Przepraszam, wystąpił błąd podczas generowania odpowiedzi. Spróbuj ponownie później.",
                data={"error": str(e)},
                success=False,
            )

    def get_metadata(self) -> Dict[str, Any]:
        """Return agent metadata including capabilities"""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "capabilities": [
                "document_processing",
                "vector_search",
                "source_tracking",
            ],
            "document_count": 0, # Synchronous alternative needed
        }
