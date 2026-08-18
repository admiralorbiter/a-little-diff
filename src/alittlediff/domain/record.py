"""Epistemic record domain model."""

from typing import Any, Optional
from pydantic import BaseModel, Field
from alittlediff.domain.evidence import Evidence
from alittlediff.domain.relation import Relation


class EpistemicRecord(BaseModel):
    """An individual unit of project knowledge, belief, constraint, or decision."""
    id: str = Field(
        ...,
        description="Unique stable identifier for the record within the epistemic state.",
    )
    kind: str = Field(
        ...,
        description="Normalized category (e.g. Constraint, Decision, Requirement, Assumption, Plan, Lesson, Question).",
    )
    title: Optional[str] = Field(
        default=None,
        description="Short human-readable title or label.",
    )
    claim: Optional[str] = Field(
        default=None,
        description="Full proposition, description, or statement of belief.",
    )
    status: Optional[str] = Field(
        default="active",
        description="Lifecycle status (e.g. active, superseded, retracted, draft, retired).",
    )
    relations: list[Relation] = Field(
        default_factory=list,
        description="Outgoing typed relations originating from this record.",
    )
    evidence: list[Evidence] = Field(
        default_factory=list,
        description="Evidence supporting this record.",
    )
    source_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Source-specific raw properties preserved for auditing.",
    )
