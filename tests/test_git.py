import subprocess
from pathlib import Path
import pytest

from alittlediff.git import (
    is_git_repo,
    resolve_ref,
    parse_revision_range,
    load_text_at_ref,
    load_moosedev_snapshot,
    NotGitRepositoryError,
    UnknownRevisionError,
    MissingKnowledgeSnapshotError,
)





def test_is_git_repo(temp_git_repo: Path, tmp_path: Path):
    assert is_git_repo(temp_git_repo) is True
    non_repo = tmp_path / "non_repo"
    non_repo.mkdir()
    assert is_git_repo(non_repo) is False


def test_resolve_ref(temp_git_repo: Path):
    head_sha = resolve_ref(temp_git_repo, "HEAD")
    assert len(head_sha) == 40
    
    v01_sha = resolve_ref(temp_git_repo, "v0.1")
    assert len(v01_sha) == 40
    assert head_sha != v01_sha

    head_minus_1 = resolve_ref(temp_git_repo, "HEAD~1")
    assert head_minus_1 == v01_sha


def test_resolve_ref_errors(temp_git_repo: Path, tmp_path: Path):
    non_repo = tmp_path / "non_repo_dir"
    non_repo.mkdir()
    with pytest.raises(NotGitRepositoryError):
        resolve_ref(non_repo, "HEAD")

    with pytest.raises(UnknownRevisionError):
        resolve_ref(temp_git_repo, "non_existent_ref_12345")


def test_parse_revision_range(temp_git_repo: Path):
    base_sha, head_sha = parse_revision_range(temp_git_repo, "HEAD~1..HEAD")
    assert len(base_sha) == 40
    assert len(head_sha) == 40
    assert base_sha != head_sha

    with pytest.raises(ValueError):
        parse_revision_range(temp_git_repo, "invalid_range_syntax")


def test_load_text_at_ref(temp_git_repo: Path):
    base_content = load_text_at_ref(temp_git_repo, "v0.1", ".moosedev/kg.nq")
    assert "Premise A" in base_content
    assert "(revised)" not in base_content

    head_content = load_text_at_ref(temp_git_repo, "HEAD", ".moosedev/kg.nq")
    assert "Premise A (revised)" in head_content

    other_content = load_text_at_ref(temp_git_repo, "HEAD", "other.txt")
    assert "Hello world" in other_content


def test_load_moosedev_snapshot_missing(temp_git_repo: Path):
    # 'other.txt' does not exist in v0.1
    with pytest.raises(MissingKnowledgeSnapshotError):
        load_text_at_ref(temp_git_repo, "v0.1", "other.txt")

    # non-existent file
    with pytest.raises(MissingKnowledgeSnapshotError):
        load_text_at_ref(temp_git_repo, "HEAD", ".moosedev/non_existent.nq")


def test_load_snapshot_ignores_uncommitted_working_tree_changes(temp_git_repo: Path):
    # Modify working tree without committing
    kg_file = temp_git_repo / ".moosedev" / "kg.nq"
    kg_file.write_text("UNCOMMITTED DIRTY DATA", encoding="utf-8")

    # Loading at HEAD should return committed HEAD, NOT dirty working tree
    content = load_moosedev_snapshot(temp_git_repo, "HEAD")
    assert "UNCOMMITTED DIRTY DATA" not in content
    assert "Premise A (revised)" in content
