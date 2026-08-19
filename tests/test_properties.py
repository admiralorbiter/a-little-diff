"""Hypothesis property-based testing suite for universal epistemic invariants."""

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

        # Optional relations to other records
        if n_recs > 1:
            n_rels = draw(st.integers(min_value=0, max_value=2))
            for _ in range(n_rels):
                target_id = draw(st.sampled_from([o for o in record_ids if o != r_id]))
                pred = draw(st.sampled_from(PREDICATES))
                lines.append(f"<{r_id}> <https://moosedev.org/ontology/{pred}> <{target_id}> .")

    return "\n".join(lines) + "\n"


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
    """Property 2: Permuting line order in state inputs produces identical changes and impacts."""
    adapter = MOOSEDevAdapter()

    base_a = adapter.parse_nquads(state_a_text, revision="base_a")
    base_b = adapter.parse_nquads(state_b_text, revision="base_b")
    base_changes = diff_states(base_a, base_b)
    base_impacts = find_impacts(base_changes, base_a, base_b)

    # Shuffled version
    lines_a = [l for l in state_a_text.splitlines() if l.strip()]
    lines_b = [l for l in state_b_text.splitlines() if l.strip()]
    random.Random(42).shuffle(lines_a)
    random.Random(42).shuffle(lines_b)

    shuf_a = adapter.parse_nquads("\n".join(lines_a), revision="shuf_a")
    shuf_b = adapter.parse_nquads("\n".join(lines_b), revision="shuf_b")
    shuf_changes = diff_states(shuf_a, shuf_b)
    shuf_impacts = find_impacts(shuf_changes, shuf_a, shuf_b)

    assert len(base_changes) == len(shuf_changes)
    assert len(base_impacts) == len(shuf_impacts)


@settings(max_examples=30, deadline=None)
@given(
    state_a_text=random_nquads_state(min_records=1, max_records=4),
    state_b_text=random_nquads_state(min_records=1, max_records=4),
)
def test_property_differential_reference_engine_equivalence(state_a_text: str, state_b_text: str):
    """Property 3: Differential testing - production find_impacts matches reference_find_impacts."""
    adapter = MOOSEDevAdapter()
    state_a = adapter.parse_nquads(state_a_text, revision="rev_a")
    state_b = adapter.parse_nquads(state_b_text, revision="rev_b")

    changes = diff_states(state_a, state_b)
    prod_impacts = find_impacts(changes, state_a, state_b, max_depth=1)
    ref_impact_sigs = reference_find_impacts(changes, state_a, state_b, max_depth=1)

    prod_impact_sigs = {(imp.source_change_id, imp.target_record_id, imp.effect, imp.confidence) for imp in prod_impacts}

    assert prod_impact_sigs == ref_impact_sigs, (
        f"Differential mismatch between production and reference engine:\n"
        f"  Production: {prod_impact_sigs}\n"
        f"  Reference:  {ref_impact_sigs}"
    )
