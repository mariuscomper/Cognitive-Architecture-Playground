"""Tests for the Metacognition module."""

import unittest
import sys
sys.path.insert(0, '/Users/mariuscomper/conductor/workspaces/conductor-playground/tianjin')

from cognitive_arch.modules.metacognition import (
    MetacognitiveMonitor, ConfidenceTracker, ReflectionEngine
)
from cognitive_arch.modules.metacognition.monitor import CognitiveIssue, CognitiveState
from cognitive_arch.modules.metacognition.confidence import BayesianConfidenceUpdater
from cognitive_arch.modules.metacognition.reflection import ReasoningStrategy
from cognitive_arch.core.types import Belief, Thought


class TestConfidenceTracker(unittest.TestCase):
    """Tests for ConfidenceTracker class."""

    def setUp(self):
        """Set up test fixtures."""
        self.tracker = ConfidenceTracker()

    def test_record_judgment(self):
        """Test recording judgments."""
        jid = self.tracker.record_judgment("Test claim", 0.8, "test")

        self.assertIsNotNone(jid)
        self.assertEqual(len(self.tracker.records), 1)

    def test_record_outcome(self):
        """Test recording outcomes."""
        jid = self.tracker.record_judgment("Test claim", 0.8)
        self.tracker.record_outcome(jid, True)

        record = self.tracker.records[0]
        self.assertTrue(record.outcome)

    def test_calibration(self):
        """Test calibration computation."""
        # Record multiple judgments with outcomes
        for i in range(20):
            conf = (i % 10) / 10 + 0.05
            correct = i % 2 == 0
            jid = self.tracker.record_judgment(f"Claim {i}", conf)
            self.tracker.record_outcome(jid, correct)

        calibration = self.tracker.get_calibration()

        self.assertIsNotNone(calibration["calibration_error"])
        self.assertIn("bins", calibration)

    def test_bias_detection(self):
        """Test bias detection."""
        # Record overconfident judgments
        for i in range(10):
            jid = self.tracker.record_judgment(f"Claim {i}", 0.9)
            self.tracker.record_outcome(jid, i < 5)  # Only 50% correct

        bias = self.tracker.get_bias()

        self.assertEqual(bias["direction"], "overconfident")
        self.assertGreater(bias["magnitude"], 0)

    def test_suggest_adjustment(self):
        """Test confidence adjustment suggestions."""
        # Record biased judgments
        for i in range(10):
            jid = self.tracker.record_judgment(f"Claim {i}", 0.9, "test_domain")
            self.tracker.record_outcome(jid, i < 3)

        raw = 0.9
        adjusted = self.tracker.suggest_adjustment(raw, "test_domain")

        self.assertLess(adjusted, raw)

    def test_domain_reliability(self):
        """Test domain reliability tracking."""
        # Record judgments in a domain
        for i in range(10):
            jid = self.tracker.record_judgment(f"Claim {i}", 0.7, "reliable_domain")
            self.tracker.record_outcome(jid, True)  # All correct

        reliability = self.tracker.get_domain_reliability("reliable_domain")

        self.assertTrue(reliability["reliable"])
        self.assertEqual(reliability["accuracy"], 1.0)


class TestBayesianUpdater(unittest.TestCase):
    """Tests for BayesianConfidenceUpdater."""

    def test_update(self):
        """Test Bayesian update."""
        prior = 0.5
        likelihood_true = 0.9
        likelihood_false = 0.1

        posterior = BayesianConfidenceUpdater.update(
            prior, likelihood_true, likelihood_false
        )

        self.assertGreater(posterior, prior)

    def test_update_from_reliable_source(self):
        """Test update from a reliable source."""
        prior = 0.5

        posterior_true = BayesianConfidenceUpdater.update_from_source(
            prior, source_reliability=0.9, source_says_true=True
        )
        posterior_false = BayesianConfidenceUpdater.update_from_source(
            prior, source_reliability=0.9, source_says_true=False
        )

        self.assertGreater(posterior_true, prior)
        self.assertLess(posterior_false, prior)

    def test_combine_independent(self):
        """Test combining independent estimates."""
        confidences = [0.8, 0.7, 0.9]

        combined = BayesianConfidenceUpdater.combine_independent(confidences)

        # Combined should be higher than individual
        self.assertGreater(combined, max(confidences))


class TestMetacognitiveMonitor(unittest.TestCase):
    """Tests for MetacognitiveMonitor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = MetacognitiveMonitor()

    def test_record_belief(self):
        """Test recording beliefs."""
        belief = Belief(content="Test belief", confidence=0.8)
        issues = self.monitor.record_belief(belief)

        self.assertIn(belief.id, self.monitor.beliefs)
        self.assertIsInstance(issues, list)

    def test_detect_contradiction(self):
        """Test contradiction detection."""
        belief1 = Belief(
            content="The door is open",
            proposition={"door_open": True}
        )
        belief2 = Belief(
            content="The door is not open",
            proposition={"door_open": False}
        )

        self.monitor.record_belief(belief1)
        issues = self.monitor.record_belief(belief2)

        contradiction_found = any(
            i.issue_type == CognitiveIssue.CONTRADICTION
            for i in issues
        )
        self.assertTrue(contradiction_found)

    def test_detect_low_confidence(self):
        """Test low confidence detection."""
        belief = Belief(content="Uncertain claim", confidence=0.1)
        issues = self.monitor.record_belief(belief)

        low_conf_found = any(
            i.issue_type == CognitiveIssue.LOW_CONFIDENCE
            for i in issues
        )
        self.assertTrue(low_conf_found)

    def test_detect_circular_reasoning(self):
        """Test circular reasoning detection."""
        chain = ["Step A", "Step B", "Step C", "Step A"]  # Circular!

        issues = self.monitor.record_reasoning_chain(chain)

        circular_found = any(
            i.issue_type == CognitiveIssue.CIRCULAR_REASONING
            for i in issues
        )
        self.assertTrue(circular_found)

    def test_detect_excessive_depth(self):
        """Test excessive reasoning depth detection."""
        chain = [f"Step {i}" for i in range(20)]

        issues = self.monitor.record_reasoning_chain(chain)

        depth_issue = any(
            i.issue_type == CognitiveIssue.RESOURCE_EXHAUSTION
            for i in issues
        )
        self.assertTrue(depth_issue)

    def test_record_state(self):
        """Test cognitive state recording."""
        state = CognitiveState(
            working_memory_load=0.95,
            average_confidence=0.3
        )

        issues = self.monitor.record_state(state)

        self.assertGreater(len(self.monitor.state_history), 0)

    def test_resolve_issue(self):
        """Test issue resolution."""
        belief = Belief(content="Uncertain", confidence=0.1)
        issues = self.monitor.record_belief(belief)

        if issues:
            issue_id = issues[0].id
            result = self.monitor.resolve_issue(issue_id)
            self.assertTrue(result)

            active = self.monitor.get_active_issues()
            resolved_in_active = any(i.id == issue_id for i in active)
            self.assertFalse(resolved_in_active)


class TestReflectionEngine(unittest.TestCase):
    """Tests for ReflectionEngine class."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = ReflectionEngine()

    def test_start_episode(self):
        """Test starting a reasoning episode."""
        episode = self.engine.start_episode(
            "Solve the puzzle",
            ReasoningStrategy.DECOMPOSITION
        )

        self.assertEqual(episode.problem_description, "Solve the puzzle")
        self.assertEqual(episode.strategy_used, ReasoningStrategy.DECOMPOSITION)

    def test_complete_episode(self):
        """Test completing a reasoning episode."""
        episode = self.engine.start_episode("Test problem")

        self.engine.complete_episode(
            episode,
            outcome="success",
            success=True,
            confidence=0.9
        )

        self.assertTrue(episode.success)
        self.assertIsNotNone(episode.completed_at)
        self.assertGreater(len(episode.lessons), 0)

    def test_strategy_recommendation(self):
        """Test strategy recommendation."""
        # Record some episodes
        for i in range(5):
            ep = self.engine.start_episode(f"Problem {i}", ReasoningStrategy.ANALYTICAL)
            self.engine.complete_episode(ep, "success", True, 0.8)

        strategy, explanation = self.engine.recommend_strategy("new problem")

        self.assertIsInstance(strategy, ReasoningStrategy)
        self.assertIsInstance(explanation, str)

    def test_reasoning_quality_assessment(self):
        """Test reasoning quality assessment."""
        episode = self.engine.start_episode("Test")

        thought1 = Thought(content="Observation", thought_type="observation")
        thought2 = Thought(
            content="Inference",
            thought_type="inference",
            parent_thoughts=[thought1.id]
        )
        thought3 = Thought(
            content="Conclusion",
            thought_type="conclusion",
            parent_thoughts=[thought2.id]
        )

        self.engine.add_step(episode, thought1)
        self.engine.add_step(episode, thought2)
        self.engine.add_step(episode, thought3)

        self.engine.complete_episode(episode, "success", True, 0.8)

        quality = self.engine.assess_reasoning_quality(episode)

        self.assertIn("coherence", quality)
        self.assertIn("depth", quality)
        self.assertIn("overall_quality", quality)

    def test_explain_reasoning(self):
        """Test reasoning explanation generation."""
        episode = self.engine.start_episode("Test", ReasoningStrategy.ANALYTICAL)
        thought = Thought(content="Test thought", thought_type="observation")
        self.engine.add_step(episode, thought)
        self.engine.complete_episode(episode, "success", True, 0.8)

        explanation = self.engine.explain_reasoning(episode)

        self.assertIn("Reasoning Explanation", explanation)
        self.assertIn("ANALYTICAL", explanation)

    def test_failure_reflection(self):
        """Test reflection on failures."""
        # Record some failures
        for i in range(3):
            ep = self.engine.start_episode(f"Failed problem {i}", ReasoningStrategy.HEURISTIC)
            self.engine.complete_episode(ep, "failure", False, 0.9)

        patterns = self.engine.reflect_on_failures()

        self.assertGreater(len(patterns), 0)


if __name__ == "__main__":
    unittest.main()
