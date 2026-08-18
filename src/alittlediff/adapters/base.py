"""Base adapter interface for epistemic knowledge sources."""

from pathlib import Path
from typing import Protocol
from alittlediff.domain.state import EpistemicState


class EpistemicAdapter(Protocol):
    """Protocol for loading normalized epistemic states from a repository at a revision."""

    def can_load(self, repo_path: Path, revision: str) -> bool:
        """Check whether this adapter can extract knowledge from the given revision."""
        ...

    def load_state(self, repo_path: Path, revision: str) -> EpistemicState:
        """Load and normalize the epistemic state at the given revision."""
        ...
