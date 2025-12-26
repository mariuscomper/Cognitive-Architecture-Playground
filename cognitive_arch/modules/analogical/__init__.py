"""Analogical Reasoning module for finding and using structural similarities."""

from .structures import Structure, StructureElement, Relation
from .mapping import StructureMapper, Mapping
from .retrieval import AnalogRetriever
from .inference import AnalogicalInference

__all__ = [
    'Structure', 'StructureElement', 'Relation',
    'StructureMapper', 'Mapping',
    'AnalogRetriever', 'AnalogicalInference'
]
