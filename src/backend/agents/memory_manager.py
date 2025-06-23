"""
Memory Management for Conversation Context
Zgodnie z regułami MDC dla zarządzania pamięcią
"""

import asyncio
import logging
import weakref
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from backend.agents.interfaces import BaseAgent, IMemoryManager

logger = logging.getLogger(__name__)


class MemoryStats(TypedDict):
    total_contexts: int
    last_cleanup: Optional[datetime]
    cleanup_count: int


class MemoryContext:
    """Context for maintaining conversation state and memory with __slots__ optimization"""

    __slots__ = [
        "session_id",
        "history",
        "active_agents",
        "last_response",
        "last_command",
        "request_id",
        "created_at",
        "last_updated",
        "__weakref__",  # Allow weak references
    ]

    def __init__(self, session_id: str, history: Optional[List[Dict]] = None) -> None:
        self.session_id = session_id
        self.history = history if history is not None else []
        self.active_agents: Dict[str, BaseAgent] = {}
        self.last_response: Optional[Any] = None
        self.last_command: Optional[str] = None
        self.request_id: Optional[str] = None
        self.created_at: datetime = datetime.now()
        self.last_updated: datetime = datetime.now()


class MemoryManager(IMemoryManager):
    """Implementation of memory management for conversation context with proper cleanup"""

    def __init__(
        self, max_contexts: int = 1000, cleanup_threshold_ratio: float = 0.8
    ) -> None:
        # Use weak references to avoid memory leaks
        self._contexts: Dict[str, weakref.ReferenceType[MemoryContext]] = {}
        self._max_contexts = max_contexts
        self._cleanup_threshold = int(max_contexts * cleanup_threshold_ratio)
        self._cleanup_lock = asyncio.Lock()
        self._memory_stats: MemoryStats = {
            "total_contexts": 0,
            "last_cleanup": None,  # Timestamp of last cleanup
            "cleanup_count": 0,  # How many times cleanup ran
        }

    async def store_context(self, context: MemoryContext) -> None:
        """Store context for later retrieval with weak reference"""
        if len(self._contexts) >= self._max_contexts:
            await self._cleanup_old_contexts()

        # Use weak reference to avoid memory leaks
        self._contexts[context.session_id] = weakref.ref(
            context, self._cleanup_callback
        )
        context.last_updated = datetime.now()
        self._memory_stats["total_contexts"] = len(self._contexts)
        logger.debug(f"Stored context for session: {context.session_id}")

    def _cleanup_callback(self, weak_ref) -> None:
        """Callback when context is garbage collected"""
        # Remove from tracking when context is GC'd
        for session_id, ref in list(self._contexts.items()):
            if ref is weak_ref:
                del self._contexts[session_id]
                logger.debug(f"Cleaned up garbage collected context: {session_id}")
                break

    async def retrieve_context(self, session_id: str) -> Optional[MemoryContext]:
        """Retrieve context for session if it exists"""
        weak_ref = self._contexts.get(session_id)
        if weak_ref:
            context = weak_ref()
            if context:  # Check if weak reference is still valid
                context.last_updated = datetime.now()
                logger.debug(f"Retrieved context for session: {session_id}")
                return context
            else:
                # Clean up invalid weak reference
                del self._contexts[session_id]
                logger.debug(
                    f"Cleaned up invalid weak reference for session: {session_id}"
                )
        return None

    async def get_context(self, session_id: str) -> MemoryContext:
        """Get or create context for session"""
        context = await self.retrieve_context(session_id)
        if context is None:
            # Create new context if it doesn't exist
            context = MemoryContext(session_id)
            await self.store_context(context)
            logger.debug(f"Created new context for session: {session_id}")
        return context

    async def update_context(
        self, context: MemoryContext, new_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update existing context with new data"""
        if context.session_id in self._contexts:
            # Add new data to context history if provided
            if new_data:
                if not hasattr(context, "history"):
                    context.history = []
                context.history.append(
                    {"timestamp": datetime.now().isoformat(), "data": new_data}
                )

            # Update weak reference
            self._contexts[context.session_id] = weakref.ref(
                context, self._cleanup_callback
            )
            context.last_updated = datetime.now()
            logger.debug(f"Updated context for session: {context.session_id}")

    async def clear_context(self, session_id: str) -> None:
        """Clear context for session"""
        if session_id in self._contexts:
            del self._contexts[session_id]
            self._memory_stats["total_contexts"] = len(self._contexts)
            logger.debug(f"Cleared context for session: {session_id}")

    async def _cleanup_old_contexts(self) -> None:
        """Remove old contexts when limit is reached with proper locking"""
        async with self._cleanup_lock:
            if len(self._contexts) <= self._cleanup_threshold:
                return

            # Get valid contexts and their timestamps
            valid_contexts = []
            for session_id, weak_ref in self._contexts.items():
                context = weak_ref()
                if context:
                    valid_contexts.append((session_id, context, context.last_updated))
                else:
                    # Clean up invalid references
                    del self._contexts[session_id]

            # Sort by last_updated and remove oldest
            valid_contexts.sort(key=lambda x: x[2], reverse=True)

            # Keep only the newest contexts
            contexts_to_keep = valid_contexts[: self._cleanup_threshold]

            # Rebuild contexts dict with weak references
            new_contexts = {}
            for session_id, context, _ in contexts_to_keep:
                new_contexts[session_id] = weakref.ref(context, self._cleanup_callback)

            removed_count = len(self._contexts) - len(new_contexts)
            self._contexts = new_contexts
            self._memory_stats["total_contexts"] = len(self._contexts)
            self._memory_stats["last_cleanup"] = datetime.now()
            self._memory_stats["cleanup_count"] += 1

            logger.info(
                f"Cleaned up {removed_count} old contexts. "
                f"Total contexts: {len(self._contexts)}"
            )

    async def register_agent_state(
        self,
        context: MemoryContext,
        agent_type: str,
        agent: BaseAgent,
        state: Dict[str, Any],
    ) -> None:
        """Register agent state in context"""
        if not hasattr(context, "active_agents"):
            context.active_agents = {}

        context.active_agents[agent_type] = {
            "agent": agent,
            "state": state,
            "timestamp": datetime.now().isoformat(),
        }

    async def get_all_contexts(self) -> Dict[str, MemoryContext]:
        """Get all stored contexts (for debugging/monitoring) with cleanup"""
        # Clean up invalid references first
        valid_contexts = {}
        for session_id, weak_ref in self._contexts.items():
            context = weak_ref()
            if context:
                valid_contexts[session_id] = context
            else:
                del self._contexts[session_id]

        self._memory_stats["total_contexts"] = len(self._contexts)
        return valid_contexts

    async def get_context_stats(self) -> Dict[str, Any]:
        """Get memory manager statistics"""
        # Clean up invalid references before stats
        await self._cleanup_old_contexts()

        valid_contexts = []
        for weak_ref in self._contexts.values():
            context = weak_ref()
            if context:
                valid_contexts.append(context)

        return {
            "total_contexts": len(valid_contexts),
            "max_contexts": self._max_contexts,
            "cleanup_threshold": self._cleanup_threshold,
            "oldest_context": min(
                (ctx.last_updated for ctx in valid_contexts), default=None
            ),
            "newest_context": max(
                (ctx.last_updated for ctx in valid_contexts), default=None
            ),
            "memory_stats": self._memory_stats,
        }

    async def cleanup_all(self) -> None:
        """Cleanup all contexts and reset memory manager"""
        async with self._cleanup_lock:
            self._contexts.clear()
            self._memory_stats["total_contexts"] = 0
            self._memory_stats["last_cleanup"] = datetime.now()
            self._memory_stats["cleanup_count"] += 1
            logger.info("Cleaned up all contexts")

    @asynccontextmanager
    async def context_manager(self, session_id: str) -> None:
        """Async context manager for memory context lifecycle"""
        context = await self.get_context(session_id)
        try:
            yield context
        finally:
            # Update context timestamp on exit
            context.last_updated = datetime.now()
            await self.update_context(context, None)
            logger.debug(f"Context manager exited for session: {session_id}")

    async def __aenter__(self) -> MemoryContext:
        """Enter async context"""
        return self.context

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context with cleanup"""
        if exc_type is not None:
            logger.error(f"Error in memory context: {exc_val}")
        await self.memory_manager.update_context(self.context)

    def get_memory_stats(self) -> "MemoryStats":
        return self._memory_stats
