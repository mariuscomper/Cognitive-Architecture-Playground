"""
Demonstration of the integrated Cognitive Architecture.

This example shows how all modules work together for complex reasoning.
"""

from cognitive_arch.core.architecture import CognitiveArchitecture
from cognitive_arch.modules.working_memory import ChunkType


def demo_basic_integration():
    """Demonstrate basic integrated operations."""
    print("=" * 60)
    print("INTEGRATED DEMO: Basic Operations")
    print("=" * 60)

    arch = CognitiveArchitecture()

    print("\n1. Remembering information...")
    arch.remember("The patient has a fever", ChunkType.FACT, confidence=0.9)
    arch.remember("The patient has a cough", ChunkType.FACT, confidence=0.85)
    arch.remember("The patient was recently traveling", ChunkType.FACT, confidence=1.0)

    print("\n2. Recalling information...")
    memories = arch.recall("patient")
    for m in memories:
        print(f"   - {m['content']} (activation: {m['activation']:.2f})")

    print("\n3. Recording confidence judgment...")
    judgment_id = arch.assess_confidence(
        "Patient has a respiratory infection",
        0.75,
        domain="medical_diagnosis"
    )
    print(f"   Judgment recorded: {judgment_id[:8]}...")

    print("\n4. Getting architecture state...")
    state = arch.get_state()
    print(f"   Working memory chunks: {state['working_memory']['total_chunks']}")
    print(f"   Session uptime: {state['uptime_seconds']:.1f}s")


def demo_causal_integration():
    """Demonstrate causal reasoning integration."""
    print("\n" + "=" * 60)
    print("INTEGRATED DEMO: Causal Reasoning")
    print("=" * 60)

    arch = CognitiveArchitecture()

    print("\n1. Creating causal model for disease...")
    arch.create_causal_model(
        "disease_model",
        variables=["Virus", "Fever", "Cough", "Fatigue", "Recovery"],
        edges=[
            ("Virus", "Fever"),
            ("Virus", "Cough"),
            ("Fever", "Fatigue"),
            ("Cough", "Fatigue"),
            ("Fatigue", "Recovery")
        ]
    )

    print("\n2. Querying causal effect...")
    result = arch.causal_query("disease_model", "Virus", "Fatigue")
    print(f"   Virus -> Fatigue identifiable: {result['identifiable']}")
    print(f"   Method: {result['method']}")
    print(f"   Adjustment set: {result['adjustment_set']}")

    print("\n3. Analyzing intervention...")
    intervention = arch.what_if("disease_model", "Fever", value="reduced")
    print(f"   Intervention: {intervention['intervention']}")
    print(f"   Affected variables: {intervention['affected_variables']}")
    print(f"   Confidence: {intervention['confidence']:.2f}")


def demo_analogical_integration():
    """Demonstrate analogical reasoning integration."""
    print("\n" + "=" * 60)
    print("INTEGRATED DEMO: Analogical Reasoning")
    print("=" * 60)

    arch = CognitiveArchitecture()

    print("\n1. Storing analog cases...")
    arch.store_analog(
        name="Pump System",
        description="A pump moving fluid through pipes",
        entities=["Pump", "Pipe", "Tank"],
        relations=[
            ("drives", "Pump", "Pipe"),
            ("fills", "Pipe", "Tank"),
            ("creates_pressure", "Pump", "Pipe")
        ],
        domain="hydraulics",
        tags=["flow", "pressure"]
    )

    arch.store_analog(
        name="Electric Circuit",
        description="A battery powering a circuit",
        entities=["Battery", "Wire", "Resistor"],
        relations=[
            ("drives", "Battery", "Wire"),
            ("powers", "Wire", "Resistor"),
            ("creates_voltage", "Battery", "Wire")
        ],
        domain="electronics",
        tags=["flow", "current"]
    )

    print("\n2. Finding analogs for new situation...")
    analogs = arch.find_analogs(
        query_entities=["Heart", "Artery", "Organ"],
        query_relations=[("pumps", "Heart", "Artery")],
        n=2
    )

    print("   Found analogs:")
    for a in analogs:
        print(f"   - {a['name']} (similarity: {a['similarity']:.2f})")
        print(f"     Domain: {a['domain']}")

    print("\n3. Transferring knowledge...")
    if analogs:
        inferences = arch.analogical_transfer(
            source_name=analogs[0]['name'],
            target_entities=["Heart", "Artery", "Organ"],
            target_relations=[("pumps", "Heart", "Artery")]
        )

        print("   Transferred inferences:")
        for inf in inferences:
            print(f"   - {inf['type']}: {inf['content']}")
            print(f"     Confidence: {inf['confidence']:.2f}")


def demo_complex_reasoning():
    """Demonstrate complex integrated reasoning."""
    print("\n" + "=" * 60)
    print("INTEGRATED DEMO: Complex Reasoning Task")
    print("=" * 60)

    arch = CognitiveArchitecture()

    print("\n1. Problem: Diagnose and treat a novel disease")

    # Store relevant knowledge
    print("\n2. Loading background knowledge...")
    arch.remember("Novel viruses often cause respiratory symptoms", ChunkType.FACT)
    arch.remember("Fever indicates immune response", ChunkType.FACT)
    arch.remember("Rest and hydration support recovery", ChunkType.FACT)

    # Create causal model
    print("\n3. Building causal disease model...")
    arch.create_causal_model(
        "novel_disease",
        ["Pathogen", "InfectionSite", "ImmuneResponse", "Symptoms", "Treatment", "Outcome"],
        [
            ("Pathogen", "InfectionSite"),
            ("InfectionSite", "ImmuneResponse"),
            ("InfectionSite", "Symptoms"),
            ("ImmuneResponse", "Symptoms"),
            ("Treatment", "Symptoms"),
            ("Treatment", "Outcome"),
            ("Symptoms", "Outcome"),
            ("ImmuneResponse", "Outcome")
        ]
    )

    # Store analog for reasoning
    print("\n4. Storing analogous disease case...")
    arch.store_analog(
        "Common Cold",
        "A well-understood respiratory infection",
        ["Rhinovirus", "Nose", "Inflammation", "Congestion", "Rest", "Recovery"],
        [
            ("infects", "Rhinovirus", "Nose"),
            ("causes", "Nose", "Inflammation"),
            ("causes", "Inflammation", "Congestion"),
            ("helps", "Rest", "Recovery")
        ],
        domain="medicine",
        tags=["respiratory", "viral"]
    )

    # Reason about the novel disease
    print("\n5. Reasoning about novel disease...")

    # Think through the problem
    arch.think("The pathogen appears to be a novel virus", "observation")
    arch.think("Similar to cold viruses, it targets respiratory system", "inference")
    arch.think("Immune response will likely cause fever", "hypothesis")

    # Query causal model
    treatment_effect = arch.causal_query("novel_disease", "Treatment", "Outcome")
    print(f"\n   Treatment -> Outcome analysis:")
    print(f"   Identifiable: {treatment_effect['identifiable']}")

    # Get intervention suggestions
    intervention = arch.what_if("novel_disease", "Treatment", "supportive_care")
    print(f"\n   If we apply supportive care:")
    print(f"   Affected: {intervention['affected_variables']}")

    # Find analogous cases
    analogs = arch.find_analogs(
        ["Virus", "Lungs", "Fever"],
        [("causes", "Virus", "Fever")]
    )

    if analogs:
        print(f"\n   Similar case found: {analogs[0]['name']}")

    # Reach conclusion
    conclusion = arch.conclude(
        "Recommend supportive treatment with close monitoring",
        confidence=0.7,
        evidence=["Causal model analysis", "Analogical reasoning from similar diseases"]
    )
    print(f"\n6. Conclusion: {conclusion.content}")
    print(f"   Confidence: {conclusion.confidence:.0%}")

    # Get reasoning explanation
    print("\n7. Reasoning trace:")
    print(arch.explain())

    # Final state
    print("\n8. Final cognitive state:")
    print(arch.summarize())


def demo_metacognitive_monitoring():
    """Demonstrate metacognitive features in integrated system."""
    print("\n" + "=" * 60)
    print("INTEGRATED DEMO: Metacognitive Monitoring")
    print("=" * 60)

    arch = CognitiveArchitecture()

    print("\n1. Making a series of predictions...")
    predictions = [
        ("Stock will rise tomorrow", 0.8, True),
        ("It will rain this week", 0.9, True),
        ("Project will finish on time", 0.7, False),
        ("Client will accept proposal", 0.6, True),
        ("Server will stay stable", 0.95, True),
    ]

    for claim, confidence, actual in predictions:
        jid = arch.assess_confidence(claim, confidence, domain="predictions")
        arch.record_outcome(jid, actual)
        print(f"   {claim}: predicted {confidence:.0%}, actual: {'correct' if actual else 'wrong'}")

    print("\n2. Checking calibration...")
    calibration = arch.get_calibration("predictions")
    print(f"   Calibration error: {calibration['calibration_error']:.3f}" if calibration['calibration_error'] else "   Not enough data")
    print(f"   Well calibrated: {calibration['calibrated']}")

    print("\n3. Checking for reasoning issues...")
    from cognitive_arch.core.types import Thought

    thoughts = [
        Thought(content="Initial assumption", thought_type="hypothesis", confidence=0.9),
        Thought(content="Supporting evidence", thought_type="observation", confidence=0.9),
        Thought(content="Confirming evidence", thought_type="observation", confidence=0.9),
        Thought(content="More confirmation", thought_type="observation", confidence=0.9),
    ]

    issues = arch.check_reasoning(thoughts)
    if issues:
        print("   Detected issues:")
        for issue in issues:
            print(f"   - {issue['type']}: {issue['description']}")
    else:
        print("   No issues detected")

    print("\n4. Starting reflection on a problem...")
    episode = arch.reflect("Why did my prediction fail?", strategy="analytical")
    print(f"   Started episode: {episode['episode_id'][:8]}...")
    print(f"   Strategy: {episode['strategy']}")


def main():
    """Run all integrated demonstrations."""
    print("\n" + "#" * 60)
    print("# COGNITIVE ARCHITECTURE: Integrated System Demonstration")
    print("#" * 60)

    demo_basic_integration()
    demo_causal_integration()
    demo_analogical_integration()
    demo_complex_reasoning()
    demo_metacognitive_monitoring()

    print("\n" + "=" * 60)
    print("Integrated demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
