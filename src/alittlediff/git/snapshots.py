"""Load file contents at specific Git revisions without checking them out."""

import subprocess
from pathlib import Path, PurePosixPath
from alittlediff.git.exceptions import (
    MissingKnowledgeSnapshotError,
    InvalidKnowledgeSnapshotError,
)
from alittlediff.git.refs import resolve_ref


def load_text_at_ref(repo_path: Path, ref: str, relative_path: str) -> str:
    """Load the textual content of a file at a specific Git revision without checking out.
    
    Args:
        repo_path: Path to the Git repository.
        ref: Git revision string (branch, tag, SHA, HEAD~1, etc.).
        relative_path: Relative path to the file within the repository.
        
    Returns:
        String content of the file at that revision.
        
    Raises:
        NotGitRepositoryError: If repo_path is not a Git repository.
        UnknownRevisionError: If ref cannot be resolved.
        MissingKnowledgeSnapshotError: If the file does not exist at that revision.
        InvalidKnowledgeSnapshotError: If the content cannot be decoded or read.
    """
    resolved_sha = resolve_ref(repo_path, ref)
    
    # Git expects forward slashes for internal tree paths
    posix_path = PurePosixPath(relative_path).as_posix()
    git_spec = f"{resolved_sha}:{posix_path}"

    result = subprocess.run(
        ["git", "show", git_spec],
        cwd=str(repo_path),
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        stderr_msg = result.stderr.decode("utf-8", errors="replace").strip()
        if "does not exist in" in stderr_msg or "fatal: path" in stderr_msg or "fatal: Path" in stderr_msg or "exists on disk, but not in" in stderr_msg:
            raise MissingKnowledgeSnapshotError(resolved_sha, posix_path)
        raise InvalidKnowledgeSnapshotError(resolved_sha, posix_path, stderr_msg)

    try:
        return result.stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InvalidKnowledgeSnapshotError(
            resolved_sha,
            posix_path,
            f"UTF-8 decoding failed: {exc}",
        )


def load_moosedev_snapshot(
    repo_path: Path,
    ref: str,
    filename: str = ".moosedev/kg.nq",
) -> str:
    """Convenience function to load a MOOSEDev N-Quads knowledge snapshot at a Git revision."""
    return load_text_at_ref(repo_path, ref, filename)
