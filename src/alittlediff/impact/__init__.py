"""Impact and consequence propagation engine."""

from alittlediff.impact.policy import (
    DEFAULT_PROPAGATION_RULES,
    PropagationRule,
    TraversalDirection,
    ImpactConfidence,
)
from alittlediff.impact.traversal import find_impacts

__all__ = [
    "DEFAULT_PROPAGATION_RULES",
    "PropagationRule",
    "TraversalDirection",
    "ImpactConfidence",
    "find_impacts",
]
