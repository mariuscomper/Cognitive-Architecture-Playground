"""
Core type definitions for the cognitive architecture.

This module defines the fundamental abstractions that all cognitive
modules share, enabling them to interoperate seamlessly.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from datetime import datetime
import uuid


class ConfidenceLevel(Enum):
    """Represents epistemic confidence in a belief or conclusion."""
    CERTAIN = auto()      # 0.95+ - Effectively no doubt
    HIGH = auto()         # 0.80-0.95 - Strong confidence
    MODERATE = auto()     # 0.50-0.80 - More likely than not
    LOW = auto()          # 0.20-0.50 - Uncertain but possible
    VERY_LOW = auto()     # 0.05-0.20 - Unlikely
    UNKNOWN = auto()      # No basis for assessment

    @classmethod
    def from_probability(cls, p: float) -> 'ConfidenceLevel':
        """Convert a probability to a confidence level."""
        if p >= 0.95:
            return cls.CERTAIN
        elif p >= 0.80:
            return cls.HIGH
        elif p >= 0.50:
            return cls.MODERATE
        elif p >= 0.20:
            return cls.LOW
        elif p >= 0.05:
            return cls.VERY_LOW
        else:
            return cls.UNKNOWN


@dataclass
class Belief:
    """
    A belief is a proposition with associated confidence and provenance.

    Beliefs are the basic currency of reasoning in this architecture.
    They track not just what is believed, but why and how confidently.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""  # Natural language description
    proposition: Dict[str, Any] = field(default_factory=dict)  # Structured form
    confidence: float = 0.5  # Probability estimate
    sources: List[str] = field(default_factory=list)  # Where did this come from?
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def confidence_level(self) -> ConfidenceLevel:
        return ConfidenceLevel.from_probability(self.confidence)

    def update_confidence(self, new_confidence: float, source: str) -> None:
        """Update confidence, recording the source of the update."""
        self.confidence = max(0.0, min(1.0, new_confidence))
        self.sources.append(f"updated:{source}")
        self.updated_at = datetime.now()


@dataclass
class Thought:
    """
    A thought is a unit of reasoning - a step in a thinking process.

    Thoughts are more ephemeral than beliefs. They represent the
    process of reasoning, not just the conclusions.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    thought_type: str = "observation"  # observation, inference, question, hypothesis, conclusion
    parent_thoughts: List[str] = field(default_factory=list)  # What led to this?
    child_thoughts: List[str] = field(default_factory=list)  # What follows from this?
    confidence: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Goal:
    """
    A goal represents something the system is trying to achieve.

    Goals drive reasoning by providing direction and criteria for success.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    priority: float = 0.5  # 0 to 1, higher is more important
    status: str = "active"  # active, achieved, abandoned, blocked
    subgoals: List[str] = field(default_factory=list)
    parent_goal: Optional[str] = None
    success_criteria: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class ReasoningTrace:
    """
    A trace of reasoning steps, useful for explanation and debugging.

    The trace maintains the full history of how conclusions were reached,
    enabling metacognitive analysis and explanation generation.
    """

    def __init__(self):
        self.steps: List[Dict[str, Any]] = []
        self.created_at: datetime = datetime.now()

    def add_step(self, step_type: str, content: str,
                 inputs: Optional[List[str]] = None,
                 outputs: Optional[List[str]] = None,
                 confidence: float = 0.5,
                 metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a reasoning step to the trace."""
        step_id = str(uuid.uuid4())
        self.steps.append({
            "id": step_id,
            "type": step_type,
            "content": content,
            "inputs": inputs or [],
            "outputs": outputs or [],
            "confidence": confidence,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        })
        return step_id

    def get_step(self, step_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a step by its ID."""
        for step in self.steps:
            if step["id"] == step_id:
                return step
        return None

    def get_chain(self, final_step_id: str) -> List[Dict[str, Any]]:
        """Get the chain of reasoning leading to a particular step."""
        # Build a dependency graph
        step_map = {s["id"]: s for s in self.steps}
        if final_step_id not in step_map:
            return []

        chain = []
        to_visit = [final_step_id]
        visited = set()

        while to_visit:
            current_id = to_visit.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            if current_id in step_map:
                step = step_map[current_id]
                chain.append(step)
                to_visit.extend(step.get("inputs", []))

        return list(reversed(chain))

    def summarize(self) -> str:
        """Generate a summary of the reasoning trace."""
        if not self.steps:
            return "No reasoning steps recorded."

        summary_lines = [f"Reasoning trace with {len(self.steps)} steps:"]
        for i, step in enumerate(self.steps, 1):
            conf_str = f"[{step['confidence']:.2f}]"
            summary_lines.append(f"  {i}. {step['type']}: {step['content'][:50]}... {conf_str}")

        return "\n".join(summary_lines)


class CognitiveModule(ABC):
    """
    Abstract base class for all cognitive modules.

    Each module must implement the core interface for receiving
    information, processing it, and producing outputs.
    """

    def __init__(self, name: str):
        self.name = name
        self.trace = ReasoningTrace()
        self._is_active = True

    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """Process input and produce output."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the module to its initial state."""
        pass

    def get_trace(self) -> ReasoningTrace:
        """Get the reasoning trace for this module."""
        return self.trace

    def activate(self) -> None:
        """Activate the module."""
        self._is_active = True

    def deactivate(self) -> None:
        """Deactivate the module."""
        self._is_active = False

    @property
    def is_active(self) -> bool:
        return self._is_active
