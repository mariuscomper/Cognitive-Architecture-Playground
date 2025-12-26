"""
Causal Graph representation and manipulation.

This module implements causal graphs (directed acyclic graphs representing
causal relationships) based on Pearl's causal model framework.

Key concepts:
- Nodes represent variables
- Edges represent causal influence
- The graph structure encodes assumptions about causal mechanisms
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Tuple, FrozenSet
from enum import Enum, auto
import uuid
from collections import deque


class NodeType(Enum):
    """Types of nodes in a causal graph."""
    OBSERVED = auto()      # Observable variable
    LATENT = auto()        # Unobservable/hidden variable
    INTERVENTION = auto()  # Intervention node (do-operator target)
    OUTCOME = auto()       # Outcome of interest


class EdgeType(Enum):
    """Types of causal edges."""
    DIRECT = auto()        # Direct causal effect
    CONFOUNDING = auto()   # Common cause (often latent)
    SELECTION = auto()     # Selection/conditioning


@dataclass
class CausalNode:
    """A node in the causal graph representing a variable."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    node_type: NodeType = NodeType.OBSERVED
    description: str = ""
    domain: Optional[List[Any]] = None  # Possible values
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, CausalNode):
            return self.id == other.id
        return False


@dataclass
class CausalEdge:
    """An edge representing a causal relationship."""
    source_id: str = ""
    target_id: str = ""
    edge_type: EdgeType = EdgeType.DIRECT
    strength: Optional[float] = None  # If known, causal effect size
    confidence: float = 1.0  # Confidence in the edge existing
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.source_id, self.target_id))


class CausalGraph:
    """
    A directed acyclic graph representing causal relationships.

    Provides methods for:
    - Graph construction and manipulation
    - Path finding (causal and non-causal)
    - D-separation testing
    - Identifying confounders and mediators
    - Intervention modeling (do-operator)
    """

    def __init__(self, name: str = ""):
        self.name = name
        self.nodes: Dict[str, CausalNode] = {}
        self.edges: Dict[Tuple[str, str], CausalEdge] = {}

        # Adjacency lists for efficient traversal
        self._parents: Dict[str, Set[str]] = {}
        self._children: Dict[str, Set[str]] = {}

    def add_node(self, node: CausalNode) -> str:
        """Add a node to the graph."""
        self.nodes[node.id] = node
        self._parents[node.id] = set()
        self._children[node.id] = set()
        return node.id

    def add_node_by_name(self, name: str,
                         node_type: NodeType = NodeType.OBSERVED,
                         description: str = "") -> str:
        """Convenience method to add a node by name."""
        node = CausalNode(name=name, node_type=node_type, description=description)
        return self.add_node(node)

    def add_edge(self, source_id: str, target_id: str,
                edge_type: EdgeType = EdgeType.DIRECT,
                strength: Optional[float] = None,
                confidence: float = 1.0) -> bool:
        """
        Add a causal edge from source to target.

        Returns False if adding the edge would create a cycle.
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return False

        # Check for cycles
        if self._would_create_cycle(source_id, target_id):
            return False

        edge = CausalEdge(
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            strength=strength,
            confidence=confidence
        )
        self.edges[(source_id, target_id)] = edge
        self._parents[target_id].add(source_id)
        self._children[source_id].add(target_id)
        return True

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all its edges."""
        if node_id not in self.nodes:
            return False

        # Remove edges
        for parent_id in list(self._parents[node_id]):
            self.remove_edge(parent_id, node_id)
        for child_id in list(self._children[node_id]):
            self.remove_edge(node_id, child_id)

        del self.nodes[node_id]
        del self._parents[node_id]
        del self._children[node_id]
        return True

    def remove_edge(self, source_id: str, target_id: str) -> bool:
        """Remove an edge."""
        key = (source_id, target_id)
        if key not in self.edges:
            return False

        del self.edges[key]
        self._parents[target_id].discard(source_id)
        self._children[source_id].discard(target_id)
        return True

    def get_node(self, node_id: str) -> Optional[CausalNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_node_by_name(self, name: str) -> Optional[CausalNode]:
        """Get a node by name."""
        for node in self.nodes.values():
            if node.name == name:
                return node
        return None

    def get_parents(self, node_id: str) -> Set[str]:
        """Get the parent node IDs (direct causes)."""
        return self._parents.get(node_id, set()).copy()

    def get_children(self, node_id: str) -> Set[str]:
        """Get the child node IDs (direct effects)."""
        return self._children.get(node_id, set()).copy()

    def get_ancestors(self, node_id: str) -> Set[str]:
        """Get all ancestor node IDs (all causes, direct and indirect)."""
        ancestors = set()
        to_visit = list(self._parents.get(node_id, set()))

        while to_visit:
            current = to_visit.pop()
            if current not in ancestors:
                ancestors.add(current)
                to_visit.extend(self._parents.get(current, set()))

        return ancestors

    def get_descendants(self, node_id: str) -> Set[str]:
        """Get all descendant node IDs (all effects, direct and indirect)."""
        descendants = set()
        to_visit = list(self._children.get(node_id, set()))

        while to_visit:
            current = to_visit.pop()
            if current not in descendants:
                descendants.add(current)
                to_visit.extend(self._children.get(current, set()))

        return descendants

    def _would_create_cycle(self, source_id: str, target_id: str) -> bool:
        """Check if adding an edge would create a cycle."""
        if source_id == target_id:
            return True
        # If target is an ancestor of source, adding edge creates cycle
        return source_id in self.get_ancestors(target_id)

    def find_all_paths(self, source_id: str, target_id: str,
                      max_length: int = 10) -> List[List[str]]:
        """Find all directed paths from source to target."""
        if source_id not in self.nodes or target_id not in self.nodes:
            return []

        paths = []
        stack = [(source_id, [source_id])]

        while stack:
            current, path = stack.pop()

            if len(path) > max_length:
                continue

            if current == target_id:
                paths.append(path)
                continue

            for child in self._children.get(current, set()):
                if child not in path:  # Avoid cycles
                    stack.append((child, path + [child]))

        return paths

    def find_backdoor_paths(self, treatment_id: str, outcome_id: str) -> List[List[str]]:
        """
        Find all backdoor paths from treatment to outcome.

        Backdoor paths are non-causal paths that go "backwards" through
        a common cause. These create confounding.
        """
        # A backdoor path starts by going from treatment to a parent
        backdoor_paths = []

        for parent in self._parents.get(treatment_id, set()):
            # Find all paths from parent to outcome
            paths = self._find_undirected_paths(parent, outcome_id, {treatment_id})
            for path in paths:
                backdoor_paths.append([treatment_id] + path)

        return backdoor_paths

    def _find_undirected_paths(self, source_id: str, target_id: str,
                               blocked: Set[str] = None,
                               max_length: int = 10) -> List[List[str]]:
        """Find paths treating edges as undirected."""
        if blocked is None:
            blocked = set()

        if source_id == target_id:
            return [[source_id]]

        paths = []
        visited = blocked.copy()
        stack = [(source_id, [source_id])]

        while stack:
            current, path = stack.pop()

            if len(path) > max_length:
                continue

            if current == target_id:
                paths.append(path)
                continue

            if current in visited:
                continue
            visited.add(current)

            # Consider both directions
            neighbors = (self._parents.get(current, set()) |
                        self._children.get(current, set()))

            for neighbor in neighbors:
                if neighbor not in visited:
                    stack.append((neighbor, path + [neighbor]))

        return paths

    def is_d_separated(self, x_id: str, y_id: str,
                      z_ids: Set[str] = None) -> bool:
        """
        Test if X and Y are d-separated given Z.

        D-separation is the graphical criterion for conditional independence.
        X and Y are d-separated by Z if Z blocks all paths between them.
        """
        if z_ids is None:
            z_ids = set()

        # Use Bayes-Ball algorithm for d-separation
        # Find all paths and check if any are open
        paths = self._find_undirected_paths(x_id, y_id)

        for path in paths:
            if self._is_path_open(path, z_ids):
                return False  # Found an open path, not d-separated

        return True  # All paths blocked

    def _is_path_open(self, path: List[str], conditioned: Set[str]) -> bool:
        """
        Check if a path is open (unblocked) given conditioning set.

        A path is blocked if:
        - It contains a chain (A -> B -> C) or fork (A <- B -> C)
          where the middle node is conditioned
        - It contains a collider (A -> B <- C) where neither B
          nor any descendant of B is conditioned
        """
        if len(path) < 3:
            return True  # Too short to be blocked

        for i in range(1, len(path) - 1):
            prev_node = path[i - 1]
            curr_node = path[i]
            next_node = path[i + 1]

            # Check edge directions to determine structure
            is_chain_or_fork = (
                (curr_node in self._children.get(prev_node, set()) and
                 next_node in self._children.get(curr_node, set())) or
                (prev_node in self._children.get(curr_node, set()) and
                 next_node in self._children.get(curr_node, set())) or
                (curr_node in self._children.get(prev_node, set()) and
                 curr_node in self._children.get(next_node, set()))
            )

            is_collider = (
                prev_node in self._parents.get(curr_node, set()) and
                next_node in self._parents.get(curr_node, set())
            )

            if is_collider:
                # Collider: open only if conditioned on collider or descendant
                descendants = self.get_descendants(curr_node)
                if curr_node not in conditioned and not (descendants & conditioned):
                    return False  # Blocked at collider

            elif is_chain_or_fork:
                # Chain or fork: blocked if middle node conditioned
                if curr_node in conditioned:
                    return False  # Blocked at chain/fork

        return True  # Path is open

    def get_confounders(self, treatment_id: str, outcome_id: str) -> Set[str]:
        """
        Identify confounders between treatment and outcome.

        A confounder is a common cause of both treatment and outcome.
        """
        treatment_ancestors = self.get_ancestors(treatment_id)
        outcome_ancestors = self.get_ancestors(outcome_id)

        # Confounders are common ancestors
        return treatment_ancestors & outcome_ancestors

    def get_mediators(self, treatment_id: str, outcome_id: str) -> Set[str]:
        """
        Identify mediators between treatment and outcome.

        A mediator is on a causal path from treatment to outcome.
        """
        treatment_descendants = self.get_descendants(treatment_id)
        outcome_ancestors = self.get_ancestors(outcome_id)

        # Mediators are both descendants of treatment and ancestors of outcome
        return treatment_descendants & outcome_ancestors

    def get_minimal_adjustment_set(self, treatment_id: str,
                                   outcome_id: str) -> Optional[Set[str]]:
        """
        Find a minimal set of variables to adjust for to identify causal effect.

        Uses the backdoor criterion: a set Z satisfies the backdoor criterion
        relative to (X, Y) if:
        1. No node in Z is a descendant of X
        2. Z blocks every backdoor path from X to Y
        """
        descendants = self.get_descendants(treatment_id)
        confounders = self.get_confounders(treatment_id, outcome_id)

        # Start with confounders that are not descendants
        candidates = confounders - descendants

        # Check if this blocks all backdoor paths
        if self.is_d_separated(treatment_id, outcome_id, candidates):
            # Try to minimize
            for node_id in list(candidates):
                test_set = candidates - {node_id}
                if self.is_d_separated(treatment_id, outcome_id, test_set):
                    candidates = test_set

            return candidates

        # Need to add more nodes
        all_nodes = set(self.nodes.keys()) - {treatment_id, outcome_id} - descendants
        for node_id in all_nodes:
            candidates.add(node_id)
            if self.is_d_separated(treatment_id, outcome_id, candidates):
                return candidates

        return None  # No valid adjustment set found

    def do_intervention(self, intervention_node: str, value: Any = None) -> 'CausalGraph':
        """
        Create a new graph representing the result of do(X=x).

        The do-operator removes all edges into the intervention node,
        simulating an external intervention that sets the variable.
        """
        new_graph = CausalGraph(name=f"{self.name}_do({intervention_node})")

        # Copy all nodes
        for node in self.nodes.values():
            new_node = CausalNode(
                id=node.id,
                name=node.name,
                node_type=NodeType.INTERVENTION if node.id == intervention_node else node.node_type,
                description=node.description,
                domain=node.domain,
                metadata=node.metadata.copy()
            )
            new_graph.add_node(new_node)

        # Copy edges except those into intervention node
        for edge in self.edges.values():
            if edge.target_id != intervention_node:
                new_graph.add_edge(
                    edge.source_id, edge.target_id,
                    edge.edge_type, edge.strength, edge.confidence
                )

        return new_graph

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary representation."""
        return {
            "name": self.name,
            "nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "type": n.node_type.name,
                    "description": n.description
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "type": e.edge_type.name,
                    "strength": e.strength,
                    "confidence": e.confidence
                }
                for e in self.edges.values()
            ]
        }

    def summarize(self) -> str:
        """Generate a human-readable summary."""
        lines = [f"Causal Graph: {self.name or '(unnamed)'}"]
        lines.append(f"Nodes: {len(self.nodes)}, Edges: {len(self.edges)}")
        lines.append("")

        for node in self.nodes.values():
            parents = self._parents.get(node.id, set())
            children = self._children.get(node.id, set())
            parent_names = [self.nodes[p].name for p in parents]
            child_names = [self.nodes[c].name for c in children]

            lines.append(f"  {node.name} ({node.node_type.name})")
            if parent_names:
                lines.append(f"    <- {', '.join(parent_names)}")
            if child_names:
                lines.append(f"    -> {', '.join(child_names)}")

        return "\n".join(lines)


def create_simple_graph(*edges: Tuple[str, str]) -> CausalGraph:
    """
    Convenience function to create a simple causal graph.

    Example: create_simple_graph(("A", "B"), ("B", "C"), ("A", "C"))
    """
    graph = CausalGraph()
    nodes = {}

    for source, target in edges:
        if source not in nodes:
            nodes[source] = graph.add_node_by_name(source)
        if target not in nodes:
            nodes[target] = graph.add_node_by_name(target)

        graph.add_edge(nodes[source], nodes[target])

    return graph
