"""Hypothesis property-based testing suite for universal epistemic invariants."""

from collections import Counter
import random
from hypothesis import given, settings, strategies as st

from alittlediff.adapters.moosedev import MOOSEDevAdapter
from alittlediff.diff.structural import diff_states
from alittlediff.impact import find_impacts
from tests.reference_evaluator import reference_find_impacts

KINDS = ["Decision", "Constraint", "Requirement", "Lesson", "Consequence", "CodeEntity"]
STATUSES = ["accepted", "proposed", "rejected", "superseded", "retracted"]
PREDICATES = ["constrains", "isConstrainedBy", "isMotivatedBy", "resultsIn", "learnedFrom", "concerns"]


@st.composite
def random_nquads_state(draw, min_records=1, max_records=6):
    """Generate a syntactically valid synthetic N-Quads epistemic snapshot."""
    n_recs = draw(st.integers(min_value=min_records, max_value=max_records))
    record_ids = [f"urn:rec:entity_{i}" for i in range(n_recs)]

    lines = []
    for r_id in record_ids:
        kind = draw(st.sampled_from(KINDS))
        status = draw(st.sampled_from(STATUSES))
        title = draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))) or "Item"

        lines.append(f"<{r_id}> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/{kind}> .")
        lines.append(f"<{r_id}> <https://moosedev.org/ontology/hasTitle> \"{title}\" .")
        lines.append(f"<{r_id}> <https://moosedev.org/ontology/hasLifecycleStatus> \"{status}\" .")

        if n_recs > 1:
            n_rels = draw(st.integers(min_value=0, max_value=2))
            for _ in range(n_rels):
                target_id = draw(st.sampled_from([o for o in record_ids if o != r_id]))
                pred = draw(st.sampled_from(PREDICATES))
                lines.append(f"<{r_id}> <https://moosedev.org/ontology/{pred}> <{target_id}> .")

    return "\n".join(lines) + "\n"


@st.composite
def causal_state_transition(draw):
    """Generate a realistic state transition (State A -> State B) by applying a discrete operation."""
    n_recs = draw(st.integers(min_value=2, max_value=5))
    record_ids = [f"urn:rec:node_{i}" for i in range(n_recs)]

    records = {}
    for r_id in record_ids:
        records[r_id] = {
            "kind": draw(st.sampled_from(["Decision", "Constraint", "Requirement", "Lesson", "Consequence"])),
            "status": "accepted",
            "title": f"Initial {r_id.split(':')[-1]}",
            "relations": [],
        }

    # Add 1-3 initial relations
    for _ in range(draw(st.integers(min_value=1, max_value=3))):
        src = draw(st.sampled_from(record_ids))
        dst = draw(st.sampled_from([r for r in record_ids if r != src]))
        pred = draw(st.sampled_from(PREDICATES))
        records[src]["relations"].append((pred, dst))

    def _build_nquads(rec_dict):
        lines = []
        for rid, rdata in rec_dict.items():
            lines.append(f"<{rid}> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/{rdata['kind']}> .")
            lines.append(f"<{rid}> <https://moosedev.org/ontology/hasTitle> \"{rdata['title']}\" .")
            lines.append(f"<{rid}> <https://moosedev.org/ontology/hasLifecycleStatus> \"{rdata['status']}\" .")
            for pred, target in rdata["relations"]:
                lines.append(f"<{rid}> <https://moosedev.org/ontology/{pred}> <{target}> .")
        return "\n".join(lines) + "\n"

    state_a_nquads = _build_nquads(records)

    # Derive State B by applying an operation
    op = draw(st.sampled_from(["add", "modify", "supersede", "retract", "relate", "inverse_rel"]))
    records_b = {k: {"kind": v["kind"], "status": v["status"], "title": v["title"], "relations": list(v["relations"])} for k, v in records.items()}

    if op == "add":
        new_id = f"urn:rec:node_{n_recs}"
        records_b[new_id] = {
            "kind": draw(st.sampled_from(["Decision", "Constraint", "Requirement"])),
            "status": "accepted",
            "title": "Newly Added Record",
            "relations": [],
        }
    elif op == "modify":
        target = draw(st.sampled_from(record_ids))
        records_b[target]["title"] = records_b[target]["title"] + " Modified"
    elif op == "supersede":
        old_id = draw(st.sampled_from(record_ids))
        new_id = f"urn:rec:node_{n_recs}"
        records_b[old_id]["status"] = "superseded"
        records_b[old_id]["relations"].append(("isSupersededBy", new_id))
        records_b[new_id] = {
            "kind": records[old_id]["kind"],
            "status": "accepted",
            "title": f"Superseding {records[old_id]['title']}",
            "relations": [("supersedes", old_id)],
        }
    elif op == "retract":
        target = draw(st.sampled_from(record_ids))
        records_b[target]["status"] = "retracted"
    elif op == "relate":
        src = draw(st.sampled_from(record_ids))
        dst = draw(st.sampled_from([r for r in record_ids if r != src]))
        pred = draw(st.sampled_from(PREDICATES))
        records_b[src]["relations"].append((pred, dst))

    state_b_nquads = _build_nquads(records_b)
    return state_a_nquads, state_b_nquads, op


@settings(max_examples=40, deadline=None)
@given(state_text=random_nquads_state(min_records=1, max_records=5))
def test_property_identity_noop(state_text: str):
    """Property 1: Diffing any valid state against itself yields 0 changes and 0 impacts."""
    adapter = MOOSEDevAdapter()
    state_a = adapter.parse_nquads(state_text, revision="rev_a")
    state_b = adapter.parse_nquads(state_text, revision="rev_b")

    changes = diff_states(state_a, state_b)
    impacts = find_impacts(changes, state_a, state_b)

    assert len(changes) == 0
    assert len(impacts) == 0


@settings(max_examples=30, deadline=None)
@given(
    state_a_text=random_nquads_state(min_records=1, max_records=4),
    state_b_text=random_nquads_state(min_records=1, max_records=4),
)
def test_property_permutation_invariance(state_a_text: str, state_b_text: str):
    """Property 2: Permuting line order produces exact identical change and impact signature multisets."""
    adapter = MOOSEDevAdapter()

    base_a = adapter.parse_nquads(state_a_text, revision="base_a")
    base_b = adapter.parse_nquads(state_b_text, revision="base_b")
    base_changes = diff_states(base_a, base_b)
    base_impacts = find_impacts(base_changes, base_a, base_b)

    # Shuffled serialization version
    lines_a = [l for l in state_a_text.splitlines() if l.strip()]
    lines_b = [l for l in state_b_text.splitlines() if l.strip()]
    random.Random(42).shuffle(lines_a)
    random.Random(42).shuffle(lines_b)

    shuf_a = adapter.parse_nquads("\n".join(lines_a), revision="shuf_a")
    shuf_b = adapter.parse_nquads("\n".join(lines_b), revision="shuf_b")
    shuf_changes = diff_states(shuf_a, shuf_b)
    shuf_impacts = find_impacts(shuf_changes, shuf_a, shuf_b)

    # Assert exact change signatures match
    base_chg_sigs = Counter((c.structural_type, c.before.id if c.before else None, c.after.id if c.after else None) for c in base_changes)
    shuf_chg_sigs = Counter((c.structural_type, c.before.id if c.before else None, c.after.id if c.after else None) for c in shuf_changes)
    assert base_chg_sigs == shuf_chg_sigs

    # Assert exact impact signatures match
    base_imp_sigs = Counter((i.source_change_id, i.target_record_id, i.effect, i.confidence, tuple(r.predicate for r in i.path)) for i in base_impacts)
    shuf_imp_sigs = Counter((i.source_change_id, i.target_record_id, i.effect, i.confidence, tuple(r.predicate for r in i.path)) for i in shuf_impacts)
    assert base_imp_sigs == shuf_imp_sigs


@settings(max_examples=30, deadline=None)
@given(transition=causal_state_transition())
def test_property_state_transition_differential_equivalence(transition):
    """Property 3: Causal transitions verify differential equivalence with multi-hop reference BFS."""
    state_a_text, state_b_text, op = transition
    adapter = MOOSEDevAdapter()
    state_a = adapter.parse_nquads(state_a_text, revision="rev_a")
    state_b = adapter.parse_nquads(state_b_text, revision="rev_b")

    changes = diff_states(state_a, state_b)
    prod_impacts = find_impacts(changes, state_a, state_b, max_depth=1)
    ref_impact_sigs = reference_find_impacts(changes, state_a, state_b, max_depth=1)

    prod_impact_sigs = {(imp.source_change_id, imp.target_record_id, imp.effect, imp.confidence) for imp in prod_impacts}

    assert prod_impact_sigs == ref_impact_sigs, (
        f"Differential mismatch on operation '{op}':\n"
        f"  Production: {prod_impact_sigs}\n"
        f"  Reference:  {ref_impact_sigs}"
    )
