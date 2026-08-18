"""Epistemic record domain model."""

from typing import Any, Optional
from pydantic import BaseModel, Field
from alittlediff.domain.evidence import Evidence
from alittlediff.domain.relation import Relation


RETIRED_STATUSES = {"superseded", "retracted", "retired", "deprecated"}
NON_AUTHORITATIVE_STATUSES = {"proposed", "rejected", "draft"}
AUTHORITATIVE_ACTIVE_STATUSES = {"accepted", "active"}


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
        default="accepted",
        description="Lifecycle status (e.g. accepted, active, superseded, deprecated, retracted, proposed, rejected).",
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

    @property
    def is_authoritative_active(self) -> bool:
        """Check if record is an authoritative, active project belief."""
        if not self.status:
            return True
        st = self.status.lower()
        if st in RETIRED_STATUSES or st in NON_AUTHORITATIVE_STATUSES:
            return False
        return True
