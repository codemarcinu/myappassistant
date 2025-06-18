#!/usr/bin/env python3
"""
RAG Integration Example

This script demonstrates how to integrate the RAG system into an existing application,
showing a practical example of enhancing a Q&A system with document knowledge.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from src.backend.agents.enhanced_rag_agent import EnhancedRAGAgent
from src.backend.core.hybrid_llm_client import ModelComplexity, hybrid_llm_client

# Add parent directory to sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("rag-example")


class EnhancedQASystem:
    """Example application that uses RAG to improve answers"""

    def __init__(self):
        """Initialize the QA system with RAG capabilities"""
        self.rag_agent = EnhancedRAGAgent("qa-system-rag")
        logger.info("Initialized Enhanced QA System with RAG capabilities")

    async def initialize_knowledge_base(self):
        """Initialize the knowledge base with documents"""
        docs_dir = Path("data/docs")

        if not docs_dir.exists():
            logger.warning(f"Documents directory {docs_dir} does not exist")
            return False

        logger.info(f"Loading documents from {docs_dir}")
        result = await self.rag_agent.add_directory(
            docs_dir, file_extensions=[".txt", ".md", ".pdf", ".docx"], recursive=True
        )

        logger.info(
            f"Loaded {result.get('successful_files', 0)} documents with "
            f"{result.get('total_chunks_processed', 0)} chunks"
        )
        return True

    async def add_knowledge_source(
        self, source_type: str, source_path: str, metadata: Optional[Dict] = None
    ):
        """
        Add a new knowledge source to the system

        Args:
            source_type: Type of source ('file', 'url', or 'text')
            source_path: Path to file, URL, or text content
            metadata: Optional metadata for the source
        """
        if not metadata:
            metadata = {}

        logger.info(f"Adding {source_type} source: {source_path}")

        if source_type == "file":
            result = await self.rag_agent.add_file(source_path, metadata)
            logger.info(f"Added file with {result.get('chunks_processed', 0)} chunks")
        elif source_type == "url":
            result = await self.rag_agent.add_url(source_path, metadata)
            logger.info(f"Added URL with {result.get('chunks_processed', 0)} chunks")
        elif source_type == "text":
            # For text, use the path as the content and the metadata source as identifier
            source_id = metadata.get("source", f"text-{hash(source_path)}")
            result = await self.rag_agent.add_document(source_path, source_id, metadata)
            logger.info(f"Added text document with {len(result)} chunks")
        else:
            logger.error(f"Unknown source type: {source_type}")
            return None

        return result

    async def answer_question(
        self, question: str, use_rag: bool = True
    ) -> Dict[str, Any]:
        """
        Answer a question using RAG if enabled

        Args:
            question: The question to answer
            use_rag: Whether to use RAG or just the base LLM

        Returns:
            Response with answer and optional sources
        """
        logger.info(f"Processing question: {question}")

        if use_rag:
            # Use RAG to answer the question
            response = await self.rag_agent.process({"query": question})
            answer = response.text
            data = response.data
            success = response.success
        else:
            # Use base LLM without RAG
            llm_response = await hybrid_llm_client.chat(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": question},
                ],
                force_complexity=ModelComplexity.STANDARD,
                stream=False,
            )

            if llm_response and "message" in llm_response:
                answer = llm_response["message"]["content"]
                data = {}
                success = True
            else:
                answer = "Failed to generate an answer."
                data = {}
                success = False

        logger.info(f"Question answered (RAG: {use_rag}, Success: {success})")

        return {
            "question": question,
            "answer": answer,
            "used_rag": use_rag,
            "sources": data.get("sources", []),
            "success": success,
        }

    async def compare_answers(self, question: str) -> Dict[str, Any]:
        """
        Compare answers with and without RAG

        Args:
            question: The question to answer

        Returns:
            Response with both answers for comparison
        """
        logger.info(f"Comparing answers for question: {question}")

        # Get answers with and without RAG
        rag_answer = await self.answer_question(question, use_rag=True)
        base_answer = await self.answer_question(question, use_rag=False)

        return {
            "question": question,
            "rag_answer": rag_answer["answer"],
            "base_answer": base_answer["answer"],
            "sources": rag_answer.get("sources", []),
        }


async def main():
    """Main demonstration function"""
    # Create the QA system
    qa_system = EnhancedQASystem()

    # Initialize with existing documents
    await qa_system.initialize_knowledge_base()

    # Add an additional knowledge source (example)
    await qa_system.add_knowledge_source(
        source_type="text",
        source_path="""
        # Embedding Models for RAG Systems

        When implementing RAG systems, the choice of embedding model is critical.
        Some popular embedding models include:

        1. OpenAI's text-embedding-ada-002
        2. Sentence-Transformers models like all-MiniLM-L6-v2
        3. Deepseek-R1 and other Ollama-compatible models
        4. BGE models, which are optimized for multilingual retrieval

        The choice depends on factors such as:
        - Embedding quality
        - Inference speed
        - Token context length
        - Multilingual support
        - Computational requirements
        """,
        metadata={
            "source": "embedding-models-doc",
            "author": "AI Assistant",
            "category": "Technical",
            "tags": ["embeddings", "models", "RAG"],
        },
    )

    # Example questions to demonstrate RAG benefits
    questions = [
        "What is RAG and how does it work?",
        "What vector databases can I use with RAG?",
        "Which embedding models are recommended for RAG systems?",
        "How should I chunk documents for RAG?",
    ]

    # Answer each question with and without RAG
    print("\n=== Comparing Answers With and Without RAG ===\n")

    for question in questions:
        comparison = await qa_system.compare_answers(question)

        print(f"\nQuestion: {comparison['question']}")
        print("\n--- Answer with RAG ---")
        print(comparison["rag_answer"])
        print("\n--- Answer without RAG ---")
        print(comparison["base_answer"])
        print("\n" + "=" * 60)

    print("\nDemonstration complete!")


if __name__ == "__main__":
    asyncio.run(main())
