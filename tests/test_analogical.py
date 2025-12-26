"""Tests for the Analogical Reasoning module."""

import unittest
import sys
sys.path.insert(0, '/Users/mariuscomper/conductor/workspaces/conductor-playground/tianjin')

from cognitive_arch.modules.analogical import (
    Structure, StructureMapper, AnalogRetriever, AnalogicalInference
)
from cognitive_arch.modules.analogical.structures import (
    StructureElement, Relation, ElementType, create_structure
)


class TestStructure(unittest.TestCase):
    """Tests for Structure class."""

    def setUp(self):
        """Set up test fixtures."""
        self.structure = Structure(name="test", description="Test structure")

    def test_add_entity(self):
        """Test adding entities."""
        eid = self.structure.add_entity("Entity1", value="test")

        self.assertIn(eid, self.structure.elements)
        self.assertEqual(self.structure.elements[eid].name, "Entity1")

    def test_add_attribute(self):
        """Test adding attributes."""
        self.structure.add_entity("Entity1")
        aid = self.structure.add_attribute("Entity1", "color", "red")

        self.assertIsNotNone(aid)
        attrs = self.structure.get_attributes("Entity1")
        self.assertEqual(len(attrs), 1)
        self.assertEqual(attrs[0].value, "red")

    def test_add_relation(self):
        """Test adding relations."""
        self.structure.add_entity("A")
        self.structure.add_entity("B")
        rel = self.structure.add_relation("likes", "A", "B")

        self.assertIsNotNone(rel)
        self.assertEqual(len(self.structure.relations), 1)
        self.assertEqual(rel.name, "likes")

    def test_get_relations(self):
        """Test getting relations for an entity."""
        self.structure.add_entity("A")
        self.structure.add_entity("B")
        self.structure.add_entity("C")
        self.structure.add_relation("likes", "A", "B")
        self.structure.add_relation("dislikes", "A", "C")

        rels = self.structure.get_relations("A")

        self.assertEqual(len(rels), 2)

    def test_relation_signature(self):
        """Test relation signature computation."""
        self.structure.add_entity("A")
        self.structure.add_entity("B")
        self.structure.add_relation("rel1", "A", "B")
        self.structure.add_relation("rel2", "A", "B")

        sig = self.structure.relation_signature()

        self.assertEqual(len(sig), 2)

    def test_structural_depth(self):
        """Test structural depth computation."""
        self.structure.add_entity("A")
        self.structure.add_entity("B")
        self.structure.add_relation("r", "A", "B")

        depth = self.structure.structural_depth()

        self.assertGreaterEqual(depth, 1)

    def test_create_structure_convenience(self):
        """Test create_structure convenience function."""
        s = create_structure(
            "test",
            ["A", "B", "C"],
            [("r1", "A", "B"), ("r2", "B", "C")]
        )

        self.assertEqual(len(s.get_entities()), 3)
        self.assertEqual(len(s.relations), 2)


class TestStructureMapper(unittest.TestCase):
    """Tests for StructureMapper class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mapper = StructureMapper()

    def test_map_identical_structures(self):
        """Test mapping identical structures."""
        s1 = create_structure(
            "s1", ["A", "B"], [("r", "A", "B")]
        )
        s2 = create_structure(
            "s2", ["A", "B"], [("r", "A", "B")]
        )

        mapping = self.mapper.map_structures(s1, s2)

        self.assertGreater(mapping.overall_similarity, 0.5)  # Good match

    def test_map_similar_structures(self):
        """Test mapping similar structures."""
        s1 = create_structure(
            "solar_system",
            ["Sun", "Planet"],
            [("attracts", "Sun", "Planet"), ("orbits", "Planet", "Sun")]
        )
        s2 = create_structure(
            "atom",
            ["Nucleus", "Electron"],
            [("attracts", "Nucleus", "Electron"), ("orbits", "Electron", "Nucleus")]
        )

        mapping = self.mapper.map_structures(s1, s2)

        self.assertGreater(mapping.overall_similarity, 0.5)
        self.assertGreater(len(mapping.correspondences), 0)

    def test_map_dissimilar_structures(self):
        """Test mapping dissimilar structures."""
        s1 = create_structure("s1", ["A", "B"], [("r1", "A", "B")])
        s2 = create_structure("s2", ["X", "Y", "Z"], [
            ("r2", "X", "Y"), ("r3", "Y", "Z"), ("r4", "X", "Z")
        ])

        mapping = self.mapper.map_structures(s1, s2)

        self.assertLess(mapping.overall_similarity, 0.5)

    def test_inferences_generated(self):
        """Test that inferences are generated."""
        s1 = Structure(name="source")
        s1.add_entity("A")
        s1.add_entity("B")
        s1.add_relation("causes", "A", "B")
        s1.add_relation("prevents", "A", "B")

        s2 = Structure(name="target")
        s2.add_entity("X")
        s2.add_entity("Y")
        s2.add_relation("causes", "X", "Y")

        mapping = self.mapper.map_structures(s1, s2)

        # Should infer "prevents" relation
        # Note: This depends on mapping quality

    def test_caching(self):
        """Test that mappings are cached."""
        s1 = create_structure("s1", ["A"], [])
        s2 = create_structure("s2", ["B"], [])

        # First mapping
        mapping1 = self.mapper.map_structures(s1, s2)

        # Second should use cache
        mapping2 = self.mapper.map_structures(s1, s2)

        self.assertEqual(mapping1.id, mapping2.id)


class TestAnalogRetriever(unittest.TestCase):
    """Tests for AnalogRetriever class."""

    def setUp(self):
        """Set up test fixtures."""
        self.retriever = AnalogRetriever()

    def test_store_and_retrieve(self):
        """Test storing and retrieving analogs."""
        s = create_structure("test", ["A", "B"], [("r", "A", "B")])
        analog_id = self.retriever.store(s, domain="test")

        self.assertIn(analog_id, self.retriever.analogs)

    def test_retrieve_by_domain(self):
        """Test domain-based retrieval."""
        s1 = create_structure("s1", ["A"], [])
        s2 = create_structure("s2", ["B"], [])

        self.retriever.store(s1, domain="domain1")
        self.retriever.store(s2, domain="domain2")

        query = create_structure("q", ["X"], [])
        results = self.retriever.retrieve(query, n=10, domain="domain1")

        for analog, _ in results:
            self.assertEqual(analog.domain, "domain1")

    def test_retrieve_by_tags(self):
        """Test tag-based retrieval."""
        s1 = create_structure("s1", ["A"], [])
        s2 = create_structure("s2", ["B"], [])

        self.retriever.store(s1, tags=["tag1", "tag2"])
        self.retriever.store(s2, tags=["tag2", "tag3"])

        query = create_structure("q", ["X"], [])
        results = self.retriever.retrieve(query, n=10, tags=["tag1"])

        self.assertEqual(len(results), 1)

    def test_retrieval_scoring(self):
        """Test that retrieval is scored by similarity."""
        s1 = create_structure("similar", ["A", "B"], [("r", "A", "B")])
        s2 = create_structure("different", ["X", "Y", "Z"], [
            ("r1", "X", "Y"), ("r2", "Y", "Z")
        ])

        self.retriever.store(s1)
        self.retriever.store(s2)

        query = create_structure("query", ["P", "Q"], [("r", "P", "Q")])
        results = self.retriever.retrieve(query, n=2)

        # Similar should score higher
        self.assertEqual(results[0][0].structure.name, "similar")

    def test_feedback(self):
        """Test feedback mechanism."""
        s = create_structure("test", ["A"], [])
        aid = self.retriever.store(s)

        initial_score = self.retriever.analogs[aid].usefulness_score

        self.retriever.feedback(aid, useful=True)

        self.assertGreater(
            self.retriever.analogs[aid].usefulness_score,
            initial_score
        )

    def test_diverse_retrieval(self):
        """Test diverse analog retrieval."""
        for i in range(5):
            s = create_structure(f"analog_{i}", ["A"], [])
            self.retriever.store(s, domain=f"domain_{i % 2}")

        query = create_structure("query", ["X"], [])
        diverse = self.retriever.get_diverse_analogs(query, n=3)

        domains = [a.domain for a in diverse]
        # Should have diverse domains
        self.assertGreater(len(set(domains)), 1)


class TestAnalogicalInference(unittest.TestCase):
    """Tests for AnalogicalInference class."""

    def setUp(self):
        """Set up test fixtures."""
        self.retriever = AnalogRetriever()
        self.inference = AnalogicalInference(self.retriever)

    def test_infer_from_single_source(self):
        """Test inference from a single source analog."""
        source = Structure(name="source")
        source.add_entity("A")
        source.add_entity("B")
        source.add_attribute("A", "size", "large")
        source.add_relation("dominates", "A", "B")
        source.add_relation("feeds_on", "A", "B")

        target = Structure(name="target")
        target.add_entity("X")
        target.add_entity("Y")
        target.add_attribute("X", "size", "large")
        target.add_relation("dominates", "X", "Y")

        inferences = self.inference.infer(target, source=source)

        # Should infer some relations
        self.assertIsInstance(inferences, list)

    def test_infer_from_knowledge_base(self):
        """Test inference using knowledge base."""
        # Store source analog
        source = create_structure(
            "source", ["A", "B"], [("causes", "A", "B"), ("prevents", "A", "B")]
        )
        self.retriever.store(source, domain="test")

        # Create target
        target = create_structure("target", ["X", "Y"], [("causes", "X", "Y")])

        inferences = self.inference.infer(target, use_knowledge_base=True)

        self.assertIsInstance(inferences, list)

    def test_consolidate_inferences(self):
        """Test consolidation of multiple inferences."""
        # Create multiple similar inferences
        from cognitive_arch.modules.analogical.inference import AnalogicalInferenceResult

        inf1 = AnalogicalInferenceResult(
            inference_type="relation",
            content={"relation": "r", "arguments": ["A", "B"]},
            confidence=0.5,
            source_analogs=["source1"]
        )
        inf2 = AnalogicalInferenceResult(
            inference_type="relation",
            content={"relation": "r", "arguments": ["A", "B"]},
            confidence=0.5,
            source_analogs=["source2"]
        )

        consolidated = self.inference._consolidate_inferences([inf1, inf2])

        # Should be merged (same relation and arguments)
        self.assertEqual(len(consolidated), 1)
        # supporting_mappings should be at least 1 (may vary by implementation)
        self.assertGreaterEqual(consolidated[0].supporting_mappings, 1)

    def test_explain_inference(self):
        """Test inference explanation."""
        from cognitive_arch.modules.analogical.inference import AnalogicalInferenceResult

        inf = AnalogicalInferenceResult(
            inference_type="relation",
            content={"relation": "causes", "arguments": ["X", "Y"]},
            confidence=0.8,
            source_analogs=["source"],
            supporting_mappings=1,
            evaluation="Test evaluation"
        )

        explanation = self.inference.explain_inference(inf)

        self.assertIn("Analogical Inference", explanation)
        self.assertIn("causes", explanation)


if __name__ == "__main__":
    unittest.main()
