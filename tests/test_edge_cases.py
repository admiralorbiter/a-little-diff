import subprocess
from pathlib import Path
import pytest

from alittlediff.adapters.moosedev import MOOSEDevAdapter
from alittlediff.git import (
    load_text_at_ref,
    load_moosedev_snapshot,
    resolve_ref,
    parse_revision_range,
    MissingKnowledgeSnapshotError,
    UnknownRevisionError,
    NotGitRepositoryError,
)


def test_empty_nquads_parsing():
    adapter = MOOSEDevAdapter()
    state = adapter.parse_nquads("", revision="rev_empty")
    assert state.source == "moosedev"
    assert state.revision == "rev_empty"
    assert len(state.records) == 0


def test_unicode_and_special_characters_parsing():
    unicode_nquads = """
<urn:record:constraint:unicode> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Constraint> .
<urn:record:constraint:unicode> <http://purl.org/dc/terms/title> "Unicode test: üñîçødè & “smart quotes” — em-dash" .
<urn:record:constraint:unicode> <http://purl.org/dc/terms/description> "Testing special symbols: 🚀 λ → ∀ ∃" .
<urn:record:constraint:unicode> <https://moosedev.org/ontology/status> "active" .
""".strip()

    adapter = MOOSEDevAdapter()
    state = adapter.parse_nquads(unicode_nquads, revision="rev_unicode")
    rec = state.get_record("urn:record:constraint:unicode")
    assert rec is not None
    assert "“smart quotes”" in rec.title
    assert "🚀 λ → ∀ ∃" in rec.claim


def test_can_load_false_when_missing(tmp_path: Path):
    repo = tmp_path / "repo_no_moose"
    repo.mkdir()

    def run_git(*args: str):
        subprocess.run(
            ["git", *args],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=True,
        )

    run_git("init", "-b", "main")
    run_git("config", "user.name", "Test User")
    run_git("config", "user.email", "test@example.com")
    (repo / "README.md").write_text("# Test", encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", "Initial")

    adapter = MOOSEDevAdapter()
    assert adapter.can_load(repo, "HEAD") is False


def test_revision_range_parsing_edge_cases(temp_git_repo: Path):
    # Whitespace in range
    base, head = parse_revision_range(temp_git_repo, "  HEAD~1 .. HEAD  ")
    assert len(base) == 40
    assert len(head) == 40

    # Default base or head when omitted in range
    base2, head2 = parse_revision_range(temp_git_repo, "..HEAD")
    assert len(base2) == 40
    assert head2 == resolve_ref(temp_git_repo, "HEAD")

    base3, head3 = parse_revision_range(temp_git_repo, "v0.1..")
    assert base3 == resolve_ref(temp_git_repo, "v0.1")
    assert head3 == resolve_ref(temp_git_repo, "HEAD")

    # Invalid range without '..'
    with pytest.raises(ValueError, match="Expected format"):
        parse_revision_range(temp_git_repo, "HEAD")

    # Empty ref
    with pytest.raises(UnknownRevisionError):
        resolve_ref(temp_git_repo, "   ")
