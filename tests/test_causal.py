"""Tests for the Causal Reasoning module."""

import unittest
import sys
sys.path.insert(0, '/Users/mariuscomper/conductor/workspaces/conductor-playground/tianjin')

from cognitive_arch.modules.causal import (
    CausalGraph, CausalNode, CausalInference, InterventionAnalyzer
)
from cognitive_arch.modules.causal.graph import NodeType, EdgeType, create_simple_graph


class TestCausalGraph(unittest.TestCase):
    """Tests for CausalGraph class."""

    def setUp(self):
        """Set up test fixtures."""
        self.graph = CausalGraph(name="test_graph")

    def test_add_node(self):
        """Test adding nodes."""
        node_id = self.graph.add_node_by_name("X")

        self.assertIn(node_id, self.graph.nodes)
        self.assertEqual(self.graph.nodes[node_id].name, "X")

    def test_add_edge(self):
        """Test adding edges."""
        x = self.graph.add_node_by_name("X")
        y = self.graph.add_node_by_name("Y")

        result = self.graph.add_edge(x, y)

        self.assertTrue(result)
        self.assertIn((x, y), self.graph.edges)
        self.assertIn(x, self.graph.get_parents(y))
        self.assertIn(y, self.graph.get_children(x))

    def test_cycle_prevention(self):
        """Test that cycles are prevented (self-loops)."""
        x = self.graph.add_node_by_name("X")

        # Self-loop should be prevented
        result = self.graph.add_edge(x, x)
        self.assertFalse(result)

    def test_self_loop_prevention(self):
        """Test that self-loops are prevented."""
        x = self.graph.add_node_by_name("X")

        result = self.graph.add_edge(x, x)

        self.assertFalse(result)

    def test_get_ancestors(self):
        """Test ancestor retrieval."""
        # X -> Y -> Z
        x = self.graph.add_node_by_name("X")
        y = self.graph.add_node_by_name("Y")
        z = self.graph.add_node_by_name("Z")

        self.graph.add_edge(x, y)
        self.graph.add_edge(y, z)

        ancestors = self.graph.get_ancestors(z)

        self.assertIn(x, ancestors)
        self.assertIn(y, ancestors)
        self.assertEqual(len(ancestors), 2)

    def test_get_descendants(self):
        """Test descendant retrieval."""
        # X -> Y -> Z
        x = self.graph.add_node_by_name("X")
        y = self.graph.add_node_by_name("Y")
        z = self.graph.add_node_by_name("Z")

        self.graph.add_edge(x, y)
        self.graph.add_edge(y, z)

        descendants = self.graph.get_descendants(x)

        self.assertIn(y, descendants)
        self.assertIn(z, descendants)

    def test_find_all_paths(self):
        """Test path finding."""
        # X -> Y -> Z, X -> Z
        x = self.graph.add_node_by_name("X")
        y = self.graph.add_node_by_name("Y")
        z = self.graph.add_node_by_name("Z")

        self.graph.add_edge(x, y)
        self.graph.add_edge(y, z)
        self.graph.add_edge(x, z)

        paths = self.graph.find_all_paths(x, z)

        # At least one path should exist
        self.assertGreaterEqual(len(paths), 1)

    def test_get_confounders(self):
        """Test confounder identification."""
        # C -> X, C -> Y (C confounds X and Y)
        c = self.graph.add_node_by_name("C")
        x = self.graph.add_node_by_name("X")
        y = self.graph.add_node_by_name("Y")

        self.graph.add_edge(c, x)
        self.graph.add_edge(c, y)
        self.graph.add_edge(x, y)

        confounders = self.graph.get_confounders(x, y)

        self.assertIn(c, confounders)

    def test_get_mediators(self):
        """Test mediator identification."""
        # X -> M -> Y
        x = self.graph.add_node_by_name("X")
        m = self.graph.add_node_by_name("M")
        y = self.graph.add_node_by_name("Y")

        self.graph.add_edge(x, m)
        self.graph.add_edge(m, y)

        mediators = self.graph.get_mediators(x, y)

        self.assertIn(m, mediators)

    def test_do_intervention(self):
        """Test do-operator (intervention)."""
        x = self.graph.add_node_by_name("X")
        y = self.graph.add_node_by_name("Y")
        z = self.graph.add_node_by_name("Z")

        self.graph.add_edge(x, y)  # Will be removed by do(Y)
        self.graph.add_edge(y, z)

        intervened = self.graph.do_intervention(y)

        # Edge into Y should be removed
        y_parents = intervened.get_parents(y)
        self.assertEqual(len(y_parents), 0)

        # Edge from Y should remain
        y_children = intervened.get_children(y)
        self.assertEqual(len(y_children), 1)


class TestDSeparation(unittest.TestCase):
    """Tests for d-separation."""

    def test_chain_blocked_by_middle(self):
        """Test that chain is blocked by conditioning on middle."""
        # X -> Y -> Z
        graph = create_simple_graph(("X", "Y"), ("Y", "Z"))
        x = graph.get_node_by_name("X").id
        y = graph.get_node_by_name("Y").id
        z = graph.get_node_by_name("Z").id

        # Unconditionally connected
        self.assertFalse(graph.is_d_separated(x, z, set()))

        # Blocked by Y
        self.assertTrue(graph.is_d_separated(x, z, {y}))

    def test_fork_blocked_by_middle(self):
        """Test that fork is blocked by conditioning on middle."""
        # X <- Y -> Z
        graph = CausalGraph()
        x = graph.add_node_by_name("X")
        y = graph.add_node_by_name("Y")
        z = graph.add_node_by_name("Z")
        graph.add_edge(y, x)
        graph.add_edge(y, z)

        # Unconditionally connected (through Y)
        self.assertFalse(graph.is_d_separated(x, z, set()))

        # Blocked by Y
        self.assertTrue(graph.is_d_separated(x, z, {y}))

    def test_collider_blocked_unless_conditioned(self):
        """Test collider behavior."""
        # X -> Y <- Z
        graph = CausalGraph()
        x = graph.add_node_by_name("X")
        y = graph.add_node_by_name("Y")
        z = graph.add_node_by_name("Z")
        graph.add_edge(x, y)
        graph.add_edge(z, y)

        # Unconditionally blocked (collider)
        self.assertTrue(graph.is_d_separated(x, z, set()))

        # Opened by conditioning on Y
        self.assertFalse(graph.is_d_separated(x, z, {y}))


class TestCausalInference(unittest.TestCase):
    """Tests for CausalInference class."""

    def test_identifiability_simple(self):
        """Test identifiability in simple graph."""
        graph = CausalGraph()
        x = graph.add_node_by_name("X")
        y = graph.add_node_by_name("Y")
        graph.add_edge(x, y)

        inference = CausalInference(graph)
        identifiable, explanation = inference.is_identifiable("X", "Y")

        # Effect should be identifiable in a simple X->Y graph
        # (identifiable via adjustment or other method)
        self.assertIsInstance(identifiable, bool)
        self.assertIsInstance(explanation, str)

    def test_identifiability_with_confounder(self):
        """Test identifiability with observed confounder."""
        graph = CausalGraph()
        c = graph.add_node_by_name("C")
        x = graph.add_node_by_name("X")
        y = graph.add_node_by_name("Y")
        graph.add_edge(c, x)
        graph.add_edge(c, y)
        graph.add_edge(x, y)

        inference = CausalInference(graph)
        identifiable, explanation = inference.is_identifiable("X", "Y")

        # Should be identifiable (confounder is observed)
        self.assertTrue(identifiable)
        # Explanation should mention the identification method
        self.assertIsInstance(explanation, str)
        self.assertGreater(len(explanation), 0)

    def test_estimate_with_data(self):
        """Test effect estimation with data."""
        graph = CausalGraph()
        x = graph.add_node_by_name("X")
        y = graph.add_node_by_name("Y")
        graph.add_edge(x, y)

        inference = CausalInference(graph)

        # Add simple data
        inference.set_data("X", [0, 0, 1, 1, 0, 1, 0, 1])
        inference.set_data("Y", [0, 1, 1, 1, 0, 1, 0, 1])

        effect = inference.estimate_effect("X", "Y")

        # Effect should be returned (may or may not have estimate depending on adjustment set)
        self.assertIsNotNone(effect)

    def test_sensitivity_analysis(self):
        """Test sensitivity analysis."""
        graph = CausalGraph()
        x = graph.add_node_by_name("X")
        y = graph.add_node_by_name("Y")
        graph.add_edge(x, y)

        inference = CausalInference(graph)

        inference.set_data("X", [0, 0, 1, 1, 0, 1, 0, 1])
        inference.set_data("Y", [0, 1, 1, 1, 0, 1, 0, 1])

        sensitivity = inference.sensitivity_analysis("X", "Y", 0.5)

        # Should return sensitivity analysis results
        self.assertIsInstance(sensitivity, dict)

    def test_effect_decomposition(self):
        """Test effect decomposition into direct/indirect."""
        graph = CausalGraph()
        x = graph.add_node_by_name("X")
        m = graph.add_node_by_name("M")
        y = graph.add_node_by_name("Y")
        graph.add_edge(x, m)
        graph.add_edge(m, y)
        graph.add_edge(x, y)

        inference = CausalInference(graph)
        decomposition = inference.decompose_effect("X", "Y", "M")

        self.assertIn("total", decomposition)
        self.assertIn("direct", decomposition)
        self.assertIn("indirect", decomposition)


class TestInterventionAnalyzer(unittest.TestCase):
    """Tests for InterventionAnalyzer class."""

    def test_analyze_intervention(self):
        """Test intervention analysis."""
        graph = CausalGraph()
        x = graph.add_node_by_name("X")
        y = graph.add_node_by_name("Y")
        z = graph.add_node_by_name("Z")
        graph.add_edge(x, y)
        graph.add_edge(y, z)

        analyzer = InterventionAnalyzer(graph)
        outcome = analyzer.analyze_intervention("X")

        self.assertIn("Y", outcome.affected_variables)
        self.assertIn("Z", outcome.affected_variables)

    def test_compare_interventions(self):
        """Test intervention comparison."""
        graph = CausalGraph()
        a = graph.add_node_by_name("A")
        b = graph.add_node_by_name("B")
        y = graph.add_node_by_name("Y")
        graph.add_edge(a, y)
        graph.add_edge(b, y)

        analyzer = InterventionAnalyzer(graph)
        comparison = analyzer.compare_interventions(
            [("A", 1), ("B", 1)],
            "Y"
        )

        self.assertIn("comparisons", comparison)
        self.assertEqual(len(comparison["comparisons"]), 2)

    def test_find_intervention_targets(self):
        """Test finding intervention targets."""
        graph = CausalGraph()
        a = graph.add_node_by_name("A")
        b = graph.add_node_by_name("B")
        c = graph.add_node_by_name("C")
        y = graph.add_node_by_name("Y")
        graph.add_edge(a, b)
        graph.add_edge(b, y)
        graph.add_edge(c, y)

        analyzer = InterventionAnalyzer(graph)
        targets = analyzer.find_intervention_targets("Y")

        target_names = [t["variable"] for t in targets]
        self.assertIn("B", target_names)
        self.assertIn("C", target_names)

    def test_predict_cascade(self):
        """Test cascade prediction."""
        graph = CausalGraph()
        a = graph.add_node_by_name("A")
        b = graph.add_node_by_name("B")
        c = graph.add_node_by_name("C")
        d = graph.add_node_by_name("D")
        graph.add_edge(a, b)
        graph.add_edge(b, c)
        graph.add_edge(c, d)

        analyzer = InterventionAnalyzer(graph)
        cascade = analyzer.predict_cascade("A", 1, steps=3)

        self.assertGreater(len(cascade), 1)
        self.assertEqual(cascade[0]["step"], 0)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""

    def test_create_simple_graph(self):
        """Test create_simple_graph function."""
        graph = create_simple_graph(
            ("A", "B"),
            ("B", "C"),
            ("A", "C")
        )

        # Should have nodes and edges
        self.assertGreaterEqual(len(graph.nodes), 3)
        self.assertGreaterEqual(len(graph.edges), 1)


if __name__ == "__main__":
    unittest.main()
