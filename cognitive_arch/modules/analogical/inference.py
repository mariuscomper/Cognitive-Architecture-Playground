"""
Analogical inference engine.

Uses analogies to generate new knowledge through:
- Candidate inference projection
- Inference evaluation and filtering
- Multi-analog combination
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid

from .structures import Structure
from .mapping import StructureMapper, Mapping
from .retrieval import AnalogRetriever


@dataclass
class AnalogicalInferenceResult:
    """Result of analogical inference."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    inference_type: str = ""  # relation, attribute, structure
    content: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    source_analogs: List[str] = field(default_factory=list)
    supporting_mappings: int = 0
    conflicting_mappings: int = 0
    evaluation: str = ""
    created_at: datetime = field(default_factory=datetime.now)


class AnalogicalInference:
    """
    Engine for generating and evaluating analogical inferences.

    Combines structural mapping with inference projection to
    generate new knowledge from analogies.
    """

    def __init__(self, retriever: Optional[AnalogRetriever] = None):
        self.retriever = retriever or AnalogRetriever()
        self.mapper = StructureMapper()
        self.inference_history: List[AnalogicalInferenceResult] = []

        # Thresholds for inference acceptance
        self.min_confidence = 0.3
        self.min_support = 1

    def infer(self, target: Structure,
             source: Optional[Structure] = None,
             use_knowledge_base: bool = True,
             n_analogs: int = 3) -> List[AnalogicalInferenceResult]:
        """
        Generate inferences about target from analogies.

        Args:
            target: The structure to make inferences about
            source: Optional specific source analog
            use_knowledge_base: Whether to search knowledge base
            n_analogs: Number of analogs to use from knowledge base

        Returns:
            List of generated inferences
        """
        inferences = []

        if source:
            # Use specific source
            mapping = self.mapper.map_structures(source, target)
            inferences.extend(
                self._extract_inferences(source, target, mapping)
            )
        elif use_knowledge_base:
            # Retrieve from knowledge base
            analogs = self.retriever.retrieve(target, n=n_analogs)
            for analog, score in analogs:
                mapping = self.mapper.map_structures(analog.structure, target)
                analog_inferences = self._extract_inferences(
                    analog.structure, target, mapping
                )
                for inf in analog_inferences:
                    inf.source_analogs.append(analog.structure.name)
                inferences.extend(analog_inferences)

        # Consolidate and evaluate inferences
        consolidated = self._consolidate_inferences(inferences)
        evaluated = self._evaluate_inferences(consolidated, target)

        self.inference_history.extend(evaluated)
        return evaluated

    def _extract_inferences(self, source: Structure, target: Structure,
                           mapping: Mapping) -> List[AnalogicalInferenceResult]:
        """Extract inferences from a mapping."""
        results = []

        for inf in mapping.inferences:
            if inf["type"] == "projected_relation":
                result = AnalogicalInferenceResult(
                    inference_type="relation",
                    content={
                        "relation": inf["relation"],
                        "arguments": inf["arguments"],
                        "projected_from": source.name
                    },
                    confidence=inf["confidence"],
                    source_analogs=[source.name],
                    supporting_mappings=1
                )
                results.append(result)

        # Also infer attributes
        for corr in mapping.correspondences:
            source_elem = source.elements.get(corr.source_id)
            if not source_elem:
                continue

            # Get source attributes
            for attr in source.get_attributes(source_elem.name):
                # Check if target has this attribute
                target_elem = target.elements.get(corr.target_id)
                if not target_elem:
                    continue

                target_attrs = {a.name for a in target.get_attributes(target_elem.name)}
                if attr.name not in target_attrs:
                    result = AnalogicalInferenceResult(
                        inference_type="attribute",
                        content={
                            "entity": target_elem.name,
                            "attribute": attr.name,
                            "inferred_value": attr.value,
                            "from_entity": source_elem.name
                        },
                        confidence=corr.similarity * 0.6,
                        source_analogs=[source.name],
                        supporting_mappings=1
                    )
                    results.append(result)

        return results

    def _consolidate_inferences(self, inferences: List[AnalogicalInferenceResult]
                               ) -> List[AnalogicalInferenceResult]:
        """
        Consolidate similar inferences from multiple sources.

        Inferences about the same thing from multiple analogs
        increase confidence.
        """
        consolidated = {}

        for inf in inferences:
            # Create a key for this inference
            if inf.inference_type == "relation":
                key = (inf.inference_type,
                      inf.content.get("relation"),
                      tuple(inf.content.get("arguments", [])))
            elif inf.inference_type == "attribute":
                key = (inf.inference_type,
                      inf.content.get("entity"),
                      inf.content.get("attribute"))
            else:
                key = (inf.id,)  # Unique

            if key in consolidated:
                # Merge with existing
                existing = consolidated[key]
                existing.supporting_mappings += 1
                existing.source_analogs.extend(inf.source_analogs)
                # Boost confidence for convergent evidence
                boost = 0.1 * (existing.supporting_mappings - 1)
                existing.confidence = min(1.0, existing.confidence + boost)
            else:
                consolidated[key] = inf

        return list(consolidated.values())

    def _evaluate_inferences(self, inferences: List[AnalogicalInferenceResult],
                            target: Structure) -> List[AnalogicalInferenceResult]:
        """
        Evaluate and filter inferences.

        Applies quality criteria and adds evaluation notes.
        """
        evaluated = []

        for inf in inferences:
            # Apply minimum thresholds
            if inf.confidence < self.min_confidence:
                continue

            # Check for conflicts
            has_conflict = self._check_conflict(inf, target)
            if has_conflict:
                inf.conflicting_mappings = 1
                inf.confidence *= 0.5

            # Generate evaluation
            if inf.supporting_mappings > 1:
                inf.evaluation = f"Supported by {inf.supporting_mappings} analogs"
            elif inf.conflicting_mappings > 0:
                inf.evaluation = "Potential conflict with existing structure"
            else:
                inf.evaluation = "Single-source inference"

            evaluated.append(inf)

        # Sort by confidence
        evaluated.sort(key=lambda x: x.confidence, reverse=True)
        return evaluated

    def _check_conflict(self, inference: AnalogicalInferenceResult,
                       target: Structure) -> bool:
        """Check if inference conflicts with existing knowledge."""
        if inference.inference_type == "relation":
            # Check if contradictory relation exists
            rel_name = inference.content.get("relation")
            arguments = inference.content.get("arguments", [])

            # Look for same relation with different arguments
            for rel in target.relations:
                if rel.name == rel_name:
                    # Same relation exists - could be conflict
                    return True

        elif inference.inference_type == "attribute":
            entity_name = inference.content.get("entity")
            attr_name = inference.content.get("attribute")

            # Check if entity already has this attribute with different value
            attrs = target.get_attributes(entity_name)
            for attr in attrs:
                if attr.name == attr_name:
                    if attr.value != inference.content.get("inferred_value"):
                        return True

        return False

    def infer_by_analogy(self, base_domain: str, target_domain: str,
                        base_fact: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Make an inference by explicit analogy.

        Given: "A is to B as C is to D"
        Infer: If fact F holds for A-B, what holds for C-D?
        """
        # This is a simplified proportional analogy
        # base_fact describes something in base_domain
        # We want to project it to target_domain

        base_structure = self.retriever.retrieve(
            Structure(name=base_domain),
            n=1,
            domain=base_domain
        )

        if not base_structure:
            return None

        target_structure = self.retriever.retrieve(
            Structure(name=target_domain),
            n=1,
            domain=target_domain
        )

        if not target_structure:
            return None

        # Map and project
        mapping = self.mapper.map_structures(
            base_structure[0][0].structure,
            target_structure[0][0].structure
        )

        # Transform the fact using the mapping
        projected_fact = {}
        for key, value in base_fact.items():
            # Try to map the value
            if isinstance(value, str):
                # Check if it's an entity name
                base_entity = base_structure[0][0].structure.get_entity(value)
                if base_entity:
                    mapped = mapping.get_target_for(base_entity.id)
                    if mapped:
                        target_elem = target_structure[0][0].structure.elements.get(mapped)
                        if target_elem:
                            projected_fact[key] = target_elem.name
                            continue

            projected_fact[key] = value

        return {
            "original_fact": base_fact,
            "projected_fact": projected_fact,
            "base_domain": base_domain,
            "target_domain": target_domain,
            "confidence": mapping.overall_similarity
        }

    def explain_inference(self, inference: AnalogicalInferenceResult) -> str:
        """Generate explanation for an inference."""
        lines = [f"Analogical Inference ({inference.inference_type})"]
        lines.append("-" * 40)

        if inference.inference_type == "relation":
            rel = inference.content.get("relation")
            args = inference.content.get("arguments", [])
            lines.append(f"Inferred: {rel}({', '.join(args)})")
        elif inference.inference_type == "attribute":
            entity = inference.content.get("entity")
            attr = inference.content.get("attribute")
            value = inference.content.get("inferred_value")
            lines.append(f"Inferred: {entity}.{attr} = {value}")

        lines.append(f"\nConfidence: {inference.confidence:.2f}")
        lines.append(f"Source analogs: {', '.join(inference.source_analogs)}")
        lines.append(f"Supporting mappings: {inference.supporting_mappings}")

        if inference.conflicting_mappings > 0:
            lines.append(f"Conflicting evidence: {inference.conflicting_mappings}")

        lines.append(f"\nEvaluation: {inference.evaluation}")

        return "\n".join(lines)

    def get_best_inferences(self, n: int = 5) -> List[AnalogicalInferenceResult]:
        """Get the n best inferences from history."""
        sorted_inferences = sorted(
            self.inference_history,
            key=lambda x: (x.confidence, x.supporting_mappings),
            reverse=True
        )
        return sorted_inferences[:n]

    def summary(self) -> str:
        """Generate summary of inference activity."""
        lines = ["Analogical Inference Summary"]
        lines.append(f"Total inferences: {len(self.inference_history)}")

        by_type = {}
        for inf in self.inference_history:
            by_type[inf.inference_type] = by_type.get(inf.inference_type, 0) + 1

        if by_type:
            lines.append("\nBy type:")
            for itype, count in by_type.items():
                lines.append(f"  {itype}: {count}")

        high_confidence = [i for i in self.inference_history if i.confidence > 0.7]
        lines.append(f"\nHigh confidence inferences: {len(high_confidence)}")

        return "\n".join(lines)
