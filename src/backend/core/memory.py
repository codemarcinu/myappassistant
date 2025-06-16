import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS not available, falling back to simple vector store")

from ..core.llm_client import llm_client
from ..models.conversation import Conversation, Message

logger = logging.getLogger(__name__)


class MemoryEntry:
    """Represents a single memory entry with metadata for importance and recency"""

    def __init__(
        self,
        text: str,
        embedding: List[float],
        importance: float = 1.0,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.text = text
        self.embedding = embedding
        self.importance = importance  # 0-10 scale, higher = more important
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
        self.access_count = 0
        self.last_access = self.timestamp

    def access(self) -> None:
        """Record that this memory was accessed"""
        self.access_count += 1
        self.last_access = datetime.now()

    def get_decay_factor(self, half_life_days: int = 30) -> float:
        """Calculate decay factor based on recency and importance"""
        days_old = (datetime.now() - self.timestamp).days
        # Memories decay slower if they're important or frequently accessed
        adjusted_half_life = half_life_days * (
            1 + 0.1 * self.importance + 0.05 * self.access_count
        )
        decay = 2 ** (-days_old / adjusted_half_life)
        return decay

    def get_weighted_score(self) -> float:
        """Calculate weighted importance score for ranking"""
        decay = self.get_decay_factor()
        recency_bonus = 0.2 * (datetime.now() - self.last_access).days < 2
        return self.importance * decay * (1 + recency_bonus)


class LongTermMemory:
    """Vector-based long-term memory system with importance weighting and decay"""

    def __init__(self, embedding_dim: int = 384, max_memories: int = 10000):
        self.entries: List[MemoryEntry] = []
        self.embedding_dim = embedding_dim
        self.max_memories = max_memories

        # Initialize FAISS index if available
        if FAISS_AVAILABLE:
            self.index = faiss.IndexFlatL2(embedding_dim)
            self.use_faiss = True
        else:
            self.use_faiss = False

        self.last_cleanup = datetime.now()

    async def add_memory(
        self,
        text: str,
        importance: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
    ) -> None:
        """Add a new memory to the long-term store"""
        if len(self.entries) >= self.max_memories:
            self._prune_memories()

        # Get embedding if not provided
        if embedding is None:
            embedding = await llm_client.embed(model="gemma3:12b", text=text)

        # Auto-calculate importance if not provided
        if importance is None:
            importance = await self._calculate_importance(text)

        # Create memory entry
        entry = MemoryEntry(
            text=text, embedding=embedding, importance=importance, metadata=metadata
        )

        # Add to FAISS index if available
        if self.use_faiss:
            faiss.normalize_L2(np.array([embedding], dtype=np.float32))
            self.index.add(np.array([embedding], dtype=np.float32))

        self.entries.append(entry)

    async def retrieve_relevant(
        self, query: str, k: int = 5, min_similarity: float = 0.7
    ) -> List[Tuple[str, float]]:
        """Retrieve relevant memories based on query"""
        # Get query embedding
        query_embedding = await llm_client.embed(model="gemma3:12b", text=query)

        if self.use_faiss and len(self.entries) > 0:
            # Use FAISS for fast retrieval
            query_vector = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_vector)
            D, I = self.index.search(query_vector, min(k * 2, len(self.entries)))

            # Get candidates and filter by similarity
            candidates = [
                (self.entries[idx], float(score)) for score, idx in zip(D[0], I[0])
            ]
            candidates = [
                (entry, score) for entry, score in candidates if score >= min_similarity
            ]

            # Re-rank by weighted importance
            candidates.sort(
                key=lambda x: x[0].get_weighted_score() * (1 - x[1] / 10), reverse=True
            )
            results = [(entry.text, score) for entry, score in candidates[:k]]

            # Update access stats
            for entry, _ in candidates[:k]:
                entry.access()

            return results
        else:
            # Fallback to manual search
            results = []
            for entry in self.entries:
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, entry.embedding)
                if similarity >= min_similarity:
                    results.append((entry, similarity))

            # Sort by weighted score and similarity
            results.sort(key=lambda x: x[0].get_weighted_score() * x[1], reverse=True)

            # Update access stats for retrieved memories
            for entry, _ in results[:k]:
                entry.access()

            return [(entry.text, score) for entry, score in results[:k]]

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity between vectors"""
        dot_product = sum(x * y for x, y in zip(v1, v2))
        norm1 = sum(x * x for x in v1) ** 0.5
        norm2 = sum(x * x for x in v2) ** 0.5
        return dot_product / (norm1 * norm2) if norm1 * norm2 > 0 else 0

    async def _calculate_importance(self, text: str) -> float:
        """Use LLM to estimate memory importance (0-10 scale)"""
        prompt = (
            f"Evaluate the importance of this information for a personal assistant to remember (0-10 scale):\n\n"
            f'"{text}"\n\n'
            f"Rate factual information, user preferences, and scheduled events higher. "
            f"Return only a number from 0-10, with 10 being extremely important."
        )

        try:
            response = await llm_client.chat(
                model="gemma3:12b",
                messages=[
                    {
                        "role": "system",
                        "content": "You evaluate the importance of information.",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )

            if response and "message" in response:
                content = response["message"]["content"].strip()
                # Extract number from response
                import re

                match = re.search(r"(\d+(\.\d+)?)", content)
                if match:
                    importance = float(match.group(1))
                    return min(max(importance, 0), 10)  # Clamp to 0-10

            # Default importance if extraction fails
            return 5.0
        except Exception as e:
            logger.error(f"Error calculating memory importance: {e}")
            return 5.0  # Default importance

    def _prune_memories(self) -> None:
        """Remove least important memories when store is full"""
        # Only run cleanup once per hour to avoid overhead
        if (datetime.now() - self.last_cleanup) < timedelta(hours=1) and len(
            self.entries
        ) < self.max_memories:
            return

        logger.info(f"Pruning memories, current count: {len(self.entries)}")

        # Calculate weighted scores for all memories
        scored_entries = [(entry, entry.get_weighted_score()) for entry in self.entries]
        scored_entries.sort(key=lambda x: x[1])

        # Remove lowest-scoring entries to get to 80% capacity
        entries_to_remove = max(
            int(len(self.entries) * 0.2),
            len(self.entries) - int(self.max_memories * 0.8),
        )

        if entries_to_remove > 0:
            # Get indices to remove (lowest scoring first)
            to_remove = [
                self.entries.index(entry)
                for entry, _ in scored_entries[:entries_to_remove]
            ]
            to_remove.sort(reverse=True)  # Remove from end to avoid index shifting

            # Rebuild FAISS index if using it
            if self.use_faiss and to_remove:
                remaining_indices = list(set(range(len(self.entries))) - set(to_remove))
                new_index = faiss.IndexFlatL2(self.embedding_dim)

                if remaining_indices:
                    embeddings = np.array(
                        [self.entries[i].embedding for i in remaining_indices],
                        dtype=np.float32,
                    )
                    faiss.normalize_L2(embeddings)
                    new_index.add(embeddings)

                self.index = new_index

            # Remove entries
            for idx in to_remove:
                del self.entries[idx]

        self.last_cleanup = datetime.now()
        logger.info(f"Memory pruning complete, new count: {len(self.entries)}")


class ConversationMemoryManager:
    """Manages conversation memory with support for short and long-term storage"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.ltm = LongTermMemory()
        self.memory_initialized = False

    async def initialize_from_history(self, conversation: Conversation) -> None:
        """Initialize memory from conversation history"""
        if self.memory_initialized:
            return

        logger.info(f"Initializing memory for session {self.session_id}")

        # Add each message to LTM with appropriate importance
        for message in conversation.messages:
            # Skip system messages
            if message.role == "system":
                continue

            # Calculate basic importance (user messages slightly more important)
            base_importance = 6.0 if message.role == "user" else 5.0

            await self.ltm.add_memory(
                text=message.content,
                importance=base_importance,
                metadata={
                    "role": message.role,
                    "timestamp": (
                        message.created_at.isoformat() if message.created_at else None
                    ),
                },
            )

        self.memory_initialized = True

    async def add_message(
        self, role: str, content: str, importance_override: Optional[float] = None
    ) -> None:
        """Add a new message to memory"""
        # Add to long-term memory if it passes importance threshold
        await self.ltm.add_memory(
            text=content,
            importance=importance_override,
            metadata={"role": role, "timestamp": datetime.now().isoformat()},
        )

    async def retrieve_context(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant context for the current query"""
        # Get relevant memories
        memories = await self.ltm.retrieve_relevant(query, k=k)

        # Format for context inclusion
        context = []
        for memory_text, relevance in memories:
            context.append({"content": memory_text, "relevance": relevance})

        return context
