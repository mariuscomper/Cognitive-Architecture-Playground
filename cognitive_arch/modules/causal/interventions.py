"""
Intervention analysis for causal reasoning.

This module analyzes the effects of hypothetical interventions,
helping answer "what if" questions about causal systems.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
import uuid

from .graph import CausalGraph, CausalNode, NodeType


@dataclass
class Intervention:
    """Represents an intervention on a causal system."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    variable: str = ""
    value: Any = None
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class InterventionOutcome:
    """The predicted outcome of an intervention."""
    intervention: Intervention = field(default_factory=Intervention)
    affected_variables: List[str] = field(default_factory=list)
    predicted_changes: Dict[str, str] = field(default_factory=dict)
    side_effects: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    confidence: float = 0.5


class InterventionAnalyzer:
    """
    Analyzes interventions on causal systems.

    Provides:
    - Prediction of intervention effects
    - Side effect detection
    - Intervention comparison
    - Optimal intervention selection
    """

    def __init__(self, graph: CausalGraph):
        self.graph = graph
        self.history: List[InterventionOutcome] = []

    def analyze_intervention(self, variable: str, value: Any = None,
                            description: str = "") -> InterventionOutcome:
        """
        Analyze the effects of an intervention do(variable = value).

        Returns predicted changes and potential side effects.
        """
        intervention = Intervention(
            variable=variable,
            value=value,
            description=description
        )

        node = self.graph.get_node_by_name(variable)
        if not node:
            return InterventionOutcome(
                intervention=intervention,
                warnings=[f"Variable '{variable}' not found in causal graph"]
            )

        # Get affected variables (descendants)
        descendants = self.graph.get_descendants(node.id)
        affected_names = [self.graph.nodes[d].name for d in descendants]

        # Predict changes
        predicted_changes = {}
        for desc_id in descendants:
            desc_node = self.graph.nodes[desc_id]
            # Trace causal path
            paths = self.graph.find_all_paths(node.id, desc_id)
            if paths:
                path_names = [
                    " -> ".join(self.graph.nodes[n].name for n in path)
                    for path in paths[:3]  # Limit to 3 paths
                ]
                predicted_changes[desc_node.name] = f"Via: {'; '.join(path_names)}"

        # Detect side effects (unintended consequences)
        side_effects = []
        for desc_id in descendants:
            desc_node = self.graph.nodes[desc_id]
            # Check if this variable has other effects
            desc_descendants = self.graph.get_descendants(desc_id)
            for dd_id in desc_descendants:
                if dd_id not in descendants:
                    dd_name = self.graph.nodes[dd_id].name
                    side_effects.append(
                        f"Intervention may cascade to {dd_name} via {desc_node.name}"
                    )

        # Check for latent confounders
        warnings = []
        for other_id in self.graph.nodes:
            other = self.graph.nodes[other_id]
            if other.node_type == NodeType.LATENT:
                if other_id in self.graph.get_ancestors(node.id):
                    warnings.append(
                        f"Latent variable '{other.name}' may affect intervention response"
                    )

        outcome = InterventionOutcome(
            intervention=intervention,
            affected_variables=affected_names,
            predicted_changes=predicted_changes,
            side_effects=side_effects,
            warnings=warnings,
            confidence=0.7 if not warnings else 0.5
        )

        self.history.append(outcome)
        return outcome

    def compare_interventions(self, interventions: List[Tuple[str, Any]],
                             target: str) -> Dict[str, Any]:
        """
        Compare multiple possible interventions for achieving a target outcome.

        Args:
            interventions: List of (variable, value) tuples
            target: The target variable we want to affect

        Returns:
            Comparison of intervention effectiveness
        """
        target_node = self.graph.get_node_by_name(target)
        if not target_node:
            return {"error": f"Target '{target}' not found"}

        comparisons = []

        for variable, value in interventions:
            outcome = self.analyze_intervention(variable, value)

            affects_target = target in outcome.affected_variables

            # Count paths to target
            var_node = self.graph.get_node_by_name(variable)
            if var_node:
                paths = self.graph.find_all_paths(var_node.id, target_node.id)
                path_count = len(paths)
                shortest_path = min(len(p) for p in paths) if paths else None
            else:
                path_count = 0
                shortest_path = None

            comparisons.append({
                "intervention": f"do({variable} = {value})",
                "affects_target": affects_target,
                "path_count": path_count,
                "shortest_path_length": shortest_path,
                "side_effects_count": len(outcome.side_effects),
                "warnings_count": len(outcome.warnings),
                "confidence": outcome.confidence
            })

        # Rank by effectiveness (affects target, fewer side effects, shorter path)
        def score(c):
            if not c["affects_target"]:
                return -1000
            path_penalty = (c["shortest_path_length"] or 10) * 0.1
            side_effect_penalty = c["side_effects_count"] * 0.2
            warning_penalty = c["warnings_count"] * 0.3
            return c["confidence"] - path_penalty - side_effect_penalty - warning_penalty

        comparisons.sort(key=score, reverse=True)

        best = comparisons[0] if comparisons else None

        return {
            "target": target,
            "comparisons": comparisons,
            "recommended": best["intervention"] if best and best["affects_target"] else None,
            "recommendation_reason": (
                f"Most direct path ({best['shortest_path_length']} steps) with "
                f"fewest side effects ({best['side_effects_count']})"
                if best and best["affects_target"] else
                "No intervention affects target"
            )
        }

    def find_intervention_targets(self, outcome: str,
                                 desired_direction: str = "increase"
                                 ) -> List[Dict[str, Any]]:
        """
        Find variables that could be intervened on to affect an outcome.

        Args:
            outcome: The outcome variable to affect
            desired_direction: "increase" or "decrease"

        Returns:
            List of potential intervention targets with analysis
        """
        outcome_node = self.graph.get_node_by_name(outcome)
        if not outcome_node:
            return []

        # Find all ancestors of outcome (potential intervention points)
        ancestors = self.graph.get_ancestors(outcome_node.id)
        targets = []

        for anc_id in ancestors:
            anc_node = self.graph.nodes[anc_id]

            # Skip latent variables (can't intervene on them)
            if anc_node.node_type == NodeType.LATENT:
                continue

            # Analyze path to outcome
            paths = self.graph.find_all_paths(anc_id, outcome_node.id)
            shortest_path = min(len(p) for p in paths) if paths else None

            # Check for competing effects (might cancel out)
            path_count = len(paths)
            competing = path_count > 1  # Multiple paths might have opposing effects

            # Get other affected variables (collateral effects)
            descendants = self.graph.get_descendants(anc_id)
            other_effects = len(descendants - {outcome_node.id})

            targets.append({
                "variable": anc_node.name,
                "distance_to_outcome": shortest_path,
                "path_count": path_count,
                "competing_paths": competing,
                "other_effects_count": other_effects,
                "is_root": len(self.graph.get_parents(anc_id)) == 0,
                "recommendation": self._recommend_target(
                    shortest_path, competing, other_effects
                )
            })

        # Sort by recommendation quality
        targets.sort(key=lambda t: (
            0 if "Good" in t["recommendation"] else
            1 if "Moderate" in t["recommendation"] else 2,
            t["distance_to_outcome"] or 10,
            t["other_effects_count"]
        ))

        return targets

    def _recommend_target(self, distance: Optional[int], competing: bool,
                         other_effects: int) -> str:
        """Generate a recommendation for an intervention target."""
        if distance == 1 and not competing and other_effects < 2:
            return "Good: Direct effect, minimal side effects"
        elif distance == 1 and other_effects < 3:
            return "Moderate: Direct but has some side effects"
        elif not competing and other_effects < 3:
            return "Moderate: Indirect but focused effect"
        elif competing:
            return "Caution: Multiple paths may have opposing effects"
        else:
            return "Uncertain: Complex causal structure"

    def suggest_minimal_intervention(self, current_state: Dict[str, Any],
                                    desired_outcome: Dict[str, Any]
                                    ) -> Dict[str, Any]:
        """
        Suggest the minimal intervention to achieve a desired outcome.

        Tries to find the intervention that:
        1. Achieves the desired outcome
        2. Changes the fewest other variables
        3. Has highest confidence
        """
        interventions_needed = []

        for outcome_var, desired_value in desired_outcome.items():
            current_value = current_state.get(outcome_var)

            if current_value == desired_value:
                continue  # Already at desired state

            # Find potential intervention points
            targets = self.find_intervention_targets(outcome_var)

            if targets:
                best = targets[0]  # Already sorted by quality
                interventions_needed.append({
                    "target_variable": best["variable"],
                    "to_affect": outcome_var,
                    "current_value": current_value,
                    "desired_value": desired_value,
                    "confidence": 0.8 if "Good" in best["recommendation"] else 0.5
                })
            else:
                interventions_needed.append({
                    "target_variable": outcome_var,
                    "to_affect": outcome_var,
                    "current_value": current_value,
                    "desired_value": desired_value,
                    "confidence": 0.9,  # Direct intervention
                    "note": "Direct intervention on outcome (if possible)"
                })

        return {
            "current_state": current_state,
            "desired_outcome": desired_outcome,
            "suggested_interventions": interventions_needed,
            "total_interventions": len(interventions_needed)
        }

    def predict_cascade(self, intervention: str, value: Any,
                       steps: int = 3) -> List[Dict[str, Any]]:
        """
        Predict the cascade of effects from an intervention over time.

        Models how effects propagate through the causal network.
        """
        node = self.graph.get_node_by_name(intervention)
        if not node:
            return []

        cascade = [{
            "step": 0,
            "changes": {intervention: f"Set to {value} (intervention)"},
            "cumulative_affected": {intervention}
        }]

        current_frontier = {node.id}
        all_affected = {node.id}

        for step in range(1, steps + 1):
            next_frontier = set()
            step_changes = {}

            for frontier_id in current_frontier:
                children = self.graph.get_children(frontier_id)
                for child_id in children:
                    if child_id not in all_affected:
                        child_name = self.graph.nodes[child_id].name
                        parent_name = self.graph.nodes[frontier_id].name
                        step_changes[child_name] = f"Affected by change in {parent_name}"
                        next_frontier.add(child_id)
                        all_affected.add(child_id)

            if not next_frontier:
                break

            cascade.append({
                "step": step,
                "changes": step_changes,
                "cumulative_affected": {self.graph.nodes[n].name for n in all_affected}
            })

            current_frontier = next_frontier

        return cascade

    def summarize_history(self) -> str:
        """Summarize intervention analysis history."""
        lines = [f"Intervention Analysis History: {len(self.history)} analyses"]

        for outcome in self.history[-5:]:
            lines.append(f"\n  do({outcome.intervention.variable})")
            lines.append(f"    Affects: {', '.join(outcome.affected_variables[:3])}")
            if outcome.warnings:
                lines.append(f"    Warnings: {len(outcome.warnings)}")

        return "\n".join(lines)
