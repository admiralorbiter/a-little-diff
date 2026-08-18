from alittlediff.adapters.moosedev import MOOSEDevAdapter
from alittlediff.diff.structural import diff_states
from alittlediff.domain import EpistemicRecord, EpistemicState, Relation
from alittlediff.impact import (
    DEFAULT_PROPAGATION_RULES,
    PropagationRule,
    find_impacts,
)
from tests.fixtures.moosedev_fixtures import NQUADS_STATE_A, NQUADS_STATE_B


def test_impact_engine_1hop_supersession():
    adapter = MOOSEDevAdapter()
    state_a = adapter.parse_nquads(NQUADS_STATE_A, revision="rev_a")
    state_b = adapter.parse_nquads(NQUADS_STATE_B, revision="rev_b")

    changes = diff_states(state_a, state_b)
    assert len(changes) == 1
    assert changes[0].structural_type == "superseded"

    # Find 1-hop impacts
    impacts = find_impacts(changes, state_a, state_b, max_depth=1)

    # In State A, Decision 1 isMotivatedBy Constraint 1.
    # When Constraint 1 is superseded, Decision 1 should be flagged with effect justification_may_have_changed.
    assert len(impacts) >= 1
    dec_impact = next((i for i in impacts if i.target_record_id == "urn:record:decision:1"), None)
    assert dec_impact is not None
    assert dec_impact.effect == "justification_may_have_changed"
    assert dec_impact.confidence == "high"
    assert len(dec_impact.path) == 1
    assert dec_impact.path[0].predicate == "isMotivatedBy"
    assert len(dec_impact.evidence) >= 1


def test_impact_engine_2hop_propagation():
    adapter = MOOSEDevAdapter()
    state_a = adapter.parse_nquads(NQUADS_STATE_A, revision="rev_a")
    state_b = adapter.parse_nquads(NQUADS_STATE_B, revision="rev_b")

    changes = diff_states(state_a, state_b)
    # Find 2-hop impacts: Constraint 1 -> Decision 1 -> Requirement 1 (via concerns)
    impacts = find_impacts(changes, state_a, state_b, max_depth=2)

    req_impact = next((i for i in impacts if i.target_record_id == "urn:record:requirement:1"), None)
    assert req_impact is not None
    assert len(req_impact.path) == 2


def test_impact_engine_ignores_unrelated_records():
    adapter = MOOSEDevAdapter()
    state_a = adapter.parse_nquads(NQUADS_STATE_A, revision="rev_a")
    state_b = adapter.parse_nquads(NQUADS_STATE_B, revision="rev_b")

    # Add an unrelated active decision that does NOT point to Constraint 1
    unrelated_dec = EpistemicRecord(
        id="urn:record:decision:unrelated",
        kind="Decision",
        title="Unrelated decision",
        status="active",
    )
    state_a.records[unrelated_dec.id] = unrelated_dec
    state_b.records[unrelated_dec.id] = unrelated_dec

    changes = diff_states(state_a, state_b)
    impacts = find_impacts(changes, state_a, state_b, max_depth=1)

    # The unrelated decision must NOT appear in impacts
    assert all(i.target_record_id != "urn:record:decision:unrelated" for i in impacts)


def test_impact_engine_suppresses_already_retired_targets():
    # If the dependent decision is itself superseded or retired, it should not be flagged for active reconsideration
    rec_c1 = EpistemicRecord(id="urn:rec:c1", kind="Constraint", status="superseded")
    rel = Relation(predicate="isMotivatedBy", subject_id="urn:rec:d1", object_id="urn:rec:c1")
    rec_d1 = EpistemicRecord(id="urn:rec:d1", kind="Decision", status="retired", relations=[rel])

    state_a = EpistemicState(source="test", revision="a", records={rec_c1.id: rec_c1, rec_d1.id: rec_d1})
    state_b = EpistemicState(source="test", revision="b", records={rec_c1.id: rec_c1, rec_d1.id: rec_d1})

    chg = diff_states(state_a, state_b)
    impacts = find_impacts(chg, state_a, state_b)
    assert len(impacts) == 0


def test_impact_engine_custom_rules():
    # Test with custom forward propagation rule
    custom_rules = {
        "customRel": PropagationRule(
            predicate="customRel",
            direction="forward",
            effect="custom_effect",
            confidence="medium",
        )
    }

    rel = Relation(predicate="customRel", subject_id="urn:rec:src", object_id="urn:rec:tgt")
    rec_src_a = EpistemicRecord(id="urn:rec:src", kind="Constraint", status="active", relations=[rel])
    rec_src_b = EpistemicRecord(id="urn:rec:src", kind="Constraint", status="retracted", relations=[rel])
    rec_tgt = EpistemicRecord(id="urn:rec:tgt", kind="Plan", status="active")

    state_a = EpistemicState(source="test", revision="a", records={rec_src_a.id: rec_src_a, rec_tgt.id: rec_tgt})
    state_b = EpistemicState(source="test", revision="b", records={rec_src_b.id: rec_src_b, rec_tgt.id: rec_tgt})

    changes = diff_states(state_a, state_b)
    impacts = find_impacts(changes, state_a, state_b, rules=custom_rules)

    assert len(impacts) == 1
    assert impacts[0].target_record_id == "urn:rec:tgt"
    assert impacts[0].effect == "custom_effect"


def test_impact_engine_constrains_forward():
    """Constraint --constrains--> Decision: changed Constraint propagates forward to Decision."""
    rel = Relation(predicate="constrains", subject_id="urn:rec:c1", object_id="urn:rec:d1")
    c1_a = EpistemicRecord(id="urn:rec:c1", kind="Constraint", status="accepted", relations=[rel])
    c1_b = EpistemicRecord(id="urn:rec:c1", kind="Constraint", status="superseded", relations=[rel])
    d1 = EpistemicRecord(id="urn:rec:d1", kind="ArchitecturalDecision", status="accepted")

    state_a = EpistemicState(source="test", revision="a", records={c1_a.id: c1_a, d1.id: d1})
    state_b = EpistemicState(source="test", revision="b", records={c1_b.id: c1_b, d1.id: d1})

    changes = diff_states(state_a, state_b)
    impacts = find_impacts(changes, state_a, state_b)

    assert len(impacts) == 1
    assert impacts[0].target_record_id == "urn:rec:d1"
    assert impacts[0].effect == "constraint_context_changed"
    assert impacts[0].confidence == "high"


def test_impact_engine_negative_constrains_does_not_flag_upstream_constraint():
    """When a Decision changes, it must NOT traverse backwards along constrains to flag its Constraint."""
    rel = Relation(predicate="constrains", subject_id="urn:rec:c1", object_id="urn:rec:d1")
    c1 = EpistemicRecord(id="urn:rec:c1", kind="Constraint", status="accepted", relations=[rel])
    d1_a = EpistemicRecord(id="urn:rec:d1", kind="ArchitecturalDecision", status="accepted", claim="v1")
    d1_b = EpistemicRecord(id="urn:rec:d1", kind="ArchitecturalDecision", status="accepted", claim="v2")

    state_a = EpistemicState(source="test", revision="a", records={c1.id: c1, d1_a.id: d1_a})
    state_b = EpistemicState(source="test", revision="b", records={c1.id: c1, d1_b.id: d1_b})

    changes = diff_states(state_a, state_b)
    impacts = find_impacts(changes, state_a, state_b)

    # c1 must NOT be flagged as an impact of d1's modification
    assert all(i.target_record_id != "urn:rec:c1" for i in impacts)


def test_impact_engine_is_constrained_by_reverse():
    """Decision --isConstrainedBy--> Constraint: changed Constraint propagates in reverse to Decision."""
    rel = Relation(predicate="isConstrainedBy", subject_id="urn:rec:d1", object_id="urn:rec:c1")
    c1_a = EpistemicRecord(id="urn:rec:c1", kind="Constraint", status="accepted")
    c1_b = EpistemicRecord(id="urn:rec:c1", kind="Constraint", status="superseded")
    d1 = EpistemicRecord(id="urn:rec:d1", kind="ArchitecturalDecision", status="accepted", relations=[rel])

    state_a = EpistemicState(source="test", revision="a", records={c1_a.id: c1_a, d1.id: d1})
    state_b = EpistemicState(source="test", revision="b", records={c1_b.id: c1_b, d1.id: d1})

    changes = diff_states(state_a, state_b)
    impacts = find_impacts(changes, state_a, state_b)

    assert len(impacts) == 1
    assert impacts[0].target_record_id == "urn:rec:d1"
    assert impacts[0].effect == "constraint_context_changed"
    assert impacts[0].confidence == "high"


def test_impact_engine_learned_from_reverse():
    """Lesson --learnedFrom--> Decision: changed Decision propagates in reverse to Lesson."""
    rel = Relation(predicate="learnedFrom", subject_id="urn:rec:l1", object_id="urn:rec:d1")
    d1_a = EpistemicRecord(id="urn:rec:d1", kind="ArchitecturalDecision", status="accepted")
    d1_b = EpistemicRecord(id="urn:rec:d1", kind="ArchitecturalDecision", status="superseded")
    l1 = EpistemicRecord(id="urn:rec:l1", kind="Lesson", status="accepted", relations=[rel])

    state_a = EpistemicState(source="test", revision="a", records={d1_a.id: d1_a, l1.id: l1})
    state_b = EpistemicState(source="test", revision="b", records={d1_b.id: d1_b, l1.id: l1})

    changes = diff_states(state_a, state_b)
    impacts = find_impacts(changes, state_a, state_b)

    assert len(impacts) == 1
    assert impacts[0].target_record_id == "urn:rec:l1"
    assert impacts[0].effect == "lesson_context_changed"
    assert impacts[0].confidence == "medium"


def test_impact_engine_results_from_reverse():
    """Consequence --resultsFrom--> Decision: changed Decision propagates in reverse to Consequence."""
    rel = Relation(predicate="resultsFrom", subject_id="urn:rec:q1", object_id="urn:rec:d1")
    d1_a = EpistemicRecord(id="urn:rec:d1", kind="ArchitecturalDecision", status="accepted")
    d1_b = EpistemicRecord(id="urn:rec:d1", kind="ArchitecturalDecision", status="superseded")
    q1 = EpistemicRecord(id="urn:rec:q1", kind="Consequence", status="accepted", relations=[rel])

    state_a = EpistemicState(source="test", revision="a", records={d1_a.id: d1_a, q1.id: q1})
    state_b = EpistemicState(source="test", revision="b", records={d1_b.id: d1_b, q1.id: q1})

    changes = diff_states(state_a, state_b)
    impacts = find_impacts(changes, state_a, state_b)

    assert len(impacts) == 1
    assert impacts[0].target_record_id == "urn:rec:q1"
    assert impacts[0].effect == "consequence_may_have_changed"
    assert impacts[0].confidence == "medium"
