#!/usr/bin/env python3
"""
RAG CLI Tool

This command-line utility provides an easy way to manage the RAG knowledge base:
- Add documents (files, directories, URLs)
- Search the knowledge base
- View vector store statistics

Usage:
  python rag_cli.py add-file path/to/document.pdf
  python rag_cli.py add-directory data/documents --recursive
  python rag_cli.py add-url https://example.com/article
  python rag_cli.py search "What is RAG?"
  python rag_cli.py stats
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from src.backend.agents.enhanced_rag_agent import EnhancedRAGAgent
from src.backend.core.enhanced_vector_store import enhanced_vector_store
from src.backend.core.rag_document_processor import RAGDocumentProcessor

# Initialize RAG document processor
rag_document_processor = RAGDocumentProcessor()

# Add parent directory to path to import modules from the project
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("rag-cli")


async def add_file(args):
    """Add a file to the RAG knowledge base"""
    file_path = Path(args.file_path).resolve()

    if not file_path.exists() or not file_path.is_file():
        logger.error(f"File not found: {file_path}")
        return

    logger.info(f"Processing file: {file_path}")

    # Add any additional metadata
    metadata = {}
    if args.tags:
        metadata["tags"] = args.tags.split(",")

    if args.category:
        metadata["category"] = args.category

    # Process the file
    result = await rag_document_processor.process_file(file_path, metadata)

    if result["success"]:
        logger.info(
            f"Successfully processed file with {result['chunks_processed']} chunks"
        )
    else:
        logger.error(f"Failed to process file: {result.get('error', 'Unknown error')}")

    # Save the vector store if requested
    if args.save:
        await enhanced_vector_store.save_index_async()
        logger.info("Vector store saved")


async def add_directory(args):
    """Add all files in a directory to the RAG knowledge base"""
    directory_path = Path(args.directory_path).resolve()

    if not directory_path.exists() or not directory_path.is_dir():
        logger.error(f"Directory not found: {directory_path}")
        return

    logger.info(f"Processing directory: {directory_path}")

    # Process the directory
    file_extensions = None
    if args.extensions:
        file_extensions = args.extensions.split(",")

    result = await rag_document_processor.process_directory(
        directory_path,
        file_extensions=file_extensions,
        recursive=args.recursive,
        batch_size=args.batch_size,
    )

    if result["success"]:
        logger.info(
            f"Successfully processed {result['successful_files']}/{result['files_processed']} files"
        )
        logger.info(f"Total chunks processed: {result['total_chunks_processed']}")

        if result["failed_files"] > 0:
            logger.warning(f"Failed to process {result['failed_files']} files")
    else:
        logger.error(
            f"Failed to process directory: {result.get('error', 'Unknown error')}"
        )

    # Save the vector store if requested
    if args.save:
        await enhanced_vector_store.save_index_async()
        logger.info("Vector store saved")


async def add_url(args):
    """Add content from a URL to the RAG knowledge base"""
    url = args.url

    logger.info(f"Processing URL: {url}")

    # Add any additional metadata
    metadata = {"source_type": "url"}
    if args.tags:
        metadata["tags"] = args.tags.split(",")

    if args.category:
        metadata["category"] = args.category

    # Process the URL
    result = await rag_document_processor.process_url(url, metadata)

    if result["success"]:
        logger.info(
            f"Successfully processed URL with {result['chunks_processed']} chunks"
        )
    else:
        logger.error(f"Failed to process URL: {result.get('error', 'Unknown error')}")

    # Save the vector store if requested
    if args.save:
        await enhanced_vector_store.save_index_async()
        logger.info("Vector store saved")


async def search(args):
    """Search the RAG knowledge base"""
    query = args.query

    logger.info(f"Searching: '{query}'")

    # Create RAG agent instance
    rag_agent = EnhancedRAGAgent("rag-cli-agent")

    # Apply metadata filters if provided
    filter_metadata = {}
    if args.tags:
        filter_metadata["tags"] = args.tags.split(",")

    if args.category:
        filter_metadata["category"] = args.category

    # Search the knowledge base
    results = await rag_agent.search(
        query=query,
        k=args.limit,
        filter_metadata=filter_metadata if filter_metadata else None,
        min_similarity=args.min_similarity,
    )

    # Display results
    if not results:
        logger.info("No matching documents found")
        return

    logger.info(f"Found {len(results)} matching documents:")

    for i, result in enumerate(results):
        print(f"\n--- Result {i+1} (similarity: {result['similarity']:.2f}) ---")
        print(f"Source: {result['metadata'].get('source', 'Unknown')}")

        # Print tags and category if available
        tags = result["metadata"].get("tags")
        if tags:
            print(f"Tags: {', '.join(tags)}")

        category = result["metadata"].get("category")
        if category:
            print(f"Category: {category}")

        # Print chunk text (truncated if very long)
        text = result["text"]
        if len(text) > 500 and not args.full_text:
            print(
                f"\nText: {text[:500]}...\n(truncated, use --full-text to see complete text)"
            )
        else:
            print(f"\nText: {text}")


async def get_stats(args):
    """Display statistics about the vector store"""
    # Basic stats
    chunk_count = len(enhanced_vector_store.chunks)

    # Get unique sources
    sources = set()
    for chunk in enhanced_vector_store.chunks:
        source = chunk.metadata.get("source", "unknown")
        sources.add(source)

    # Get categories if available
    categories = {}
    for chunk in enhanced_vector_store.chunks:
        category = chunk.metadata.get("category")
        if category:
            categories[category] = categories.get(category, 0) + 1

    # Get tags if available
    tags = {}
    for chunk in enhanced_vector_store.chunks:
        chunk_tags = chunk.metadata.get("tags", [])
        if isinstance(chunk_tags, list):
            for tag in chunk_tags:
                tags[tag] = tags.get(tag, 0) + 1

    # Print stats
    print("\n=== RAG Vector Store Statistics ===")
    print(f"Total chunks: {chunk_count}")
    print(f"Unique sources: {len(sources)}")

    if categories:
        print("\nCategories:")
        for category, count in sorted(
            categories.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  - {category}: {count} chunks")

    if tags:
        print("\nTags:")
        for tag, count in sorted(tags.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  - {tag}: {count} chunks")
        if len(tags) > 10:
            print(f"  (and {len(tags) - 10} more tags)")

    # If JSON output requested
    if args.json:
        stats = {
            "total_chunks": chunk_count,
            "unique_sources": len(sources),
            "sources": list(sources),
            "categories": categories,
            "tags": tags,
        }

        print("\nJSON Stats:")
        print(json.dumps(stats, indent=2))


def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(description="RAG CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Add file command
    file_parser = subparsers.add_parser(
        "add-file", help="Add a file to the RAG knowledge base"
    )
    file_parser.add_argument("file_path", help="Path to the file")
    file_parser.add_argument("--tags", help="Comma-separated tags for the document")
    file_parser.add_argument("--category", help="Category for the document")
    file_parser.add_argument(
        "--save", action="store_true", help="Save the vector store after processing"
    )

    # Add directory command
    dir_parser = subparsers.add_parser(
        "add-directory", help="Add all files in a directory"
    )
    dir_parser.add_argument("directory_path", help="Path to the directory")
    dir_parser.add_argument(
        "--recursive", action="store_true", help="Process subdirectories recursively"
    )
    dir_parser.add_argument(
        "--extensions", help="Comma-separated list of file extensions to include"
    )
    dir_parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of files to process concurrently",
    )
    dir_parser.add_argument(
        "--save", action="store_true", help="Save the vector store after processing"
    )

    # Add URL command
    url_parser = subparsers.add_parser("add-url", help="Add content from a URL")
    url_parser.add_argument("url", help="URL to process")
    url_parser.add_argument("--tags", help="Comma-separated tags for the document")
    url_parser.add_argument("--category", help="Category for the document")
    url_parser.add_argument(
        "--save", action="store_true", help="Save the vector store after processing"
    )

    # Search command
    search_parser = subparsers.add_parser(
        "search", help="Search the RAG knowledge base"
    )
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--limit", type=int, default=5, help="Maximum number of results"
    )
    search_parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.65,
        help="Minimum similarity threshold",
    )
    search_parser.add_argument("--tags", help="Filter by comma-separated tags")
    search_parser.add_argument("--category", help="Filter by category")
    search_parser.add_argument(
        "--full-text", action="store_true", help="Show full text of results"
    )

    # Stats command
    stats_parser = subparsers.add_parser(
        "stats", help="Display vector store statistics"
    )
    stats_parser.add_argument(
        "--json", action="store_true", help="Output stats in JSON format"
    )

    # Parse arguments
    args = parser.parse_args()

    # Execute command
    if args.command == "add-file":
        asyncio.run(add_file(args))
    elif args.command == "add-directory":
        asyncio.run(add_directory(args))
    elif args.command == "add-url":
        asyncio.run(add_url(args))
    elif args.command == "search":
        asyncio.run(search(args))
    elif args.command == "stats":
        asyncio.run(get_stats(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
