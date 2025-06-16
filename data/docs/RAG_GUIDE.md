# Retrieval-Augmented Generation (RAG) System Guide

This guide provides detailed instructions on how to add documents to the Retrieval-Augmented Generation (RAG) system in your project, using LangChain and local vector stores (FAISS or Pinecone).

## Table of Contents

- [Overview](#overview)
- [Components](#components)
- [Installation](#installation)
- [Document Processing](#document-processing)
- [Using the CLI Tool](#using-the-cli-tool)
- [Integration in Python Code](#integration-in-python-code)
- [Jupyter Notebook Example](#jupyter-notebook-example)
- [Advanced Usage](#advanced-usage)

## Overview

The RAG system enhances LLM capabilities by providing relevant context from a knowledge base. The implementation includes:

- Document loading from various sources (PDF, Word, HTML, text)
- Smart text chunking with configurable size and overlap
- Embedding generation using local or remote models
- Vector storage with FAISS (local) or Pinecone (cloud)
- Semantic search with metadata filtering
- Integration with the hybrid LLM client

## Components

The system consists of the following key components:

1. **RAG Document Processor** (`src/backend/core/rag_document_processor.py`): Handles document loading, chunking, and embedding generation
2. **Enhanced RAG Agent** (`src/backend/agents/enhanced_rag_agent.py`): Provides high-level interface for RAG operations
3. **CLI Tool** (`scripts/rag_cli.py`): Command-line utility for managing the RAG knowledge base
4. **Example Notebook** (`examples/rag_system_demo.ipynb`): Jupyter notebook demonstrating RAG usage

## Installation

Ensure you have the necessary dependencies:

```bash
pip install langchain faiss-cpu sentence-transformers unstructured
pip install pinecone-client  # Optional, for Pinecone support
```

## Document Processing

### 1. Preparing Documents

Before indexing, documents need to be processed:

1. **Loading**: Use appropriate document loaders based on file type:
   ```python
   from src.backend.core.rag_document_processor import rag_document_processor
   
   # Load from file
   content = rag_document_processor.load_document("path/to/document.pdf")
   
   # Load from URL
   content = rag_document_processor.load_from_url("https://example.com/article")
   ```

2. **Chunking**: Documents are automatically split into semantic chunks:
   ```python
   chunks = rag_document_processor.chunk_text(content)
   ```

### 2. Generating Embeddings

Embeddings can be generated using:
- Local models via sentence-transformers
- Ollama models (if installed)
- Remote LLM API

```python
# Generate embeddings for a text chunk
embedding = await rag_document_processor.embed_text("Your text here")

# Optionally normalize
normalized_emb = await rag_document_processor.normalize_embedding(embedding)
```

### 3. Storing Vectors

Documents can be stored in:

#### FAISS (local)
```python
# FAISS is used automatically when available
await rag_document_processor.process_document(
    content="Document text",
    source_id="doc1",
    metadata={"category": "tutorial"}
)
```

#### Pinecone (cloud)
```python
# Initialize with Pinecone configuration
from src.backend.core.rag_document_processor import RAGDocumentProcessor

processor = RAGDocumentProcessor(
    pinecone_api_key="your-api-key",
    pinecone_index="your-index-name"
)

# Process and store
await processor.process_document(
    content="Document text",
    source_id="doc1",
    metadata={"category": "tutorial"}
)
```

## Using the CLI Tool

The `rag_cli.py` script provides convenient command-line access to RAG functionality:

### Adding Documents

```bash
# Add a single file
python scripts/rag_cli.py add-file data/docs/document.pdf --tags="AI,tutorial" --category="education"

# Add a directory of documents
python scripts/rag_cli.py add-directory data/docs --recursive --extensions=".pdf,.docx,.txt"

# Add content from a URL
python scripts/rag_cli.py add-url https://example.com/article --tags="news,tech" --category="current-events"
```

### Searching

```bash
# Basic search
python scripts/rag_cli.py search "What are vector databases?"

# Search with filters
python scripts/rag_cli.py search "RAG architecture" --tags="tutorial" --category="education" --limit=10

# Show full text in results
python scripts/rag_cli.py search "embedding models" --full-text
```

### Statistics

```bash
# View knowledge base stats
python scripts/rag_cli.py stats

# Get JSON stats
python scripts/rag_cli.py stats --json
```

## Integration in Python Code

### Using the Enhanced RAG Agent

```python
import asyncio
from src.backend.agents.enhanced_rag_agent import EnhancedRAGAgent

async def main():
    # Create agent
    rag_agent = EnhancedRAGAgent("my-rag-agent")
    
    # Add documents
    await rag_agent.add_file("path/to/document.pdf")
    
    # Search
    results = await rag_agent.search("What is RAG?", k=5)
    
    # Answer questions
    response = await rag_agent.process({"query": "Explain RAG architecture"})
    print(response.text)

# Run
asyncio.run(main())
```

### Batch Processing

```python
import asyncio
from src.backend.core.rag_document_processor import rag_document_processor

async def process_batch():
    documents = [
        ("Document 1 content", {"source": "doc1", "category": "tech"}),
        ("Document 2 content", {"source": "doc2", "category": "finance"}),
        # More documents...
    ]
    
    results = await rag_document_processor.process_batch(documents)
    print(f"Processed {len(results)} documents")

# Run
asyncio.run(process_batch())
```

## Jupyter Notebook Example

A comprehensive example is available in `examples/rag_system_demo.ipynb`. This notebook demonstrates:

1. Adding documents from text and files
2. Searching the knowledge base
3. Asking questions with RAG
4. Filtering search results
5. Saving the vector store

## Advanced Usage

### Custom Chunking Strategy

```python
from src.backend.core.rag_document_processor import RAGDocumentProcessor

# Create processor with custom chunking parameters
processor = RAGDocumentProcessor(
    chunk_size=1000,  # Larger chunks
    chunk_overlap=100  # More overlap
)

# Process documents with custom chunking
await processor.process_file("path/to/document.pdf")
```

### Local Embedding Models

```python
from src.backend.core.rag_document_processor import RAGDocumentProcessor

# Use local embedding model
processor = RAGDocumentProcessor(
    use_local_embeddings=True  # Uses sentence-transformers
)

# Process with local embeddings
await processor.process_file("path/to/document.pdf")
```

### Incremental Indexing

For continuously updating a knowledge base with new documents:

```python
from pathlib import Path
import asyncio
from src.backend.core.rag_document_processor import AsyncDocumentLoader
from src.backend.core.enhanced_vector_store import enhanced_vector_store

async def setup_incremental_indexing():
    # Create loader
    loader = AsyncDocumentLoader(enhanced_vector_store)
    
    # Start incremental indexing
    await loader.start_incremental_indexing(
        directory="data/docs",
        glob_pattern="**/*.pdf",  # Match pattern
        check_interval=300  # Check every 5 minutes
    )
    
    # Run indefinitely
    try:
        while True:
            await asyncio.sleep(3600)  # Check status every hour
            print("Monitoring for document changes...")
    except KeyboardInterrupt:
        # Stop indexing when interrupted
        await loader.stop_indexing()
        print("Indexing stopped")

# Run in background
asyncio.create_task(setup_incremental_indexing())
```

---

By following this guide, you can effectively add documents to your RAG system and leverage their content to enhance your AI application's responses with relevant, accurate information.