"""Independent reference evaluator for differential testing.

A deliberately simple, direct BFS implementation of causal impact traversal,
kept completely separate from production code paths to prevent correlated bugs.
"""

REF_RULES = {
    "isMotivatedBy": ("reverse", "justification_may_have_changed", "high"),
    "motivates": ("forward", "justification_may_have_changed", "high"),
    "constrains": ("forward", "constraint_context_changed", "high"),
    "isConstrainedBy": ("reverse", "constraint_context_changed", "high"),
    "constrainedBy": ("reverse", "constraint_context_changed", "high"),
    "dependsOn": ("reverse", "dependency_may_have_changed", "high"),
    "resultsIn": ("forward", "consequence_may_have_changed", "medium"),
    "resultsFrom": ("reverse", "consequence_may_have_changed", "medium"),
    "learnedFrom": ("reverse", "lesson_context_changed", "medium"),
    "concerns": ("both", "inspect", "low"),
    "justifiedBy": ("reverse", "justification_may_have_changed", "high"),
}


def reference_find_impacts(
    changes,
    base_state,
    head_state,
    max_depth: int = 1,
) -> set[tuple[str, str, str, str]]:
    """Compute impacts using a minimal BFS algorithm.
    
    Returns:
        Set of (source_change_id, target_record_id, effect, confidence) tuples.
    """
    results: set[tuple[str, str, str, str]] = set()
    seen_keys: set[tuple[str, str]] = set()

    for chg in changes:
        triggers = set()
        if chg.structural_type == "superseded":
            if chg.before:
                triggers.add(chg.before.id)
            if chg.after:
                triggers.add(chg.after.id)
            if "superseded_id" in chg.details:
                triggers.add(chg.details["superseded_id"])
            if "superseding_id" in chg.details:
                triggers.add(chg.details["superseding_id"])
        elif chg.structural_type in ("removed", "status_changed", "modified"):
            if chg.before:
                triggers.add(chg.before.id)
            if chg.after:
                triggers.add(chg.after.id)

        for trigger_id in triggers:
            # 1. Reverse traversal: records pointing to trigger_id
            all_records = list(base_state.records.values()) + list(head_state.records.values())
            for rec in all_records:
                if rec.id == trigger_id:
                    continue
                for rel in rec.relations:
                    if rel.object_id == trigger_id and rel.predicate in REF_RULES:
                        direction, effect, conf = REF_RULES[rel.predicate]
                        if direction in ("reverse", "both"):
                            _ref_add(results, seen_keys, chg.change_id, rec.id, effect, conf, head_state, base_state)

            # 2. Forward traversal: relations originating from trigger_id
            trigger_recs = [r for r in (base_state.get_record(trigger_id), head_state.get_record(trigger_id)) if r]
            for trigger_rec in trigger_recs:
                for rel in trigger_rec.relations:
                    if rel.predicate in REF_RULES:
                        direction, effect, conf = REF_RULES[rel.predicate]
                        if direction in ("forward", "both"):
                            _ref_add(results, seen_keys, chg.change_id, rel.object_id, effect, conf, head_state, base_state)

    return results


def _ref_add(results, seen_keys, change_id, target_id, effect, confidence, head_state, base_state):
    key = (change_id, target_id)
    if key in seen_keys:
        return

    target = head_state.get_record(target_id) or base_state.get_record(target_id)
    if target and target.status == "accepted":
        seen_keys.add(key)
        results.add((change_id, target_id, effect, confidence))
