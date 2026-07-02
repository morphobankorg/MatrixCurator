__all__ = [
    "MatrixCuratorError",
    "DocumentParseError",
    "NexusFormatError",
    "LLMServiceError",
    "ContextLengthExceededError",
]


class MatrixCuratorError(Exception):
    """Base exception for all MatrixCurator errors."""

    pass


class DocumentParseError(MatrixCuratorError):
    """Raised when a document cannot be parsed."""

    pass


class NexusFormatError(MatrixCuratorError):
    """Raised when a NEXUS file is malformed or cannot be processed."""

    pass


class LLMServiceError(MatrixCuratorError):
    """Raised when an LLM service fails."""

    pass


class ContextLengthExceededError(MatrixCuratorError):
    """Raised when the context exceeds the LLM's maximum context window."""

    pass
