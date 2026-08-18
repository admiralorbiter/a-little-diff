"""Epistemic state domain model representing a project snapshot."""

from typing import Optional
from pydantic import BaseModel, Field
from alittlediff.domain.record import EpistemicRecord
from alittlediff.domain.relation import Relation


class EpistemicState(BaseModel):
    """A normalized snapshot of what a project treats as true, active, or constrained at a specific revision."""
    source: str = Field(
        ...,
        description="Source adapter identifier (e.g. moosedev, adr, github).",
    )
    revision: str = Field(
        ...,
        description="Git commit SHA or snapshot revision identifier.",
    )
    records: dict[str, EpistemicRecord] = Field(
        default_factory=dict,
        description="Map of record ID to EpistemicRecord.",
    )

    def get_record(self, record_id: str) -> Optional[EpistemicRecord]:
        """Get record by ID."""
        return self.records.get(record_id)

    @property
    def active_records(self) -> dict[str, EpistemicRecord]:
        """Filter records that are currently authoritative and active (not retired or proposed/rejected)."""
        return {
            rid: rec for rid, rec in self.records.items()
            if rec.is_authoritative_active
        }

    def get_all_relations(self) -> list[Relation]:
        """Collect all outgoing relations across all records in the state."""
        all_rels = []
        for rec in self.records.values():
            all_rels.extend(rec.relations)
        return all_rels

    def get_incoming_relations(self, target_id: str) -> list[Relation]:
        """Find all relations pointing to target_id."""
        return [
            rel for rec in self.records.values()
            for rel in rec.relations
            if rel.object_id == target_id
        ]
