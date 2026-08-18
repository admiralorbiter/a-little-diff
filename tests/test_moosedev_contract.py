"""Canonical 8-case MOOSEDev contract evaluation test suite."""

import subprocess
from pathlib import Path
import pytest

from alittlediff.adapters.moosedev import MOOSEDevAdapter
from alittlediff.diff.structural import diff_states
from alittlediff.domain import EpistemicRecord, EpistemicState, Relation
from alittlediff.impact import find_impacts
from tests.fixtures.moosedev_fixtures import NQUADS_STATE_A, NQUADS_STATE_B


# Case 1: A -> A Exact semantic no-op
def test_contract_case_1_exact_semantic_noop():
    adapter = MOOSEDevAdapter()
    state_a1 = adapter.parse_nquads(NQUADS_STATE_A, revision="sha_a1")
    state_a2 = adapter.parse_nquads(NQUADS_STATE_A, revision="sha_a2")

    changes = diff_states(state_a1, state_a2)
    impacts = find_impacts(changes, state_a1, state_a2)

    assert len(changes) == 0
    assert len(impacts) == 0


# Case 2: Code-only commit (knowledge graph unchanged)
def test_contract_case_2_code_only_commit(tmp_path: Path):
    repo = tmp_path / "code_only_repo"
    repo.mkdir()

    def run_git(*args: str):
        subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True, check=True)

    run_git("init", "-b", "main")
    run_git("config", "user.name", "Test")
    run_git("config", "user.email", "test@test.com")

    moose_dir = repo / ".moosedev"
    moose_dir.mkdir()
    (moose_dir / "kg.nq").write_text(NQUADS_STATE_A, encoding="utf-8")
    (repo / "app.py").write_text("print('version 1')\n", encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", "Commit A: initial with code and memory")
    run_git("tag", "state_a")

    # Commit B: code change only, kg.nq unchanged
    (repo / "app.py").write_text("print('version 2: bugfix')\n", encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", "Commit B: code-only refactor")

    adapter = MOOSEDevAdapter()
    state_a = adapter.load_state(repo, "state_a")
    state_b = adapter.load_state(repo, "HEAD")

    changes = diff_states(state_a, state_b)
    impacts = find_impacts(changes, state_a, state_b)

    assert len(changes) == 0
    assert len(impacts) == 0


# Case 3: Accepted record added (normal expansion)
def test_contract_case_3_accepted_record_added():
    state_a_text = """
<urn:record:constraint:1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Constraint> .
<urn:record:constraint:1> <https://moosedev.org/ontology/hasTitle> "Constraint 1" .
<urn:record:constraint:1> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" .
""".strip()

    state_b_text = """
<urn:record:constraint:1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Constraint> .
<urn:record:constraint:1> <https://moosedev.org/ontology/hasTitle> "Constraint 1" .
<urn:record:constraint:1> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" .

<urn:record:constraint:2> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Constraint> .
<urn:record:constraint:2> <https://moosedev.org/ontology/hasTitle> "Constraint 2" .
<urn:record:constraint:2> <https://moosedev.org/ontology/hasDescription> "New security requirement." .
<urn:record:constraint:2> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" .
""".strip()

    adapter = MOOSEDevAdapter()
    state_a = adapter.parse_nquads(state_a_text, revision="a")
    state_b = adapter.parse_nquads(state_b_text, revision="b")

    changes = diff_states(state_a, state_b)
    assert len(changes) == 1
    assert changes[0].structural_type == "added"
    assert changes[0].after.id == "urn:record:constraint:2"
    assert changes[0].after.title == "Constraint 2"


# Case 4: Constraint superseded with MOOSEDev vocabulary and absorbed Rationale
def test_contract_case_4_supersession_and_rationale_absorption():
    adapter = MOOSEDevAdapter()
    state_a = adapter.parse_nquads(NQUADS_STATE_A, revision="a")
    state_b = adapter.parse_nquads(NQUADS_STATE_B, revision="b")

    changes = diff_states(state_a, state_b)

    # Constraint C1 is superseded by C2, with a Rationale node attached.
    # The Rationale node must be absorbed into the supersession event, NOT output as a separate added record!
    assert len(changes) == 1
    chg = changes[0]
    assert chg.structural_type == "superseded"
    assert chg.before.id == "urn:record:constraint:1"
    assert chg.after.id == "urn:record:constraint:2"
    assert chg.details["superseded_id"] == "urn:record:constraint:1"
    assert chg.details["superseded_by"] == "urn:record:constraint:2"
    assert chg.details.get("rationale") == "Vendor released attendance endpoint."


# Case 5: Superseded constraint with motivated decision (downstream impact)
def test_contract_case_5_superseded_constraint_with_motivated_decision():
    adapter = MOOSEDevAdapter()
    state_a = adapter.parse_nquads(NQUADS_STATE_A, revision="a")
    state_b = adapter.parse_nquads(NQUADS_STATE_B, revision="b")

    changes = diff_states(state_a, state_b)
    impacts = find_impacts(changes, state_a, state_b, max_depth=1)

    # Decision 1 was motivated by Constraint 1 in State A.
    # When Constraint 1 is superseded, Decision 1 must be flagged for reconsideration.
    assert len(impacts) == 1
    imp = impacts[0]
    assert imp.target_record_id == "urn:record:decision:1"
    assert imp.target_record.title == "Manual attendance workflow"
    assert imp.effect == "justification_may_have_changed"
    assert imp.confidence == "high"
    assert imp.path[0].predicate == "isMotivatedBy"


# Case 6: Unrelated decision (zero false-positive impact)
def test_contract_case_6_unrelated_decision_no_false_positive():
    adapter = MOOSEDevAdapter()
    state_a = adapter.parse_nquads(NQUADS_STATE_A, revision="a")
    state_b = adapter.parse_nquads(NQUADS_STATE_B, revision="b")

    # Add an unrelated decision
    unrelated_dec = EpistemicRecord(
        id="urn:record:decision:unrelated",
        kind="Decision",
        title="Use PostgreSQL for analytics",
        status="accepted",
    )
    state_a.records[unrelated_dec.id] = unrelated_dec
    state_b.records[unrelated_dec.id] = unrelated_dec

    changes = diff_states(state_a, state_b)
    impacts = find_impacts(changes, state_a, state_b, max_depth=1)

    assert all(i.target_record_id != "urn:record:decision:unrelated" for i in impacts)


# Case 7: Proposed / Rejected / Deprecated record working-set semantics
def test_contract_case_7_working_set_semantics():
    state_text = """
<urn:record:rec:accepted> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Decision> .
<urn:record:rec:accepted> <https://moosedev.org/ontology/hasTitle> "Accepted Decision" .
<urn:record:rec:accepted> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" .

<urn:record:rec:proposed> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Decision> .
<urn:record:rec:proposed> <https://moosedev.org/ontology/hasTitle> "Proposed Idea" .
<urn:record:rec:proposed> <https://moosedev.org/ontology/hasLifecycleStatus> "proposed" .

<urn:record:rec:rejected> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Decision> .
<urn:record:rec:rejected> <https://moosedev.org/ontology/hasTitle> "Rejected Idea" .
<urn:record:rec:rejected> <https://moosedev.org/ontology/hasLifecycleStatus> "rejected" .

<urn:record:rec:deprecated> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Constraint> .
<urn:record:rec:deprecated> <https://moosedev.org/ontology/hasTitle> "Deprecated Constraint" .
<urn:record:rec:deprecated> <https://moosedev.org/ontology/hasLifecycleStatus> "deprecated" .
""".strip()

    adapter = MOOSEDevAdapter()
    state = adapter.parse_nquads(state_text, revision="rev_ws")

    assert len(state.records) == 4

    # active_records working set should contain ONLY accepted/authoritative records
    active = state.active_records
    assert len(active) == 1
    assert "urn:record:rec:accepted" in active
    assert "urn:record:rec:proposed" not in active
    assert "urn:record:rec:rejected" not in active
    assert "urn:record:rec:deprecated" not in active


# Case 8: Historical edge retention
# Decision D was motivated by C1 in base state, but relation was dropped/modified in head state.
# When C1 is superseded, Decision D must still be flagged via its historical motivation.
def test_contract_case_8_historical_edge_retention():
    # Base state: Decision D1 isMotivatedBy Constraint C1
    c1 = EpistemicRecord(id="urn:rec:c1", kind="Constraint", title="API v1 limit", status="accepted")
    rel_hist = Relation(predicate="isMotivatedBy", subject_id="urn:rec:d1", object_id="urn:rec:c1")
    d1_base = EpistemicRecord(id="urn:rec:d1", kind="Decision", title="Batching strategy", status="accepted", relations=[rel_hist])

    state_a = EpistemicState(source="moosedev", revision="sha_a", records={c1.id: c1, d1_base.id: d1_base})

    # Head state: C1 superseded by C2. D1 has NO outgoing relations in head state (relation was dropped).
    c2 = EpistemicRecord(id="urn:rec:c2", kind="Constraint", title="API v2 unlimited", status="accepted", relations=[
        Relation(predicate="supersedes", subject_id="urn:rec:c2", object_id="urn:rec:c1")
    ])
    c1_head = EpistemicRecord(id="urn:rec:c1", kind="Constraint", title="API v1 limit", status="superseded")
    d1_head = EpistemicRecord(id="urn:rec:d1", kind="Decision", title="Batching strategy", status="accepted", relations=[])

    state_b = EpistemicState(source="moosedev", revision="sha_b", records={c1_head.id: c1_head, c2.id: c2, d1_head.id: d1_head})

    changes = diff_states(state_a, state_b)
    assert len(changes) >= 1
    assert any(c.structural_type == "superseded" for c in changes)

    impacts = find_impacts(changes, state_a, state_b, max_depth=1)

    # Decision D1 MUST be surfaced because historically in State A it was motivated by C1
    assert len(impacts) == 1
    assert impacts[0].target_record_id == "urn:rec:d1"
    assert impacts[0].effect == "justification_may_have_changed"
    assert impacts[0].path[0].predicate == "isMotivatedBy"
