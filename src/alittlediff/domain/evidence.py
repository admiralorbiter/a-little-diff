"""Evidence and provenance domain model."""

from typing import Optional
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """Traceable evidence supporting a claim, relation, or epistemic change."""
    source_type: str = Field(
        ...,
        description="Type of source: git, moosedev, adr, issue, pr, doc, test, etc.",
    )
    source_id: Optional[str] = Field(
        default=None,
        description="Unique identifier in the source system (e.g. record IRI, PR #).",
    )
    revision: Optional[str] = Field(
        default=None,
        description="Git commit SHA or revision identifier where this evidence exists.",
    )
    path: Optional[str] = Field(
        default=None,
        description="File path relative to repository root.",
    )
    locator: Optional[str] = Field(
        default=None,
        description="Line number, section header, or fragment identifier.",
    )
    excerpt: Optional[str] = Field(
        default=None,
        description="Quoted snippet or textual representation of the evidence.",
    )
