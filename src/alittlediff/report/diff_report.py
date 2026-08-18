"""Diff report container domain model."""

from pydantic import BaseModel, Field
from alittlediff.domain.change import EpistemicChange
from alittlediff.domain.impact import Impact


class DiffReport(BaseModel):
    """The structured result of an epistemic diff analysis across two revisions."""
    base_revision: str = Field(
        ...,
        description="Baseline Git revision or commit SHA.",
    )
    head_revision: str = Field(
        ...,
        description="Target Git revision or commit SHA.",
    )
    source: str = Field(
        default="moosedev",
        description="Epistemic source system identifier.",
    )
    changes: list[EpistemicChange] = Field(
        default_factory=list,
        description="List of detected epistemic changes.",
    )
    impacts: list[Impact] = Field(
        default_factory=list,
        description="List of detected downstream impacts/consequences.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Diagnostic warnings or non-fatal anomalies.",
    )

    @property
    def change_count(self) -> int:
        """Total number of epistemic changes."""
        return len(self.changes)

    @property
    def impact_count(self) -> int:
        """Total number of downstream impacts."""
        return len(self.impacts)
