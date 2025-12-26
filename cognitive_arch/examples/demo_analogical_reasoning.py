"""
Demonstration of the Analogical Reasoning module.

This example shows:
- Creating structured representations
- Finding structural mappings
- Retrieving analogous cases
- Making analogical inferences
"""

from cognitive_arch.modules.analogical import (
    Structure, StructureMapper, AnalogRetriever, AnalogicalInference
)
from cognitive_arch.modules.analogical.structures import create_structure


def demo_structure_creation():
    """Demonstrate creating structured representations."""
    print("=" * 60)
    print("ANALOGICAL REASONING DEMO: Structure Creation")
    print("=" * 60)

    # Create the classic Rutherford atom analogy
    # Solar system structure
    solar_system = Structure(
        name="Solar System",
        description="The sun and planets"
    )

    # Add entities
    solar_system.add_entity("Sun", value="massive, bright")
    solar_system.add_entity("Planet", value="orbits sun")
    solar_system.add_entity("Gravity", value="attractive force")

    # Add attributes
    solar_system.add_attribute("Sun", "mass", "large")
    solar_system.add_attribute("Sun", "charge", "none")
    solar_system.add_attribute("Planet", "mass", "small")

    # Add relations
    solar_system.add_relation("attracts", "Sun", "Planet", relation_type="causal")
    solar_system.add_relation("orbits", "Planet", "Sun", relation_type="spatial")
    solar_system.add_relation("causes", "Gravity", "attracts",
                              relation_type="causal")

    print("\n1. Solar System structure:")
    print(solar_system.summarize())

    # Atom structure
    atom = Structure(
        name="Atom",
        description="Nucleus and electrons"
    )

    atom.add_entity("Nucleus", value="protons and neutrons")
    atom.add_entity("Electron", value="orbits nucleus")
    atom.add_entity("ElectricForce", value="attractive force")

    atom.add_attribute("Nucleus", "mass", "large")
    atom.add_attribute("Nucleus", "charge", "positive")
    atom.add_attribute("Electron", "mass", "small")
    atom.add_attribute("Electron", "charge", "negative")

    atom.add_relation("attracts", "Nucleus", "Electron", relation_type="causal")
    atom.add_relation("orbits", "Electron", "Nucleus", relation_type="spatial")
    atom.add_relation("causes", "ElectricForce", "attracts",
                      relation_type="causal")

    print("\n2. Atom structure:")
    print(atom.summarize())

    return solar_system, atom


def demo_structure_mapping():
    """Demonstrate structure mapping between analogs."""
    print("\n" + "=" * 60)
    print("ANALOGICAL REASONING DEMO: Structure Mapping")
    print("=" * 60)

    solar_system, atom = demo_structure_creation()

    mapper = StructureMapper()

    print("\n3. Mapping Solar System to Atom...")
    mapping = mapper.map_structures(solar_system, atom)

    print(f"\n4. Mapping results:")
    print(f"   Overall similarity: {mapping.overall_similarity:.2f}")
    print(f"   Systematicity: {mapping.systematicity:.2f}")
    print(f"   Coverage: {mapping.coverage:.1%}")

    print("\n5. Correspondences:")
    for corr in mapping.correspondences:
        source_name = solar_system.elements.get(
            corr.source_id, type('', (), {'name': '?'})()
        ).name
        target_name = atom.elements.get(
            corr.target_id, type('', (), {'name': '?'})()
        ).name
        print(f"   {source_name} <-> {target_name} (sim: {corr.similarity:.2f})")

    print("\n6. Potential inferences:")
    for inf in mapping.inferences:
        print(f"   - {inf}")

    # Get full explanation
    print("\n7. Full explanation:")
    print(mapper.explain_mapping(solar_system, atom, mapping))

    return mapper


def demo_analog_retrieval():
    """Demonstrate analog retrieval from knowledge base."""
    print("\n" + "=" * 60)
    print("ANALOGICAL REASONING DEMO: Analog Retrieval")
    print("=" * 60)

    retriever = AnalogRetriever()

    # Store several analogs
    print("\n1. Storing analogs in knowledge base...")

    # Water flow
    water_flow = create_structure(
        "Water Flow",
        ["Reservoir", "Pipe", "Bucket"],
        [("flows_from", "Reservoir", "Pipe"),
         ("flows_to", "Pipe", "Bucket"),
         ("pressure_drives", "Reservoir", "Pipe")]
    )
    retriever.store(water_flow, domain="physics", tags=["flow", "pressure"])
    print("   - Stored: Water Flow (physics)")

    # Electric circuit
    circuit = create_structure(
        "Electric Circuit",
        ["Battery", "Wire", "Bulb"],
        [("current_from", "Battery", "Wire"),
         ("current_to", "Wire", "Bulb"),
         ("voltage_drives", "Battery", "Wire")]
    )
    retriever.store(circuit, domain="physics", tags=["flow", "voltage"])
    print("   - Stored: Electric Circuit (physics)")

    # Blood circulation
    blood = create_structure(
        "Blood Circulation",
        ["Heart", "Artery", "Organ"],
        [("pumps_from", "Heart", "Artery"),
         ("delivers_to", "Artery", "Organ"),
         ("pressure_drives", "Heart", "Artery")]
    )
    retriever.store(blood, domain="biology", tags=["flow", "pressure"])
    print("   - Stored: Blood Circulation (biology)")

    # Information flow
    info_flow = create_structure(
        "Information Network",
        ["Server", "Network", "Client"],
        [("sends_from", "Server", "Network"),
         ("receives_at", "Network", "Client"),
         ("bandwidth_enables", "Server", "Network")]
    )
    retriever.store(info_flow, domain="computing", tags=["flow", "network"])
    print("   - Stored: Information Network (computing)")

    # Query for analogs
    print("\n2. Querying for analogs to Heat Flow...")
    query = create_structure(
        "Heat Flow",
        ["Heater", "Conductor", "Room"],
        [("transfers_from", "Heater", "Conductor"),
         ("transfers_to", "Conductor", "Room"),
         ("temperature_drives", "Heater", "Conductor")]
    )

    results = retriever.retrieve(query, n=3)

    print("\n3. Retrieved analogs:")
    for analog, score in results:
        print(f"   - {analog.structure.name} ({analog.domain}): {score:.2f}")

    # Try domain-specific retrieval
    print("\n4. Retrieving physics analogs only...")
    physics_results = retriever.retrieve(query, n=2, domain="physics")
    for analog, score in physics_results:
        print(f"   - {analog.structure.name}: {score:.2f}")

    # Get diverse analogs
    print("\n5. Getting diverse analogs...")
    diverse = retriever.get_diverse_analogs(query, n=3)
    for analog in diverse:
        print(f"   - {analog.structure.name} ({analog.domain})")

    print("\n6. Knowledge base stats:")
    print(retriever.summarize())

    return retriever


def demo_analogical_inference():
    """Demonstrate making inferences from analogies."""
    print("\n" + "=" * 60)
    print("ANALOGICAL REASONING DEMO: Analogical Inference")
    print("=" * 60)

    retriever = AnalogRetriever()

    # Store source analog with rich structure
    print("\n1. Storing source analog (Teacher-Student)...")
    teaching = Structure(name="Teaching", description="Educational interaction")
    teaching.add_entity("Teacher")
    teaching.add_entity("Student")
    teaching.add_entity("Knowledge")
    teaching.add_entity("Exam")

    teaching.add_attribute("Teacher", "expertise", "high")
    teaching.add_attribute("Student", "expertise", "low")
    teaching.add_attribute("Knowledge", "type", "academic")

    teaching.add_relation("transmits", "Teacher", "Knowledge", relation_type="causal")
    teaching.add_relation("receives", "Student", "Knowledge", relation_type="causal")
    teaching.add_relation("evaluates", "Exam", "Student", relation_type="assessment")
    teaching.add_relation("guides", "Teacher", "Student", relation_type="social")

    retriever.store(teaching, domain="education", tags=["knowledge", "transfer"])

    # Create target analog (incomplete)
    print("\n2. Creating target structure (Mentorship)...")
    mentorship = Structure(name="Mentorship", description="Professional guidance")
    mentorship.add_entity("Mentor")
    mentorship.add_entity("Protege")
    mentorship.add_entity("Skills")

    mentorship.add_attribute("Mentor", "expertise", "high")
    mentorship.add_attribute("Protege", "expertise", "low")
    mentorship.add_attribute("Skills", "type", "professional")

    mentorship.add_relation("transmits", "Mentor", "Skills", relation_type="causal")
    mentorship.add_relation("receives", "Protege", "Skills", relation_type="causal")

    print(mentorship.summarize())

    # Make inferences
    print("\n3. Making analogical inferences...")
    inference_engine = AnalogicalInference(retriever)
    inferences = inference_engine.infer(mentorship, source=teaching)

    print("\n4. Generated inferences:")
    for inf in inferences:
        print(inference_engine.explain_inference(inf))
        print()

    # Best inferences
    print("\n5. Best inferences summary:")
    best = inference_engine.get_best_inferences(3)
    for inf in best:
        print(f"   - {inf.inference_type}: {inf.content}")
        print(f"     Confidence: {inf.confidence:.2f}")

    return inference_engine


def demo_classic_analogies():
    """Demonstrate classic analogy examples."""
    print("\n" + "=" * 60)
    print("ANALOGICAL REASONING DEMO: Classic Analogies")
    print("=" * 60)

    mapper = StructureMapper()

    # 1. Fortress/Tumor analogy (Duncker's radiation problem)
    print("\n1. Fortress Attack / Tumor Radiation analogy")

    fortress = Structure(name="Fortress Attack")
    fortress.add_entity("Army")
    fortress.add_entity("Fortress")
    fortress.add_entity("Roads")
    fortress.add_relation("attacks", "Army", "Fortress")
    fortress.add_relation("divides_into", "Army", "Roads")
    fortress.add_relation("converge_at", "Roads", "Fortress")

    tumor = Structure(name="Tumor Radiation")
    tumor.add_entity("Radiation")
    tumor.add_entity("Tumor")
    tumor.add_entity("Paths")
    tumor.add_relation("destroys", "Radiation", "Tumor")

    mapping1 = mapper.map_structures(fortress, tumor)
    print(f"   Similarity: {mapping1.overall_similarity:.2f}")
    print("   Correspondences:")
    for corr in mapping1.correspondences:
        s_name = fortress.elements.get(corr.source_id, type('', (), {'name': '?'})()).name
        t_name = tumor.elements.get(corr.target_id, type('', (), {'name': '?'})()).name
        print(f"     {s_name} -> {t_name}")

    if mapping1.inferences:
        print("   Inferences (solution strategy):")
        for inf in mapping1.inferences:
            print(f"     - {inf}")

    # 2. Heat/Water flow analogy
    print("\n2. Heat Flow / Water Flow analogy")

    heat = create_structure(
        "Heat Flow",
        ["HotObject", "ColdObject", "Temperature"],
        [("flows_from", "HotObject", "ColdObject"),
         ("causes", "Temperature", "flows_from")]
    )

    water = create_structure(
        "Water Flow",
        ["HighContainer", "LowContainer", "Pressure"],
        [("flows_from", "HighContainer", "LowContainer"),
         ("causes", "Pressure", "flows_from")]
    )

    mapping2 = mapper.map_structures(heat, water)
    print(f"   Similarity: {mapping2.overall_similarity:.2f}")
    print("   This analogy was historically important in thermodynamics!")


def main():
    """Run all demonstrations."""
    print("\n" + "#" * 60)
    print("# COGNITIVE ARCHITECTURE: Analogical Reasoning Demonstration")
    print("#" * 60)

    demo_structure_creation()
    demo_structure_mapping()
    demo_analog_retrieval()
    demo_analogical_inference()
    demo_classic_analogies()

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
