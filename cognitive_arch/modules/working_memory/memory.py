"""
Working Memory implementation.

Working memory is the cognitive workspace where active reasoning occurs.
It maintains a limited set of highly-activated chunks and manages the
flow of information during problem-solving.

This implementation draws on:
- ACT-R's declarative memory system
- Baddeley's working memory model
- Global Workspace Theory
"""

from typing import Any, Dict, List, Optional, Set, Callable, Tuple
from datetime import datetime
import heapq

from ...core.types import CognitiveModule, ReasoningTrace, Thought
from .chunks import Chunk, ChunkType, create_fact, create_goal, create_hypothesis
from .attention import AttentionManager


class WorkingMemory(CognitiveModule):
    """
    Working Memory: The cognitive workspace for active reasoning.

    Features:
    - Capacity-limited storage of active chunks
    - Activation-based retrieval
    - Automatic decay and interference
    - Attention-modulated access
    - Support for different chunk types (facts, goals, hypotheses, etc.)
    """

    def __init__(self,
                 capacity: int = 7,  # Miller's magical number
                 decay_rate: float = 0.1,
                 retrieval_threshold: float = 0.0):
        """
        Initialize working memory.

        Args:
            capacity: Maximum number of highly-active chunks
            decay_rate: Rate of activation decay over time
            retrieval_threshold: Minimum activation for retrieval
        """
        super().__init__("WorkingMemory")
        self.capacity = capacity
        self.decay_rate = decay_rate
        self.retrieval_threshold = retrieval_threshold

        # Chunk storage
        self.chunks: Dict[str, Chunk] = {}

        # Indices for efficient access
        self._by_type: Dict[ChunkType, Set[str]] = {ct: set() for ct in ChunkType}
        self._by_name: Dict[str, str] = {}  # name -> id

        # Attention management
        self.attention = AttentionManager(max_focus_size=4)

        # Statistics
        self.stats = {
            "retrievals": 0,
            "failures": 0,
            "stores": 0,
            "evictions": 0
        }

    def process(self, input_data: Any) -> Any:
        """
        Process input - the main interface required by CognitiveModule.

        Input can be:
        - A Chunk to store
        - A dict with action ("store", "retrieve", "query")
        - A string query to search for
        """
        if isinstance(input_data, Chunk):
            return self.store(input_data)
        elif isinstance(input_data, dict):
            action = input_data.get("action", "query")
            if action == "store":
                chunk = input_data.get("chunk")
                if chunk:
                    return self.store(chunk)
            elif action == "retrieve":
                chunk_id = input_data.get("id")
                if chunk_id:
                    return self.retrieve(chunk_id)
            elif action == "query":
                pattern = input_data.get("pattern", {})
                return self.query(pattern)
        elif isinstance(input_data, str):
            # Treat as a search query
            return self.search(input_data)

        return None

    def reset(self) -> None:
        """Reset working memory to empty state."""
        self.chunks.clear()
        self._by_type = {ct: set() for ct in ChunkType}
        self._by_name.clear()
        self.attention.reset()
        self.trace = ReasoningTrace()

    def store(self, chunk: Chunk) -> str:
        """
        Store a chunk in working memory.

        If capacity is exceeded, lowest-activation chunks may be evicted.
        Returns the chunk ID.
        """
        # Apply decay to existing chunks first
        self._apply_decay()

        # Check if we need to evict
        while len(self.chunks) >= self.capacity:
            self._evict_lowest()

        # Store the chunk
        self.chunks[chunk.id] = chunk
        self._by_type[chunk.chunk_type].add(chunk.id)
        if chunk.name:
            self._by_name[chunk.name] = chunk.id

        # Initial activation boost for new chunks
        chunk.activation = 1.0
        chunk.access()

        self.stats["stores"] += 1
        self.trace.add_step(
            "store",
            f"Stored chunk: {chunk.name or chunk.id} ({chunk.chunk_type.name})",
            confidence=1.0
        )

        return chunk.id

    def retrieve(self, chunk_id: str) -> Optional[Chunk]:
        """
        Retrieve a chunk by ID.

        Updates activation on successful retrieval.
        """
        chunk = self.chunks.get(chunk_id)
        if chunk and chunk.activation >= self.retrieval_threshold:
            chunk.access()
            self.attention.focus_on(chunk, strength=0.5)
            self.stats["retrievals"] += 1
            return chunk
        else:
            self.stats["failures"] += 1
            return None

    def retrieve_by_name(self, name: str) -> Optional[Chunk]:
        """Retrieve a chunk by its name."""
        chunk_id = self._by_name.get(name)
        if chunk_id:
            return self.retrieve(chunk_id)
        return None

    def query(self, pattern: Dict[str, Any],
              chunk_type: Optional[ChunkType] = None,
              limit: int = 5) -> List[Chunk]:
        """
        Query for chunks matching a pattern.

        Args:
            pattern: Slot values to match (None matches any)
            chunk_type: Optional filter by chunk type
            limit: Maximum number of results

        Returns:
            List of matching chunks, sorted by activation
        """
        self._apply_decay()

        candidates = []
        search_set = self._by_type[chunk_type] if chunk_type else set(self.chunks.keys())

        for chunk_id in search_set:
            chunk = self.chunks[chunk_id]
            if chunk.activation >= self.retrieval_threshold and chunk.matches(pattern):
                candidates.append(chunk)

        # Sort by activation (highest first)
        candidates.sort(key=lambda c: c.activation, reverse=True)

        # Mark as accessed
        for chunk in candidates[:limit]:
            chunk.access()

        self.stats["retrievals"] += len(candidates[:limit])
        return candidates[:limit]

    def search(self, query_str: str, limit: int = 5) -> List[Chunk]:
        """
        Search for chunks using a text query.

        This is a simple keyword-based search across chunk names and slots.
        """
        query_lower = query_str.lower()
        scored_chunks = []

        for chunk in self.chunks.values():
            if chunk.activation < self.retrieval_threshold:
                continue

            score = 0.0

            # Check name
            if chunk.name and query_lower in chunk.name.lower():
                score += 2.0

            # Check slots
            for slot_name, slot_value in chunk.slots.items():
                if query_lower in slot_name.lower():
                    score += 0.5
                if isinstance(slot_value, str) and query_lower in slot_value.lower():
                    score += 1.0

            if score > 0:
                scored_chunks.append((score * chunk.activation, chunk))

        # Sort by score
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        results = [chunk for _, chunk in scored_chunks[:limit]]
        for chunk in results:
            chunk.access()

        return results

    def get_most_active(self, n: int = 5) -> List[Chunk]:
        """Get the n most active chunks."""
        self._apply_decay()
        return heapq.nlargest(n, self.chunks.values(), key=lambda c: c.activation)

    def get_by_type(self, chunk_type: ChunkType) -> List[Chunk]:
        """Get all chunks of a specific type."""
        return [self.chunks[cid] for cid in self._by_type[chunk_type]
                if cid in self.chunks]

    def get_goals(self) -> List[Chunk]:
        """Convenience method to get all goal chunks."""
        return self.get_by_type(ChunkType.GOAL)

    def get_hypotheses(self) -> List[Chunk]:
        """Convenience method to get all hypothesis chunks."""
        return self.get_by_type(ChunkType.HYPOTHESIS)

    def get_active_context(self) -> Dict[str, Any]:
        """
        Get a summary of the current working memory context.

        Useful for metacognition and explanation.
        """
        self._apply_decay()

        return {
            "total_chunks": len(self.chunks),
            "chunks_by_type": {
                ct.name: len(ids) for ct, ids in self._by_type.items() if ids
            },
            "most_active": [
                {"name": c.name, "type": c.chunk_type.name, "activation": c.activation}
                for c in self.get_most_active(3)
            ],
            "focus": {
                "primary": self.attention.current_focus.primary_chunk_id,
                "secondary": list(self.attention.current_focus.secondary_chunk_ids)
            },
            "stats": self.stats.copy()
        }

    def link_chunks(self, chunk_id1: str, chunk_id2: str) -> bool:
        """Create a bidirectional link between two chunks."""
        if chunk_id1 in self.chunks and chunk_id2 in self.chunks:
            self.chunks[chunk_id1].link_to(self.chunks[chunk_id2])
            return True
        return False

    def spread_activation(self, source_chunk: Chunk, amount: float = 0.5) -> None:
        """Spread activation from a source chunk to its linked chunks."""
        for linked_id in source_chunk.linked_chunks:
            if linked_id in self.chunks:
                target = self.chunks[linked_id]
                target.activation += amount * 0.5
                target.activation = min(target.activation, 10.0)  # Cap activation

    def focus_on(self, chunk: Chunk) -> None:
        """Set attention focus to a specific chunk."""
        self.attention.focus_on(chunk)
        self.spread_activation(chunk, 0.5)

    def _apply_decay(self) -> None:
        """Apply time-based decay to all chunks."""
        current_time = datetime.now()
        for chunk in self.chunks.values():
            chunk.decay(self.decay_rate, current_time)

    def _evict_lowest(self) -> Optional[str]:
        """Evict the chunk with lowest activation."""
        if not self.chunks:
            return None

        # Find lowest activation chunk not in focus
        candidates = [
            (c.activation, c.id) for c in self.chunks.values()
            if not self.attention.is_in_focus(c.id)
        ]

        if not candidates:
            # All chunks in focus, evict lowest overall
            candidates = [(c.activation, c.id) for c in self.chunks.values()]

        if candidates:
            _, evict_id = min(candidates)
            self._remove_chunk(evict_id)
            self.stats["evictions"] += 1
            return evict_id

        return None

    def _remove_chunk(self, chunk_id: str) -> None:
        """Remove a chunk from all indices."""
        if chunk_id in self.chunks:
            chunk = self.chunks[chunk_id]
            self._by_type[chunk.chunk_type].discard(chunk_id)
            if chunk.name in self._by_name:
                del self._by_name[chunk.name]

            # Remove from other chunks' links
            for other in self.chunks.values():
                other.linked_chunks.discard(chunk_id)

            del self.chunks[chunk_id]
            self.attention.remove_from_focus(chunk_id)

    def dump(self) -> List[Dict[str, Any]]:
        """Dump all chunks as dictionaries (for debugging/serialization)."""
        return [chunk.to_dict() for chunk in self.chunks.values()]

    def summarize(self) -> str:
        """Generate a human-readable summary of working memory contents."""
        lines = [f"Working Memory ({len(self.chunks)}/{self.capacity} chunks):"]

        for ct in ChunkType:
            type_chunks = self.get_by_type(ct)
            if type_chunks:
                lines.append(f"\n  {ct.name}s:")
                for chunk in sorted(type_chunks, key=lambda c: -c.activation)[:3]:
                    focus_marker = "*" if self.attention.is_in_focus(chunk.id) else " "
                    lines.append(f"    {focus_marker}[{chunk.activation:.2f}] {chunk.name}")

        return "\n".join(lines)
