#!/usr/bin/env python3
"""
Test RAG System

This script tests the RAG system functionality including:
- Document processing
- Database synchronization
- Search functionality
- Vector store operations
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Dodaj src/backend do PYTHONPATH dla importów absolutnych
backend_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../src/backend")
)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from backend.core.rag_document_processor import RAGDocumentProcessor
from backend.core.rag_integration import rag_integration
from backend.core.vector_store import vector_store
from backend.infrastructure.database.database import AsyncSessionLocal

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_document_processing():
    """Test document processing functionality"""
    logger.info("Testing document processing...")

    # Create test document
    test_content = """
    # Test Document for RAG System

    This is a test document to verify the RAG system functionality.

    ## Key Features
    - Document chunking
    - Embedding generation
    - Vector storage
    - Semantic search

    ## Usage
    The RAG system can process various document types including:
    - PDF files
    - Word documents
    - Text files
    - Markdown files
    - HTML files

    ## Benefits
    - Improved search accuracy
    - Context-aware responses
    - Source attribution
    - Real-time knowledge updates
    """

    # Process document
    result = await rag_integration.rag_processor.process_document(
        content=test_content,
        source_id="test_document_001",
        metadata={
            "type": "test",
            "category": "documentation",
            "tags": ["test", "rag", "documentation"],
        },
    )

    logger.info(f"Document processed: {len(result)} chunks created")
    return result


async def test_database_sync():
    """Test database synchronization"""
    logger.info("Testing database synchronization...")

    async with AsyncSessionLocal() as db:
        # Test pantry sync
        pantry_result = await rag_integration.sync_pantry_to_rag(db)
        logger.info(f"Pantry sync result: {pantry_result}")

        # Test receipts sync
        receipts_result = await rag_integration.sync_receipts_to_rag(db)
        logger.info(f"Receipts sync result: {receipts_result}")

        # Test conversations sync
        conversations_result = await rag_integration.sync_conversations_to_rag(db)
        logger.info(f"Conversations sync result: {conversations_result}")

        return {
            "pantry": pantry_result,
            "receipts": receipts_result,
            "conversations": conversations_result,
        }


async def test_search_functionality():
    """Test search functionality"""
    logger.info("Testing search functionality...")

    # Test queries
    test_queries = [
        "RAG system features",
        "document processing",
        "vector storage",
        "semantic search",
        "test document",
        "cooking recipes",
        "shopping list",
        "pantry items",
    ]

    results = {}

    for query in test_queries:
        logger.info(f"Searching for: {query}")
        search_results = await vector_store.search(query=query, k=5, min_similarity=0.5)

        results[query] = {
            "count": len(search_results),
            "top_result": search_results[0] if search_results else None,
        }

        logger.info(f"Found {len(search_results)} results for '{query}'")

        if search_results:
            top_result = search_results[0]
            logger.info(f"Top result similarity: {top_result['similarity']:.3f}")
            logger.info(
                f"Top result source: {top_result['metadata'].get('source', 'unknown')}"
            )

    return results


async def test_vector_store_stats():
    """Test vector store statistics"""
    logger.info("Testing vector store statistics...")

    stats = await vector_store.get_statistics()
    logger.info(f"Vector store statistics: {stats}")

    return stats


async def test_file_processing():
    """Test file processing"""
    logger.info("Testing file processing...")

    # Create test file
    test_file_path = Path("data/test_rag_document.md")
    test_file_path.parent.mkdir(parents=True, exist_ok=True)

    test_content = """
    # Test RAG Document

    This is a test document created for RAG system testing.

    ## Content
    - Multiple sections
    - Different topics
    - Various formatting

    ## Purpose
    To verify that the RAG system can properly process files
    and extract meaningful chunks for search and retrieval.

    ## Expected Results
    - Document should be chunked appropriately
    - Embeddings should be generated
    - Chunks should be stored in vector database
    - Search should return relevant results
    """

    # Write test file
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_content)

    try:
        # Process file
        result = await rag_integration.rag_processor.process_file(
            test_file_path,
            metadata={
                "type": "test_file",
                "category": "testing",
                "tags": ["test", "file", "processing"],
            },
        )

        logger.info(f"File processed: {result}")
        return result

    finally:
        # Clean up test file
        test_file_path.unlink(missing_ok=True)


async def main():
    """Run all RAG system tests"""
    logger.info("Starting RAG system tests...")

    try:
        # Test 1: Document processing
        await test_document_processing()

        # Test 2: File processing
        await test_file_processing()

        # Test 3: Database synchronization
        sync_results = await test_database_sync()

        # Test 4: Search functionality
        search_results = await test_search_functionality()

        # Test 5: Vector store statistics
        stats = await test_vector_store_stats()

        # Summary
        logger.info("=== RAG System Test Summary ===")
        logger.info(f"Database sync results: {sync_results}")
        logger.info(f"Search results summary: {len(search_results)} queries tested")
        logger.info(f"Vector store stats: {stats}")

        logger.info("All tests completed successfully!")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
