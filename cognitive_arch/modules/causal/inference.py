"""
Causal Inference engine.

This module implements causal inference algorithms for:
- Estimating causal effects from observational data
- Identifying causal relationships
- Counterfactual reasoning
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum, auto
import math
import uuid

from .graph import CausalGraph, CausalNode


class EffectType(Enum):
    """Types of causal effects."""
    TOTAL = auto()      # Total effect of X on Y
    DIRECT = auto()     # Direct effect (not through mediators)
    INDIRECT = auto()   # Indirect effect (through mediators)
    CONTROLLED = auto() # Effect controlling for specific variables


@dataclass
class CausalEffect:
    """Represents an estimated causal effect."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    treatment: str = ""
    outcome: str = ""
    effect_type: EffectType = EffectType.TOTAL
    estimate: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    p_value: Optional[float] = None
    adjustment_set: List[str] = field(default_factory=list)
    method: str = ""
    assumptions: List[str] = field(default_factory=list)
    is_identifiable: bool = True
    explanation: str = ""


class CausalInference:
    """
    Engine for causal inference and effect estimation.

    Provides methods for:
    - Checking identifiability of causal effects
    - Estimating effects using various methods
    - Counterfactual reasoning
    - Sensitivity analysis
    """

    def __init__(self, graph: CausalGraph):
        self.graph = graph
        self.data: Dict[str, List[float]] = {}  # Variable -> observations
        self.results: List[CausalEffect] = []

    def set_data(self, variable: str, observations: List[float]) -> None:
        """Set observational data for a variable."""
        self.data[variable] = observations

    def is_identifiable(self, treatment: str, outcome: str) -> Tuple[bool, str]:
        """
        Check if the causal effect of treatment on outcome is identifiable.

        An effect is identifiable if it can be computed from observational data
        given the causal graph structure.
        """
        treatment_node = self.graph.get_node_by_name(treatment)
        outcome_node = self.graph.get_node_by_name(outcome)

        if not treatment_node or not outcome_node:
            return False, "Treatment or outcome not found in graph"

        # Check for valid adjustment set
        adjustment_set = self.graph.get_minimal_adjustment_set(
            treatment_node.id, outcome_node.id
        )

        if adjustment_set is not None:
            names = [self.graph.nodes[n].name for n in adjustment_set]
            return True, f"Identifiable via adjustment for: {', '.join(names) or 'nothing'}"

        # Check for instrumental variables
        instruments = self._find_instruments(treatment_node.id, outcome_node.id)
        if instruments:
            names = [self.graph.nodes[n].name for n in instruments]
            return True, f"Identifiable via instrumental variable: {', '.join(names)}"

        # Check front-door criterion
        if self._check_front_door(treatment_node.id, outcome_node.id):
            return True, "Identifiable via front-door adjustment"

        return False, "Effect not identifiable from observational data"

    def _find_instruments(self, treatment_id: str, outcome_id: str) -> List[str]:
        """
        Find instrumental variables for the treatment-outcome relationship.

        An instrumental variable Z must:
        1. Be associated with treatment X
        2. Not be associated with outcome Y except through X
        3. Not share a common cause with Y
        """
        instruments = []

        # Candidates are nodes connected to treatment but not to outcome directly
        treatment_parents = self.graph.get_parents(treatment_id)
        outcome_ancestors = self.graph.get_ancestors(outcome_id)
        confounders = self.graph.get_confounders(treatment_id, outcome_id)

        for node_id in self.graph.nodes:
            if node_id in (treatment_id, outcome_id):
                continue

            # Check if node is connected to treatment
            connected_to_treatment = (
                node_id in treatment_parents or
                treatment_id in self.graph.get_descendants(node_id)
            )

            if not connected_to_treatment:
                continue

            # Check if node only affects outcome through treatment
            node_descendants = self.graph.get_descendants(node_id)
            if outcome_id in node_descendants and treatment_id not in node_descendants:
                continue  # Direct path to outcome

            # Check no common cause with outcome (outside treatment path)
            node_ancestors = self.graph.get_ancestors(node_id)
            common_with_outcome = node_ancestors & outcome_ancestors
            if common_with_outcome - self.graph.get_ancestors(treatment_id):
                continue  # Shared ancestor outside treatment path

            instruments.append(node_id)

        return instruments

    def _check_front_door(self, treatment_id: str, outcome_id: str) -> bool:
        """
        Check if the front-door criterion can be used.

        The front-door criterion applies when:
        1. Treatment fully mediates through observable mediators M
        2. No backdoor path from treatment to M
        3. Confounders of treatment-outcome are blocked by treatment for M-outcome
        """
        mediators = self.graph.get_mediators(treatment_id, outcome_id)

        if not mediators:
            return False

        # All direct paths must go through mediators
        direct_paths = self.graph.find_all_paths(treatment_id, outcome_id)
        for path in direct_paths:
            if len(path) == 2:  # Direct edge
                return False  # Has direct effect not through mediator
            # Check if path goes through at least one mediator
            path_mediators = set(path[1:-1]) & mediators
            if not path_mediators:
                return False

        return True

    def estimate_effect(self, treatment: str, outcome: str,
                       method: str = "auto") -> CausalEffect:
        """
        Estimate the causal effect of treatment on outcome.

        Methods:
        - "adjustment": Covariate adjustment
        - "ipw": Inverse probability weighting
        - "iv": Instrumental variables
        - "auto": Automatically select method
        """
        treatment_node = self.graph.get_node_by_name(treatment)
        outcome_node = self.graph.get_node_by_name(outcome)

        if not treatment_node or not outcome_node:
            return CausalEffect(
                treatment=treatment,
                outcome=outcome,
                is_identifiable=False,
                explanation="Treatment or outcome not found in graph"
            )

        identifiable, explanation = self.is_identifiable(treatment, outcome)

        if not identifiable:
            return CausalEffect(
                treatment=treatment,
                outcome=outcome,
                is_identifiable=False,
                explanation=explanation
            )

        # Select method
        if method == "auto":
            adjustment_set = self.graph.get_minimal_adjustment_set(
                treatment_node.id, outcome_node.id
            )
            if adjustment_set is not None:
                method = "adjustment"
            else:
                instruments = self._find_instruments(treatment_node.id, outcome_node.id)
                if instruments:
                    method = "iv"
                else:
                    method = "front_door"

        # Perform estimation
        if method == "adjustment":
            return self._estimate_by_adjustment(treatment_node, outcome_node)
        elif method == "iv":
            return self._estimate_by_iv(treatment_node, outcome_node)
        elif method == "front_door":
            return self._estimate_by_front_door(treatment_node, outcome_node)
        else:
            return self._estimate_by_adjustment(treatment_node, outcome_node)

    def _estimate_by_adjustment(self, treatment: CausalNode,
                               outcome: CausalNode) -> CausalEffect:
        """Estimate effect using covariate adjustment."""
        adjustment_set = self.graph.get_minimal_adjustment_set(treatment.id, outcome.id)
        adj_names = [self.graph.nodes[n].name for n in adjustment_set] if adjustment_set else []

        # Check if we have data
        if treatment.name not in self.data or outcome.name not in self.data:
            return CausalEffect(
                treatment=treatment.name,
                outcome=outcome.name,
                effect_type=EffectType.TOTAL,
                estimate=None,
                adjustment_set=adj_names,
                method="adjustment",
                assumptions=[
                    "No unmeasured confounding",
                    "Correct causal graph specification",
                    "Positivity (all covariate combinations possible)"
                ],
                explanation=f"Effect identifiable via adjustment for: {', '.join(adj_names) or 'nothing'}. "
                           f"Data required for actual estimation."
            )

        # Simple difference in means if no adjustment needed
        if not adjustment_set:
            t_data = self.data[treatment.name]
            y_data = self.data[outcome.name]

            if len(t_data) != len(y_data):
                return CausalEffect(
                    treatment=treatment.name,
                    outcome=outcome.name,
                    is_identifiable=True,
                    explanation="Data length mismatch"
                )

            # Simple correlation/regression coefficient
            n = len(t_data)
            mean_t = sum(t_data) / n
            mean_y = sum(y_data) / n

            cov = sum((t - mean_t) * (y - mean_y) for t, y in zip(t_data, y_data)) / n
            var_t = sum((t - mean_t) ** 2 for t in t_data) / n

            if var_t == 0:
                estimate = 0.0
            else:
                estimate = cov / var_t

            # Simple confidence interval approximation
            se = math.sqrt((1 - (estimate ** 2)) / (n - 2)) if n > 2 else 0
            ci = (estimate - 1.96 * se, estimate + 1.96 * se)

            return CausalEffect(
                treatment=treatment.name,
                outcome=outcome.name,
                effect_type=EffectType.TOTAL,
                estimate=estimate,
                confidence_interval=ci,
                adjustment_set=[],
                method="adjustment",
                assumptions=[
                    "Linear relationship",
                    "No unmeasured confounding",
                    "Correct graph specification"
                ],
                explanation=f"Estimated effect: {estimate:.3f} (95% CI: {ci[0]:.3f}, {ci[1]:.3f})"
            )

        return CausalEffect(
            treatment=treatment.name,
            outcome=outcome.name,
            effect_type=EffectType.TOTAL,
            estimate=None,
            adjustment_set=adj_names,
            method="adjustment",
            explanation=f"Adjustment required for: {', '.join(adj_names)}. Full data needed."
        )

    def _estimate_by_iv(self, treatment: CausalNode,
                       outcome: CausalNode) -> CausalEffect:
        """Estimate effect using instrumental variables."""
        instruments = self._find_instruments(treatment.id, outcome.id)
        inst_names = [self.graph.nodes[i].name for i in instruments]

        return CausalEffect(
            treatment=treatment.name,
            outcome=outcome.name,
            effect_type=EffectType.TOTAL,
            estimate=None,
            adjustment_set=inst_names,
            method="instrumental_variables",
            assumptions=[
                "Instrument relevance (strong first stage)",
                "Exclusion restriction",
                "No instrument-outcome confounding"
            ],
            explanation=f"Identified via instruments: {', '.join(inst_names)}"
        )

    def _estimate_by_front_door(self, treatment: CausalNode,
                                outcome: CausalNode) -> CausalEffect:
        """Estimate effect using front-door adjustment."""
        mediators = self.graph.get_mediators(treatment.id, outcome.id)
        med_names = [self.graph.nodes[m].name for m in mediators]

        return CausalEffect(
            treatment=treatment.name,
            outcome=outcome.name,
            effect_type=EffectType.TOTAL,
            estimate=None,
            adjustment_set=med_names,
            method="front_door",
            assumptions=[
                "Complete mediation through observed mediators",
                "No backdoor path treatment to mediators",
                "Correct graph specification"
            ],
            explanation=f"Identified via front-door through: {', '.join(med_names)}"
        )

    def counterfactual(self, observation: Dict[str, Any],
                      intervention: Dict[str, Any],
                      query: str) -> Dict[str, Any]:
        """
        Answer a counterfactual query.

        Given an observation of what happened, and a hypothetical intervention,
        what would the query variable have been?

        Example:
            observation = {"treatment": 0, "outcome": 1}
            intervention = {"treatment": 1}
            query = "outcome"
            -> "What would outcome have been if treatment were 1?"
        """
        # This is a simplified counterfactual analysis
        # Full implementation would require structural equations

        query_node = self.graph.get_node_by_name(query)
        if not query_node:
            return {"error": f"Query variable '{query}' not found"}

        # Find what changes with the intervention
        intervention_effects = {}
        for var, value in intervention.items():
            node = self.graph.get_node_by_name(var)
            if node:
                descendants = self.graph.get_descendants(node.id)
                for desc_id in descendants:
                    desc_name = self.graph.nodes[desc_id].name
                    intervention_effects[desc_name] = f"Affected by do({var}={value})"

        if query in intervention:
            return {
                "query": query,
                "counterfactual_value": intervention[query],
                "reasoning": f"{query} was directly set by intervention",
                "certainty": "deterministic"
            }

        if query in intervention_effects:
            return {
                "query": query,
                "counterfactual_value": None,  # Would need structural equations
                "reasoning": intervention_effects[query],
                "certainty": "structural equations required for exact value"
            }

        return {
            "query": query,
            "counterfactual_value": observation.get(query),
            "reasoning": f"{query} not affected by intervention",
            "certainty": "no change from observed"
        }

    def sensitivity_analysis(self, treatment: str, outcome: str,
                            unmeasured_confounder_strength: float = 0.5
                            ) -> Dict[str, Any]:
        """
        Perform sensitivity analysis for unmeasured confounding.

        Analyzes how robust the causal estimate is to potential
        unmeasured confounders.
        """
        effect = self.estimate_effect(treatment, outcome)

        if effect.estimate is None:
            return {
                "warning": "No effect estimate available",
                "robust": None
            }

        # Simulate effect of unmeasured confounder
        bias = unmeasured_confounder_strength * abs(effect.estimate)

        return {
            "original_estimate": effect.estimate,
            "confounder_strength": unmeasured_confounder_strength,
            "potential_bias": bias,
            "adjusted_range": (effect.estimate - bias, effect.estimate + bias),
            "sign_robust": effect.estimate > 0 and (effect.estimate - bias) > 0 or
                          effect.estimate < 0 and (effect.estimate + bias) < 0,
            "interpretation": (
                f"If unmeasured confounder has {unmeasured_confounder_strength:.0%} "
                f"of the effect of treatment, the true effect could range from "
                f"{effect.estimate - bias:.3f} to {effect.estimate + bias:.3f}"
            )
        }

    def decompose_effect(self, treatment: str, outcome: str,
                        mediator: str) -> Dict[str, CausalEffect]:
        """
        Decompose total effect into direct and indirect effects.

        The indirect effect goes through the specified mediator.
        """
        treatment_node = self.graph.get_node_by_name(treatment)
        outcome_node = self.graph.get_node_by_name(outcome)
        mediator_node = self.graph.get_node_by_name(mediator)

        if not all([treatment_node, outcome_node, mediator_node]):
            return {"error": "One or more variables not found"}

        # Total effect
        total = self.estimate_effect(treatment, outcome)
        total.effect_type = EffectType.TOTAL

        # Direct effect (controlling for mediator)
        direct = CausalEffect(
            treatment=treatment,
            outcome=outcome,
            effect_type=EffectType.DIRECT,
            adjustment_set=[mediator],
            method="mediation_analysis",
            assumptions=[
                "No mediator-outcome confounding",
                "No treatment-mediator interaction"
            ],
            explanation=f"Direct effect of {treatment} on {outcome} not through {mediator}"
        )

        # Indirect effect (through mediator)
        indirect = CausalEffect(
            treatment=treatment,
            outcome=outcome,
            effect_type=EffectType.INDIRECT,
            adjustment_set=[mediator],
            method="mediation_analysis",
            explanation=f"Indirect effect of {treatment} on {outcome} through {mediator}"
        )

        return {
            "total": total,
            "direct": direct,
            "indirect": indirect,
            "mediator": mediator
        }

    def summary(self) -> str:
        """Generate a summary of causal inference results."""
        lines = ["Causal Inference Summary"]
        lines.append("=" * 40)
        lines.append(f"Graph: {self.graph.name}")
        lines.append(f"Variables with data: {len(self.data)}")
        lines.append(f"Effects estimated: {len(self.results)}")

        if self.results:
            lines.append("\nRecent results:")
            for effect in self.results[-5:]:
                id_str = "identifiable" if effect.is_identifiable else "NOT identifiable"
                est_str = f"= {effect.estimate:.3f}" if effect.estimate else ""
                lines.append(
                    f"  {effect.treatment} -> {effect.outcome}: {id_str} {est_str}"
                )

        return "\n".join(lines)
