"""Independent reference evaluator for differential causal impact testing.

A clean, direct adjacency-list and BFS queue implementation that traverses
causal edges up to arbitrary max_depth. Kept completely separate from
production code paths to prevent correlated implementation bugs.
"""

from collections import deque
from typing import Any

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
    changes: list[Any],
    base_state: Any,
    head_state: Any,
    max_depth: int = 1,
) -> set[tuple[str, str, str, str]]:
    """Compute impacts using an independent adjacency-list BFS queue.
    
    Args:
        changes: EpistemicChange list from diff_states.
        base_state: Baseline EpistemicState.
        head_state: Target EpistemicState.
        max_depth: Maximum traversal hops from trigger nodes.

    Returns:
        Set of (source_change_id, target_record_id, effect, confidence) tuples.
    """
    # 1. Build adjacency structures across both base and head states
    outgoing_edges: dict[str, list[tuple[str, str]]] = {}
    incoming_edges: dict[str, list[tuple[str, str]]] = {}

    all_records = list(base_state.records.values()) + list(head_state.records.values())
    for rec in all_records:
        for rel in rec.relations:
            src = rel.subject_id
            dst = rel.object_id
            pred = rel.predicate

            outgoing_edges.setdefault(src, []).append((pred, dst))
            incoming_edges.setdefault(dst, []).append((pred, src))

    results: set[tuple[str, str, str, str]] = set()
    seen_keys: set[tuple[str, str]] = set()

    for chg in changes:
        triggers = _extract_triggers(chg)

        for trigger_id in triggers:
            # BFS queue: (current_node, current_depth)
            queue = deque([(trigger_id, 1)])
            visited = {trigger_id}

            while queue:
                curr_node, curr_depth = queue.popleft()
                if curr_depth > max_depth:
                    continue

                # Reverse causal propagation: records pointing to curr_node
                for pred, src_id in incoming_edges.get(curr_node, []):
                    if pred in REF_RULES:
                        direction, effect, conf = REF_RULES[pred]
                        if direction in ("reverse", "both"):
                            _ref_add(results, seen_keys, chg.change_id, src_id, effect, conf, head_state, base_state)
                            if curr_depth < max_depth and src_id not in visited:
                                visited.add(src_id)
                                queue.append((src_id, curr_depth + 1))

                # Forward causal propagation: relations originating from curr_node
                for pred, dst_id in outgoing_edges.get(curr_node, []):
                    if pred in REF_RULES:
                        direction, effect, conf = REF_RULES[pred]
                        if direction in ("forward", "both"):
                            _ref_add(results, seen_keys, chg.change_id, dst_id, effect, conf, head_state, base_state)
                            if curr_depth < max_depth and dst_id not in visited:
                                visited.add(dst_id)
                                queue.append((dst_id, curr_depth + 1))

    return results


def _extract_triggers(chg: Any) -> set[str]:
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
    return triggers


def _ref_add(
    results: set[tuple[str, str, str, str]],
    seen_keys: set[tuple[str, str]],
    change_id: str,
    target_id: str,
    effect: str,
    confidence: str,
    head_state: Any,
    base_state: Any,
):
    key = (change_id, target_id)
    if key in seen_keys:
        return

    target = head_state.get_record(target_id) or base_state.get_record(target_id)
    if target and target.status == "accepted":
        seen_keys.add(key)
        results.add((change_id, target_id, effect, confidence))
