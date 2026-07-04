"""Draft.js-compatible constants used by the exporter.

Defines the block types, inline styles, and entity categories supported
by Draft.js, plus a small enum helper.
"""


# http://stackoverflow.com/a/22723724/1798491
class Enum:
    """Minimal enum-like container exposing a fixed set of string attributes.

    Accessing a registered attribute returns its name. Accessing any other
    attribute raises ``AttributeError``.
    """

    __slots__ = "elements"

    def __init__(self, *elements: str) -> None:
        """Store the allowed attribute names for the enum."""
        self.elements = tuple(elements)

    def __getattr__(self, name: str) -> str:
        """Return the attribute name if it is a registered enum element.

        Parameters:
            name: Attribute name being accessed.

        Returns:
            The requested attribute name.

        Raises:
            AttributeError: If the name is not a registered element.
        """
        if name not in self.elements:
            raise AttributeError(f"'Enum' has no attribute '{name}'")

        return name


# https://github.com/facebook/draft-js/blob/master/src/model/constants/DraftBlockType.js
class BLOCK_TYPES:
    """Draft.js block types mapped to HTML elements."""

    UNSTYLED = "unstyled"
    HEADER_ONE = "header-one"
    HEADER_TWO = "header-two"
    HEADER_THREE = "header-three"
    HEADER_FOUR = "header-four"
    HEADER_FIVE = "header-five"
    HEADER_SIX = "header-six"
    UNORDERED_LIST_ITEM = "unordered-list-item"
    ORDERED_LIST_ITEM = "ordered-list-item"
    BLOCKQUOTE = "blockquote"
    PRE = "pre"
    CODE = "code-block"
    ATOMIC = "atomic"
    # Special type to configure handling of missing components.
    FALLBACK = "fallback"


ENTITY_TYPES = Enum(
    "LINK",
    "DOCUMENT",
    "IMAGE",
    "EMBED",
    "HORIZONTAL_RULE",
    # Special type to configure handling of missing components.
    "FALLBACK",
)
"""Draft.js entity categories."""

INLINE_STYLES = Enum(
    "BOLD",
    "CODE",
    "ITALIC",
    "UNDERLINE",
    "STRIKETHROUGH",
    "SUPERSCRIPT",
    "SUBSCRIPT",
    "MARK",
    "QUOTATION",
    "SMALL",
    "SAMPLE",
    "INSERT",
    "DELETE",
    "KEYBOARD",
    # Special type to configure handling of missing components.
    "FALLBACK",
)
"""Draft.js inline style names."""
