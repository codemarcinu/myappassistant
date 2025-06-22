"""
Vector Store Implementation with FAISS
Zgodnie z regułami MDC dla zarządzania pamięcią i optymalizacji
"""

import asyncio
import logging
import os
import weakref
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS not available, falling back to simple vector store")

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Document chunk with metadata and embedding support"""

    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class SmartChunker:
    """Intelligent document chunking with semantic boundaries"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [
            "\n\n",
            "\n",
            ". ",
            "! ",
            "? ",
            "; ",
            ":",
            " - ",
            "\t",
            "  ",
        ]

    def chunk_document(
        self, text: str, metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """Split document into semantically meaningful chunks"""
        chunks: List[DocumentChunk] = []

        # Handle empty or very short documents
        if not text or len(text) < self.chunk_size / 2:
            if isinstance(metadata, dict):
                metadata_copy = metadata.copy()
            else:
                metadata_copy = {"content": str(metadata)}
            return [DocumentChunk(id="", content=text, metadata=metadata_copy)]

        current_pos = 0
        while current_pos < len(text):
            end_pos = min(current_pos + self.chunk_size, len(text))
            if end_pos < len(text):
                for separator in self.separators:
                    boundary = text.rfind(separator, current_pos, end_pos)
                    if boundary != -1:
                        end_pos = boundary + len(separator)
                        break
            chunk_text = text[current_pos:end_pos].strip()
            if chunk_text:
                if isinstance(metadata, dict):
                    chunk_metadata = metadata.copy()
                else:
                    chunk_metadata = {"content": str(metadata)}
                chunk_metadata.update(
                    {
                        "start_pos": current_pos,
                        "end_pos": end_pos,
                        "chunk_index": len(chunks),
                    }
                )
                chunks.append(
                    DocumentChunk(id="", content=chunk_text, metadata=chunk_metadata)
                )
            next_pos = end_pos - self.chunk_overlap
            current_pos = max(current_pos + 1, next_pos)
        return chunks


class VectorStore:
    """FAISS-based vector store with proper memory management and optimizations"""

    def __init__(self, dimension: int = 768, index_type: str = "IndexIVFFlat"):
        self.dimension = dimension
        self.index_type = index_type

        # Initialize optimized FAISS index
        if index_type == "IndexFlatL2":
            self.index = faiss.IndexFlatL2(dimension)
        elif index_type == "IndexIVFFlat":
            # Use IVF for better memory efficiency and speed
            quantizer = faiss.IndexFlatL2(dimension)
            self.index = faiss.IndexIVFFlat(quantizer, dimension, 100)
            # Train the index (will be done when vectors are added)
            self._is_trained = False
        elif index_type == "IndexIVFPQ":
            # Use Product Quantization for memory efficiency
            quantizer = faiss.IndexFlatL2(dimension)
            # 8 bits per sub-vector, 8 sub-vectors
            self.index = faiss.IndexIVFPQ(quantizer, dimension, 100, 8, 8)
            self._is_trained = False
        else:
            raise ValueError(f"Unsupported index type: {index_type}")

        # Use weak references to avoid memory leaks
        self._documents: Dict[str, weakref.ref[DocumentChunk]] = {}
        self._document_ids: List[str] = []

        # Memory management
        self._max_documents = 10000
        self._cleanup_threshold = 8000
        self._cleanup_lock = asyncio.Lock()

        # Cache for frequently accessed vectors
        self._vector_cache: Dict[str, np.ndarray] = {}
        self._cache_max_size = 1000
        self._cache_hits = 0
        self._cache_misses = 0

        # Memory mapping for large indices
        self._use_memory_mapping = False
        self._index_file_path: Optional[str] = None

        # Performance tracking
        self._stats = {
            "total_documents": 0,
            "total_vectors": 0,
            "last_cleanup": 0.0,
            "cleanup_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # Track chunks since last save
        self.chunks_since_save = 0

    def _cleanup_callback(self, weak_ref):
        """Callback when document is garbage collected"""
        for doc_id, ref in list(self._documents.items()):
            if ref is weak_ref:
                del self._documents[doc_id]
                if doc_id in self._document_ids:
                    self._document_ids.remove(doc_id)
                # Remove from cache if present
                if doc_id in self._vector_cache:
                    del self._vector_cache[doc_id]
                logger.debug(f"Cleaned up garbage collected document: {doc_id}")
                break

    def _get_cached_embedding(self, doc_id: str) -> Optional[np.ndarray]:
        """Get embedding from cache"""
        if doc_id in self._vector_cache:
            self._stats["cache_hits"] = int(self._stats.get("cache_hits", 0)) + 1
            return self._vector_cache[doc_id]
        self._stats["cache_misses"] = int(self._stats.get("cache_misses", 0)) + 1
        return None

    def _cache_embedding(self, doc_id: str, embedding: np.ndarray):
        """Cache embedding with LRU eviction"""
        if len(self._vector_cache) >= self._cache_max_size:
            # Remove oldest entry (simple LRU)
            oldest_key = next(iter(self._vector_cache))
            del self._vector_cache[oldest_key]
        self._vector_cache[doc_id] = embedding

    async def add_document(self, text: str, metadata: Dict[str, Any]) -> None:
        """Add a single document to the vector store"""
        # Create a simple document chunk
        doc = DocumentChunk(
            id=f"doc_{len(self._documents)}", content=text, metadata=metadata
        )
        await self.add_documents([doc])

    async def add_documents(self, documents: List[DocumentChunk]) -> None:
        """Add documents to vector store with memory management and caching"""
        if len(self._documents) + len(documents) >= self._max_documents:
            await self._cleanup_old_documents()
        embeddings = []
        for doc in documents:
            if doc.embedding is not None:
                embeddings.append(doc.embedding)
                self._cache_embedding(doc.id, doc.embedding)
                self._documents[doc.id] = weakref.ref(doc, self._cleanup_callback)
                self._document_ids.append(doc.id)
                self._stats["total_documents"] = (
                    int(self._stats.get("total_documents", 0)) + 1
                )
                self.chunks_since_save += 1
        if embeddings:
            embeddings_array = np.array(embeddings, dtype=np.float32)
            if hasattr(self, "_is_trained") and not self._is_trained:
                if len(embeddings_array) >= 100:
                    self.index.train(embeddings_array)
                    self._is_trained = True
                    logger.info("Trained FAISS index")
                else:
                    self.index = faiss.IndexFlatL2(self.dimension)
                    logger.info("Using FlatL2 index for small dataset")
            self.index.add(embeddings_array)
            self._stats["total_vectors"] = int(self.index.ntotal)
            logger.debug(f"Added {len(documents)} documents to vector store")

    async def search(
        self, query_embedding: np.ndarray, k: int = 5
    ) -> List[Tuple[DocumentChunk, float]]:
        """Search for similar documents with caching and proper error handling"""
        try:
            # Ensure query embedding is 2D
            if query_embedding.ndim == 1:
                query_embedding = query_embedding.reshape(1, -1)

            # Search in FAISS index
            distances, indices = self.index.search(query_embedding, k)

            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self._document_ids):
                    doc_id = self._document_ids[idx]

                    # Try cache first
                    cached_embedding = self._get_cached_embedding(doc_id)
                    if cached_embedding is not None:
                        # Create minimal document chunk with cached data
                        doc = DocumentChunk(
                            id=doc_id,
                            content="",  # Content not cached for memory efficiency
                            metadata={"cached": True},
                            embedding=cached_embedding,
                        )
                        results.append((doc, float(distance)))
                        continue

                    weak_ref = self._documents.get(doc_id)

                    doc_chunk: Optional[DocumentChunk] = (
                        weak_ref() if weak_ref else None
                    )
                    if doc_chunk is not None:
                        results.append((doc_chunk, float(distance)))
                    else:
                        # Clean up invalid reference
                        if doc_id in self._documents:
                            del self._documents[doc_id]
                        if doc_id in self._document_ids:
                            self._document_ids.remove(doc_id)
            return results
        except Exception as e:
            logger.error(f"Error during vector search: {e}")
            return []

    async def get_document(self, doc_id: str) -> Optional[DocumentChunk]:
        """Get document by ID with cleanup and caching"""
        cached_embedding = self._get_cached_embedding(doc_id)
        if cached_embedding is not None:
            return DocumentChunk(
                id=doc_id,
                content="",  # Content not cached
                metadata={"cached": True},
                embedding=cached_embedding,
            )
        weak_ref = self._documents.get(doc_id)
        doc: Optional[DocumentChunk] = weak_ref() if weak_ref else None
        if doc is not None:
            return doc
        else:
            if doc_id in self._documents:
                del self._documents[doc_id]
            if doc_id in self._document_ids:
                self._document_ids.remove(doc_id)
            logger.debug(f"Cleaned up invalid weak reference for document: {doc_id}")
        return None

    async def remove_document(self, doc_id: str) -> bool:
        """Remove document from vector store and cache"""
        if doc_id in self._documents:
            del self._documents[doc_id]
            if doc_id in self._document_ids:
                self._document_ids.remove(doc_id)
            # Remove from cache
            if doc_id in self._vector_cache:
                del self._vector_cache[doc_id]
            self._stats["total_documents"] = len(self._documents)
            logger.debug(f"Removed document: {doc_id}")
            return True
        return False

    async def _cleanup_old_documents(self) -> None:
        """Remove old documents when limit is reached with proper locking"""
        async with self._cleanup_lock:
            if len(self._documents) <= self._cleanup_threshold:
                return
            valid_documents = []
            for doc_id, weak_ref in self._documents.items():
                doc = weak_ref()
                if doc:
                    created_at = doc.created_at or ""
                    valid_documents.append((doc_id, doc, created_at))
                else:
                    del self._documents[doc_id]
                    if doc_id in self._document_ids:
                        self._document_ids.remove(doc_id)
                    if doc_id in self._vector_cache:
                        del self._vector_cache[doc_id]
            valid_documents.sort(key=lambda x: str(x[2]), reverse=True)
            docs_to_keep = valid_documents[: self._cleanup_threshold]
            new_documents = {}
            new_document_ids = []
            for doc_id, doc, _ in docs_to_keep:
                new_documents[doc_id] = weakref.ref(doc, self._cleanup_callback)
                new_document_ids.append(doc_id)
            removed_count = len(self._documents) - len(new_documents)
            self._documents = new_documents
            self._document_ids = new_document_ids
            self._stats["total_documents"] = len(self._documents)
            self._stats["last_cleanup"] = float(asyncio.get_event_loop().time())
            self._stats["cleanup_count"] = int(self._stats.get("cleanup_count", 0)) + 1
            logger.info(
                f"Cleaned up {removed_count} old documents. "
                f"Total documents: {len(self._documents)}"
            )

    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics with cleanup and cache info"""
        await self._cleanup_old_documents()

        valid_documents = []
        for weak_ref in self._documents.values():
            doc = weak_ref()
            if doc:
                valid_documents.append(doc)

        cache_hits = int(self._stats.get("cache_hits", 0))
        cache_misses = int(self._stats.get("cache_misses", 0))
        total_cache_attempts = cache_hits + cache_misses

        return {
            "total_documents": len(valid_documents),
            "total_vectors": int(self.index.ntotal),
            "max_documents": self._max_documents,
            "cleanup_threshold": self._cleanup_threshold,
            "index_type": self.index_type,
            "dimension": self.dimension,
            "cache_size": len(self._vector_cache),
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "cache_hit_rate": cache_hits / max(1, total_cache_attempts),
            "stats": self._stats,
        }

    async def clear_all(self) -> None:
        """Clear all documents and reset vector store"""
        async with self._cleanup_lock:
            self._documents.clear()
            self._document_ids.clear()
            self._vector_cache.clear()
            self.index.reset()
            self._stats["total_documents"] = 0
            self._stats["total_vectors"] = 0
            self._stats["cache_hits"] = 0
            self._stats["cache_misses"] = 0
            self._stats["last_cleanup"] = float(asyncio.get_event_loop().time())
            self._stats["cleanup_count"] = int(self._stats.get("cleanup_count", 0)) + 1
            self.chunks_since_save = 0
            logger.info("Cleared all documents from vector store")

    async def save_index_async(self) -> None:
        """Save index asynchronously"""
        if self._index_file_path:
            self.save_index(self._index_file_path)
            self.chunks_since_save = 0

    @asynccontextmanager
    async def context_manager(self):
        """Async context manager for vector store lifecycle"""
        try:
            yield self
        finally:
            # Optional cleanup on exit
            await self._cleanup_old_documents()
            logger.debug("Vector store context manager exited")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup"""
        await self.clear_all()

    def save_index(self, filepath: str) -> None:
        """Save FAISS index to file with memory mapping support"""
        try:
            faiss.write_index(self.index, filepath)
            self._index_file_path = filepath
            logger.info(f"Saved FAISS index to: {filepath}")
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")
            raise

    def load_index(self, filepath: str, use_memory_mapping: bool = False) -> None:
        """Load FAISS index from file with optional memory mapping"""
        try:
            if use_memory_mapping and os.path.exists(filepath):
                # Use memory mapping for large indices
                self.index = faiss.read_index(filepath, faiss.IO_FLAG_MMAP)
                self._use_memory_mapping = True
                self._index_file_path = filepath
                logger.info(f"Loaded FAISS index with memory mapping from: {filepath}")
            else:
                self.index = faiss.read_index(filepath)
                self._use_memory_mapping = False
                logger.info(f"Loaded FAISS index from: {filepath}")

            self._stats["total_vectors"] = self.index.ntotal
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")
            raise

    async def list_directories(self) -> list[dict]:
        """Zwraca listę katalogów z liczbą dokumentów"""
        directories = {}
        for doc_id, ref in self._documents.items():
            doc = ref()
            if doc and hasattr(doc, "metadata"):
                dir_path = doc.metadata.get("directory_path", "default")
                if dir_path not in directories:
                    directories[dir_path] = 0
                directories[dir_path] += 1
        return [
            {"path": path, "document_count": count}
            for path, count in directories.items()
        ]


class AsyncDocumentLoader:
    """Asynchronous document loader with incremental indexing"""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.loading_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self.last_modified_times: Dict[str, float] = {}

    async def load_directory(
        self,
        directory: str,
        glob_pattern: str = "**/*.*",
        metadata_fn: Optional[Callable] = None,
    ) -> None:
        """Load all documents from a directory with pattern matching"""
        # Collect all matching files
        path = Path(directory)
        files = list(path.glob(glob_pattern))

        loaded_count = 0
        for file_path in files:
            if self._stop_event.is_set():
                logger.info("Loading interrupted")
                break

            try:
                # Skip non-text files
                if file_path.suffix.lower() not in [
                    ".txt",
                    ".md",
                    ".csv",
                    ".json",
                    ".html",
                    ".xml",
                    ".py",
                    ".js",
                ]:
                    continue

                # Read file content
                text = file_path.read_text(errors="replace")

                # Generate metadata
                if metadata_fn:
                    metadata = metadata_fn(file_path)
                else:
                    metadata = {
                        "source": str(file_path),
                        "filename": file_path.name,
                        "extension": file_path.suffix,
                        "last_modified": datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat(),
                    }

                # Add to vector store
                await self.vector_store.add_document(text, metadata)
                loaded_count += 1

                # Periodically log progress
                if loaded_count % 10 == 0:
                    logger.info(f"Loaded {loaded_count}/{len(files)} documents")

            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")

        # Save index after loading all documents
        await self.vector_store.save_index_async()
        logger.info(f"Completed loading {loaded_count} documents")

    async def start_incremental_indexing(
        self,
        directory: str,
        glob_pattern: str = "**/*.*",
        check_interval: int = 300,  # seconds
        metadata_fn: Optional[Callable] = None,
    ) -> None:
        """Start background task for incremental indexing of new/modified files"""
        self._stop_event.clear()

        # Track last modified times
        self.last_modified_times.clear()

        async def _indexing_task():
            while not self._stop_event.is_set():
                try:
                    # Collect all matching files
                    path = Path(directory)
                    files = list(path.glob(glob_pattern))

                    for file_path in files:
                        # Skip non-text files
                        if file_path.suffix.lower() not in [
                            ".txt",
                            ".md",
                            ".csv",
                            ".json",
                            ".html",
                            ".xml",
                            ".py",
                            ".js",
                        ]:
                            continue

                        file_str = str(file_path)
                        mtime = file_path.stat().st_mtime

                        # Check if file is new or modified
                        if (
                            file_str not in self.last_modified_times
                            or self.last_modified_times[file_str] < mtime
                        ):
                            try:
                                # Read file content
                                text = file_path.read_text(errors="replace")

                                # Generate metadata
                                if metadata_fn:
                                    metadata = metadata_fn(file_path)
                                else:
                                    metadata = {
                                        "source": file_str,
                                        "filename": file_path.name,
                                        "extension": file_path.suffix,
                                        "last_modified": datetime.fromtimestamp(
                                            mtime
                                        ).isoformat(),
                                    }

                                # Add to vector store
                                await self.vector_store.add_document(text, metadata)
                                self.last_modified_times[file_str] = mtime
                                logger.info(f"Indexed new/modified file: {file_path}")

                            except Exception as e:
                                logger.error(f"Error indexing {file_path}: {e}")

                    # Check for any deleted files and remove from tracking
                    current_files = set(str(f) for f in files)
                    tracked_files = set(self.last_modified_times.keys())
                    for deleted_file in tracked_files - current_files:
                        del self.last_modified_times[deleted_file]

                    # Save index periodically
                    if self.vector_store.chunks_since_save > 0:
                        await self.vector_store.save_index_async()

                    # Wait for next check interval
                    try:
                        await asyncio.wait_for(
                            self._stop_event.wait(), timeout=check_interval
                        )
                    except asyncio.TimeoutError:
                        pass  # This is expected when timeout occurs

                except Exception as e:
                    logger.error(f"Error in incremental indexing: {e}")
                    # Wait before retrying
                    await asyncio.sleep(60)

        # Start the indexing task
        self.loading_task = asyncio.create_task(_indexing_task())


# Global instance with optimized index
vector_store = VectorStore(index_type="IndexIVFFlat")
