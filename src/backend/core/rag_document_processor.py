"""
RAG Document Processor with Memory Management
Zgodnie z regułami MDC dla zarządzania pamięcią i optymalizacji
"""

import asyncio
import hashlib
import logging
import weakref
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import (Any, AsyncGenerator, Callable, Dict, List, Optional, Tuple,
                    Union)

import numpy as np

# Import MMLW client
try:
    from backend.core.mmlw_embedding_client import mmlw_client

    MMLW_AVAILABLE = True
except ImportError:
    MMLW_AVAILABLE = False

# Import existing clients
from backend.core.hybrid_llm_client import hybrid_llm_client
from backend.core.interfaces import VectorStore
from backend.infrastructure.vector_store.vector_store_impl import \
    EnhancedVectorStoreImpl

# LangChain imports (optional)
try:
    from langchain.document_loaders.base import BaseLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
    from langchain_community.document_loaders.email import \
        UnstructuredEmailLoader
    from langchain_community.document_loaders.markdown import \
        UnstructuredMarkdownLoader
    from langchain_community.document_loaders.powerpoint import \
        UnstructuredPowerPointLoader
    from langchain_community.document_loaders.word_document import \
        UnstructuredWordDocumentLoader

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain not available, falling back to basic document loading")

# SentenceTransformers imports (optional)
try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning(
        "SentenceTransformers not available, falling back to LLM-based embeddings"
    )

# FAISS imports (optional)
try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS not available, falling back to simple vector store")

# Pinecone imports (optional)
try:
    import pinecone

    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logging.warning("Pinecone not available, falling back to local vector store")

logger = logging.getLogger(__name__)


@dataclass
class Stats:
    total_processed: int = 0
    total_chunks: int = 0
    last_cleanup: float = 0.0
    cleanup_count: int = 0


class RAGDocumentProcessor:
    """RAG Document Processor with proper memory management and cleanup"""

    text_splitter: Optional["RecursiveCharacterTextSplitter"]

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        embedding_model: str = "SpeakLeash/bielik-4.5b-v3.0-instruct: Q8_0",
        use_local_embeddings: bool = False,
        pinecone_api_key: Optional[str] = None,
        pinecone_index: Optional[str] = None,
    ) -> None:
        """
        Initialize the RAG document processor

        Args:
            vector_store: Optional VectorStore to use (uses global instance if None)
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens
            embedding_model: Model to use for embeddings
            use_local_embeddings: Whether to use local SentenceTransformers for embeddings
            pinecone_api_key: API key for Pinecone (if using Pinecone)
            pinecone_index: Index name for Pinecone (if using Pinecone)
        """
        self.vector_store = vector_store or EnhancedVectorStoreImpl(
            llm_client=hybrid_llm_client
        )

        # Memory management
        self._processed_documents: Dict[str, weakref.ref[Dict[str, Any]]] = {}
        self._document_hashes: Dict[str, str] = {}
        self._max_documents = 1000
        self._cleanup_threshold = 800
        self._cleanup_lock = asyncio.Lock()

        # Performance tracking
        self._stats = Stats()

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

        Priority order:
        1. MMLW model (if available and enabled) - najlepszy dla języka polskiego
        2. Local SentenceTransformers (if available and configured)
        3. Ollama embeddings
        4. Hybrid LLM client as fallback
        """
        # Import settings here to avoid circular imports
        from backend.config import settings

        # Try MMLW first (best for Polish language)
        if MMLW_AVAILABLE and settings.USE_MMLW_EMBEDDINGS:
            try:
                if not mmlw_client.is_available():
                    await mmlw_client.initialize()

                if mmlw_client.is_available():
                    embedding = await mmlw_client.embed_text(text)
                    if embedding:
                        logger.debug("Using MMLW embeddings")
                        return embedding
            except Exception as e:
                logger.warning(f"Failed to use MMLW embeddings: {e}")

        # Try local SentenceTransformers
        if self.use_local_embeddings and self.embedding_model_local:
            try:
                embedding = self.embedding_model_local.encode(
                    text, convert_to_tensor=False
                ).tolist()
                logger.debug("Using local SentenceTransformers embeddings")
                return embedding
            except Exception as e:
                logger.warning(f"Failed to use local embeddings: {e}")

        # Try Ollama embeddings
        try:
            import ollama

            response = await asyncio.to_thread(
                ollama.embeddings, model=self.embedding_model, prompt=text
            )
            logger.debug("Using Ollama embeddings")
            return response["embedding"]
        except Exception as e:
            logger.warning(f"Failed to use Ollama embeddings: {e}")

        # Fall back to hybrid_llm_client
        try:
            embedding = await hybrid_llm_client.embed(
                text=text, model=settings.DEFAULT_EMBEDDING_MODEL
            )
            logger.debug("Using hybrid LLM client embeddings")
            return embedding
        except Exception as e:
            logger.error(f"All embedding methods failed: {e}")
            return []

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

    def _get_loader_for_file(self, file_path: str) -> Optional[BaseLoader]:
        """Returns the appropriate loader based on the file extension."""
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".pdf":
            return PyPDFLoader(str(path))
        elif suffix in [".doc", ".docx"]:
            return UnstructuredWordDocumentLoader(str(path))
        elif suffix in [".eml", ".msg"]:
            return UnstructuredEmailLoader(str(path))
        elif suffix in [".ppt", ".pptx"]:
            return UnstructuredPowerPointLoader(str(path))
        elif suffix in [".md", ".markdown"]:
            return UnstructuredMarkdownLoader(str(path))
        else:
            return None

    def load_document(
        self, file_path: Union[str, Path]
    ) -> List[Union[str, Dict[str, Any]]]:
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

        try:
            loader = self._get_loader_for_file(str(path))

            if isinstance(loader, PyPDFLoader):
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

            if loader:
                documents = loader.load()
                return [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                    }
                    for doc in documents
                ]

            # Fallback for unhandled types, including .html
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return [content]

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

        # Normalize directory path in metadata
        if "directory_path" in base_metadata:
            base_metadata["directory_path"] = self._normalize_path(
                base_metadata["directory_path"]
            )
        else:
            base_metadata["directory_path"] = "default"

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
                    "chunk_index": str(i),  # Convert to string
                    "total_chunks": str(len(chunks)),  # Convert to string
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
        loaded_content = self.load_document(path)

        if not loaded_content:
            raise ValueError(f"Could not load document from {path}")

        # The first part of the loaded content should be the main text
        main_content = loaded_content[0]
        if isinstance(main_content, dict):
            # If it's a dictionary, extract the content
            main_content = main_content.get("content", "")
        elif not isinstance(main_content, str):
            raise TypeError(f"Expected string content, but got {type(main_content)}")

        # Process document
        processing_result = await self.process_document(
            str(main_content), source_id, base_metadata
        )

        return {
            "source_id": source_id,
            "success": True,
            "chunks_processed": len(processing_result),
            "chunks": processing_result,
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
                {"section_index": str(i), "total_sections": str(len(contents))}
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
        file_extensions: Optional[List[str]] = None,
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
        results = await asyncio.gather(*tasks)
        # Flatten the results since each task returns a list
        flattened_results = []
        for result_list in results:
            flattened_results.extend(result_list)
        return flattened_results

    def _cleanup_callback(self, weak_ref) -> None:
        """Callback when document is garbage collected"""
        for doc_id, ref in list(self._processed_documents.items()):
            if ref is weak_ref:
                del self._processed_documents[doc_id]
                if doc_id in self._document_hashes:
                    del self._document_hashes[doc_id]
                logger.debug(f"Cleaned up garbage collected document: {doc_id}")
                break

    def _calculate_document_hash(self, content: str) -> str:
        """Calculate hash for document content"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _normalize_path(self, path: str) -> str:
        """
        Normalize directory path for consistent storage

        Args:
            path: Directory path to normalize

        Returns:
            Normalized path string
        """
        if not path or path.strip() == "":
            return "default"

        # Remove leading/trailing slashes and normalize
        normalized = path.strip().strip("/").strip("\\")

        # Replace backslashes with forward slashes
        normalized = normalized.replace("\\", "/")

        # Remove any double slashes
        while "//" in normalized:
            normalized = normalized.replace("//", "/")

        # Handle special characters and ensure valid path
        import re

        # Allow alphanumeric, hyphens, underscores, dots, and forward slashes
        normalized = re.sub(r"[^a-zA-Z0-9_/\-\.]", "_", normalized)

        # Ensure it's not empty after normalization
        if not normalized:
            return "default"

        return normalized

    async def get_document_info(self, doc_hash: str) -> Optional[Dict[str, Any]]:
        """Get document info by hash with cleanup"""
        weak_ref = self._processed_documents.get(doc_hash)
        if weak_ref:
            doc_info = weak_ref()
            if doc_info:  # Check if weak reference is still valid
                return doc_info
            else:
                # Clean up invalid reference
                del self._processed_documents[doc_hash]
                if doc_hash in self._document_hashes:
                    del self._document_hashes[doc_hash]
                logger.debug(
                    f"Cleaned up invalid weak reference for document: {doc_hash}"
                )
        return None

    async def remove_document(self, doc_hash: str) -> bool:
        """Remove document from processor"""
        if doc_hash in self._processed_documents:
            del self._processed_documents[doc_hash]
            if doc_hash in self._document_hashes:
                del self._document_hashes[doc_hash]
            self._stats.total_processed = len(self._processed_documents)
            logger.debug(f"Removed document: {doc_hash}")
            return True
        return False

    async def _cleanup_old_documents(self) -> None:
        """Remove old documents when limit is reached with proper locking"""
        async with self._cleanup_lock:
            if len(self._processed_documents) <= self._cleanup_threshold:
                return

            # Get valid documents and their timestamps
            valid_documents = []
            for doc_hash, weak_ref in self._processed_documents.items():
                doc_info = weak_ref()
                if doc_info:
                    valid_documents.append(
                        (doc_hash, doc_info, doc_info["processed_at"])
                    )
                else:
                    # Clean up invalid references
                    del self._processed_documents[doc_hash]
                    if doc_hash in self._document_hashes:
                        del self._document_hashes[doc_hash]

            # Sort by processed_at and remove oldest
            valid_documents.sort(key=lambda x: x[2], reverse=True)

            # Keep only the newest documents
            docs_to_keep = valid_documents[: self._cleanup_threshold]

            # Rebuild documents dict with weak references
            new_documents = {}
            new_hashes = {}
            for doc_hash, doc_info, _ in docs_to_keep:
                new_documents[doc_hash] = weakref.ref(doc_info, self._cleanup_callback)
                new_hashes[doc_hash] = doc_hash

            removed_count = len(self._processed_documents) - len(new_documents)
            self._processed_documents = new_documents
            self._document_hashes = new_hashes
            self._stats.total_processed = len(self._processed_documents)
            self._stats.last_cleanup = float(asyncio.get_event_loop().time())
            current_cleanup_count = self._stats.cleanup_count
            self._stats.cleanup_count = current_cleanup_count + 1

            logger.info(
                f"Cleaned up {removed_count} old documents. "
                f"Total documents: {len(self._processed_documents)}"
            )

    async def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics with cleanup"""
        # Clean up invalid references before stats
        await self._cleanup_old_documents()

        valid_documents = []
        for weak_ref in self._processed_documents.values():
            doc_info = weak_ref()
            if doc_info:
                valid_documents.append(doc_info)

        vector_store_stats = await self.vector_store.get_stats()

        return {
            "total_processed": len(valid_documents),
            "total_chunks": self._stats.total_chunks,
            "max_documents": self._max_documents,
            "cleanup_threshold": self._cleanup_threshold,
            "vector_store_stats": vector_store_stats,
            "processor_stats": self._stats,
        }

    async def clear_all(self) -> None:
        """Clear all documents and reset processor"""
        async with self._cleanup_lock:
            self._processed_documents.clear()
            self._document_hashes.clear()
            await self.vector_store.clear_all()
            self._stats.total_processed = 0
            self._stats.total_chunks = 0
            self._stats.last_cleanup = float(asyncio.get_event_loop().time())
            current_cleanup_count = self._stats.cleanup_count
            self._stats.cleanup_count = current_cleanup_count + 1
            logger.info("Cleared all documents from processor")

    @asynccontextmanager
    async def context_manager(self) -> AsyncGenerator["RAGDocumentProcessor", None]:
        """Async context manager for RAGDocumentProcessor lifecycle"""
        try:
            yield self
        finally:
            await self._cleanup_old_documents()
            logger.debug("RAGDocumentProcessor context manager exited")

    async def __aenter__(self) -> "RAGDocumentProcessor":
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit with cleanup"""
        await self.clear_all()


# Create default instance
rag_document_processor = RAGDocumentProcessor()
