"""
Demonstration of the Causal Reasoning module.

This example shows:
- Building causal graphs
- Testing d-separation
- Identifying confounders
- Estimating causal effects
- Analyzing interventions
"""

from cognitive_arch.modules.causal import (
    CausalGraph, CausalNode, CausalInference, InterventionAnalyzer
)
from cognitive_arch.modules.causal.graph import NodeType, create_simple_graph


def demo_basic_graph():
    """Demonstrate basic causal graph construction."""
    print("=" * 60)
    print("CAUSAL REASONING DEMO: Basic Graph Construction")
    print("=" * 60)

    # Create a simple graph: Smoking -> Cancer, Smoking -> Tar, Tar -> Cancer
    graph = CausalGraph(name="Smoking and Cancer")

    smoking = graph.add_node_by_name("Smoking")
    tar = graph.add_node_by_name("Tar")
    cancer = graph.add_node_by_name("Cancer")

    graph.add_edge(smoking, tar)
    graph.add_edge(tar, cancer)
    graph.add_edge(smoking, cancer)

    print("\n1. Graph structure:")
    print(graph.summarize())

    print("\n2. Causal relationships:")
    print(f"   Smoking -> Tar: Direct cause")
    print(f"   Smoking -> Cancer: Direct cause")
    print(f"   Tar -> Cancer: Direct cause")

    # Find paths
    print("\n3. Causal paths from Smoking to Cancer:")
    paths = graph.find_all_paths(smoking, cancer)
    for path in paths:
        path_names = [graph.nodes[n].name for n in path]
        print(f"   {' -> '.join(path_names)}")

    return graph


def demo_confounding():
    """Demonstrate confounder detection."""
    print("\n" + "=" * 60)
    print("CAUSAL REASONING DEMO: Confounding")
    print("=" * 60)

    # Classic confounding example:
    # SocioEconomicStatus (SES) affects both Education and Income
    # We want to know: Does Education cause Income?

    graph = CausalGraph(name="Education and Income")

    ses = graph.add_node_by_name("SES")
    education = graph.add_node_by_name("Education")
    income = graph.add_node_by_name("Income")
    ability = graph.add_node_by_name("Ability", node_type=NodeType.LATENT)

    # SES affects both education and income (confounding)
    graph.add_edge(ses, education)
    graph.add_edge(ses, income)

    # Education affects income (the causal effect we want)
    graph.add_edge(education, income)

    # Ability also affects both (latent confounder)
    graph.add_edge(ability, education)
    graph.add_edge(ability, income)

    print("\n1. Graph structure:")
    print(graph.summarize())

    print("\n2. Identifying confounders...")
    confounders = graph.get_confounders(education, income)
    confounder_names = [graph.nodes[c].name for c in confounders]
    print(f"   Confounders between Education and Income: {confounder_names}")

    print("\n3. Finding backdoor paths...")
    backdoors = graph.find_backdoor_paths(education, income)
    for path in backdoors:
        path_names = [graph.nodes[n].name for n in path]
        print(f"   Backdoor: {' <- '.join(path_names)}")

    print("\n4. Finding minimal adjustment set...")
    adjustment_set = graph.get_minimal_adjustment_set(education, income)
    if adjustment_set:
        adj_names = [graph.nodes[a].name for a in adjustment_set]
        print(f"   Adjust for: {adj_names}")
    else:
        print("   No valid adjustment set found (unidentifiable)")

    return graph


def demo_d_separation():
    """Demonstrate d-separation testing."""
    print("\n" + "=" * 60)
    print("CAUSAL REASONING DEMO: D-Separation")
    print("=" * 60)

    # Create a graph with various structures
    graph = CausalGraph(name="D-Separation Example")

    x = graph.add_node_by_name("X")
    y = graph.add_node_by_name("Y")
    z = graph.add_node_by_name("Z")
    w = graph.add_node_by_name("W")

    # X -> Z -> Y (chain)
    # X -> W <- Y (collider)
    graph.add_edge(x, z)
    graph.add_edge(z, y)
    graph.add_edge(x, w)
    graph.add_edge(y, w)

    print("\n1. Graph structure:")
    print(graph.summarize())

    # Test various conditional independences
    print("\n2. D-separation tests:")

    # X and Y unconditionally
    result = graph.is_d_separated(x, y, set())
    print(f"   X _||_ Y | {} : {result}")

    # X and Y given Z
    result = graph.is_d_separated(x, y, {z})
    print(f"   X _||_ Y | {{Z}} : {result}")

    # X and Y given W (conditioning on collider opens path)
    result = graph.is_d_separated(x, y, {w})
    print(f"   X _||_ Y | {{W}} : {result}")

    # X and Y given Z and W
    result = graph.is_d_separated(x, y, {z, w})
    print(f"   X _||_ Y | {{Z, W}} : {result}")


def demo_causal_inference():
    """Demonstrate causal effect estimation."""
    print("\n" + "=" * 60)
    print("CAUSAL REASONING DEMO: Causal Inference")
    print("=" * 60)

    # Create a graph with data
    graph = CausalGraph(name="Treatment Effect")

    treatment = graph.add_node_by_name("Treatment")
    outcome = graph.add_node_by_name("Outcome")
    confounder = graph.add_node_by_name("Age")

    graph.add_edge(confounder, treatment)
    graph.add_edge(confounder, outcome)
    graph.add_edge(treatment, outcome)

    inference = CausalInference(graph)

    print("\n1. Graph structure:")
    print(graph.summarize())

    # Check identifiability
    print("\n2. Checking identifiability...")
    identifiable, explanation = inference.is_identifiable("Treatment", "Outcome")
    print(f"   Identifiable: {identifiable}")
    print(f"   Explanation: {explanation}")

    # Estimate effect (without data)
    print("\n3. Estimating causal effect...")
    effect = inference.estimate_effect("Treatment", "Outcome")
    print(f"   Method: {effect.method}")
    print(f"   Adjustment set: {effect.adjustment_set}")
    print(f"   Assumptions: {effect.assumptions}")

    # Add some simple data
    print("\n4. With observational data:")
    inference.set_data("Treatment", [0, 0, 1, 1, 0, 1, 0, 1, 1, 0])
    inference.set_data("Outcome", [1, 0, 1, 1, 0, 1, 1, 0, 1, 0])

    effect = inference.estimate_effect("Treatment", "Outcome")
    if effect.estimate is not None:
        print(f"   Estimated effect: {effect.estimate:.3f}")
        print(f"   95% CI: {effect.confidence_interval}")


def demo_interventions():
    """Demonstrate intervention analysis."""
    print("\n" + "=" * 60)
    print("CAUSAL REASONING DEMO: Interventions")
    print("=" * 60)

    # Create a more complex graph
    graph = CausalGraph(name="Drug Trial")

    gene = graph.add_node_by_name("Gene")
    drug = graph.add_node_by_name("Drug")
    biomarker = graph.add_node_by_name("Biomarker")
    symptoms = graph.add_node_by_name("Symptoms")
    recovery = graph.add_node_by_name("Recovery")

    graph.add_edge(gene, biomarker)
    graph.add_edge(gene, symptoms)
    graph.add_edge(drug, biomarker)
    graph.add_edge(biomarker, symptoms)
    graph.add_edge(symptoms, recovery)
    graph.add_edge(drug, recovery)

    analyzer = InterventionAnalyzer(graph)

    print("\n1. Graph structure:")
    print(graph.summarize())

    # Analyze intervention on drug
    print("\n2. Analyzing intervention do(Drug = active)...")
    outcome = analyzer.analyze_intervention("Drug", "active")
    print(f"   Affected variables: {outcome.affected_variables}")
    print(f"   Side effects: {outcome.side_effects}")
    print(f"   Confidence: {outcome.confidence:.2f}")

    # Compare interventions
    print("\n3. Comparing interventions for Recovery...")
    comparison = analyzer.compare_interventions(
        [("Drug", "active"), ("Biomarker", "high"), ("Symptoms", "none")],
        "Recovery"
    )
    print(f"   Recommended: {comparison['recommended']}")
    print(f"   Reason: {comparison['recommendation_reason']}")

    # Predict cascade
    print("\n4. Predicting cascade from Drug intervention...")
    cascade = analyzer.predict_cascade("Drug", "active", steps=3)
    for step in cascade:
        print(f"   Step {step['step']}: {list(step['changes'].keys())}")

    # The do-operator
    print("\n5. Applying do-operator...")
    intervened_graph = graph.do_intervention(drug, "active")
    print(f"   Original graph edges: {len(graph.edges)}")
    print(f"   Intervened graph edges: {len(intervened_graph.edges)}")
    print(f"   Edges removed: {len(graph.edges) - len(intervened_graph.edges)}")


def demo_counterfactuals():
    """Demonstrate counterfactual reasoning."""
    print("\n" + "=" * 60)
    print("CAUSAL REASONING DEMO: Counterfactuals")
    print("=" * 60)

    graph = CausalGraph(name="Counterfactual Example")

    aspirin = graph.add_node_by_name("Aspirin")
    headache = graph.add_node_by_name("Headache")
    stress = graph.add_node_by_name("Stress")

    graph.add_edge(stress, headache)
    graph.add_edge(aspirin, headache)

    inference = CausalInference(graph)

    print("\n1. Scenario: Patient took aspirin and headache went away")
    observation = {"Aspirin": 1, "Headache": 0, "Stress": 1}
    print(f"   Observed: {observation}")

    print("\n2. Counterfactual query: What if patient hadn't taken aspirin?")
    result = inference.counterfactual(
        observation=observation,
        intervention={"Aspirin": 0},
        query="Headache"
    )
    print(f"   Result: {result}")


def main():
    """Run all demonstrations."""
    print("\n" + "#" * 60)
    print("# COGNITIVE ARCHITECTURE: Causal Reasoning Demonstration")
    print("#" * 60)

    demo_basic_graph()
    demo_confounding()
    demo_d_separation()
    demo_causal_inference()
    demo_interventions()
    demo_counterfactuals()

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
