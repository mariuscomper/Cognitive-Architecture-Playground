"""
Reflection engine for metacognition.

This module enables the system to reflect on its own reasoning processes,
generate explanations, and improve future performance.

Key capabilities:
- Explanation generation
- Reasoning quality assessment
- Strategy selection
- Learning from experience
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime
from enum import Enum, auto
import uuid

from ...core.types import ReasoningTrace, Thought, Belief


class ReasoningStrategy(Enum):
    """Different strategies for approaching problems."""
    ANALYTICAL = auto()      # Step-by-step logical analysis
    ANALOGICAL = auto()      # Find similar solved problems
    HEURISTIC = auto()       # Use rules of thumb
    DECOMPOSITION = auto()   # Break into sub-problems
    GENERATE_TEST = auto()   # Generate hypotheses and test
    CONSTRAINT = auto()      # Work from constraints
    MEANS_ENDS = auto()      # Reduce difference from goal


@dataclass
class ReasoningEpisode:
    """A record of a complete reasoning episode."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    problem_description: str = ""
    strategy_used: ReasoningStrategy = ReasoningStrategy.ANALYTICAL
    steps: List[Thought] = field(default_factory=list)
    outcome: str = ""  # success, failure, partial, abandoned
    success: Optional[bool] = None
    duration_seconds: float = 0.0
    confidence: float = 0.5
    lessons: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class ReflectionEngine:
    """
    Enables reflection on reasoning processes.

    The reflection engine:
    - Records reasoning episodes
    - Assesses reasoning quality
    - Generates explanations
    - Recommends strategies
    - Extracts lessons learned
    """

    def __init__(self):
        self.episodes: List[ReasoningEpisode] = []
        self.strategy_performance: Dict[ReasoningStrategy, Dict[str, Any]] = {
            s: {"successes": 0, "failures": 0, "total_confidence": 0.0}
            for s in ReasoningStrategy
        }
        self.lessons_learned: List[Dict[str, Any]] = []

    def start_episode(self, problem: str,
                     strategy: ReasoningStrategy = ReasoningStrategy.ANALYTICAL
                     ) -> ReasoningEpisode:
        """Start recording a new reasoning episode."""
        episode = ReasoningEpisode(
            problem_description=problem,
            strategy_used=strategy
        )
        self.episodes.append(episode)
        return episode

    def add_step(self, episode: ReasoningEpisode, thought: Thought) -> None:
        """Add a reasoning step to an episode."""
        episode.steps.append(thought)

    def complete_episode(self, episode: ReasoningEpisode,
                        outcome: str, success: bool,
                        confidence: float = 0.5) -> None:
        """Complete a reasoning episode and update performance stats."""
        episode.outcome = outcome
        episode.success = success
        episode.confidence = confidence
        episode.completed_at = datetime.now()
        episode.duration_seconds = (
            episode.completed_at - episode.started_at
        ).total_seconds()

        # Update strategy performance
        stats = self.strategy_performance[episode.strategy_used]
        if success:
            stats["successes"] += 1
        else:
            stats["failures"] += 1
        stats["total_confidence"] += confidence

        # Extract lessons
        lessons = self._extract_lessons(episode)
        episode.lessons = lessons
        for lesson in lessons:
            self.lessons_learned.append({
                "lesson": lesson,
                "episode_id": episode.id,
                "strategy": episode.strategy_used.name,
                "learned_at": datetime.now().isoformat()
            })

    def _extract_lessons(self, episode: ReasoningEpisode) -> List[str]:
        """Extract lessons from a completed episode."""
        lessons = []

        # Lesson from success/failure
        if episode.success:
            lessons.append(
                f"Strategy {episode.strategy_used.name} worked for: {episode.problem_description[:50]}"
            )
        else:
            lessons.append(
                f"Strategy {episode.strategy_used.name} failed for: {episode.problem_description[:50]}"
            )

        # Lesson from step count
        step_count = len(episode.steps)
        if step_count > 10:
            lessons.append(
                f"Complex problem required {step_count} steps - consider decomposition"
            )
        elif step_count < 3 and not episode.success:
            lessons.append(
                "Quick failure - problem may need more thorough analysis"
            )

        # Lesson from confidence
        if episode.confidence < 0.3:
            lessons.append(
                "Low confidence outcome - consider gathering more evidence"
            )
        elif episode.confidence > 0.9 and not episode.success:
            lessons.append(
                "Overconfident failure - calibration may be off"
            )

        return lessons

    def recommend_strategy(self, problem_type: str,
                          context: Optional[Dict[str, Any]] = None
                          ) -> Tuple[ReasoningStrategy, str]:
        """
        Recommend a reasoning strategy based on past performance.

        Args:
            problem_type: Description of the problem type
            context: Additional context

        Returns:
            Recommended strategy and explanation
        """
        # Calculate success rates for each strategy
        strategy_scores = {}
        for strategy, stats in self.strategy_performance.items():
            total = stats["successes"] + stats["failures"]
            if total > 0:
                success_rate = stats["successes"] / total
                avg_confidence = stats["total_confidence"] / total
                # Score combines success rate and confidence
                strategy_scores[strategy] = (success_rate * 0.7 + avg_confidence * 0.3)
            else:
                strategy_scores[strategy] = 0.5  # Default for untried strategies

        # Apply heuristics based on problem type keywords
        problem_lower = problem_type.lower()

        if "compare" in problem_lower or "similar" in problem_lower:
            strategy_scores[ReasoningStrategy.ANALOGICAL] += 0.2
        if "break" in problem_lower or "parts" in problem_lower:
            strategy_scores[ReasoningStrategy.DECOMPOSITION] += 0.2
        if "quick" in problem_lower or "fast" in problem_lower:
            strategy_scores[ReasoningStrategy.HEURISTIC] += 0.2
        if "test" in problem_lower or "verify" in problem_lower:
            strategy_scores[ReasoningStrategy.GENERATE_TEST] += 0.2
        if "limit" in problem_lower or "constraint" in problem_lower:
            strategy_scores[ReasoningStrategy.CONSTRAINT] += 0.2
        if "goal" in problem_lower or "achieve" in problem_lower:
            strategy_scores[ReasoningStrategy.MEANS_ENDS] += 0.2

        # Select best strategy
        best_strategy = max(strategy_scores.items(), key=lambda x: x[1])
        strategy = best_strategy[0]
        score = best_strategy[1]

        # Generate explanation
        stats = self.strategy_performance[strategy]
        total = stats["successes"] + stats["failures"]
        if total > 0:
            success_rate = stats["successes"] / total
            explanation = (
                f"Recommending {strategy.name} based on {success_rate:.1%} success rate "
                f"across {total} past episodes"
            )
        else:
            explanation = f"Recommending {strategy.name} as a default for this problem type"

        return strategy, explanation

    def explain_reasoning(self, episode: ReasoningEpisode) -> str:
        """Generate an explanation of the reasoning in an episode."""
        lines = [f"Reasoning Explanation for: {episode.problem_description}"]
        lines.append(f"Strategy used: {episode.strategy_used.name}")
        lines.append("")

        for i, step in enumerate(episode.steps, 1):
            confidence_str = f"[{step.confidence:.0%}]" if step.confidence else ""
            lines.append(f"{i}. {step.thought_type.upper()}: {step.content} {confidence_str}")

            if step.parent_thoughts:
                lines.append(f"   (follows from: {', '.join(step.parent_thoughts[:2])})")

        lines.append("")
        lines.append(f"Outcome: {episode.outcome}")
        lines.append(f"Final confidence: {episode.confidence:.0%}")

        if episode.lessons:
            lines.append("")
            lines.append("Lessons learned:")
            for lesson in episode.lessons:
                lines.append(f"  - {lesson}")

        return "\n".join(lines)

    def assess_reasoning_quality(self, episode: ReasoningEpisode) -> Dict[str, Any]:
        """
        Assess the quality of reasoning in an episode.

        Returns metrics on:
        - Coherence: How well steps connect
        - Depth: How thorough the analysis
        - Efficiency: Steps vs. problem complexity
        - Confidence calibration: Match between confidence and outcome
        """
        metrics = {}

        # Coherence: Check step connections
        connected_steps = sum(1 for s in episode.steps if s.parent_thoughts)
        total_steps = len(episode.steps)
        metrics["coherence"] = connected_steps / total_steps if total_steps > 0 else 0

        # Depth: Count inference steps
        inference_steps = sum(1 for s in episode.steps if s.thought_type == "inference")
        metrics["depth"] = min(inference_steps / 3, 1.0)  # Normalize to 3 being "deep"

        # Efficiency: Inverse of step count for successful episodes
        if episode.success:
            metrics["efficiency"] = max(0, 1 - (total_steps / 20))
        else:
            metrics["efficiency"] = 0

        # Confidence calibration
        if episode.success is not None:
            expected = episode.confidence
            actual = 1.0 if episode.success else 0.0
            metrics["calibration"] = 1 - abs(expected - actual)
        else:
            metrics["calibration"] = None

        # Overall quality score
        valid_metrics = [v for v in metrics.values() if v is not None]
        metrics["overall_quality"] = sum(valid_metrics) / len(valid_metrics) if valid_metrics else 0

        return metrics

    def get_strategy_report(self) -> str:
        """Generate a report on strategy performance."""
        lines = ["Strategy Performance Report"]
        lines.append("=" * 40)

        for strategy, stats in self.strategy_performance.items():
            total = stats["successes"] + stats["failures"]
            if total > 0:
                success_rate = stats["successes"] / total
                avg_confidence = stats["total_confidence"] / total
                lines.append(f"\n{strategy.name}:")
                lines.append(f"  Episodes: {total}")
                lines.append(f"  Success rate: {success_rate:.1%}")
                lines.append(f"  Avg confidence: {avg_confidence:.1%}")
            else:
                lines.append(f"\n{strategy.name}: (no data)")

        return "\n".join(lines)

    def get_lessons_summary(self, max_lessons: int = 10) -> str:
        """Get a summary of lessons learned."""
        lines = ["Lessons Learned Summary"]
        lines.append("-" * 30)

        recent_lessons = self.lessons_learned[-max_lessons:]
        for lesson_info in recent_lessons:
            lines.append(f"- {lesson_info['lesson']}")
            lines.append(f"  (from {lesson_info['strategy']} episode)")

        return "\n".join(lines)

    def find_similar_episodes(self, problem: str, n: int = 3) -> List[ReasoningEpisode]:
        """Find past episodes with similar problems."""
        # Simple keyword matching - could be enhanced with embeddings
        problem_words = set(problem.lower().split())

        scored_episodes = []
        for episode in self.episodes:
            if episode.completed_at is None:
                continue
            episode_words = set(episode.problem_description.lower().split())
            overlap = len(problem_words & episode_words)
            if overlap > 0:
                score = overlap / max(len(problem_words), len(episode_words))
                scored_episodes.append((score, episode))

        scored_episodes.sort(key=lambda x: x[0], reverse=True)
        return [ep for _, ep in scored_episodes[:n]]

    def reflect_on_failures(self) -> List[Dict[str, Any]]:
        """Analyze failure patterns to identify systematic issues."""
        failures = [e for e in self.episodes if e.success is False]

        if not failures:
            return []

        patterns = []

        # Group by strategy
        by_strategy = {}
        for ep in failures:
            if ep.strategy_used not in by_strategy:
                by_strategy[ep.strategy_used] = []
            by_strategy[ep.strategy_used].append(ep)

        for strategy, episodes in by_strategy.items():
            if len(episodes) >= 2:
                patterns.append({
                    "pattern": f"Multiple failures with {strategy.name}",
                    "count": len(episodes),
                    "suggestion": f"Consider alternative to {strategy.name} for similar problems"
                })

        # Check for overconfident failures
        overconfident = [e for e in failures if e.confidence > 0.7]
        if overconfident:
            patterns.append({
                "pattern": "Overconfident failures",
                "count": len(overconfident),
                "suggestion": "Calibrate confidence downward for similar situations"
            })

        # Check for quick failures (few steps)
        quick_failures = [e for e in failures if len(e.steps) < 3]
        if quick_failures:
            patterns.append({
                "pattern": "Quick failures (insufficient analysis)",
                "count": len(quick_failures),
                "suggestion": "Ensure thorough analysis before concluding"
            })

        return patterns

    def summary(self) -> str:
        """Generate a summary of reflection engine state."""
        lines = ["Reflection Engine Summary"]
        lines.append("-" * 30)

        total_episodes = len(self.episodes)
        completed = len([e for e in self.episodes if e.completed_at])
        successes = len([e for e in self.episodes if e.success])

        lines.append(f"Total episodes: {total_episodes}")
        lines.append(f"Completed: {completed}")
        if completed > 0:
            lines.append(f"Success rate: {successes/completed:.1%}")

        lines.append(f"\nLessons learned: {len(self.lessons_learned)}")

        # Best performing strategy
        best = max(
            self.strategy_performance.items(),
            key=lambda x: x[1]["successes"] / max(x[1]["successes"] + x[1]["failures"], 1)
        )
        if best[1]["successes"] + best[1]["failures"] > 0:
            lines.append(f"Best strategy: {best[0].name}")

        return "\n".join(lines)
