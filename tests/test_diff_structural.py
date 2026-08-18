from alittlediff.adapters.moosedev import MOOSEDevAdapter
from alittlediff.diff.structural import diff_states
from alittlediff.domain import EpistemicRecord, EpistemicState, Relation
from tests.fixtures.moosedev_fixtures import NQUADS_STATE_A, NQUADS_STATE_B


def test_diff_supersession_collapsing():
    adapter = MOOSEDevAdapter()
    state_a = adapter.parse_nquads(NQUADS_STATE_A, revision="rev_a")
    state_b = adapter.parse_nquads(NQUADS_STATE_B, revision="rev_b")

    changes = diff_states(state_a, state_b)

    # In STATE_A -> STATE_B:
    # Constraint 1 was active and superseded by Constraint 2.
    # Decision 1 and Requirement 1 did not change.
    assert len(changes) == 1
    chg = changes[0]
    assert chg.structural_type == "superseded"
    assert chg.before.id == "urn:record:constraint:1"
    assert chg.after.id == "urn:record:constraint:2"
    assert chg.details["superseded_id"] == "urn:record:constraint:1"
    assert chg.details["superseded_by"] == "urn:record:constraint:2"
    assert len(chg.evidence) >= 1


def test_diff_record_added_and_removed():
    rec1 = EpistemicRecord(id="urn:rec:1", kind="Requirement", title="Req 1")
    rec2 = EpistemicRecord(id="urn:rec:2", kind="Decision", title="Dec 2")

    state_a = EpistemicState(source="test", revision="a", records={"urn:rec:1": rec1})
    state_b = EpistemicState(source="test", revision="b", records={"urn:rec:2": rec2})

    changes = diff_states(state_a, state_b)
    assert len(changes) == 2

    # Ordered: added before removed per priority
    change_types = [c.structural_type for c in changes]
    assert "added" in change_types
    assert "removed" in change_types

    added_chg = next(c for c in changes if c.structural_type == "added")
    assert added_chg.after.id == "urn:rec:2"

    removed_chg = next(c for c in changes if c.structural_type == "removed")
    assert removed_chg.before.id == "urn:rec:1"


def test_diff_status_changed():
    rec_a = EpistemicRecord(id="urn:rec:1", kind="Decision", title="Dec 1", status="active")
    rec_b = EpistemicRecord(id="urn:rec:1", kind="Decision", title="Dec 1", status="retracted")

    state_a = EpistemicState(source="test", revision="a", records={"urn:rec:1": rec_a})
    state_b = EpistemicState(source="test", revision="b", records={"urn:rec:1": rec_b})

    changes = diff_states(state_a, state_b)
    assert len(changes) == 1
    assert changes[0].structural_type == "status_changed"
    assert changes[0].details["old_status"] == "active"
    assert changes[0].details["new_status"] == "retracted"


def test_diff_modified_content():
    rec_a = EpistemicRecord(id="urn:rec:1", kind="Constraint", title="Old title", claim="Old claim")
    rec_b = EpistemicRecord(id="urn:rec:1", kind="Constraint", title="New title", claim="New claim")

    state_a = EpistemicState(source="test", revision="a", records={"urn:rec:1": rec_a})
    state_b = EpistemicState(source="test", revision="b", records={"urn:rec:1": rec_b})

    changes = diff_states(state_a, state_b)
    assert len(changes) == 1
    assert changes[0].structural_type == "modified"
    assert "title" in changes[0].details["changed_fields"]
    assert "claim" in changes[0].details["changed_fields"]


def test_diff_relation_added_and_removed():
    rel1 = Relation(predicate="concerns", subject_id="urn:rec:1", object_id="urn:rec:2")
    rel2 = Relation(predicate="isMotivatedBy", subject_id="urn:rec:1", object_id="urn:rec:3")

    rec_a = EpistemicRecord(id="urn:rec:1", kind="Decision", title="Dec", relations=[rel1])
    rec_b = EpistemicRecord(id="urn:rec:1", kind="Decision", title="Dec", relations=[rel2])

    state_a = EpistemicState(source="test", revision="a", records={"urn:rec:1": rec_a})
    state_b = EpistemicState(source="test", revision="b", records={"urn:rec:1": rec_b})

    changes = diff_states(state_a, state_b)
    types = [c.structural_type for c in changes]
    assert "relation_added" in types
    assert "relation_removed" in types


def test_diff_noop():
    adapter = MOOSEDevAdapter()
    state_a1 = adapter.parse_nquads(NQUADS_STATE_A, revision="rev_a1")
    state_a2 = adapter.parse_nquads(NQUADS_STATE_A, revision="rev_a2")

    changes = diff_states(state_a1, state_a2)
    assert len(changes) == 0


def test_diff_superseded_status_only():
    rec_a = EpistemicRecord(id="urn:rec:1", kind="Constraint", title="C1", status="active")
    rec_b = EpistemicRecord(id="urn:rec:1", kind="Constraint", title="C1", status="superseded")

    state_a = EpistemicState(source="test", revision="a", records={"urn:rec:1": rec_a})
    state_b = EpistemicState(source="test", revision="b", records={"urn:rec:1": rec_b})

    changes = diff_states(state_a, state_b)
    assert len(changes) == 1
    assert changes[0].structural_type == "superseded"
    assert changes[0].details["superseded_id"] == "urn:rec:1"
