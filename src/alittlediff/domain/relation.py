"""Typed relationship domain model."""

from pydantic import BaseModel, Field
from alittlediff.domain.evidence import Evidence


class Relation(BaseModel):
    """A typed directed edge between two epistemic records."""
    predicate: str = Field(
        ...,
        description="Semantic predicate linking subject to object (e.g. isMotivatedBy, supersedes, constrains).",
    )
    subject_id: str = Field(
        ...,
        description="Identifier of the source epistemic record.",
    )
    object_id: str = Field(
        ...,
        description="Identifier of the target epistemic record.",
    )
    evidence: list[Evidence] = Field(
        default_factory=list,
        description="Evidence supporting this relation.",
    )

    def key(self) -> tuple[str, str, str]:
        """Unique key for relationship equality comparison."""
        return (self.predicate, self.subject_id, self.object_id)
