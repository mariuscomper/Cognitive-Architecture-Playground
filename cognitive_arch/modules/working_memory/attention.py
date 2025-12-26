"""
Attention management for working memory.

This module implements a simple attention mechanism that determines
which chunks are currently in focus and how activation spreads.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict, Any
from datetime import datetime
from .chunks import Chunk, ChunkType


@dataclass
class AttentionFocus:
    """Represents the current focus of attention."""
    primary_chunk_id: Optional[str] = None
    secondary_chunk_ids: Set[str] = field(default_factory=set)
    focus_strength: float = 1.0
    established_at: datetime = field(default_factory=datetime.now)


class AttentionManager:
    """
    Manages attention within working memory.

    Key responsibilities:
    - Maintaining focus on relevant chunks
    - Spreading activation based on attention
    - Managing attention shifts
    - Tracking attention history for metacognition
    """

    def __init__(self, max_focus_size: int = 4):
        """
        Initialize the attention manager.

        Args:
            max_focus_size: Maximum number of chunks that can be in focus
                           (based on cognitive limitations, typically 3-5)
        """
        self.max_focus_size = max_focus_size
        self.current_focus = AttentionFocus()
        self.focus_history: List[AttentionFocus] = []
        self.attention_shifts = 0

    def focus_on(self, chunk: Chunk, strength: float = 1.0) -> None:
        """
        Set the primary focus to a specific chunk.

        This shifts attention to the chunk, boosting its activation
        and potentially displacing other chunks from focus.
        """
        # Save current focus to history
        if self.current_focus.primary_chunk_id:
            self.focus_history.append(self.current_focus)
            self.attention_shifts += 1

        # Limit history size
        if len(self.focus_history) > 100:
            self.focus_history = self.focus_history[-50:]

        # Set new focus
        self.current_focus = AttentionFocus(
            primary_chunk_id=chunk.id,
            focus_strength=strength,
            established_at=datetime.now()
        )

        # Boost the chunk's activation
        chunk.access()
        chunk.activation += strength * 2.0

    def add_to_focus(self, chunk: Chunk) -> bool:
        """
        Add a chunk to secondary focus.

        Returns True if successful, False if focus is at capacity.
        """
        if len(self.current_focus.secondary_chunk_ids) >= self.max_focus_size - 1:
            return False

        self.current_focus.secondary_chunk_ids.add(chunk.id)
        chunk.access()
        chunk.activation += 0.5  # Smaller boost than primary focus
        return True

    def remove_from_focus(self, chunk_id: str) -> None:
        """Remove a chunk from focus."""
        if self.current_focus.primary_chunk_id == chunk_id:
            # Promote a secondary chunk if available
            if self.current_focus.secondary_chunk_ids:
                new_primary = self.current_focus.secondary_chunk_ids.pop()
                self.current_focus.primary_chunk_id = new_primary
            else:
                self.current_focus.primary_chunk_id = None
        else:
            self.current_focus.secondary_chunk_ids.discard(chunk_id)

    def is_in_focus(self, chunk_id: str) -> bool:
        """Check if a chunk is currently in focus."""
        return (chunk_id == self.current_focus.primary_chunk_id or
                chunk_id in self.current_focus.secondary_chunk_ids)

    def get_focus_strength(self, chunk_id: str) -> float:
        """Get the attention strength for a chunk."""
        if chunk_id == self.current_focus.primary_chunk_id:
            return self.current_focus.focus_strength
        elif chunk_id in self.current_focus.secondary_chunk_ids:
            return self.current_focus.focus_strength * 0.5
        else:
            return 0.0

    def apply_attention_to_chunks(self, chunks: Dict[str, Chunk],
                                  spreading_factor: float = 0.3) -> None:
        """
        Apply attention effects to all chunks.

        This spreads activation from focused chunks to linked chunks.
        """
        # First, apply attention boost to focused chunks
        if self.current_focus.primary_chunk_id in chunks:
            primary = chunks[self.current_focus.primary_chunk_id]
            primary.activation += self.current_focus.focus_strength

        for chunk_id in self.current_focus.secondary_chunk_ids:
            if chunk_id in chunks:
                chunks[chunk_id].activation += self.current_focus.focus_strength * 0.5

        # Then, spread activation from focused chunks
        focused_ids = {self.current_focus.primary_chunk_id} | self.current_focus.secondary_chunk_ids
        focused_ids.discard(None)

        for chunk_id in focused_ids:
            if chunk_id not in chunks:
                continue
            source_chunk = chunks[chunk_id]
            for linked_id in source_chunk.linked_chunks:
                if linked_id in chunks:
                    target_chunk = chunks[linked_id]
                    spread_amount = source_chunk.activation * spreading_factor
                    target_chunk.activation += spread_amount

    def get_attention_stats(self) -> Dict[str, Any]:
        """Get statistics about attention patterns."""
        return {
            "total_shifts": self.attention_shifts,
            "current_focus_size": len(self.current_focus.secondary_chunk_ids) + (
                1 if self.current_focus.primary_chunk_id else 0
            ),
            "focus_duration": (
                (datetime.now() - self.current_focus.established_at).total_seconds()
                if self.current_focus.established_at else 0
            ),
            "history_length": len(self.focus_history)
        }

    def reset(self) -> None:
        """Reset attention state."""
        self.current_focus = AttentionFocus()
        self.focus_history = []
        self.attention_shifts = 0

    def get_recent_focuses(self, n: int = 5) -> List[str]:
        """Get the IDs of recently focused chunks."""
        recent = []
        for focus in reversed(self.focus_history[-n:]):
            if focus.primary_chunk_id:
                recent.append(focus.primary_chunk_id)
        return recent
