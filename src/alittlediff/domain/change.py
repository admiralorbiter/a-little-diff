"""Epistemic change domain model."""

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field
from alittlediff.domain.evidence import Evidence
from alittlediff.domain.record import EpistemicRecord


StructuralChangeType = Literal[
    "added",
    "removed",
    "status_changed",
    "superseded",
    "relation_added",
    "relation_removed",
    "modified",
]

SemanticChangeType = Literal[
    "expansion",
    "contraction",
    "revision",
    "world_update",
    "refinement",
    "contradiction",
    "semantic_noop",
    "unknown",
]

JudgmentSource = Literal[
    "deterministic",
    "model",
    "human",
]


class EpistemicChange(BaseModel):
    """Represents a delta in a project's beliefs or records between two revisions."""
    change_id: str = Field(
        ...,
        description="Unique identifier for the change event.",
    )
    structural_type: StructuralChangeType = Field(
        ...,
        description="Deterministic structural difference category.",
    )
    semantic_type: Optional[SemanticChangeType] = Field(
        default=None,
        description="High-level epistemic interpretation (revision, world_update, etc.).",
    )
    before: Optional[EpistemicRecord] = Field(
        default=None,
        description="Record state at base revision.",
    )
    after: Optional[EpistemicRecord] = Field(
        default=None,
        description="Record state at head revision.",
    )
    evidence: list[Evidence] = Field(
        default_factory=list,
        description="Traceable evidence supporting this change.",
    )
    judgment_source: JudgmentSource = Field(
        default="deterministic",
        description="Source of the classification judgment.",
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured context (e.g. superseding_record_id, changed_fields).",
    )
