"""
RAG Document Processor

This module handles the process of preparing documents for RAG systems:
1. Loading documents from various sources and formats
2. Chunking text with appropriate overlap
3. Generating embeddings
4. Storing in vector databases (FAISS or Pinecone)
"""

import asyncio
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS not available, falling back to simple vector store")

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
    from langchain_community.document_loaders.email import UnstructuredEmailLoader
    from langchain_community.document_loaders.markdown import UnstructuredMarkdownLoader
    from langchain_community.document_loaders.powerpoint import (
        UnstructuredPowerPointLoader,
    )
    from langchain_community.document_loaders.word_document import (
        UnstructuredWordDocumentLoader,
    )

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain not available, falling back to basic document loading")

try:
    import pinecone

    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logging.warning("Pinecone not available, falling back to local vector store")

try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning(
        "SentenceTransformers not available, falling back to LLM-based embeddings"
    )

from ..core.enhanced_vector_store import EnhancedVectorStore, enhanced_vector_store
from ..core.hybrid_llm_client import hybrid_llm_client

logger = logging.getLogger(__name__)


class RAGDocumentProcessor:
    """
    Comprehensive document processor for RAG systems

    This processor handles the end-to-end flow of:
    - Loading documents from various sources
    - Chunking text appropriately
    - Generating embeddings
    - Storing vectors in FAISS or Pinecone
    """

    def __init__(
        self,
        vector_store: Optional[EnhancedVectorStore] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        embedding_model: str = "deepseek-r1",
        use_local_embeddings: bool = False,
        pinecone_api_key: Optional[str] = None,
        pinecone_index: Optional[str] = None,
    ):
        """
        Initialize the RAG document processor

        Args:
            vector_store: Optional EnhancedVectorStore to use (uses global instance if None)
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens
            embedding_model: Model to use for embeddings
            use_local_embeddings: Whether to use local SentenceTransformers for embeddings
            pinecone_api_key: API key for Pinecone (if using Pinecone)
            pinecone_index: Index name for Pinecone (if using Pinecone)
        """
        self.vector_store = vector_store or enhanced_vector_store
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_model = embedding_model
        self.use_local_embeddings = use_local_embeddings

        # Initialize text splitter
        if LANGCHAIN_AVAILABLE:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=self._token_counter,
                separators=["\n\n", "\n", ". ", "! ", "? ", ";", ":", " - ", "\t", " "],
            )
        else:
            self.text_splitter = None

        # Initialize embedding model if using local embeddings
        if use_local_embeddings and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedding_model_local = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Initialized local embedding model: all-MiniLM-L6-v2")
            except Exception as e:
                logger.error(f"Failed to initialize local embedding model: {e}")
                self.embedding_model_local = None
                self.use_local_embeddings = False
        else:
            self.embedding_model_local = None

        # Initialize Pinecone if available and API key is provided
        self.use_pinecone = False
        if PINECONE_AVAILABLE and pinecone_api_key and pinecone_index:
            try:
                pinecone.init(api_key=pinecone_api_key)
                self.pinecone_index = pinecone.Index(pinecone_index)
                self.use_pinecone = True
                logger.info(f"Initialized Pinecone index: {pinecone_index}")
            except Exception as e:
                logger.error(f"Failed to initialize Pinecone: {e}")
                self.pinecone_index = None

    def _token_counter(self, text: str) -> int:
        """
        Estimate token count for a text string

        This is a simple approximation that works for English text
        """
        return len(text.split())

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embeddings for a text chunk

        Uses local SentenceTransformers if available and configured,
        otherwise uses Ollama or hybrid_llm_client
        """
        if self.use_local_embeddings and self.embedding_model_local:
            # Use SentenceTransformers (synchronous, but fast)
            embedding = self.embedding_model_local.encode(
                text, convert_to_tensor=False
            ).tolist()
            return embedding

        try:
            # Try using Ollama directly for embeddings (much faster than the LLM API)
            import ollama

            response = await asyncio.to_thread(
                ollama.embeddings, model=self.embedding_model, prompt=text
            )
            return response["embedding"]
        except Exception as e:
            logger.warning(
                f"Failed to use Ollama for embeddings: {e}, falling back to hybrid_llm_client"
            )
            # Fall back to hybrid_llm_client
            embedding = await hybrid_llm_client.embed(text=text, model="gemma3:12b")
            return embedding

    async def normalize_embedding(self, embedding: List[float]) -> np.ndarray:
        """Normalize embedding with L2 normalization"""
        if not embedding:
            return np.array([], dtype=np.float32)

        emb_array = np.array([embedding], dtype=np.float32)
        if FAISS_AVAILABLE:
            faiss.normalize_L2(emb_array)
        else:
            # Manual L2 normalization
            norm = np.linalg.norm(emb_array)
            if norm > 0:
                emb_array = emb_array / norm

        return emb_array

    def load_document(self, file_path: Union[str, Path]) -> List[str]:
        """
        Load a document from a file path

        Supports various file formats using LangChain document loaders
        """
        if not LANGCHAIN_AVAILABLE:
            # Basic fallback to just read the file as text
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                return [content]
            except Exception as e:
                logger.error(f"Failed to read file {file_path}: {e}")
                return []

        path = Path(file_path) if isinstance(file_path, str) else file_path
        suffix = path.suffix.lower()

        try:
            if suffix == ".pdf":
                loader = PyPDFLoader(str(path))
                documents = loader.load()
                return [
                    {
                        "content": doc.page_content,
                        "metadata": {
                            **doc.metadata,
                            "page": str(
                                doc.metadata.get("page", "0")
                            ),  # Ensure page is string
                        },
                    }
                    for doc in documents
                ]
            elif suffix in [".doc", ".docx"]:
                loader = UnstructuredWordDocumentLoader(str(path))
            elif suffix == ".html":
                # Treating it as a local file, not a URL
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                return [content]
            elif suffix in [".eml", ".msg"]:
                loader = UnstructuredEmailLoader(str(path))
            elif suffix in [".ppt", ".pptx"]:
                loader = UnstructuredPowerPointLoader(str(path))
            elif suffix in [".md", ".markdown"]:
                loader = UnstructuredMarkdownLoader(str(path))
            else:
                # Default case, treat as text file
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                return [content]

            # Load the document
            documents = loader.load()
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                }
                for doc in documents
            ]

        except Exception as e:
            logger.error(f"Failed to load document {path}: {e}")
            return []

    def load_from_url(self, url: str) -> List[str]:
        """Load content from a URL"""
        if not LANGCHAIN_AVAILABLE:
            logger.error("LangChain not available, cannot load from URL")
            return []

        try:
            loader = WebBaseLoader(url)
            documents = loader.load()
            return [doc.page_content for doc in documents]
        except Exception as e:
            logger.error(f"Failed to load from URL {url}: {e}")
            return []

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap

        Uses LangChain text splitter if available, otherwise
        implements a simple chunking strategy
        """
        if not text:
            return []

        if LANGCHAIN_AVAILABLE and self.text_splitter:
            chunks = self.text_splitter.split_text(text)
            return chunks

        # Simple fallback chunking implementation
        tokens = text.split()
        chunks = []

        for i in range(0, len(tokens), self.chunk_size - self.chunk_overlap):
            chunk_tokens = tokens[i : i + self.chunk_size]
            chunks.append(" ".join(chunk_tokens))

        return chunks

    def generate_chunk_id(self, text: str, source: str) -> str:
        """Generate a unique ID for a text chunk"""
        combined = f"{source}::{text[:100]}"
        return hashlib.md5(combined.encode()).hexdigest()

    async def process_document(
        self, content: str, source_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process a document: chunk it, embed the chunks, and store them

        Returns a list of processed chunk information
        """
        # Create base metadata
        base_metadata = {
            "source": source_id,
            "processed_at": datetime.now().isoformat(),
        }

        # Add additional metadata if provided
        if metadata:
            base_metadata.update(metadata)

        # Chunk the document
        chunks = self.chunk_text(content)

        # Process each chunk
        processed_chunks = []

        for i, chunk in enumerate(chunks):
            # Skip empty chunks
            if not chunk or len(chunk.strip()) < 10:
                continue

            # Create chunk metadata
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update(
                {
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                }
            )

            # Generate chunk ID
            chunk_id = self.generate_chunk_id(chunk, source_id)

            # Generate embedding
            embedding = await self.embed_text(chunk)

            # Store in vector database
            if self.use_pinecone:
                # Store in Pinecone
                try:
                    await self.store_in_pinecone(
                        chunk_id, embedding, chunk, chunk_metadata
                    )
                    storage = "pinecone"
                except Exception as e:
                    logger.error(f"Failed to store in Pinecone: {e}")
                    # Fall back to vector store
                    await self.vector_store.add_document(chunk, chunk_metadata)
                    storage = "vector_store"
            else:
                # Store in local vector store
                await self.vector_store.add_document(chunk, chunk_metadata)
                storage = "vector_store"

            # Record processed chunk
            processed_chunks.append(
                {
                    "chunk_id": chunk_id,
                    "chunk_index": i,
                    "text_length": len(chunk),
                    "source": source_id,
                    "storage": storage,
                }
            )

        return processed_chunks

    async def store_in_pinecone(
        self, chunk_id: str, embedding: List[float], text: str, metadata: Dict[str, Any]
    ) -> None:
        """Store a document chunk in Pinecone"""
        if not self.use_pinecone or not self.pinecone_index:
            raise ValueError("Pinecone is not configured")

        # Ensure metadata doesn't contain the text (to avoid duplicating storage)
        metadata_copy = metadata.copy()
        metadata_copy["chunk"] = text

        # Use asyncio to make this non-blocking
        await asyncio.to_thread(
            self.pinecone_index.upsert, vectors=[(chunk_id, embedding, metadata_copy)]
        )

    async def process_file(
        self, file_path: Union[str, Path], metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a file: load it, chunk it, embed the chunks, and store them

        Returns summary information about the processing
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path

        # Create source ID from path
        source_id = str(path)

        # Create base metadata
        base_metadata = {
            "filename": path.name,
            "extension": path.suffix,
            "file_path": str(path),
            "file_size": str(path.stat().st_size),  # Convert to string
            "last_modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        }

        # Add additional metadata if provided
        if metadata:
            base_metadata.update(metadata)

        # Load document
        contents = self.load_document(path)

        if not contents:
            return {
                "source_id": source_id,
                "success": False,
                "error": "Failed to load document or document is empty",
                "chunks_processed": 0,
            }

        # Process each content section
        all_chunks = []

        for i, content in enumerate(contents):
            # Update metadata with section information
            section_metadata = base_metadata.copy()

            # Get content metadata if available (from PDF loader etc)
            content_metadata = {}
            if isinstance(content, dict) and "metadata" in content:
                content_metadata = content["metadata"]
                # Ensure numeric metadata values are strings
                for k, v in content_metadata.items():
                    if isinstance(v, (int, float)):
                        content_metadata[k] = str(v)

            section_metadata.update(
                {
                    "section_index": str(i),  # Convert to string
                    "total_sections": str(len(contents)),  # Convert to string
                    **content_metadata,
                }
            )

            # Process this section
            section_chunks = await self.process_document(
                content, f"{source_id}#section{i}", section_metadata
            )

            all_chunks.extend(section_chunks)

        return {
            "source_id": source_id,
            "success": True,
            "chunks_processed": len(all_chunks),
            "chunks": all_chunks,
        }

    async def process_url(
        self, url: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process content from a URL

        Returns summary information about the processing
        """
        # Create base metadata
        base_metadata = {
            "source_type": "url",
            "url": url,
            "processed_at": datetime.now().isoformat(),
        }

        # Add additional metadata if provided
        if metadata:
            base_metadata.update(metadata)

        # Load content
        contents = self.load_from_url(url)

        if not contents:
            return {
                "source_id": url,
                "success": False,
                "error": "Failed to load content from URL",
                "chunks_processed": 0,
            }

        # Process each content section
        all_chunks = []

        for i, content in enumerate(contents):
            # Update metadata with section information
            section_metadata = base_metadata.copy()
            section_metadata.update(
                {"section_index": i, "total_sections": len(contents)}
            )

            # Process this section
            section_chunks = await self.process_document(
                content, f"{url}#section{i}", section_metadata
            )

            all_chunks.extend(section_chunks)

        return {
            "source_id": url,
            "success": True,
            "chunks_processed": len(all_chunks),
            "chunks": all_chunks,
        }

    async def process_directory(
        self,
        directory: Union[str, Path],
        file_extensions: List[str] = None,
        recursive: bool = True,
        metadata_fn: Optional[Callable[[Path], Dict[str, Any]]] = None,
        batch_size: int = 5,
    ) -> Dict[str, Any]:
        """
        Process all files in a directory

        Args:
            directory: Path to directory
            file_extensions: List of file extensions to process (e.g., ['.pdf', '.docx'])
            recursive: Whether to process subdirectories
            metadata_fn: Function to generate metadata from file path
            batch_size: Number of files to process concurrently

        Returns:
            Summary of processing results
        """
        path = Path(directory) if isinstance(directory, str) else directory

        if not path.is_dir():
            return {
                "success": False,
                "error": f"Not a directory: {path}",
                "files_processed": 0,
            }

        # Get all files
        if recursive:
            files = list(path.glob("**/*"))
        else:
            files = list(path.glob("*"))

        # Filter for files and extensions
        files = [f for f in files if f.is_file()]

        if file_extensions:
            files = [f for f in files if f.suffix.lower() in file_extensions]

        if not files:
            return {
                "success": True,
                "message": "No matching files found",
                "files_processed": 0,
            }

        # Process files in batches
        results = []

        for i in range(0, len(files), batch_size):
            batch_files = files[i : i + batch_size]
            tasks = []

            for file_path in batch_files:
                # Generate metadata if function provided
                metadata = metadata_fn(file_path) if metadata_fn else None
                tasks.append(self.process_file(file_path, metadata))

            # Process batch concurrently
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

            # Log progress
            logger.info(f"Processed {i + len(batch_files)}/{len(files)} files")

        # Calculate summary
        successful = [r for r in results if r.get("success", False)]
        failed = [r for r in results if not r.get("success", False)]
        total_chunks = sum(r.get("chunks_processed", 0) for r in results)

        return {
            "success": True,
            "files_processed": len(results),
            "successful_files": len(successful),
            "failed_files": len(failed),
            "total_chunks_processed": total_chunks,
            "results": results,
        }

    async def process_batch(
        self, batch: List[Tuple[str, Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Process a batch of documents (text + metadata)

        Args:
            batch: List of (text, metadata) tuples

        Returns:
            List of processing results
        """
        tasks = []

        for i, (text, metadata) in enumerate(batch):
            # Generate a source ID if not in metadata
            source_id = metadata.get("source", f"batch_doc_{i}")

            # Process document
            tasks.append(self.process_document(text, source_id, metadata))

        # Process concurrently
        return await asyncio.gather(*tasks)


# Create default instance
rag_document_processor = RAGDocumentProcessor()
