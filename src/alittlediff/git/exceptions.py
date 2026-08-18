"""Git-related exceptions for A Little Diff."""


class GitError(Exception):
    """Base exception for all Git-related errors."""
    pass


class NotGitRepositoryError(GitError):
    """Raised when the specified path is not a valid Git repository."""
    def __init__(self, path: str):
        super().__init__(f"Directory is not a valid Git repository: {path}")
        self.path = path


class UnknownRevisionError(GitError):
    """Raised when a specified Git revision cannot be resolved."""
    def __init__(self, revision: str, details: str = ""):
        message = f"Unknown revision: '{revision}'"
        if details:
            message += f" ({details})"
        super().__init__(message)
        self.revision = revision


class MissingKnowledgeSnapshotError(GitError):
    """Raised when the requested knowledge snapshot file does not exist at the specified revision."""
    def __init__(self, revision: str, filepath: str):
        super().__init__(f"Knowledge snapshot '{filepath}' not found at revision '{revision}'")
        self.revision = revision
        self.filepath = filepath


class InvalidKnowledgeSnapshotError(GitError):
    """Raised when a knowledge snapshot cannot be read or is corrupted."""
    def __init__(self, revision: str, filepath: str, reason: str):
        super().__init__(f"Invalid knowledge snapshot '{filepath}' at revision '{revision}': {reason}")
        self.revision = revision
        self.filepath = filepath
        self.reason = reason
