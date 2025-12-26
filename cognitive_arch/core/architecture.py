"""
Cognitive Architecture Integration Layer

This module provides the unified interface for the cognitive architecture,
integrating all modules into a coherent reasoning system.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from .types import CognitiveModule, ReasoningTrace, Thought, Belief, Goal

# Import all modules
from ..modules.working_memory import WorkingMemory, Chunk, ChunkType
from ..modules.metacognition import MetacognitiveMonitor, ConfidenceTracker, ReflectionEngine
from ..modules.causal import CausalGraph, CausalInference, InterventionAnalyzer
from ..modules.analogical import (
    Structure, StructureMapper, AnalogRetriever, AnalogicalInference
)


@dataclass
class CognitiveContext:
    """Context for a reasoning session."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=datetime.now)
    goals: List[Goal] = field(default_factory=list)
    current_goal: Optional[Goal] = None
    reasoning_depth: int = 0
    total_thoughts: int = 0


class CognitiveArchitecture:
    """
    The unified cognitive architecture.

    Integrates:
    - Working Memory: Active information store
    - Metacognition: Self-monitoring and reflection
    - Causal Reasoning: Cause-effect analysis
    - Analogical Reasoning: Cross-domain inference

    The architecture provides a unified interface for complex reasoning
    tasks while allowing direct access to individual modules.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the cognitive architecture.

        Args:
            config: Optional configuration dictionary with settings for modules
        """
        config = config or {}

        # Initialize core modules
        self.working_memory = WorkingMemory(
            capacity=config.get("wm_capacity", 7),
            decay_rate=config.get("decay_rate", 0.1)
        )

        self.metacognition = MetacognitiveMonitor()
        self.confidence = ConfidenceTracker()
        self.reflection = ReflectionEngine()

        # Causal reasoning (lazily initialized with specific graphs)
        self._causal_graphs: Dict[str, CausalGraph] = {}
        self._causal_inference: Dict[str, CausalInference] = {}

        # Analogical reasoning
        self.analog_retriever = AnalogRetriever()
        self.structure_mapper = StructureMapper()
        self.analogical_inference = AnalogicalInference(self.analog_retriever)

        # Session context
        self.context = CognitiveContext()

        # Global reasoning trace
        self.trace = ReasoningTrace()

        # Event callbacks
        self._callbacks: Dict[str, List[Callable]] = {
            "thought": [],
            "belief": [],
            "goal": [],
            "issue": []
        }

    # =================================================================
    # WORKING MEMORY INTERFACE
    # =================================================================

    def remember(self, content: str, chunk_type: ChunkType = ChunkType.FACT,
                confidence: float = 1.0, **slots) -> str:
        """Store information in working memory."""
        chunk = Chunk(
            chunk_type=chunk_type,
            name=content[:50],  # Use beginning as name
            slots={"content": content, **slots},
            confidence=confidence
        )
        chunk_id = self.working_memory.store(chunk)

        self.trace.add_step(
            "remember",
            f"Stored: {content[:50]}...",
            confidence=confidence
        )

        return chunk_id

    def recall(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve information from working memory."""
        chunks = self.working_memory.search(query, limit=limit)
        return [
            {
                "id": c.id,
                "content": c.slots.get("content", c.name),
                "type": c.chunk_type.name,
                "activation": c.activation,
                "confidence": c.confidence
            }
            for c in chunks
        ]

    def focus(self, chunk_id: str) -> bool:
        """Focus attention on a specific chunk."""
        chunk = self.working_memory.retrieve(chunk_id)
        if chunk:
            self.working_memory.focus_on(chunk)
            return True
        return False

    # =================================================================
    # METACOGNITION INTERFACE
    # =================================================================

    def assess_confidence(self, claim: str, confidence: float,
                         domain: str = "general") -> str:
        """Record a confidence judgment for later calibration."""
        return self.confidence.record_judgment(claim, confidence, domain)

    def record_outcome(self, judgment_id: str, correct: bool) -> None:
        """Record whether a judgment was correct."""
        self.confidence.record_outcome(judgment_id, correct)

    def get_calibration(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """Get confidence calibration statistics."""
        return self.confidence.get_calibration(domain)

    def check_reasoning(self, thoughts: List[Thought]) -> List[Dict[str, Any]]:
        """Check a sequence of thoughts for issues."""
        issues = self.metacognition._analyze_thoughts(thoughts)
        return [
            {
                "type": i.issue_type.name,
                "severity": i.severity,
                "description": i.description,
                "suggestions": i.suggested_actions
            }
            for i in issues
        ]

    def reflect(self, problem: str, strategy: str = "analytical") -> Dict[str, Any]:
        """Start a reflection episode for a problem."""
        from ..modules.metacognition.reflection import ReasoningStrategy

        strategy_enum = ReasoningStrategy[strategy.upper()]
        episode = self.reflection.start_episode(problem, strategy_enum)

        return {
            "episode_id": episode.id,
            "problem": problem,
            "strategy": strategy
        }

    # =================================================================
    # CAUSAL REASONING INTERFACE
    # =================================================================

    def create_causal_model(self, name: str,
                           variables: List[str],
                           edges: List[tuple]) -> str:
        """Create a causal graph model."""
        graph = CausalGraph(name=name)

        # Add variables as nodes
        node_ids = {}
        for var in variables:
            node_ids[var] = graph.add_node_by_name(var)

        # Add causal edges
        for source, target in edges:
            if source in node_ids and target in node_ids:
                graph.add_edge(node_ids[source], node_ids[target])

        self._causal_graphs[name] = graph
        self._causal_inference[name] = CausalInference(graph)

        return name

    def causal_query(self, model_name: str, treatment: str,
                    outcome: str) -> Dict[str, Any]:
        """Query a causal effect."""
        if model_name not in self._causal_inference:
            return {"error": f"Model '{model_name}' not found"}

        inference = self._causal_inference[model_name]
        identifiable, explanation = inference.is_identifiable(treatment, outcome)
        effect = inference.estimate_effect(treatment, outcome)

        return {
            "treatment": treatment,
            "outcome": outcome,
            "identifiable": identifiable,
            "explanation": explanation,
            "estimate": effect.estimate,
            "method": effect.method,
            "adjustment_set": effect.adjustment_set
        }

    def what_if(self, model_name: str, intervention: str,
               value: Any = None) -> Dict[str, Any]:
        """Analyze a hypothetical intervention."""
        if model_name not in self._causal_graphs:
            return {"error": f"Model '{model_name}' not found"}

        graph = self._causal_graphs[model_name]
        analyzer = InterventionAnalyzer(graph)
        outcome = analyzer.analyze_intervention(intervention, value)

        return {
            "intervention": f"do({intervention} = {value})",
            "affected_variables": outcome.affected_variables,
            "predicted_changes": outcome.predicted_changes,
            "side_effects": outcome.side_effects,
            "warnings": outcome.warnings,
            "confidence": outcome.confidence
        }

    # =================================================================
    # ANALOGICAL REASONING INTERFACE
    # =================================================================

    def store_analog(self, name: str, description: str,
                    entities: List[str],
                    relations: List[tuple],
                    domain: str = "",
                    tags: Optional[List[str]] = None) -> str:
        """Store an analog in the knowledge base."""
        from ..modules.analogical.structures import create_structure

        structure = create_structure(name, entities, relations)
        structure.description = description

        return self.analog_retriever.store(
            structure, domain=domain, tags=tags, description=description
        )

    def find_analogs(self, query_entities: List[str],
                    query_relations: List[tuple],
                    n: int = 3) -> List[Dict[str, Any]]:
        """Find analogs for a query structure."""
        from ..modules.analogical.structures import create_structure

        query = create_structure("query", query_entities, query_relations)
        results = self.analog_retriever.retrieve(query, n=n)

        return [
            {
                "name": analog.structure.name,
                "description": analog.description,
                "domain": analog.domain,
                "similarity": score,
                "entities": [e.name for e in analog.structure.get_entities()],
                "relations": [r.name for r in analog.structure.relations]
            }
            for analog, score in results
        ]

    def analogical_transfer(self, source_name: str,
                           target_entities: List[str],
                           target_relations: List[tuple]) -> List[Dict[str, Any]]:
        """Transfer knowledge from a source analog to a target."""
        from ..modules.analogical.structures import create_structure

        # Find source
        source_analogs = self.analog_retriever.retrieve(
            Structure(name=source_name), n=1
        )

        if not source_analogs:
            return []

        source = source_analogs[0][0].structure

        # Create target
        target = create_structure("target", target_entities, target_relations)

        # Get inferences
        inferences = self.analogical_inference.infer(target, source=source)

        return [
            {
                "type": inf.inference_type,
                "content": inf.content,
                "confidence": inf.confidence,
                "source": source_name
            }
            for inf in inferences
        ]

    # =================================================================
    # INTEGRATED REASONING
    # =================================================================

    def reason(self, problem: str, approach: str = "auto") -> Dict[str, Any]:
        """
        Perform integrated reasoning on a problem.

        This combines multiple cognitive modules as appropriate.
        """
        self.context.current_goal = Goal(description=problem)
        self.context.goals.append(self.context.current_goal)

        result = {
            "problem": problem,
            "approach": approach,
            "steps": [],
            "conclusions": [],
            "confidence": 0.5,
            "issues": []
        }

        # Store problem in working memory
        problem_chunk = self.remember(problem, ChunkType.GOAL)
        result["steps"].append(f"Stored problem in working memory: {problem_chunk}")

        # Check for analogies
        analogs = self.find_analogs(
            query_entities=problem.split()[:5],  # Simple tokenization
            query_relations=[],
            n=2
        )

        if analogs and analogs[0]["similarity"] > 0.5:
            result["steps"].append(f"Found relevant analog: {analogs[0]['name']}")
            result["analogs_used"] = analogs

        # Record confidence judgment
        judgment_id = self.assess_confidence(
            f"Can solve: {problem}",
            0.7,
            "problem_solving"
        )

        # Complete the episode
        self.context.current_goal.status = "achieved"
        result["confidence"] = 0.7

        return result

    def think(self, content: str, thought_type: str = "observation") -> Thought:
        """
        Create and record a thought.

        Thoughts are added to the reasoning trace and checked for issues.
        """
        thought = Thought(
            content=content,
            thought_type=thought_type,
            confidence=0.7
        )

        self.context.total_thoughts += 1
        self.trace.add_step(
            thought_type,
            content,
            confidence=thought.confidence
        )

        # Notify callbacks
        for callback in self._callbacks.get("thought", []):
            callback(thought)

        return thought

    def conclude(self, conclusion: str, confidence: float = 0.7,
                evidence: Optional[List[str]] = None) -> Belief:
        """
        Record a conclusion as a belief.
        """
        belief = Belief(
            content=conclusion,
            confidence=confidence,
            sources=evidence or []
        )

        # Check for contradictions
        issues = self.metacognition.record_belief(belief)
        for issue in issues:
            for callback in self._callbacks.get("issue", []):
                callback(issue)

        self.trace.add_step(
            "conclusion",
            conclusion,
            confidence=confidence
        )

        return belief

    # =================================================================
    # UTILITY METHODS
    # =================================================================

    def on(self, event: str, callback: Callable) -> None:
        """Register a callback for events."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def get_state(self) -> Dict[str, Any]:
        """Get the current cognitive state."""
        return {
            "session_id": self.context.session_id,
            "uptime_seconds": (datetime.now() - self.context.started_at).total_seconds(),
            "working_memory": self.working_memory.get_active_context(),
            "goals": {
                "total": len(self.context.goals),
                "current": self.context.current_goal.description if self.context.current_goal else None
            },
            "metacognition": {
                "issues": len(self.metacognition.get_active_issues()),
                "calibration": self.confidence.get_calibration()
            },
            "causal_models": list(self._causal_graphs.keys()),
            "analogs_stored": len(self.analog_retriever.analogs),
            "total_thoughts": self.context.total_thoughts,
            "trace_steps": len(self.trace.steps)
        }

    def explain(self) -> str:
        """Generate an explanation of recent reasoning."""
        return self.trace.summarize()

    def reset(self) -> None:
        """Reset the architecture to initial state."""
        self.working_memory.reset()
        self.metacognition.reset()
        self.context = CognitiveContext()
        self.trace = ReasoningTrace()

    def summarize(self) -> str:
        """Generate a comprehensive summary."""
        lines = ["Cognitive Architecture Summary"]
        lines.append("=" * 50)

        state = self.get_state()
        lines.append(f"\nSession: {state['session_id'][:8]}...")
        lines.append(f"Uptime: {state['uptime_seconds']:.1f}s")
        lines.append(f"Total thoughts: {state['total_thoughts']}")

        lines.append("\n--- Working Memory ---")
        lines.append(self.working_memory.summarize())

        lines.append("\n--- Metacognition ---")
        lines.append(self.metacognition.diagnose())

        lines.append("\n--- Causal Models ---")
        lines.append(f"Models: {', '.join(state['causal_models']) or '(none)'}")

        lines.append("\n--- Analog Knowledge ---")
        lines.append(self.analog_retriever.summarize())

        return "\n".join(lines)
