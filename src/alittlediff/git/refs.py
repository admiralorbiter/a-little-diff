"""Git revision resolution and parsing."""

import subprocess
from pathlib import Path
from alittlediff.git.exceptions import NotGitRepositoryError, UnknownRevisionError


def is_git_repo(repo_path: Path) -> bool:
    """Check if the provided path is inside a valid Git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def resolve_ref(repo_path: Path, ref_str: str) -> str:
    """Resolve a revision string (branch, tag, SHA, HEAD~1, etc.) to a full 40-character commit SHA.
    
    Args:
        repo_path: Path to the Git repository.
        ref_str: Git revision identifier.
        
    Returns:
        Full 40-character commit SHA string.
        
    Raises:
        NotGitRepositoryError: If repo_path is not a Git repository.
        UnknownRevisionError: If ref_str cannot be resolved.
    """
    if not is_git_repo(repo_path):
        raise NotGitRepositoryError(str(repo_path))

    ref_str = ref_str.strip()
    if not ref_str:
        raise UnknownRevisionError(ref_str, "empty revision string")

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"{ref_str}^{{commit}}"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise NotGitRepositoryError(f"Git executable not found: {exc}")

    if result.returncode != 0:
        # Fallback to direct rev-parse without ^{commit} in case of lightweight tags or tree-ish
        fallback = subprocess.run(
            ["git", "rev-parse", "--verify", ref_str],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            check=False,
        )
        if fallback.returncode != 0:
            raise UnknownRevisionError(ref_str, result.stderr.strip() or fallback.stderr.strip())
        return fallback.stdout.strip()

    return result.stdout.strip()


def parse_revision_range(repo_path: Path, range_str: str) -> tuple[str, str]:
    """Parse a revision range string such as 'A..B' into two resolved commit SHAs.
    
    Args:
        repo_path: Path to the Git repository.
        range_str: Revision range (e.g. 'HEAD~1..HEAD' or 'main..feat').
        
    Returns:
        Tuple of (base_sha, head_sha).
        
    Raises:
        ValueError: If the range format is invalid.
        NotGitRepositoryError: If repo_path is not a Git repository.
        UnknownRevisionError: If either revision cannot be resolved.
    """
    range_str = range_str.strip()
    if ".." in range_str:
        parts = range_str.split("..", 1)
        base_ref = parts[0].strip()
        head_ref = parts[1].strip()
        if not base_ref:
            base_ref = "HEAD~1"
        if not head_ref:
            head_ref = "HEAD"
    else:
        raise ValueError(
            f"Invalid revision range '{range_str}'. Expected format: '<base>..<head>' (e.g. HEAD~1..HEAD)"
        )

    base_sha = resolve_ref(repo_path, base_ref)
    head_sha = resolve_ref(repo_path, head_ref)
    return base_sha, head_sha
