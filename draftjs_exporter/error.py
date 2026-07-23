"""Custom exceptions raised by the exporter."""


class ExporterException(Exception):
    """Base exception for all exporter errors."""


class ConfigException(ExporterException):
    """Raised when the exporter configuration is invalid or unsupported."""


class MarkdownParseError(ExporterException):
    """Raised when Markdown input cannot be parsed.

    Carries an optional 1-based line number pointing at the source of
    the failure.
    """

    __slots__ = ("line", "message")

    def __init__(self, message: str, line: int | None = None) -> None:
        """Initialize the error with a message and optional line number.

        Parameters:
            message: Human-readable description of the failure.
            line: 1-based source line number, if known.
        """
        self.message = message
        self.line = line
        super().__init__(f"line {line}: {message}" if line is not None else message)
