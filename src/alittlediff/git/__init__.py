"""Git operations and snapshot loading."""

from alittlediff.git.exceptions import (
    GitError,
    NotGitRepositoryError,
    UnknownRevisionError,
    MissingKnowledgeSnapshotError,
    InvalidKnowledgeSnapshotError,
)
from alittlediff.git.refs import (
    is_git_repo,
    resolve_ref,
    parse_revision_range,
)
from alittlediff.git.snapshots import (
    load_text_at_ref,
    load_moosedev_snapshot,
)

__all__ = [
    "GitError",
    "NotGitRepositoryError",
    "UnknownRevisionError",
    "MissingKnowledgeSnapshotError",
    "InvalidKnowledgeSnapshotError",
    "is_git_repo",
    "resolve_ref",
    "parse_revision_range",
    "load_text_at_ref",
    "load_moosedev_snapshot",
]
