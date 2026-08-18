"""Shared test fixtures for A Little Diff."""

import subprocess
from pathlib import Path
import pytest


@pytest.fixture
def temp_git_repo(tmp_path: Path) -> Path:
    """Fixture to create a temporary Git repository with multiple commits and tags."""
    repo = tmp_path / "test_repo"
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

    # Commit 1: Initial commit with .moosedev/kg.nq at state 1
    moose_dir = repo / ".moosedev"
    moose_dir.mkdir()
    kg_file = moose_dir / "kg.nq"
    kg_file.write_text("<urn:record:1> <urn:prop:claim> \"Premise A\" .\n", encoding="utf-8")
    
    run_git("add", ".")
    run_git("commit", "-m", "Initial commit with premise A")
    run_git("tag", "v0.1")

    # Commit 2: Update .moosedev/kg.nq with state 2
    kg_file.write_text("<urn:record:1> <urn:prop:claim> \"Premise A (revised)\" .\n", encoding="utf-8")
    other_file = repo / "other.txt"
    other_file.write_text("Hello world\n", encoding="utf-8")
    
    run_git("add", ".")
    run_git("commit", "-m", "Revise premise A and add other.txt")

    return repo
