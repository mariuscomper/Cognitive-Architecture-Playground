"""
Chunk representations for working memory.

Chunks are the fundamental units of information in working memory.
They can represent facts, goals, procedures, or any structured information.

This implementation is inspired by ACT-R's chunk system but simplified
and adapted for our purposes.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
import uuid
import math


class ChunkType(Enum):
    """Types of chunks that can be stored in working memory."""
    FACT = auto()           # A piece of declarative knowledge
    GOAL = auto()           # Something to achieve
    PROCEDURE = auto()      # A method or approach
    CONTEXT = auto()        # Background/situational information
    HYPOTHESIS = auto()     # A tentative belief
    QUESTION = auto()       # An open question
    CONSTRAINT = auto()     # A limitation or requirement
    RELATION = auto()       # A relationship between other chunks


@dataclass
class Chunk:
    """
    A chunk is a unit of information in working memory.

    Chunks have:
    - An identifier and type
    - Structured content (slots)
    - Activation level (determines retrievability)
    - Links to other chunks
    - Metadata for provenance and timing
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    chunk_type: ChunkType = ChunkType.FACT
    name: str = ""
    slots: Dict[str, Any] = field(default_factory=dict)

    # Activation and memory dynamics
    base_activation: float = 0.0
    activation: float = 0.0
    access_count: int = 0
    last_accessed: Optional[datetime] = None

    # Relational structure
    linked_chunks: Set[str] = field(default_factory=set)
    source_chunks: List[str] = field(default_factory=list)  # Chunks that led to this one

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0
    importance: float = 0.5

    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at

    def access(self) -> None:
        """Record an access to this chunk, updating activation."""
        self.access_count += 1
        self.last_accessed = datetime.now()
        # Base-level learning: activation increases with use
        # Using a simplified version of ACT-R's base-level learning equation
        self.base_activation = math.log(self.access_count + 1)
        self.activation = self.base_activation

    def decay(self, decay_rate: float = 0.5, current_time: Optional[datetime] = None) -> None:
        """Apply time-based decay to activation."""
        if current_time is None:
            current_time = datetime.now()

        if self.last_accessed:
            time_since_access = (current_time - self.last_accessed).total_seconds()
            # Exponential decay
            decay_factor = math.exp(-decay_rate * time_since_access / 3600)  # Per hour
            self.activation = self.base_activation * decay_factor

    def spread_activation(self, amount: float, to_chunk: 'Chunk') -> None:
        """Spread activation to a linked chunk."""
        if to_chunk.id in self.linked_chunks:
            to_chunk.activation += amount * 0.5  # Spreading factor

    def link_to(self, other: 'Chunk', bidirectional: bool = True) -> None:
        """Create a link to another chunk."""
        self.linked_chunks.add(other.id)
        if bidirectional:
            other.linked_chunks.add(self.id)

    def unlink_from(self, other: 'Chunk', bidirectional: bool = True) -> None:
        """Remove a link to another chunk."""
        self.linked_chunks.discard(other.id)
        if bidirectional:
            other.linked_chunks.discard(self.id)

    def get_slot(self, slot_name: str, default: Any = None) -> Any:
        """Get the value of a slot."""
        return self.slots.get(slot_name, default)

    def set_slot(self, slot_name: str, value: Any) -> None:
        """Set the value of a slot."""
        self.slots[slot_name] = value

    def matches(self, pattern: Dict[str, Any]) -> bool:
        """
        Check if this chunk matches a pattern.

        The pattern is a dictionary of slot names to values.
        A None value in the pattern matches any value.
        """
        for slot_name, expected_value in pattern.items():
            if expected_value is None:
                continue
            if slot_name not in self.slots:
                return False
            if self.slots[slot_name] != expected_value:
                return False
        return True

    def similarity(self, other: 'Chunk') -> float:
        """
        Compute similarity to another chunk.

        Similarity is based on:
        - Type match
        - Slot overlap
        - Linked chunk overlap
        """
        score = 0.0
        total_weight = 0.0

        # Type similarity (weight: 0.3)
        if self.chunk_type == other.chunk_type:
            score += 0.3
        total_weight += 0.3

        # Slot similarity (weight: 0.5)
        all_slots = set(self.slots.keys()) | set(other.slots.keys())
        if all_slots:
            matching_slots = 0
            for slot in all_slots:
                if self.slots.get(slot) == other.slots.get(slot):
                    matching_slots += 1
            score += 0.5 * (matching_slots / len(all_slots))
        total_weight += 0.5

        # Link similarity (weight: 0.2)
        all_links = self.linked_chunks | other.linked_chunks
        if all_links:
            common_links = self.linked_chunks & other.linked_chunks
            score += 0.2 * (len(common_links) / len(all_links))
        total_weight += 0.2

        return score / total_weight if total_weight > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to a dictionary representation."""
        return {
            "id": self.id,
            "type": self.chunk_type.name,
            "name": self.name,
            "slots": self.slots,
            "activation": self.activation,
            "confidence": self.confidence,
            "importance": self.importance,
            "linked_chunks": list(self.linked_chunks),
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Chunk':
        """Create a chunk from a dictionary representation."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            chunk_type=ChunkType[data.get("type", "FACT")],
            name=data.get("name", ""),
            slots=data.get("slots", {}),
            activation=data.get("activation", 0.0),
            confidence=data.get("confidence", 1.0),
            importance=data.get("importance", 0.5),
            linked_chunks=set(data.get("linked_chunks", []))
        )

    def __repr__(self) -> str:
        return f"Chunk({self.chunk_type.name}: {self.name}, activation={self.activation:.2f})"


def create_fact(name: str, **slots) -> Chunk:
    """Convenience function to create a fact chunk."""
    return Chunk(
        chunk_type=ChunkType.FACT,
        name=name,
        slots=slots
    )


def create_goal(name: str, description: str, **criteria) -> Chunk:
    """Convenience function to create a goal chunk."""
    return Chunk(
        chunk_type=ChunkType.GOAL,
        name=name,
        slots={"description": description, **criteria}
    )


def create_hypothesis(name: str, proposition: str, confidence: float = 0.5) -> Chunk:
    """Convenience function to create a hypothesis chunk."""
    return Chunk(
        chunk_type=ChunkType.HYPOTHESIS,
        name=name,
        slots={"proposition": proposition},
        confidence=confidence
    )


def create_question(question: str, context: Optional[str] = None) -> Chunk:
    """Convenience function to create a question chunk."""
    return Chunk(
        chunk_type=ChunkType.QUESTION,
        name=f"q_{uuid.uuid4().hex[:8]}",
        slots={"question": question, "context": context or ""}
    )
