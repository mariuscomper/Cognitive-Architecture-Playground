"""
Structure mapping for analogical reasoning.

Implements the core structure-mapping algorithm for finding
correspondences between analogous domains.

Based on Gentner's Structure-Mapping Engine (SME) theory,
which emphasizes systematic relational structure over
surface features.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple, FrozenSet
from enum import Enum, auto
import uuid
from itertools import permutations

from .structures import Structure, StructureElement, Relation, ElementType


@dataclass
class Correspondence:
    """A mapping between elements in two structures."""
    source_id: str
    target_id: str
    similarity: float = 0.0
    confidence: float = 1.0
    evidence: List[str] = field(default_factory=list)


@dataclass
class Mapping:
    """A complete mapping between two structures."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_structure: str = ""
    target_structure: str = ""
    correspondences: List[Correspondence] = field(default_factory=list)
    overall_similarity: float = 0.0
    systematicity: float = 0.0  # How systematic/coherent is the mapping
    coverage: float = 0.0  # How much of the structures are mapped
    inferences: List[Dict[str, Any]] = field(default_factory=list)

    def get_target_for(self, source_id: str) -> Optional[str]:
        """Get the target element mapped to a source element."""
        for corr in self.correspondences:
            if corr.source_id == source_id:
                return corr.target_id
        return None

    def get_source_for(self, target_id: str) -> Optional[str]:
        """Get the source element mapped to a target element."""
        for corr in self.correspondences:
            if corr.target_id == target_id:
                return corr.source_id
        return None


class StructureMapper:
    """
    Maps structure between analogous domains.

    Implements key principles of structure-mapping theory:
    1. Structural consistency: 1-to-1 mappings
    2. Parallel connectivity: If relations map, their arguments should too
    3. Systematicity: Prefer mappings with higher-order structure
    """

    def __init__(self):
        self.cache: Dict[Tuple[str, str], Mapping] = {}

    def map_structures(self, source: Structure, target: Structure,
                      prefer_relations: bool = True) -> Mapping:
        """
        Create a mapping between source and target structures.

        Args:
            source: The source (base) structure
            target: The target structure
            prefer_relations: Weight relational matches higher than attributes

        Returns:
            The best mapping found
        """
        cache_key = (source.id, target.id)
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Step 1: Find local matches (potential correspondences)
        local_matches = self._find_local_matches(source, target)

        # Step 2: Build consistent global mappings
        global_mappings = self._build_global_mappings(source, target, local_matches)

        # Step 3: Score and select best mapping
        if not global_mappings:
            mapping = Mapping(
                source_structure=source.name,
                target_structure=target.name,
                overall_similarity=0.0
            )
        else:
            # Score each mapping
            scored = []
            for mapping in global_mappings:
                score = self._score_mapping(source, target, mapping, prefer_relations)
                scored.append((score, mapping))

            scored.sort(key=lambda x: x[0], reverse=True)
            best_score, best_mapping = scored[0]

            best_mapping.overall_similarity = best_score
            best_mapping.source_structure = source.name
            best_mapping.target_structure = target.name
            mapping = best_mapping

        # Step 4: Generate inferences from the mapping
        mapping.inferences = self._generate_inferences(source, target, mapping)

        self.cache[cache_key] = mapping
        return mapping

    def _find_local_matches(self, source: Structure, target: Structure
                           ) -> Dict[str, List[Tuple[str, float]]]:
        """
        Find potential local matches between elements.

        Returns a dict mapping source element IDs to lists of
        (target_id, similarity_score) tuples.
        """
        matches: Dict[str, List[Tuple[str, float]]] = {}

        # Match entities (based on attributes and connected relations)
        source_entities = source.get_entities()
        target_entities = target.get_entities()

        for se in source_entities:
            matches[se.id] = []
            for te in target_entities:
                sim = self._element_similarity(source, se, target, te)
                if sim > 0:
                    matches[se.id].append((te.id, sim))

        # Match relations (based on name and arity)
        for sr in source.relations:
            # Create a pseudo-ID for the relation
            sr_id = f"rel:{sr.name}:{sr.arguments}"
            matches[sr_id] = []

            for tr in target.relations:
                if sr.name == tr.name and len(sr.arguments) == len(tr.arguments):
                    # Same relation type and arity
                    tr_id = f"rel:{tr.name}:{tr.arguments}"
                    matches[sr_id].append((tr_id, 1.0))
                elif len(sr.arguments) == len(tr.arguments):
                    # Same arity, different name - partial match
                    tr_id = f"rel:{tr.name}:{tr.arguments}"
                    matches[sr_id].append((tr_id, 0.3))

        return matches

    def _element_similarity(self, source: Structure, se: StructureElement,
                           target: Structure, te: StructureElement) -> float:
        """Compute similarity between two elements."""
        # Same type is required
        if se.element_type != te.element_type:
            return 0.0

        score = 0.5  # Base score for type match

        # Attribute similarity
        if se.element_type == ElementType.ENTITY:
            source_attrs = {a.name: a.value for a in source.get_attributes(se.name)}
            target_attrs = {a.name: a.value for a in target.get_attributes(te.name)}

            # Count matching attribute names
            common = set(source_attrs.keys()) & set(target_attrs.keys())
            all_attrs = set(source_attrs.keys()) | set(target_attrs.keys())

            if all_attrs:
                attr_similarity = len(common) / len(all_attrs)
                score += 0.3 * attr_similarity

            # Relational similarity (same types of relations)
            source_rels = {r.name for r in source.get_relations(se.name)}
            target_rels = {r.name for r in target.get_relations(te.name)}

            common_rels = source_rels & target_rels
            all_rels = source_rels | target_rels

            if all_rels:
                rel_similarity = len(common_rels) / len(all_rels)
                score += 0.2 * rel_similarity

        return min(1.0, score)

    def _build_global_mappings(self, source: Structure, target: Structure,
                               local_matches: Dict[str, List[Tuple[str, float]]]
                               ) -> List[Mapping]:
        """
        Build structurally consistent global mappings from local matches.

        Enforces 1-to-1 constraint and parallel connectivity.
        """
        mappings = []

        # Get entity mappings first (most constrained)
        source_entities = [e.id for e in source.get_entities()]
        target_entities = [e.id for e in target.get_entities()]

        if not source_entities or not target_entities:
            return mappings

        # Try different entity alignments
        # For efficiency, limit to top matches
        def get_top_matches(sid: str, n: int = 3) -> List[str]:
            matches = local_matches.get(sid, [])
            matches.sort(key=lambda x: x[1], reverse=True)
            return [m[0] for m in matches[:n]]

        # Generate candidate mappings using greedy matching
        used_targets: Set[str] = set()
        correspondences: List[Correspondence] = []

        for se_id in source_entities:
            best_match = None
            best_score = 0.0

            for te_id, score in local_matches.get(se_id, []):
                if te_id not in used_targets and score > best_score:
                    best_match = te_id
                    best_score = score

            if best_match:
                used_targets.add(best_match)
                correspondences.append(Correspondence(
                    source_id=se_id,
                    target_id=best_match,
                    similarity=best_score
                ))

        if correspondences:
            mapping = Mapping(correspondences=correspondences)
            mapping.coverage = len(correspondences) / len(source_entities)
            mappings.append(mapping)

        # Also try a second greedy pass with different ordering
        # (reversed to potentially find different mapping)
        used_targets = set()
        correspondences = []

        for se_id in reversed(source_entities):
            best_match = None
            best_score = 0.0

            for te_id, score in local_matches.get(se_id, []):
                if te_id not in used_targets and score > best_score:
                    best_match = te_id
                    best_score = score

            if best_match:
                used_targets.add(best_match)
                correspondences.append(Correspondence(
                    source_id=se_id,
                    target_id=best_match,
                    similarity=best_score
                ))

        if correspondences and len(mappings) < 2:
            mapping = Mapping(correspondences=correspondences)
            mapping.coverage = len(correspondences) / len(source_entities)
            mappings.append(mapping)

        return mappings

    def _score_mapping(self, source: Structure, target: Structure,
                      mapping: Mapping, prefer_relations: bool) -> float:
        """
        Score a mapping based on structural criteria.

        Considers:
        - Element similarity (from correspondences)
        - Parallel connectivity (relations preserved)
        - Systematicity (higher-order structure preserved)
        """
        if not mapping.correspondences:
            return 0.0

        # Base score from correspondences
        base_score = sum(c.similarity for c in mapping.correspondences)
        base_score /= len(mapping.correspondences)

        # Parallel connectivity score
        parallel_score = self._compute_parallel_connectivity(source, target, mapping)

        # Systematicity score
        systematicity = self._compute_systematicity(source, target, mapping)
        mapping.systematicity = systematicity

        # Combine scores
        if prefer_relations:
            total = 0.3 * base_score + 0.4 * parallel_score + 0.3 * systematicity
        else:
            total = 0.5 * base_score + 0.3 * parallel_score + 0.2 * systematicity

        return total

    def _compute_parallel_connectivity(self, source: Structure, target: Structure,
                                       mapping: Mapping) -> float:
        """
        Compute how well relational structure is preserved.

        For each relation in source, check if the corresponding relation
        exists in target with mapped arguments.
        """
        if not source.relations:
            return 1.0  # No relations to match

        matched_relations = 0

        for sr in source.relations:
            # Map the arguments
            mapped_args = []
            for arg_id in sr.arguments:
                mapped = mapping.get_target_for(arg_id)
                if mapped:
                    mapped_args.append(mapped)
                else:
                    break

            if len(mapped_args) != len(sr.arguments):
                continue  # Not all arguments could be mapped

            # Check if corresponding relation exists in target
            for tr in target.relations:
                if tr.name == sr.name and list(tr.arguments) == mapped_args:
                    matched_relations += 1
                    break

        return matched_relations / len(source.relations)

    def _compute_systematicity(self, source: Structure, target: Structure,
                               mapping: Mapping) -> float:
        """
        Compute systematicity of the mapping.

        Higher systematicity means more higher-order structure is preserved.
        """
        # Check depth of structure preserved
        source_depth = source.structural_depth()
        if source_depth == 0:
            return 0.5  # Neutral for flat structures

        # Check if higher-order relations are preserved
        source_ho = list(source._by_type[ElementType.HIGHER_ORDER])

        if not source_ho:
            # No higher-order structure - base on relation preservation
            return 0.5

        preserved_ho = 0
        for ho_id in source_ho:
            ho_elem = source.elements[ho_id]
            # Check if the relations it connects are preserved
            relations_preserved = True
            for arg_id in ho_elem.arguments:
                if arg_id in source.elements:
                    # Need corresponding relation in target
                    # Simplified check
                    pass

            if relations_preserved:
                preserved_ho += 1

        if source_ho:
            return preserved_ho / len(source_ho)
        return 0.5

    def _generate_inferences(self, source: Structure, target: Structure,
                            mapping: Mapping) -> List[Dict[str, Any]]:
        """
        Generate candidate inferences from the mapping.

        These are elements in source that could be projected to target.
        """
        inferences = []

        # Find source elements not yet in target
        for sr in source.relations:
            # Map arguments to target
            mapped_args = []
            can_project = True

            for arg_id in sr.arguments:
                mapped = mapping.get_target_for(arg_id)
                if mapped:
                    mapped_args.append(mapped)
                else:
                    can_project = False
                    break

            if not can_project:
                continue

            # Check if this relation already exists in target
            exists = False
            for tr in target.relations:
                if tr.name == sr.name and list(tr.arguments) == mapped_args:
                    exists = True
                    break

            if not exists:
                # Candidate inference!
                arg_names = [
                    target.elements[aid].name if aid in target.elements else "?"
                    for aid in mapped_args
                ]
                inferences.append({
                    "type": "projected_relation",
                    "relation": sr.name,
                    "arguments": arg_names,
                    "confidence": mapping.overall_similarity * 0.8,
                    "source": f"Projected from {source.name}"
                })

        return inferences

    def similarity(self, struct1: Structure, struct2: Structure) -> float:
        """
        Compute overall similarity between two structures.

        Uses the best mapping score.
        """
        mapping = self.map_structures(struct1, struct2)
        return mapping.overall_similarity

    def find_best_analog(self, target: Structure,
                        candidates: List[Structure]) -> Tuple[Structure, Mapping]:
        """
        Find the best analog for a target from a list of candidates.
        """
        best_mapping = None
        best_candidate = None
        best_score = -1

        for candidate in candidates:
            mapping = self.map_structures(candidate, target)
            if mapping.overall_similarity > best_score:
                best_score = mapping.overall_similarity
                best_mapping = mapping
                best_candidate = candidate

        return best_candidate, best_mapping

    def explain_mapping(self, source: Structure, target: Structure,
                       mapping: Mapping) -> str:
        """Generate a human-readable explanation of a mapping."""
        lines = [f"Analogy: {source.name} :: {target.name}"]
        lines.append(f"Overall similarity: {mapping.overall_similarity:.2f}")
        lines.append(f"Systematicity: {mapping.systematicity:.2f}")
        lines.append(f"Coverage: {mapping.coverage:.1%}")

        lines.append("\nCorrespondences:")
        for corr in mapping.correspondences:
            source_name = source.elements.get(corr.source_id, type('', (), {'name': '?'})()).name
            target_name = target.elements.get(corr.target_id, type('', (), {'name': '?'})()).name
            lines.append(f"  {source_name} <-> {target_name} ({corr.similarity:.2f})")

        if mapping.inferences:
            lines.append("\nPotential inferences:")
            for inf in mapping.inferences[:5]:
                if inf["type"] == "projected_relation":
                    args = ", ".join(inf["arguments"])
                    lines.append(
                        f"  {inf['relation']}({args}) "
                        f"[confidence: {inf['confidence']:.2f}]"
                    )

        return "\n".join(lines)
