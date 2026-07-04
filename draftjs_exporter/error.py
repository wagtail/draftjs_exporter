"""Custom exceptions raised by the exporter."""


class ExporterException(Exception):
    """Base exception for all exporter errors."""


class ConfigException(ExporterException):
    """Raised when the exporter configuration is invalid or unsupported."""
