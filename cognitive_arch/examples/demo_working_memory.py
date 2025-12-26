"""
Demonstration of the Working Memory module.

This example shows:
- Storing and retrieving chunks
- Activation-based retrieval
- Attention focusing
- Memory decay and capacity limits
"""

from cognitive_arch.modules.working_memory import WorkingMemory, Chunk, ChunkType
from cognitive_arch.modules.working_memory.chunks import create_fact, create_goal, create_hypothesis
import time


def demo_basic_operations():
    """Demonstrate basic working memory operations."""
    print("=" * 60)
    print("WORKING MEMORY DEMO: Basic Operations")
    print("=" * 60)

    wm = WorkingMemory(capacity=5)

    # Store some facts
    print("\n1. Storing facts...")
    fact1 = create_fact("The sky is blue", color="blue", object="sky")
    fact2 = create_fact("Water is wet", property="wet", substance="water")
    fact3 = create_fact("Fire is hot", property="hot", element="fire")

    wm.store(fact1)
    wm.store(fact2)
    wm.store(fact3)

    print(f"   Stored {len(wm.chunks)} chunks")
    print(f"   Active context: {wm.get_active_context()}")

    # Retrieve by name
    print("\n2. Retrieving by name...")
    retrieved = wm.retrieve_by_name("The sky is blue")
    if retrieved:
        print(f"   Found: {retrieved.name} (activation: {retrieved.activation:.2f})")

    # Query by pattern
    print("\n3. Querying by pattern...")
    results = wm.query({"property": "wet"})
    print(f"   Found {len(results)} chunks matching {{property: 'wet'}}")
    for r in results:
        print(f"     - {r.name}")

    # Search
    print("\n4. Text search...")
    results = wm.search("hot")
    print(f"   Found {len(results)} chunks matching 'hot'")
    for r in results:
        print(f"     - {r.name} (activation: {r.activation:.2f})")

    return wm


def demo_activation_dynamics():
    """Demonstrate activation and decay."""
    print("\n" + "=" * 60)
    print("WORKING MEMORY DEMO: Activation Dynamics")
    print("=" * 60)

    wm = WorkingMemory(capacity=5, decay_rate=0.5)

    # Store chunks
    chunks = []
    for i in range(3):
        chunk = create_fact(f"Fact {i+1}", index=i)
        wm.store(chunk)
        chunks.append(chunk)

    print("\n1. Initial activations:")
    for c in wm.get_most_active(3):
        print(f"   {c.name}: {c.activation:.2f}")

    # Access some chunks multiple times
    print("\n2. Accessing 'Fact 1' multiple times...")
    for _ in range(5):
        wm.retrieve_by_name("Fact 1")

    print("\n3. Activations after repeated access:")
    for c in wm.get_most_active(3):
        print(f"   {c.name}: {c.activation:.2f}")

    # Focus on a chunk
    print("\n4. Focusing on 'Fact 3'...")
    fact3 = wm.retrieve_by_name("Fact 3")
    if fact3:
        wm.focus_on(fact3)

    print("\n5. Activations after focus:")
    for c in wm.get_most_active(3):
        focus_marker = "*" if wm.attention.is_in_focus(c.id) else " "
        print(f"   {focus_marker}{c.name}: {c.activation:.2f}")


def demo_capacity_limits():
    """Demonstrate capacity limits and eviction."""
    print("\n" + "=" * 60)
    print("WORKING MEMORY DEMO: Capacity Limits")
    print("=" * 60)

    wm = WorkingMemory(capacity=3)

    print("\n1. Storing chunks (capacity = 3)...")
    for i in range(5):
        chunk = create_fact(f"Memory {i+1}", priority=i)
        wm.store(chunk)
        print(f"   Stored 'Memory {i+1}' - Total chunks: {len(wm.chunks)}")

    print(f"\n2. Final state ({len(wm.chunks)} chunks):")
    for c in wm.get_most_active(5):
        print(f"   - {c.name}")

    print(f"\n3. Eviction stats: {wm.stats['evictions']} chunks evicted")


def demo_goals_and_hypotheses():
    """Demonstrate goal and hypothesis management."""
    print("\n" + "=" * 60)
    print("WORKING MEMORY DEMO: Goals and Hypotheses")
    print("=" * 60)

    wm = WorkingMemory(capacity=10)

    # Store goals
    print("\n1. Creating goals...")
    goal1 = create_goal("Find cause", "Determine the root cause of the problem")
    goal2 = create_goal("Test solution", "Verify the proposed solution works")
    wm.store(goal1)
    wm.store(goal2)

    # Store hypotheses
    print("\n2. Creating hypotheses...")
    hyp1 = create_hypothesis("Memory leak", "The bug is caused by a memory leak", 0.7)
    hyp2 = create_hypothesis("Race condition", "The bug is caused by a race condition", 0.4)
    wm.store(hyp1)
    wm.store(hyp2)

    print("\n3. Active goals:")
    for goal in wm.get_goals():
        print(f"   - {goal.name}")

    print("\n4. Current hypotheses:")
    for hyp in wm.get_hypotheses():
        print(f"   - {hyp.name} (confidence: {hyp.confidence:.0%})")

    # Link hypothesis to goal
    print("\n5. Linking hypothesis to goal...")
    wm.link_chunks(hyp1.id, goal1.id)
    print(f"   Linked '{hyp1.name}' to '{goal1.name}'")

    # Spread activation
    print("\n6. Spreading activation from focused hypothesis...")
    wm.focus_on(hyp1)
    wm.spread_activation(hyp1)

    print("\n7. Most active chunks after spreading:")
    for c in wm.get_most_active(4):
        print(f"   - {c.name}: {c.activation:.2f}")


def main():
    """Run all demonstrations."""
    print("\n" + "#" * 60)
    print("# COGNITIVE ARCHITECTURE: Working Memory Demonstration")
    print("#" * 60)

    demo_basic_operations()
    demo_activation_dynamics()
    demo_capacity_limits()
    demo_goals_and_hypotheses()

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
