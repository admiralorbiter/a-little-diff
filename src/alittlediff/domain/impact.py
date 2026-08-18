"""Impact and consequence domain model."""

from typing import Literal, Optional
from pydantic import BaseModel, Field
from alittlediff.domain.evidence import Evidence
from alittlediff.domain.record import EpistemicRecord
from alittlediff.domain.relation import Relation


class Impact(BaseModel):
    """A downstream consequence of an epistemic change on a related decision, plan, or constraint."""
    impact_id: str = Field(
        ...,
        description="Unique identifier for this impact record.",
    )
    source_change_id: str = Field(
        ...,
        description="Identifier of the upstream EpistemicChange triggering this impact.",
    )
    target_record_id: str = Field(
        ...,
        description="ID of the affected downstream record.",
    )
    target_record: Optional[EpistemicRecord] = Field(
        default=None,
        description="Snapshot of the affected downstream record.",
    )
    effect: str = Field(
        ...,
        description="Human-readable effect classification (e.g. justification_may_have_changed, inspect).",
    )
    path: list[Relation] = Field(
        default_factory=list,
        description="Directed chain of relations connecting the changed premise to the target.",
    )
    evidence: list[Evidence] = Field(
        default_factory=list,
        description="Evidence supporting the impact path and target.",
    )
    confidence: Literal["high", "medium", "low"] = Field(
        default="high",
        description="Confidence level of the propagation inference.",
    )
    rationale: Optional[str] = Field(
        default=None,
        description="Textual explanation of why the consequence was flagged.",
    )
