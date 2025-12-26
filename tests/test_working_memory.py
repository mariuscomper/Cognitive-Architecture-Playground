"""Tests for the Working Memory module."""

import unittest
import time
from datetime import datetime

import sys
sys.path.insert(0, '/Users/mariuscomper/conductor/workspaces/conductor-playground/tianjin')

from cognitive_arch.modules.working_memory import WorkingMemory, Chunk, ChunkType
from cognitive_arch.modules.working_memory.chunks import create_fact, create_goal, create_hypothesis


class TestChunk(unittest.TestCase):
    """Tests for Chunk class."""

    def test_chunk_creation(self):
        """Test basic chunk creation."""
        chunk = Chunk(
            chunk_type=ChunkType.FACT,
            name="test_chunk",
            slots={"key": "value"}
        )

        self.assertEqual(chunk.chunk_type, ChunkType.FACT)
        self.assertEqual(chunk.name, "test_chunk")
        self.assertEqual(chunk.slots["key"], "value")

    def test_chunk_activation(self):
        """Test activation updates."""
        chunk = Chunk(name="test")
        initial_activation = chunk.activation

        chunk.access()

        self.assertGreater(chunk.activation, initial_activation)
        self.assertEqual(chunk.access_count, 1)

    def test_chunk_matching(self):
        """Test pattern matching."""
        chunk = Chunk(
            name="test",
            slots={"color": "red", "size": "large"}
        )

        self.assertTrue(chunk.matches({"color": "red"}))
        self.assertTrue(chunk.matches({"color": "red", "size": "large"}))
        self.assertFalse(chunk.matches({"color": "blue"}))
        self.assertTrue(chunk.matches({"color": None}))  # None matches anything

    def test_chunk_similarity(self):
        """Test similarity computation."""
        chunk1 = Chunk(
            chunk_type=ChunkType.FACT,
            name="chunk1",
            slots={"a": 1, "b": 2}
        )
        chunk2 = Chunk(
            chunk_type=ChunkType.FACT,
            name="chunk2",
            slots={"a": 1, "b": 3}
        )
        chunk3 = Chunk(
            chunk_type=ChunkType.GOAL,
            name="chunk3",
            slots={"c": 4}
        )

        sim_12 = chunk1.similarity(chunk2)
        sim_13 = chunk1.similarity(chunk3)

        self.assertGreater(sim_12, sim_13)  # Same type should be more similar

    def test_chunk_linking(self):
        """Test chunk linking."""
        chunk1 = Chunk(name="chunk1")
        chunk2 = Chunk(name="chunk2")

        chunk1.link_to(chunk2)

        self.assertIn(chunk2.id, chunk1.linked_chunks)
        self.assertIn(chunk1.id, chunk2.linked_chunks)

        chunk1.unlink_from(chunk2)

        self.assertNotIn(chunk2.id, chunk1.linked_chunks)
        self.assertNotIn(chunk1.id, chunk2.linked_chunks)

    def test_create_convenience_functions(self):
        """Test convenience functions for chunk creation."""
        fact = create_fact("My fact", key="value")
        self.assertEqual(fact.chunk_type, ChunkType.FACT)
        self.assertEqual(fact.slots["key"], "value")

        goal = create_goal("My goal", "Description", priority=1)
        self.assertEqual(goal.chunk_type, ChunkType.GOAL)
        self.assertEqual(goal.slots["priority"], 1)

        hyp = create_hypothesis("My hypothesis", "Proposition", 0.8)
        self.assertEqual(hyp.chunk_type, ChunkType.HYPOTHESIS)
        self.assertEqual(hyp.confidence, 0.8)


class TestWorkingMemory(unittest.TestCase):
    """Tests for WorkingMemory class."""

    def setUp(self):
        """Set up test fixtures."""
        self.wm = WorkingMemory(capacity=5)

    def test_store_and_retrieve(self):
        """Test basic store and retrieve."""
        chunk = create_fact("Test fact")
        chunk_id = self.wm.store(chunk)

        retrieved = self.wm.retrieve(chunk_id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test fact")

    def test_capacity_limit(self):
        """Test that capacity is enforced."""
        for i in range(10):
            chunk = create_fact(f"Fact {i}")
            self.wm.store(chunk)

        self.assertLessEqual(len(self.wm.chunks), self.wm.capacity)
        self.assertGreater(self.wm.stats["evictions"], 0)

    def test_query_by_pattern(self):
        """Test pattern-based querying."""
        self.wm.store(create_fact("Red apple", color="red", type="fruit"))
        self.wm.store(create_fact("Green apple", color="green", type="fruit"))
        self.wm.store(create_fact("Red car", color="red", type="vehicle"))

        red_things = self.wm.query({"color": "red"})
        fruits = self.wm.query({"type": "fruit"})

        self.assertEqual(len(red_things), 2)
        self.assertEqual(len(fruits), 2)

    def test_query_by_type(self):
        """Test type-based querying."""
        self.wm.store(create_fact("Fact"))
        self.wm.store(create_goal("Goal", "Do something"))
        self.wm.store(create_hypothesis("Hypothesis", "Maybe", 0.5))

        facts = self.wm.get_by_type(ChunkType.FACT)
        goals = self.wm.get_goals()
        hypotheses = self.wm.get_hypotheses()

        self.assertEqual(len(facts), 1)
        self.assertEqual(len(goals), 1)
        self.assertEqual(len(hypotheses), 1)

    def test_search(self):
        """Test text-based search."""
        self.wm.store(create_fact("The quick brown fox"))
        self.wm.store(create_fact("The lazy dog"))
        self.wm.store(create_fact("Quick response needed"))

        results = self.wm.search("quick")

        self.assertGreater(len(results), 0)
        # All results should contain 'quick'
        for chunk in results:
            found = "quick" in chunk.name.lower() or any(
                "quick" in str(v).lower() for v in chunk.slots.values()
            )
            self.assertTrue(found)

    def test_activation_retrieval(self):
        """Test that more active chunks are retrieved first."""
        chunk1 = create_fact("Chunk 1")
        chunk2 = create_fact("Chunk 2")

        self.wm.store(chunk1)
        self.wm.store(chunk2)

        # Access chunk1 multiple times
        for _ in range(5):
            self.wm.retrieve(chunk1.id)

        most_active = self.wm.get_most_active(2)

        # chunk1 should be most active
        self.assertEqual(most_active[0].id, chunk1.id)

    def test_focus_attention(self):
        """Test attention focusing."""
        chunk = create_fact("Focus me")
        self.wm.store(chunk)

        self.wm.focus_on(chunk)

        self.assertTrue(self.wm.attention.is_in_focus(chunk.id))
        self.assertGreater(
            self.wm.attention.get_focus_strength(chunk.id), 0
        )

    def test_linked_chunk_activation_spread(self):
        """Test activation spreading to linked chunks."""
        chunk1 = create_fact("Chunk 1")
        chunk2 = create_fact("Chunk 2")

        self.wm.store(chunk1)
        self.wm.store(chunk2)
        self.wm.link_chunks(chunk1.id, chunk2.id)

        initial_activation = chunk2.activation
        self.wm.spread_activation(chunk1, amount=1.0)

        self.assertGreater(chunk2.activation, initial_activation)

    def test_reset(self):
        """Test memory reset."""
        self.wm.store(create_fact("Fact 1"))
        self.wm.store(create_fact("Fact 2"))

        self.wm.reset()

        self.assertEqual(len(self.wm.chunks), 0)

    def test_dump_and_summarize(self):
        """Test dump and summarize methods."""
        self.wm.store(create_fact("Fact"))
        self.wm.store(create_goal("Goal", "Description"))

        dump = self.wm.dump()
        summary = self.wm.summarize()

        self.assertEqual(len(dump), 2)
        self.assertIn("Working Memory", summary)


class TestAttentionManager(unittest.TestCase):
    """Tests for AttentionManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.wm = WorkingMemory(capacity=10)
        self.attention = self.wm.attention

    def test_focus_on(self):
        """Test focusing on a chunk."""
        chunk = create_fact("Focus target")
        self.wm.store(chunk)

        self.attention.focus_on(chunk)

        self.assertEqual(self.attention.current_focus.primary_chunk_id, chunk.id)
        self.assertGreater(self.attention.current_focus.focus_strength, 0)

    def test_add_to_focus(self):
        """Test adding to secondary focus."""
        chunk1 = create_fact("Primary")
        chunk2 = create_fact("Secondary")

        self.wm.store(chunk1)
        self.wm.store(chunk2)

        self.attention.focus_on(chunk1)
        self.attention.add_to_focus(chunk2)

        self.assertTrue(self.attention.is_in_focus(chunk1.id))
        self.assertTrue(self.attention.is_in_focus(chunk2.id))

    def test_focus_capacity(self):
        """Test focus capacity limits."""
        chunks = [create_fact(f"Chunk {i}") for i in range(10)]
        for chunk in chunks:
            self.wm.store(chunk)

        self.attention.focus_on(chunks[0])

        added = 0
        for chunk in chunks[1:]:
            if self.attention.add_to_focus(chunk):
                added += 1

        # Should hit capacity limit
        self.assertLess(added, len(chunks) - 1)

    def test_focus_history(self):
        """Test focus history tracking."""
        chunk1 = create_fact("First")
        chunk2 = create_fact("Second")

        self.wm.store(chunk1)
        self.wm.store(chunk2)

        self.attention.focus_on(chunk1)
        self.attention.focus_on(chunk2)

        self.assertEqual(self.attention.attention_shifts, 1)
        self.assertEqual(len(self.attention.focus_history), 1)


if __name__ == "__main__":
    unittest.main()
