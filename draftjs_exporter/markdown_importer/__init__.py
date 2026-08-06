"""Public Markdown importer: parses Markdown, then filters the ContentState."""

from typing import TypedDict

from draftjs_exporter.contentstate_filter import ContentStateFilter, FilterRule
from draftjs_exporter.markdown_parser import MarkdownParser, ParserConfig
from draftjs_exporter.types import ContentState
from draftjs_exporter.utils.module_loading import import_string

DEFAULT_PARSER = "draftjs_exporter.markdown_parser.MarkdownParser"
"""Dotted path of the built-in parser engine."""


class ImporterConfig(TypedDict, total=False):
    """Configuration for the Markdown importer."""

    parser: str
    """Dotted path of the parser engine class. Defaults to the built-in parser."""

    parser_config: ParserConfig
    """Options passed to the parser engine constructor."""

    filter_rules: list[FilterRule]
    """Rules applied to the parsed ContentState."""


class MarkdownImporter:
    """Import Markdown text as a Draft.js ContentState.

    Combines a parser engine (Markdown to ContentState) with a filter
    (content policy on the result). The parser is referenced by dotted
    path so alternative engines can be swapped in.
    """

    __slots__ = ("parser", "filter")

    def __init__(self, config: ImporterConfig | None = None) -> None:
        """Initialize the importer with the given configuration.

        Parameters:
            config: Parser engine, parser options, and filter rules.
        """
        if config is None:
            config = {}
        parser_class = import_string(config.get("parser", DEFAULT_PARSER))
        self.parser: MarkdownParser = parser_class(config.get("parser_config"))
        self.filter: ContentStateFilter = ContentStateFilter(config.get("filter_rules"))

    def import_markdown(self, markdown: str) -> ContentState:
        """Parse Markdown and apply filter rules.

        Parameters:
            markdown: The Markdown text to import.

        Returns:
            The parsed, filtered ContentState.

        Raises:
            MarkdownParseError: If the input cannot be parsed.
            ConfigException: If a filter callback returns an invalid value
                during filtering.
        """
        return self.filter.apply(self.parser.parse(markdown))
