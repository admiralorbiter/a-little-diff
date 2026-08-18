from alittlediff.domain import (
    Evidence,
    Relation,
    EpistemicRecord,
    EpistemicState,
    EpistemicChange,
    Impact,
)


def test_domain_models_creation_and_serialization():
    ev = Evidence(
        source_type="git",
        source_id="commit123",
        revision="abc1234",
        path="docs/decision.md",
        excerpt="Constraint definition",
    )
    rel = Relation(
        predicate="isMotivatedBy",
        subject_id="urn:rec:decision:1",
        object_id="urn:rec:constraint:1",
        evidence=[ev],
    )
    rec1 = EpistemicRecord(
        id="urn:rec:constraint:1",
        kind="Constraint",
        title="Offline support",
        claim="System must function without active network connection.",
        status="active",
    )
    rec2 = EpistemicRecord(
        id="urn:rec:decision:1",
        kind="Decision",
        title="Local SQLite DB",
        claim="Use SQLite for local offline persistence.",
        status="active",
        relations=[rel],
    )

    state = EpistemicState(
        source="test",
        revision="abc1234",
        records={
            rec1.id: rec1,
            rec2.id: rec2,
        },
    )

    assert len(state.records) == 2
    assert state.get_record("urn:rec:constraint:1") == rec1
    assert len(state.active_records) == 2

    # Check relations querying and key
    assert len(state.get_all_relations()) == 1
    assert rel.key() == ("isMotivatedBy", "urn:rec:decision:1", "urn:rec:constraint:1")

    # Check incoming relations
    incoming = state.get_incoming_relations("urn:rec:constraint:1")
    assert len(incoming) == 1
    assert incoming[0].predicate == "isMotivatedBy"
    assert incoming[0].subject_id == "urn:rec:decision:1"


def test_epistemic_change_and_impact():
    rec_before = EpistemicRecord(
        id="urn:rec:1",
        kind="Constraint",
        title="Old constraint",
        status="active",
    )
    rec_after = EpistemicRecord(
        id="urn:rec:1",
        kind="Constraint",
        title="Old constraint",
        status="superseded",
    )

    change = EpistemicChange(
        change_id="chg-1",
        structural_type="superseded",
        semantic_type="world_update",
        before=rec_before,
        after=rec_after,
        judgment_source="deterministic",
    )

    assert change.structural_type == "superseded"
    assert change.judgment_source == "deterministic"

    impact = Impact(
        impact_id="imp-1",
        source_change_id="chg-1",
        target_record_id="urn:rec:decision:1",
        effect="justification_may_have_changed",
    )

    assert impact.effect == "justification_may_have_changed"
