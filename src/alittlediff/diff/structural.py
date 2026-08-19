"""Structural epistemic diff engine."""

from typing import Any
from alittlediff.domain.change import EpistemicChange, StructuralChangeType
from alittlediff.domain.record import EpistemicRecord
from alittlediff.domain.relation import Relation
from alittlediff.domain.state import EpistemicState

# Sorting priority for structural change types to present high-level lifecycle events first
STRUCTURAL_ORDER: dict[StructuralChangeType, int] = {
    "superseded": 0,
    "status_changed": 1,
    "added": 2,
    "removed": 3,
    "modified": 4,
    "relation_added": 5,
    "relation_removed": 6,
}


def _clean_id(raw_id: str) -> str:
    """Generate a clean slug for change IDs."""
    return raw_id.replace(":", "_").replace("/", "_").replace("#", "_")


def diff_states(
    base_state: EpistemicState,
    head_state: EpistemicState,
) -> list[EpistemicChange]:
    """Compute the deterministic structural difference between two epistemic states.
    
    High-level lifecycle changes (such as supersessions) are collapsed into single
    epistemic events rather than producing multiple fragmented property changes.
    
    Args:
        base_state: The baseline epistemic state.
        head_state: The target epistemic state.
        
    Returns:
        List of EpistemicChange records sorted deterministically.
    """
    changes: list[EpistemicChange] = []
    handled_base_ids: set[str] = set()
    handled_head_ids: set[str] = set()

    # Step 1: Detect explicit supersessions (lifecycle collapsing)
    # Check head records for outgoing 'supersedes' or 'replaces' relations pointing to base records
    for head_id, head_rec in head_state.records.items():
        base_head_rec = base_state.get_record(head_id)
        for rel in head_rec.relations:
            pred_lower = rel.predicate.lower()
            if pred_lower in ("supersedes", "replaces"):
                target_base_id = rel.object_id
                base_rec = base_state.get_record(target_base_id)
                if base_rec is not None:
                    # Check if this exact supersession already existed in base_state
                    if base_head_rec is not None:
                        already_in_base = any(
                            r.predicate.lower() in ("supersedes", "replaces") and r.object_id == target_base_id
                            for r in base_head_rec.relations
                        )
                        if already_in_base and base_rec.status == "superseded":
                            continue

                    # Valid supersession detected
                    handled_head_ids.add(head_id)
                    handled_base_ids.add(target_base_id)

                    evidence = list(head_rec.evidence)
                    if base_rec.evidence:
                        evidence.extend(base_rec.evidence)
                    if rel.evidence:
                        evidence.extend(rel.evidence)

                    # Absorb associated Rationale nodes linked via hasRationale
                    rationale_text: str | None = None
                    for h_rel in head_rec.relations:
                        if h_rel.predicate.lower() in ("hasrationale", "rationale"):
                            rat_rec = head_state.get_record(h_rel.object_id) or base_state.get_record(h_rel.object_id)
                            if rat_rec is not None:
                                handled_head_ids.add(rat_rec.id)
                                handled_base_ids.add(rat_rec.id)
                                rationale_text = rat_rec.claim or rat_rec.title or rat_rec.id
                                if rat_rec.evidence:
                                    evidence.extend(rat_rec.evidence)

                    details: dict[str, Any] = {
                        "superseded_id": target_base_id,
                        "superseded_by": head_id,
                        "relation_predicate": rel.predicate,
                        "before_title": base_rec.title,
                        "after_title": head_rec.title,
                        "before_claim": base_rec.claim,
                        "after_claim": head_rec.claim,
                    }
                    if rationale_text:
                        details["rationale"] = rationale_text

                    changes.append(
                        EpistemicChange(
                            change_id=f"chg-superseded-{_clean_id(target_base_id)}",
                            structural_type="superseded",
                            before=base_rec,
                            after=head_rec,
                            evidence=evidence,
                            judgment_source="deterministic",
                            details=details,
                        )
                    )

    # Check for inverse isSupersededBy on base or head records
    for base_id, base_rec in base_state.records.items():
        if base_id in handled_base_ids:
            continue
        head_rec = head_state.get_record(base_id)
        if head_rec is not None:
            for rel in head_rec.relations:
                if rel.predicate.lower() == "issupersededby":
                    superseding_id = rel.object_id
                    superseding_rec = head_state.get_record(superseding_id)
                    if superseding_rec is not None:
                        # Check if base_rec was already superseded by superseding_id in base_state
                        already_in_base = any(
                            r.predicate.lower() == "issupersededby" and r.object_id == superseding_id
                            for r in base_rec.relations
                        )
                        if already_in_base and base_rec.status == "superseded":
                            continue

                        handled_base_ids.add(base_id)
                        handled_head_ids.add(superseding_id)
                        changes.append(
                            EpistemicChange(
                                change_id=f"chg-superseded-{_clean_id(base_id)}",
                                structural_type="superseded",
                                before=base_rec,
                                after=superseding_rec,
                                evidence=list(superseding_rec.evidence) + list(base_rec.evidence),
                                judgment_source="deterministic",
                                details={
                                    "superseded_id": base_id,
                                    "superseded_by": superseding_id,
                                    "relation_predicate": rel.predicate,
                                    "before_title": base_rec.title,
                                    "after_title": superseding_rec.title,
                                    "before_claim": base_rec.claim,
                                    "after_claim": superseding_rec.claim,
                                },
                            )
                        )

    # Also check for base records whose status transitioned to 'superseded' in head
    for base_id, base_rec in base_state.records.items():
        if base_id in handled_base_ids:
            continue
        head_rec = head_state.get_record(base_id)
        if head_rec is not None and base_rec.status != "superseded" and head_rec.status == "superseded":
            handled_base_ids.add(base_id)
            handled_head_ids.add(base_id)
            changes.append(
                EpistemicChange(
                    change_id=f"chg-superseded-{_clean_id(base_id)}",
                    structural_type="superseded",
                    before=base_rec,
                    after=head_rec,
                    evidence=list(head_rec.evidence) + list(base_rec.evidence),
                    judgment_source="deterministic",
                    details={
                        "superseded_id": base_id,
                        "old_status": base_rec.status,
                        "new_status": head_rec.status,
                    },
                )
            )

    # Step 2: Handle newly added standalone records
    for head_id, head_rec in head_state.records.items():
        if head_id in handled_head_ids or head_id in base_state.records:
            continue
        changes.append(
            EpistemicChange(
                change_id=f"chg-added-{_clean_id(head_id)}",
                structural_type="added",
                before=None,
                after=head_rec,
                evidence=list(head_rec.evidence),
                judgment_source="deterministic",
                details={
                    "kind": head_rec.kind,
                    "title": head_rec.title,
                    "claim": head_rec.claim,
                    "status": head_rec.status,
                },
            )
        )

    # Step 3: Handle removed records
    for base_id, base_rec in base_state.records.items():
        if base_id in handled_base_ids or base_id in head_state.records:
            continue
        changes.append(
            EpistemicChange(
                change_id=f"chg-removed-{_clean_id(base_id)}",
                structural_type="removed",
                before=base_rec,
                after=None,
                evidence=list(base_rec.evidence),
                judgment_source="deterministic",
                details={
                    "kind": base_rec.kind,
                    "title": base_rec.title,
                    "claim": base_rec.claim,
                    "status": base_rec.status,
                },
            )
        )

    # Step 4: Handle shared records (status changes, modifications, relation deltas)
    for shared_id in base_state.records.keys() & head_state.records.keys():
        if shared_id in handled_base_ids or shared_id in handled_head_ids:
            continue

        base_rec = base_state.records[shared_id]
        head_rec = head_state.records[shared_id]

        # 4a. Status change
        if base_rec.status != head_rec.status:
            changes.append(
                EpistemicChange(
                    change_id=f"chg-status-{_clean_id(shared_id)}",
                    structural_type="status_changed",
                    before=base_rec,
                    after=head_rec,
                    evidence=list(head_rec.evidence) + list(base_rec.evidence),
                    judgment_source="deterministic",
                    details={
                        "old_status": base_rec.status,
                        "new_status": head_rec.status,
                    },
                )
            )

        # 4b. Content modification (title, claim, kind)
        changed_fields: dict[str, tuple[Any, Any]] = {}
        if base_rec.title != head_rec.title:
            changed_fields["title"] = (base_rec.title, head_rec.title)
        if base_rec.claim != head_rec.claim:
            changed_fields["claim"] = (base_rec.claim, head_rec.claim)
        if base_rec.kind != head_rec.kind:
            changed_fields["kind"] = (base_rec.kind, head_rec.kind)

        if changed_fields:
            changes.append(
                EpistemicChange(
                    change_id=f"chg-modified-{_clean_id(shared_id)}",
                    structural_type="modified",
                    before=base_rec,
                    after=head_rec,
                    evidence=list(head_rec.evidence) + list(base_rec.evidence),
                    judgment_source="deterministic",
                    details={
                        "changed_fields": changed_fields,
                    },
                )
            )

        # 4c. Relation deltas
        base_rel_keys = {r.key(): r for r in base_rec.relations}
        head_rel_keys = {r.key(): r for r in head_rec.relations}

        added_rel_keys = head_rel_keys.keys() - base_rel_keys.keys()
        removed_rel_keys = base_rel_keys.keys() - head_rel_keys.keys()

        if added_rel_keys:
            added_rels = [head_rel_keys[k] for k in sorted(added_rel_keys)]
            changes.append(
                EpistemicChange(
                    change_id=f"chg-rel-added-{_clean_id(shared_id)}",
                    structural_type="relation_added",
                    before=base_rec,
                    after=head_rec,
                    evidence=[ev for r in added_rels for ev in r.evidence],
                    judgment_source="deterministic",
                    details={
                        "added_relations": [r.model_dump() for r in added_rels],
                    },
                )
            )

        if removed_rel_keys:
            removed_rels = [base_rel_keys[k] for k in sorted(removed_rel_keys)]
            changes.append(
                EpistemicChange(
                    change_id=f"chg-rel-removed-{_clean_id(shared_id)}",
                    structural_type="relation_removed",
                    before=base_rec,
                    after=head_rec,
                    evidence=[ev for r in removed_rels for ev in r.evidence],
                    judgment_source="deterministic",
                    details={
                        "removed_relations": [r.model_dump() for r in removed_rels],
                    },
                )
            )

    # Sort deterministically
    def sort_key(c: EpistemicChange) -> tuple[int, str, str]:
        order = STRUCTURAL_ORDER.get(c.structural_type, 99)
        rec_id = (c.after.id if c.after else (c.before.id if c.before else ""))
        return (order, rec_id, c.change_id)

    changes.sort(key=sort_key)
    return changes
