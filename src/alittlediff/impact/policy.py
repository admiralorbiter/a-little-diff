"""Typed propagation policies for impact analysis."""

from typing import Literal
from pydantic import BaseModel, Field

TraversalDirection = Literal["forward", "reverse", "both"]
ImpactConfidence = Literal["high", "medium", "low"]


class PropagationRule(BaseModel):
    """Rule defining how changes along a specific relation propagate downstream."""
    predicate: str = Field(
        ...,
        description="Semantic predicate name (e.g. isMotivatedBy, constrains).",
    )
    direction: TraversalDirection = Field(
        ...,
        description="Direction to traverse: 'reverse' (target -> source), 'forward' (source -> target), or 'both'.",
    )
    effect: str = Field(
        ...,
        description="Categorical effect identifier (e.g. justification_may_have_changed, constraint_context_changed).",
    )
    confidence: ImpactConfidence = Field(
        default="high",
        description="Confidence level of the inferred impact.",
    )
    description: str = Field(
        default="",
        description="Human-readable explanation of why this propagation occurs.",
    )


# Conservative default propagation table for MOOSEDev and software knowledge graphs
DEFAULT_PROPAGATION_RULES: dict[str, PropagationRule] = {
    "isMotivatedBy": PropagationRule(
        predicate="isMotivatedBy",
        direction="reverse",
        effect="justification_may_have_changed",
        confidence="high",
        description="The motivating premise justifying this decision or plan changed.",
    ),
    "motivates": PropagationRule(
        predicate="motivates",
        direction="forward",
        effect="justification_may_have_changed",
        confidence="high",
        description="The premise motivating this downstream item changed.",
    ),
    "constrains": PropagationRule(
        predicate="constrains",
        direction="reverse",
        effect="constraint_context_changed",
        confidence="high",
        description="A governing constraint for this decision or requirement changed.",
    ),
    "constrainedBy": PropagationRule(
        predicate="constrainedBy",
        direction="forward",
        effect="constraint_context_changed",
        confidence="high",
        description="A governing constraint for this item changed.",
    ),
    "dependsOn": PropagationRule(
        predicate="dependsOn",
        direction="reverse",
        effect="dependency_may_have_changed",
        confidence="high",
        description="An upstream dependency was modified or superseded.",
    ),
    "resultsIn": PropagationRule(
        predicate="resultsIn",
        direction="forward",
        effect="consequence_may_have_changed",
        confidence="medium",
        description="An item that produces this consequence was modified or superseded.",
    ),
    "concerns": PropagationRule(
        predicate="concerns",
        direction="both",
        effect="inspect",
        confidence="low",
        description="A related item in the same problem domain may deserve inspection.",
    ),
    "justifiedBy": PropagationRule(
        predicate="justifiedBy",
        direction="reverse",
        effect="justification_may_have_changed",
        confidence="high",
        description="An explicit justification for this decision or conclusion changed.",
    ),
}
