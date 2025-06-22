"""
Enhanced RAG Agent

This agent extends the base RAG Agent with advanced features:
- Database integration for personalized context
- Improved document ingestion
- Enhanced retrieval strategies
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.hybrid_llm_client import ModelComplexity, hybrid_llm_client
from ..core.vector_store import DocumentChunk, VectorStore
from .interfaces import AgentResponse
from .rag_agent import RAGAgent

logger = logging.getLogger(__name__)


class EnhancedRAGAgent(RAGAgent):
    """
    Enhanced Retrieval-Augmented Generation Agent

    Features:
    - All features of base RAGAgent
    - Database integration for personalized context
    - Improved document ingestion with better chunking
    - Enhanced retrieval strategies
    """

    def __init__(
        self,
        name: str = "EnhancedRAGAgent",
        error_handler=None,
        fallback_manager=None,
        vector_store=None,
        llm_client=None,
        **kwargs,
    ):
        super().__init__(
            name=name, 
            error_handler=error_handler, 
            fallback_manager=fallback_manager,
            **kwargs
        )
        # Override vector_store and llm_client if provided (useful for testing)
        if vector_store:
            self.vector_store = vector_store
        if llm_client:
            self.llm_client = llm_client
        else:
            self.llm_client = hybrid_llm_client

    async def process(self, context: Dict[str, Any]) -> AgentResponse:
        """
        Process a query using enhanced RAG with database integration

        Args:
            context: Request context with query and optional database session

        Returns:
            AgentResponse with answer
        """
        await self.initialize()

        query = context.get("query", "")
        if not query:
            return AgentResponse(text="No query provided.", data={}, success=False)

        # Get model from context or use default
        model = context.get("model", "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M")
        
        # Check for database session to include product context
        db_session = context.get("db")
        product_context = ""
        
        if db_session:
            # Get user's products from database if available
            product_context = await self._get_product_context(db_session)

        # Get query embedding and search for relevant chunks
        query_embedding = await self._get_embedding(query)
        retrieved_docs = await self.vector_store.search(query_embedding, k=5)

        if not retrieved_docs and not product_context:
            # Fall back to general knowledge if no relevant documents found
            return await self._generate_general_response(query, model)

        # Format context from retrieved documents
        context_chunks = []
        sources = []

        for doc_chunk, similarity in retrieved_docs:
            chunk_text = doc_chunk.content
            source = doc_chunk.metadata.get("source", "unknown")
            section = doc_chunk.metadata.get("section", "")

            # Add to context with section information if available
            if section:
                context_chunks.append(f"[{section}] {chunk_text}")
            else:
                context_chunks.append(chunk_text)

            # Track source if not already included
            if source not in sources:
                sources.append(source)

        # Build prompt with context
        context_text = "\n\n".join(context_chunks)
        
        prompt = f"""Based on the following information, answer the user's question. 
If the information doesn't contain enough details to answer the question completely, provide the best answer you can.

REFERENCE INFORMATION:
{context_text}
"""

        # Add product context if available
        if product_context:
            prompt += f"\nUSER'S AVAILABLE PRODUCTS:\n{product_context}\n"

        prompt += f"\nQUESTION: {query}\n\nANSWER:"

        # Generate response using LLM
        try:
            response = await self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                force_complexity=ModelComplexity.STANDARD,
            )

            answer = response.get("message", {}).get("content", "No response generated.")

            return AgentResponse(
                text=answer,
                data={
                    "sources": sources,
                    "retrieved_chunks": len(retrieved_docs),
                    "has_product_context": bool(product_context),
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

    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using the LLM client"""
        try:
            return await self.llm_client.embed(text)
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            # Return random embedding as fallback (only for testing)
            return np.random.rand(768).tolist()

    async def _get_product_context(self, db_session: AsyncSession) -> str:
        """
        Get context about user's available products from database
        
        Args:
            db_session: Database session
            
        Returns:
            String with product information
        """
        try:
            # Import here to avoid circular imports
            from sqlalchemy import select
            from ..models.shopping import Product
            
            # Query for user's products
            result = await db_session.execute(
                select(Product).where(Product.is_consumed == 0)
            )
            products = result.scalars().all()
            
            if not products:
                return ""
                
            # Format product information
            product_lines = []
            for product in products:
                expiry_info = f", expires: {product.expiration_date}" if product.expiration_date else ""
                product_lines.append(f"- {product.name} (category: {product.category}{expiry_info})")
                
            return "Available products:\n" + "\n".join(product_lines)
            
        except Exception as e:
            logger.error(f"Error getting product context: {str(e)}")
            return ""

    async def _generate_general_response(self, query: str, model: str) -> AgentResponse:
        """
        Generate a response without specific document context
        
        Args:
            query: User query
            model: LLM model to use
            
        Returns:
            AgentResponse with general knowledge answer
        """
        prompt = f"""The user has asked a question, but I don't have specific documents in my knowledge base about this topic.
Please provide a helpful general response based on your knowledge.

Question: {query}

Answer:"""

        try:
            response = await self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                model=model,
            )
            
            answer = response.get("message", {}).get("content", "No response generated.")
            
            return AgentResponse(
                text=answer,
                data={"used_fallback": True},
                success=True,
            )
        except Exception as e:
            logger.error(f"Error generating fallback response: {str(e)}")
            return AgentResponse(
                text="Przepraszam, nie mogę odpowiedzieć na to pytanie.",
                data={"error": str(e)},
                success=False,
            )

    async def ingest_document(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Ingest a document file into the vector store
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with ingestion results
        """
        try:
            result = await self.add_file(file_path)
            return {
                "success": True,
                "file_path": str(file_path),
                "chunks_added": result.get("chunks_added", 0),
                "message": f"Successfully ingested document: {os.path.basename(file_path)}"
            }
        except Exception as e:
            logger.error(f"Error ingesting document {file_path}: {str(e)}")
            return {
                "success": False,
                "file_path": str(file_path),
                "chunks_added": 0,
                "error": str(e)
            }

    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata about this agent"""
        metadata = super().get_metadata()
        metadata.update({
            "name": self.name,
            "description": "Enhanced RAG agent with database integration and improved retrieval",
            "version": "1.1.0",
            "capabilities": [
                "document_retrieval",
                "database_integration",
                "personalized_responses",
                "fallback_to_general_knowledge"
            ],
        })
        return metadata 