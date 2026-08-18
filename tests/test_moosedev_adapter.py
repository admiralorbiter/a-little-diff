import subprocess
from pathlib import Path
import pytest

from alittlediff.adapters.moosedev import MOOSEDevAdapter
from tests.fixtures.moosedev_fixtures import NQUADS_STATE_A, NQUADS_STATE_B


def test_moosedev_adapter_parse_state_a():
    adapter = MOOSEDevAdapter()
    state = adapter.parse_nquads(NQUADS_STATE_A, revision="rev_a")

    assert state.source == "moosedev"
    assert state.revision == "rev_a"
    assert len(state.records) == 3

    # Verify Constraint 1
    c1 = state.get_record("urn:record:constraint:1")
    assert c1 is not None
    assert c1.kind == "Constraint"
    assert c1.title == "Teacher attendance constraint"
    assert c1.claim == "Teacher attendance must be entered manually."
    assert c1.status == "accepted"
    assert len(c1.evidence) == 1
    assert c1.evidence[0].source_type == "moosedev"

    # Verify Decision 1
    d1 = state.get_record("urn:record:decision:1")
    assert d1 is not None
    assert d1.kind == "Decision"
    assert d1.title == "Manual attendance workflow"
    assert len(d1.relations) == 1
    assert d1.relations[0].predicate == "isMotivatedBy"
    assert d1.relations[0].object_id == "urn:record:constraint:1"

    # Verify Requirement 1
    r1 = state.get_record("urn:record:requirement:1")
    assert r1 is not None
    assert r1.kind == "Requirement"
    assert len(r1.relations) == 1
    assert r1.relations[0].predicate == "concerns"
    assert r1.relations[0].object_id == "urn:record:decision:1"


def test_moosedev_adapter_parse_state_b():
    adapter = MOOSEDevAdapter()
    state = adapter.parse_nquads(NQUADS_STATE_B, revision="rev_b")

    # In State B: Constraint 1, Constraint 2, Rationale 1, Decision 1, Requirement 1
    assert len(state.records) == 5

    c1 = state.get_record("urn:record:constraint:1")
    assert c1 is not None
    assert c1.status == "superseded"

    c2 = state.get_record("urn:record:constraint:2")
    assert c2 is not None
    assert c2.kind == "Constraint"
    assert c2.title == "Pathful attendance import"
    assert c2.status == "accepted"
    assert any(r.predicate == "supersedes" and r.object_id == "urn:record:constraint:1" for r in c2.relations)
    assert any(r.predicate == "hasRationale" and r.object_id == "urn:record:rationale:1" for r in c2.relations)


def test_moosedev_adapter_determinism():
    adapter = MOOSEDevAdapter()
    state1 = adapter.parse_nquads(NQUADS_STATE_B, revision="rev_b")
    state2 = adapter.parse_nquads(NQUADS_STATE_B, revision="rev_b")

    assert list(state1.records.keys()) == list(state2.records.keys())
    assert state1.model_dump() == state2.model_dump()


def test_moosedev_adapter_load_from_git_repo(tmp_path: Path):
    repo = tmp_path / "moose_repo"
    repo.mkdir()

    def run_git(*args: str) -> str:
        res = subprocess.run(
            ["git", *args],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()

    run_git("init", "-b", "main")
    run_git("config", "user.name", "Test User")
    run_git("config", "user.email", "test@example.com")

    moose_dir = repo / ".moosedev"
    moose_dir.mkdir()
    (moose_dir / "kg.nq").write_text(NQUADS_STATE_A, encoding="utf-8")

    run_git("add", ".")
    run_git("commit", "-m", "Commit A")
    run_git("tag", "state_a")

    (moose_dir / "kg.nq").write_text(NQUADS_STATE_B, encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", "Commit B")

    adapter = MOOSEDevAdapter()
    assert adapter.can_load(repo, "state_a") is True
    assert adapter.can_load(repo, "HEAD") is True

    state_a = adapter.load_state(repo, "state_a")
    assert len(state_a.records) == 3
    assert state_a.get_record("urn:record:constraint:1").status == "accepted"

    state_b = adapter.load_state(repo, "HEAD")
    assert len(state_b.records) == 5
    assert state_b.get_record("urn:record:constraint:1").status == "superseded"
