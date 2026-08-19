"""Impact traversal engine."""

from typing import Optional
from alittlediff.domain.change import EpistemicChange
from alittlediff.domain.impact import Impact
from alittlediff.domain.relation import Relation
from alittlediff.domain.state import EpistemicState
from alittlediff.impact.policy import (
    DEFAULT_PROPAGATION_RULES,
    PropagationRule,
)


def _clean_id(raw_id: str) -> str:
    """Generate a clean slug for impact IDs."""
    return raw_id.replace(":", "_").replace("/", "_").replace("#", "_")


def find_impacts(
    changes: list[EpistemicChange],
    base_state: EpistemicState,
    head_state: EpistemicState,
    rules: Optional[dict[str, PropagationRule]] = None,
    max_depth: int = 1,
) -> list[Impact]:
    """Identify downstream records affected by upstream epistemic changes.
    
    Uses typed relationship semantics and conservative rules rather than generic
    reachability, ensuring reported impacts are defensible and traceable.
    
    Args:
        changes: List of computed EpistemicChange objects.
        base_state: Base epistemic snapshot.
        head_state: Head epistemic snapshot.
        rules: Propagation policy rules table.
        max_depth: Traversal depth (default 1 hop).
        
    Returns:
        List of Impact records sorted deterministically.
    """
    if rules is None:
        rules = DEFAULT_PROPAGATION_RULES

    impacts: list[Impact] = []
    seen_impact_keys: set[tuple[str, str]] = set()

    # Determine which record IDs have changed and might trigger propagation
    for chg in changes:
        # We look for records that served as upstream premises
        trigger_ids: set[str] = set()
        if chg.structural_type == "superseded":
            if chg.before:
                trigger_ids.add(chg.before.id)
            if chg.after:
                trigger_ids.add(chg.after.id)
            if "superseded_id" in chg.details:
                trigger_ids.add(chg.details["superseded_id"])
            if "superseding_id" in chg.details:
                trigger_ids.add(chg.details["superseding_id"])
        elif chg.structural_type in ("removed", "status_changed", "modified"):
            if chg.before:
                trigger_ids.add(chg.before.id)
            if chg.after:
                trigger_ids.add(chg.after.id)

        for trigger_id in trigger_ids:
            # 1. Reverse traversal: records that point TO trigger_id (e.g. Decision --isMotivatedBy--> Constraint)
            # Check relations in BOTH base_state AND head_state without overwriting to preserve historical motivations
            candidate_records = list(base_state.records.values()) + list(head_state.records.values())

            for rec in candidate_records:
                rec_id = rec.id
                if rec_id == trigger_id:
                    continue

                for rel in rec.relations:
                    if rel.object_id == trigger_id and rel.predicate in rules:
                        rule = rules[rel.predicate]
                        if rule.direction in ("reverse", "both"):
                            _add_impact(
                                impacts,
                                seen_impact_keys,
                                chg,
                                target_id=rec_id,
                                path=[rel],
                                rule=rule,
                                base_state=base_state,
                                head_state=head_state,
                            )

            # 2. Forward traversal: relations originating FROM trigger_id pointing to target (e.g. Action --resultsIn--> Effect)
            # Check relations originating from trigger_id in BOTH base_state AND head_state
            trigger_recs = [r for r in (base_state.get_record(trigger_id), head_state.get_record(trigger_id)) if r]
            for trigger_rec in trigger_recs:
                for rel in trigger_rec.relations:
                    if rel.predicate in rules:
                        rule = rules[rel.predicate]
                        if rule.direction in ("forward", "both"):
                            _add_impact(
                                impacts,
                                seen_impact_keys,
                                chg,
                                target_id=rel.object_id,
                                path=[rel],
                                rule=rule,
                                base_state=base_state,
                                head_state=head_state,
                            )

    # 2-hop propagation if max_depth >= 2
    if max_depth >= 2:
        hop1_impacts = list(impacts)
        candidate_records = list(base_state.records.values()) + list(head_state.records.values())
        for h1 in hop1_impacts:
            intermediate_id = h1.target_record_id
            for rec in candidate_records:
                rec_id = rec.id
                if rec_id == intermediate_id or (h1.source_change_id, rec_id) in seen_impact_keys:
                    continue
                for rel in rec.relations:
                    if rel.object_id == intermediate_id and rel.predicate in rules:
                        rule = rules[rel.predicate]
                        if rule.direction in ("reverse", "both"):
                            source_chg = next((c for c in changes if c.change_id == h1.source_change_id), None)
                            if source_chg:
                                _add_impact(
                                    impacts,
                                    seen_impact_keys,
                                    source_chg,
                                    target_id=rec_id,
                                    path=h1.path + [rel],
                                    rule=rule,
                                    base_state=base_state,
                                    head_state=head_state,
                                )

    # Sort deterministically
    impacts.sort(key=lambda imp: (imp.confidence, imp.target_record_id, imp.impact_id))
    return impacts


def _add_impact(
    impacts: list[Impact],
    seen_keys: set[tuple[str, str]],
    change: EpistemicChange,
    target_id: str,
    path: list[Relation],
    rule: PropagationRule,
    base_state: EpistemicState,
    head_state: EpistemicState,
):
    """Helper to construct and validate an impact candidate."""
    impact_key = (change.change_id, target_id)
    if impact_key in seen_keys:
        return

    # Check if target record exists in head_state (or base_state)
    target_rec = head_state.get_record(target_id) or base_state.get_record(target_id)
    if not target_rec:
        return

    # Suppress targets that are not authoritative or active (e.g. superseded, retired, deprecated, proposed, rejected)
    if not target_rec.is_authoritative_active:
        return

    seen_keys.add(impact_key)

    evidence = list(change.evidence)
    for r in path:
        evidence.extend(r.evidence)
    if target_rec.evidence:
        evidence.extend(target_rec.evidence)

    path_desc = " ─" + "".join(f"{r.predicate}→ " for r in path)

    impacts.append(
        Impact(
            impact_id=f"imp-{_clean_id(target_id)}-via-{_clean_id(change.change_id)}",
            source_change_id=change.change_id,
            target_record_id=target_id,
            target_record=target_rec,
            effect=rule.effect,
            path=path,
            evidence=evidence,
            confidence=rule.confidence,
            rationale=rule.description or f"Affected via {path_desc}",
        )
    )
