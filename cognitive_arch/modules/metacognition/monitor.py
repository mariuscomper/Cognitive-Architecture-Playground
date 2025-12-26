"""
Metacognitive monitoring system.

This module implements monitoring of cognitive processes - watching the
reasoning process and detecting issues like:
- Circular reasoning
- Contradictions
- Excessive uncertainty
- Cognitive resource exhaustion
- Goal drift
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Callable, Tuple
from datetime import datetime, timedelta
from enum import Enum, auto
import uuid

from ...core.types import CognitiveModule, ReasoningTrace, Thought, Belief


class CognitiveIssue(Enum):
    """Types of cognitive issues that can be detected."""
    CIRCULAR_REASONING = auto()
    CONTRADICTION = auto()
    LOW_CONFIDENCE = auto()
    EXCESSIVE_UNCERTAINTY = auto()
    GOAL_DRIFT = auto()
    RESOURCE_EXHAUSTION = auto()
    CONFIRMATION_BIAS = auto()
    ANCHORING = auto()
    STALLED_PROGRESS = auto()
    INCONSISTENT_BELIEFS = auto()


@dataclass
class Issue:
    """A detected cognitive issue."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    issue_type: CognitiveIssue = CognitiveIssue.LOW_CONFIDENCE
    severity: float = 0.5  # 0 to 1, higher is more severe
    description: str = ""
    evidence: List[str] = field(default_factory=list)
    suggested_actions: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False


@dataclass
class CognitiveState:
    """A snapshot of the current cognitive state."""
    timestamp: datetime = field(default_factory=datetime.now)
    active_goals: int = 0
    working_memory_load: float = 0.0
    average_confidence: float = 0.5
    reasoning_depth: int = 0
    contradictions_detected: int = 0
    progress_rate: float = 0.0  # Goals completed per unit time


class MetacognitiveMonitor(CognitiveModule):
    """
    Monitors cognitive processes for issues and anomalies.

    The metacognitive monitor observes:
    - Working memory state
    - Reasoning traces
    - Belief consistency
    - Goal progress
    - Resource utilization

    And can detect:
    - Circular reasoning
    - Contradictions
    - Stalled progress
    - Cognitive biases
    - Resource exhaustion
    """

    def __init__(self):
        super().__init__("MetacognitiveMonitor")
        self.issues: List[Issue] = []
        self.state_history: List[CognitiveState] = []
        self.beliefs: Dict[str, Belief] = {}
        self.reasoning_chains: List[List[str]] = []

        # Detection thresholds
        self.thresholds = {
            "low_confidence": 0.3,
            "high_uncertainty_rate": 0.5,
            "max_reasoning_depth": 10,
            "stall_threshold": 5,  # Steps without progress
            "contradiction_tolerance": 0.2
        }

        # Callbacks for issue notification
        self._issue_callbacks: List[Callable[[Issue], None]] = []

    def process(self, input_data: Any) -> Any:
        """
        Process monitoring input.

        Can accept:
        - A CognitiveState to analyze
        - A list of Thoughts to check for issues
        - A dict with specific monitoring commands
        """
        if isinstance(input_data, CognitiveState):
            return self._analyze_state(input_data)
        elif isinstance(input_data, list) and all(isinstance(t, Thought) for t in input_data):
            return self._analyze_thoughts(input_data)
        elif isinstance(input_data, dict):
            return self._handle_command(input_data)
        return None

    def reset(self) -> None:
        """Reset the monitor."""
        self.issues = []
        self.state_history = []
        self.beliefs = {}
        self.reasoning_chains = []
        self.trace = ReasoningTrace()

    def record_belief(self, belief: Belief) -> List[Issue]:
        """
        Record a belief and check for contradictions.

        Returns any issues detected.
        """
        issues = []

        # Check for contradictions with existing beliefs
        for existing_id, existing in self.beliefs.items():
            contradiction = self._check_contradiction(belief, existing)
            if contradiction:
                issue = Issue(
                    issue_type=CognitiveIssue.CONTRADICTION,
                    severity=0.8,
                    description=f"Contradiction detected between beliefs",
                    evidence=[
                        f"New belief: {belief.content}",
                        f"Existing belief: {existing.content}",
                        f"Contradiction: {contradiction}"
                    ],
                    suggested_actions=[
                        "Review evidence for both beliefs",
                        "Lower confidence in one or both",
                        "Seek additional evidence to resolve"
                    ]
                )
                issues.append(issue)
                self._report_issue(issue)

        # Check for low confidence
        if belief.confidence < self.thresholds["low_confidence"]:
            issue = Issue(
                issue_type=CognitiveIssue.LOW_CONFIDENCE,
                severity=0.3,
                description=f"Low confidence belief recorded: {belief.content}",
                evidence=[f"Confidence: {belief.confidence}"],
                suggested_actions=["Gather more evidence", "Consider alternative explanations"]
            )
            issues.append(issue)
            self._report_issue(issue)

        self.beliefs[belief.id] = belief
        return issues

    def record_reasoning_chain(self, chain: List[str]) -> List[Issue]:
        """
        Record a reasoning chain and check for circular reasoning.

        Args:
            chain: List of step IDs or descriptions in the chain

        Returns:
            Any issues detected
        """
        issues = []

        # Check for cycles
        seen = set()
        for step in chain:
            if step in seen:
                issue = Issue(
                    issue_type=CognitiveIssue.CIRCULAR_REASONING,
                    severity=0.7,
                    description="Circular reasoning detected",
                    evidence=[f"Step '{step}' appears multiple times in reasoning chain"],
                    suggested_actions=[
                        "Break the circular dependency",
                        "Find independent evidence",
                        "Re-examine premises"
                    ]
                )
                issues.append(issue)
                self._report_issue(issue)
                break
            seen.add(step)

        # Check for excessive depth
        if len(chain) > self.thresholds["max_reasoning_depth"]:
            issue = Issue(
                issue_type=CognitiveIssue.RESOURCE_EXHAUSTION,
                severity=0.5,
                description=f"Reasoning chain too deep ({len(chain)} steps)",
                evidence=[f"Chain length: {len(chain)}"],
                suggested_actions=[
                    "Simplify the reasoning",
                    "Break into sub-problems",
                    "Consider heuristic shortcuts"
                ]
            )
            issues.append(issue)
            self._report_issue(issue)

        self.reasoning_chains.append(chain)
        return issues

    def record_state(self, state: CognitiveState) -> List[Issue]:
        """Record a cognitive state snapshot and analyze for issues."""
        self.state_history.append(state)
        return self._analyze_state(state)

    def _analyze_state(self, state: CognitiveState) -> List[Issue]:
        """Analyze a cognitive state for issues."""
        issues = []

        # Check working memory load
        if state.working_memory_load > 0.9:
            issue = Issue(
                issue_type=CognitiveIssue.RESOURCE_EXHAUSTION,
                severity=0.6,
                description="Working memory near capacity",
                evidence=[f"Load: {state.working_memory_load:.1%}"],
                suggested_actions=[
                    "Consolidate information",
                    "Offload to external storage",
                    "Focus on most relevant items"
                ]
            )
            issues.append(issue)
            self._report_issue(issue)

        # Check for stalled progress
        if len(self.state_history) >= self.thresholds["stall_threshold"]:
            recent = self.state_history[-self.thresholds["stall_threshold"]:]
            if all(s.progress_rate == 0 for s in recent):
                issue = Issue(
                    issue_type=CognitiveIssue.STALLED_PROGRESS,
                    severity=0.6,
                    description="No progress detected recently",
                    evidence=[f"No goals completed in last {len(recent)} steps"],
                    suggested_actions=[
                        "Try a different approach",
                        "Break down current goal",
                        "Seek external input"
                    ]
                )
                issues.append(issue)
                self._report_issue(issue)

        # Check confidence trend
        if len(self.state_history) >= 3:
            recent_confidence = [s.average_confidence for s in self.state_history[-3:]]
            if all(c < self.thresholds["high_uncertainty_rate"] for c in recent_confidence):
                issue = Issue(
                    issue_type=CognitiveIssue.EXCESSIVE_UNCERTAINTY,
                    severity=0.5,
                    description="Sustained high uncertainty",
                    evidence=[f"Recent confidence levels: {recent_confidence}"],
                    suggested_actions=[
                        "Gather more evidence",
                        "Make simplifying assumptions",
                        "Accept uncertainty and proceed"
                    ]
                )
                issues.append(issue)
                self._report_issue(issue)

        return issues

    def _analyze_thoughts(self, thoughts: List[Thought]) -> List[Issue]:
        """Analyze a sequence of thoughts for issues."""
        issues = []

        # Build a chain from the thoughts
        chain = [t.content[:50] for t in thoughts]
        issues.extend(self.record_reasoning_chain(chain))

        # Check for anchoring (first thought dominates)
        if len(thoughts) >= 3:
            first_confidence = thoughts[0].confidence
            later_confidences = [t.confidence for t in thoughts[1:]]
            if (first_confidence > 0.8 and
                all(abs(c - first_confidence) < 0.1 for c in later_confidences)):
                issue = Issue(
                    issue_type=CognitiveIssue.ANCHORING,
                    severity=0.4,
                    description="Possible anchoring bias detected",
                    evidence=[
                        f"First thought confidence: {first_confidence}",
                        "Subsequent thoughts show little adjustment"
                    ],
                    suggested_actions=[
                        "Actively seek disconfirming evidence",
                        "Consider alternative starting points",
                        "Use structured decomposition"
                    ]
                )
                issues.append(issue)
                self._report_issue(issue)

        return issues

    def _handle_command(self, command: Dict[str, Any]) -> Any:
        """Handle monitoring commands."""
        action = command.get("action")

        if action == "get_issues":
            return self.get_active_issues()
        elif action == "resolve_issue":
            issue_id = command.get("issue_id")
            return self.resolve_issue(issue_id)
        elif action == "set_threshold":
            name = command.get("name")
            value = command.get("value")
            if name in self.thresholds:
                self.thresholds[name] = value
                return True
        elif action == "get_summary":
            return self.get_summary()

        return None

    def _check_contradiction(self, belief1: Belief, belief2: Belief) -> Optional[str]:
        """
        Check if two beliefs contradict each other.

        This is a simplified check - a full implementation would use
        logical inference.
        """
        # Check if propositions have conflicting values
        for key, value1 in belief1.proposition.items():
            if key in belief2.proposition:
                value2 = belief2.proposition[key]
                if value1 != value2 and isinstance(value1, bool):
                    return f"'{key}' is {value1} vs {value2}"

        # Check for explicit negation in content
        content1 = belief1.content.lower()
        content2 = belief2.content.lower()

        negation_patterns = [
            ("is ", "is not "),
            ("can ", "cannot "),
            ("will ", "will not "),
            ("does ", "does not ")
        ]

        for pos, neg in negation_patterns:
            if pos in content1 and neg in content2:
                return f"Possible negation: '{content1}' vs '{content2}'"
            if neg in content1 and pos in content2:
                return f"Possible negation: '{content1}' vs '{content2}'"

        return None

    def _report_issue(self, issue: Issue) -> None:
        """Report an issue and notify callbacks."""
        self.issues.append(issue)
        self.trace.add_step(
            "issue_detected",
            f"{issue.issue_type.name}: {issue.description}",
            confidence=issue.severity
        )
        for callback in self._issue_callbacks:
            try:
                callback(issue)
            except Exception:
                pass  # Don't let callback failures affect monitoring

    def get_active_issues(self) -> List[Issue]:
        """Get all unresolved issues."""
        return [i for i in self.issues if not i.resolved]

    def resolve_issue(self, issue_id: str) -> bool:
        """Mark an issue as resolved."""
        for issue in self.issues:
            if issue.id == issue_id:
                issue.resolved = True
                return True
        return False

    def on_issue(self, callback: Callable[[Issue], None]) -> None:
        """Register a callback for issue notifications."""
        self._issue_callbacks.append(callback)

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of monitoring status."""
        active_issues = self.get_active_issues()
        issue_counts = {}
        for issue in active_issues:
            issue_type = issue.issue_type.name
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1

        return {
            "total_issues_detected": len(self.issues),
            "active_issues": len(active_issues),
            "issues_by_type": issue_counts,
            "beliefs_tracked": len(self.beliefs),
            "reasoning_chains_analyzed": len(self.reasoning_chains),
            "state_snapshots": len(self.state_history)
        }

    def diagnose(self) -> str:
        """Generate a diagnostic report."""
        lines = ["Metacognitive Diagnostic Report"]
        lines.append("=" * 40)

        summary = self.get_summary()
        lines.append(f"\nBeliefs tracked: {summary['beliefs_tracked']}")
        lines.append(f"Reasoning chains analyzed: {summary['reasoning_chains_analyzed']}")
        lines.append(f"State snapshots: {summary['state_snapshots']}")

        lines.append(f"\nTotal issues detected: {summary['total_issues_detected']}")
        lines.append(f"Active issues: {summary['active_issues']}")

        if summary['issues_by_type']:
            lines.append("\nIssues by type:")
            for issue_type, count in summary['issues_by_type'].items():
                lines.append(f"  {issue_type}: {count}")

        active = self.get_active_issues()
        if active:
            lines.append("\nActive issues:")
            for issue in active[:5]:  # Show top 5
                lines.append(f"  [{issue.severity:.1f}] {issue.issue_type.name}")
                lines.append(f"       {issue.description}")

        return "\n".join(lines)
