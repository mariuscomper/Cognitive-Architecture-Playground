"""
Analog retrieval for analogical reasoning.

This module implements mechanisms for retrieving relevant analogs
from a knowledge base, supporting case-based reasoning.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid

from .structures import Structure
from .mapping import StructureMapper, Mapping


@dataclass
class StoredAnalog:
    """A stored analog case with metadata."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    structure: Structure = field(default_factory=Structure)
    domain: str = ""
    tags: List[str] = field(default_factory=list)
    description: str = ""
    usefulness_score: float = 0.5  # How useful this analog has been
    retrieval_count: int = 0
    last_retrieved: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


class AnalogRetriever:
    """
    Retrieves relevant analogs from a knowledge base.

    Supports multiple retrieval strategies:
    - Surface similarity (quick but shallow)
    - Structural similarity (deeper but slower)
    - Domain-based filtering
    - Recency and frequency weighting
    """

    def __init__(self):
        self.analogs: Dict[str, StoredAnalog] = {}
        self.mapper = StructureMapper()

        # Indices for efficient retrieval
        self._by_domain: Dict[str, List[str]] = {}
        self._by_tag: Dict[str, List[str]] = {}
        self._by_signature: Dict[tuple, List[str]] = {}

    def store(self, structure: Structure, domain: str = "",
             tags: Optional[List[str]] = None,
             description: str = "") -> str:
        """Store a new analog in the knowledge base."""
        analog = StoredAnalog(
            structure=structure,
            domain=domain,
            tags=tags or [],
            description=description
        )

        self.analogs[analog.id] = analog

        # Index by domain
        if domain:
            if domain not in self._by_domain:
                self._by_domain[domain] = []
            self._by_domain[domain].append(analog.id)

        # Index by tags
        for tag in (tags or []):
            if tag not in self._by_tag:
                self._by_tag[tag] = []
            self._by_tag[tag].append(analog.id)

        # Index by structural signature
        sig = structure.relation_signature()
        if sig not in self._by_signature:
            self._by_signature[sig] = []
        self._by_signature[sig].append(analog.id)

        return analog.id

    def retrieve(self, query: Structure, n: int = 5,
                domain: Optional[str] = None,
                tags: Optional[List[str]] = None,
                strategy: str = "hybrid") -> List[Tuple[StoredAnalog, float]]:
        """
        Retrieve the n most relevant analogs for a query.

        Args:
            query: The structure to find analogs for
            n: Number of analogs to retrieve
            domain: Optional domain filter
            tags: Optional tag filters
            strategy: Retrieval strategy ("surface", "structural", "hybrid")

        Returns:
            List of (analog, similarity_score) tuples
        """
        # Get candidates (filtered by domain/tags if specified)
        candidates = self._get_candidates(domain, tags)

        if not candidates:
            return []

        # Score candidates based on strategy
        scored = []
        for analog in candidates:
            if strategy == "surface":
                score = self._surface_similarity(query, analog.structure)
            elif strategy == "structural":
                score = self._structural_similarity(query, analog.structure)
            else:  # hybrid
                surface = self._surface_similarity(query, analog.structure)
                structural = self._structural_similarity(query, analog.structure)
                # Weight structural more heavily
                score = 0.3 * surface + 0.7 * structural

            # Apply retrieval frequency bonus (familiarity)
            frequency_bonus = min(analog.retrieval_count / 10, 0.1)
            score += frequency_bonus

            scored.append((analog, score))

        # Sort by score and take top n
        scored.sort(key=lambda x: x[1], reverse=True)
        results = scored[:n]

        # Update retrieval statistics
        for analog, _ in results:
            analog.retrieval_count += 1
            analog.last_retrieved = datetime.now()

        return results

    def _get_candidates(self, domain: Optional[str],
                       tags: Optional[List[str]]) -> List[StoredAnalog]:
        """Get candidate analogs based on filters."""
        if domain is None and tags is None:
            return list(self.analogs.values())

        candidate_ids = set(self.analogs.keys())

        if domain:
            domain_ids = set(self._by_domain.get(domain, []))
            candidate_ids &= domain_ids

        if tags:
            for tag in tags:
                tag_ids = set(self._by_tag.get(tag, []))
                candidate_ids &= tag_ids

        return [self.analogs[aid] for aid in candidate_ids]

    def _surface_similarity(self, query: Structure, target: Structure) -> float:
        """
        Compute surface similarity (quick but shallow).

        Based on:
        - Number of entities
        - Relation types present
        - Attribute overlap
        """
        score = 0.0
        total_weight = 0.0

        # Entity count similarity
        q_entities = len(query.get_entities())
        t_entities = len(target.get_entities())
        if max(q_entities, t_entities) > 0:
            entity_sim = min(q_entities, t_entities) / max(q_entities, t_entities)
            score += 0.3 * entity_sim
        total_weight += 0.3

        # Relation signature similarity
        q_sig = set(query.relation_signature())
        t_sig = set(target.relation_signature())
        if q_sig or t_sig:
            sig_overlap = len(q_sig & t_sig) / len(q_sig | t_sig) if (q_sig | t_sig) else 0
            score += 0.4 * sig_overlap
        total_weight += 0.4

        # Relation type overlap
        q_rel_types = {r.relation_type for r in query.relations}
        t_rel_types = {r.relation_type for r in target.relations}
        if q_rel_types or t_rel_types:
            type_overlap = len(q_rel_types & t_rel_types) / len(q_rel_types | t_rel_types) if (q_rel_types | t_rel_types) else 0
            score += 0.3 * type_overlap
        total_weight += 0.3

        return score / total_weight if total_weight > 0 else 0

    def _structural_similarity(self, query: Structure, target: Structure) -> float:
        """
        Compute structural similarity using full mapping.

        More accurate but slower than surface similarity.
        """
        mapping = self.mapper.map_structures(query, target)
        return mapping.overall_similarity

    def retrieve_by_signature(self, query: Structure) -> List[StoredAnalog]:
        """Retrieve analogs with matching structural signature."""
        sig = query.relation_signature()
        analog_ids = self._by_signature.get(sig, [])
        return [self.analogs[aid] for aid in analog_ids]

    def get_diverse_analogs(self, query: Structure, n: int = 5) -> List[StoredAnalog]:
        """
        Retrieve a diverse set of analogs.

        Tries to cover different domains and structural variations.
        """
        all_results = self.retrieve(query, n=n*3)  # Get more candidates

        if len(all_results) <= n:
            return [a for a, _ in all_results]

        # Select for diversity
        selected = [all_results[0][0]]  # Always include best match
        used_domains = {all_results[0][0].domain} if all_results[0][0].domain else set()

        for analog, score in all_results[1:]:
            if len(selected) >= n:
                break

            # Prefer different domains
            if analog.domain and analog.domain not in used_domains:
                selected.append(analog)
                used_domains.add(analog.domain)
            elif len(used_domains) == 0 or score > 0.5:
                # Include if no domain or high score
                selected.append(analog)

        return selected

    def feedback(self, analog_id: str, useful: bool) -> None:
        """
        Provide feedback on whether an analog was useful.

        This updates the usefulness score for future retrieval.
        """
        if analog_id not in self.analogs:
            return

        analog = self.analogs[analog_id]
        # Exponential moving average
        update = 1.0 if useful else 0.0
        analog.usefulness_score = 0.8 * analog.usefulness_score + 0.2 * update

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the analog knowledge base."""
        return {
            "total_analogs": len(self.analogs),
            "domains": list(self._by_domain.keys()),
            "tags": list(self._by_tag.keys()),
            "unique_signatures": len(self._by_signature),
            "most_retrieved": sorted(
                self.analogs.values(),
                key=lambda a: a.retrieval_count,
                reverse=True
            )[:3]
        }

    def summarize(self) -> str:
        """Generate a summary of the knowledge base."""
        stats = self.get_stats()
        lines = ["Analog Knowledge Base"]
        lines.append(f"  Total analogs: {stats['total_analogs']}")
        lines.append(f"  Domains: {', '.join(stats['domains'][:5])}")
        lines.append(f"  Unique signatures: {stats['unique_signatures']}")

        if stats['most_retrieved']:
            lines.append("\nMost retrieved:")
            for analog in stats['most_retrieved']:
                lines.append(
                    f"  - {analog.structure.name}: {analog.retrieval_count} times"
                )

        return "\n".join(lines)
