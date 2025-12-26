"""
Structure representations for analogical reasoning.

This module implements the structure-mapping theory of analogy
(Gentner, 1983), where analogies are based on relational
similarities rather than surface features.

Key concepts:
- Entities: Objects in the domain
- Attributes: Properties of entities
- Relations: Relationships between entities
- Higher-order relations: Relations between relations
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum, auto
import uuid


class ElementType(Enum):
    """Types of elements in a structure."""
    ENTITY = auto()      # An object or concept
    ATTRIBUTE = auto()   # A property of an entity
    RELATION = auto()    # A relationship between entities
    FUNCTION = auto()    # A function/transformation
    HIGHER_ORDER = auto()  # A relation between relations


@dataclass
class StructureElement:
    """An element in a structured representation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    element_type: ElementType = ElementType.ENTITY
    name: str = ""
    value: Any = None
    arguments: List[str] = field(default_factory=list)  # IDs of related elements
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, StructureElement):
            return self.id == other.id
        return False

    def arity(self) -> int:
        """Return the number of arguments (for relations)."""
        return len(self.arguments)


@dataclass
class Relation:
    """A relation with explicit structure."""
    name: str
    arguments: Tuple[str, ...]  # Ordered tuple of entity IDs
    relation_type: str = "generic"  # causal, spatial, temporal, logical, etc.
    is_symmetric: bool = False
    is_transitive: bool = False
    strength: float = 1.0

    def __hash__(self):
        if self.is_symmetric:
            return hash((self.name, frozenset(self.arguments)))
        return hash((self.name, self.arguments))


class Structure:
    """
    A structured representation of a domain or situation.

    Structures consist of:
    - Entities: The objects in the domain
    - Attributes: Properties of entities
    - Relations: Relationships between entities
    - Higher-order structure: Relations between relations

    This follows Gentner's structure-mapping theory.
    """

    def __init__(self, name: str = "", description: str = ""):
        self.name = name
        self.description = description
        self.id = str(uuid.uuid4())

        self.elements: Dict[str, StructureElement] = {}
        self.relations: List[Relation] = []

        # Indices for efficient access
        self._by_type: Dict[ElementType, Set[str]] = {et: set() for et in ElementType}
        self._by_name: Dict[str, str] = {}  # name -> id
        self._relations_by_entity: Dict[str, List[Relation]] = {}

    def add_entity(self, name: str, value: Any = None,
                  metadata: Optional[Dict] = None) -> str:
        """Add an entity to the structure."""
        element = StructureElement(
            element_type=ElementType.ENTITY,
            name=name,
            value=value,
            metadata=metadata or {}
        )
        self.elements[element.id] = element
        self._by_type[ElementType.ENTITY].add(element.id)
        self._by_name[name] = element.id
        self._relations_by_entity[element.id] = []
        return element.id

    def add_attribute(self, entity_name: str, attribute_name: str,
                     value: Any = None) -> Optional[str]:
        """Add an attribute to an entity."""
        entity_id = self._by_name.get(entity_name)
        if not entity_id:
            return None

        element = StructureElement(
            element_type=ElementType.ATTRIBUTE,
            name=attribute_name,
            value=value,
            arguments=[entity_id]
        )
        self.elements[element.id] = element
        self._by_type[ElementType.ATTRIBUTE].add(element.id)
        return element.id

    def add_relation(self, relation_name: str, *entity_names: str,
                    relation_type: str = "generic",
                    symmetric: bool = False,
                    transitive: bool = False,
                    strength: float = 1.0) -> Optional[Relation]:
        """
        Add a relation between entities.

        Args:
            relation_name: Name of the relation (e.g., "causes", "larger_than")
            entity_names: Names of entities in the relation
            relation_type: Type of relation (causal, spatial, etc.)
            symmetric: Whether R(a,b) implies R(b,a)
            transitive: Whether R(a,b) and R(b,c) implies R(a,c)
            strength: Strength/confidence of the relation
        """
        entity_ids = []
        for name in entity_names:
            eid = self._by_name.get(name)
            if not eid:
                return None
            entity_ids.append(eid)

        relation = Relation(
            name=relation_name,
            arguments=tuple(entity_ids),
            relation_type=relation_type,
            is_symmetric=symmetric,
            is_transitive=transitive,
            strength=strength
        )

        self.relations.append(relation)

        # Index by entity
        for eid in entity_ids:
            self._relations_by_entity[eid].append(relation)

        # Also add as a structural element
        element = StructureElement(
            element_type=ElementType.RELATION,
            name=relation_name,
            arguments=entity_ids,
            metadata={"type": relation_type}
        )
        self.elements[element.id] = element
        self._by_type[ElementType.RELATION].add(element.id)

        return relation

    def add_higher_order_relation(self, name: str,
                                  relation_ids: List[str]) -> Optional[str]:
        """
        Add a higher-order relation between other relations.

        Example: "causes" between two temporal relations.
        """
        # Verify all referenced relations exist
        for rid in relation_ids:
            if rid not in self.elements:
                return None
            if self.elements[rid].element_type != ElementType.RELATION:
                return None

        element = StructureElement(
            element_type=ElementType.HIGHER_ORDER,
            name=name,
            arguments=relation_ids
        )
        self.elements[element.id] = element
        self._by_type[ElementType.HIGHER_ORDER].add(element.id)
        return element.id

    def get_entity(self, name: str) -> Optional[StructureElement]:
        """Get an entity by name."""
        eid = self._by_name.get(name)
        if eid:
            return self.elements.get(eid)
        return None

    def get_entities(self) -> List[StructureElement]:
        """Get all entities."""
        return [self.elements[eid] for eid in self._by_type[ElementType.ENTITY]]

    def get_attributes(self, entity_name: str) -> List[StructureElement]:
        """Get all attributes of an entity."""
        entity_id = self._by_name.get(entity_name)
        if not entity_id:
            return []

        return [
            self.elements[eid]
            for eid in self._by_type[ElementType.ATTRIBUTE]
            if entity_id in self.elements[eid].arguments
        ]

    def get_relations(self, entity_name: Optional[str] = None) -> List[Relation]:
        """Get relations, optionally filtered by entity."""
        if entity_name is None:
            return self.relations.copy()

        entity_id = self._by_name.get(entity_name)
        if not entity_id:
            return []

        return self._relations_by_entity.get(entity_id, [])

    def get_relational_structure(self) -> Dict[str, Any]:
        """
        Extract the relational structure (ignoring surface features).

        This is what's used for analogical mapping.
        """
        structure = {
            "entities": [
                {"id": e.id, "name": e.name}
                for e in self.get_entities()
            ],
            "relations": [
                {
                    "name": r.name,
                    "arity": len(r.arguments),
                    "type": r.relation_type,
                    "arguments": r.arguments
                }
                for r in self.relations
            ],
            "higher_order": [
                {
                    "id": eid,
                    "name": self.elements[eid].name,
                    "over": self.elements[eid].arguments
                }
                for eid in self._by_type[ElementType.HIGHER_ORDER]
            ]
        }
        return structure

    def relation_signature(self) -> Tuple[Tuple[str, int], ...]:
        """
        Get the relation signature of this structure.

        The signature is a sorted tuple of (relation_name, arity) pairs.
        Useful for quick structural comparison.
        """
        sig = [(r.name, len(r.arguments)) for r in self.relations]
        return tuple(sorted(set(sig)))

    def structural_depth(self) -> int:
        """
        Calculate the structural depth (levels of nesting).

        Higher depth indicates more complex relational structure.
        """
        if not self._by_type[ElementType.HIGHER_ORDER]:
            if self.relations:
                return 1
            return 0

        # Find maximum depth through higher-order relations
        max_depth = 1
        for hoid in self._by_type[ElementType.HIGHER_ORDER]:
            element = self.elements[hoid]
            for arg_id in element.arguments:
                if arg_id in self.elements:
                    arg = self.elements[arg_id]
                    if arg.element_type == ElementType.HIGHER_ORDER:
                        max_depth = max(max_depth, 2)  # Simplified

        return max_depth + 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert structure to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "entities": [
                {"id": e.id, "name": e.name, "value": e.value}
                for e in self.get_entities()
            ],
            "attributes": [
                {"id": a.id, "name": a.name, "value": a.value, "of": a.arguments}
                for a in [self.elements[aid] for aid in self._by_type[ElementType.ATTRIBUTE]]
            ],
            "relations": [
                {
                    "name": r.name,
                    "arguments": list(r.arguments),
                    "type": r.relation_type
                }
                for r in self.relations
            ]
        }

    def summarize(self) -> str:
        """Generate a human-readable summary."""
        lines = [f"Structure: {self.name}"]
        if self.description:
            lines.append(f"  {self.description}")

        entities = self.get_entities()
        lines.append(f"\nEntities ({len(entities)}):")
        for e in entities[:5]:
            attrs = self.get_attributes(e.name)
            attr_str = ", ".join(f"{a.name}={a.value}" for a in attrs[:3])
            lines.append(f"  - {e.name}" + (f" ({attr_str})" if attr_str else ""))

        lines.append(f"\nRelations ({len(self.relations)}):")
        for r in self.relations[:5]:
            arg_names = [
                self.elements[aid].name if aid in self.elements else "?"
                for aid in r.arguments
            ]
            lines.append(f"  - {r.name}({', '.join(arg_names)})")

        ho_count = len(self._by_type[ElementType.HIGHER_ORDER])
        if ho_count > 0:
            lines.append(f"\nHigher-order relations: {ho_count}")

        return "\n".join(lines)


def create_structure(name: str, entities: List[str],
                    relations: List[Tuple[str, str, str]]) -> Structure:
    """
    Convenience function to create a simple structure.

    Args:
        name: Structure name
        entities: List of entity names
        relations: List of (relation_name, entity1, entity2) tuples
    """
    s = Structure(name=name)
    for entity in entities:
        s.add_entity(entity)
    for rel_name, e1, e2 in relations:
        s.add_relation(rel_name, e1, e2)
    return s
