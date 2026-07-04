"""Represent and build rendering commands derived from Draft.js ranges."""

from draftjs_exporter.types import Block


class Command:
    """Represent an operation applied while converting a block to HTML nodes."""

    __slots__ = ("name", "index", "data")

    def __init__(self, name: str, index: int, data: str = "") -> None:
        """Initialize a command.

        Parameters:
            name: The operation name, such as ``start_entity`` or ``stop_inline_style``.
            index: The character offset at which the command applies.
            data: The payload for the command, such as an entity key or style name.
        """
        self.name = name
        self.index = index
        self.data = data

    def __str__(self) -> str:
        """Return a human-readable representation of the command."""
        return f"<Command {self.name} {self.index} {self.data}>"

    def __repr__(self) -> str:
        """Return the same representation as ``__str__`` for debugging."""
        return str(self)

    @staticmethod
    def from_entity_ranges(block: Block) -> list["Command"]:
        """Create start and stop commands from a block's entity ranges.

        Parameters:
            block: The block containing ``entityRanges``.

        Returns:
            A list of start_entity and stop_entity commands.
        """
        commands: list["Command"] = []
        for r in block.get("entityRanges", []):
            # Entity key is an integer in entity ranges, while a string in the entity map.
            data = str(r["key"])
            start = r["offset"]
            stop = start + r["length"]
            commands.append(Command("start_entity", start, data))
            commands.append(Command("stop_entity", stop, data))

        return commands

    @staticmethod
    def from_style_ranges(block: Block) -> list["Command"]:
        """Create start and stop commands from a block's inline style ranges.

        Parameters:
            block: The block containing ``inlineStyleRanges``.

        Returns:
            A list of start_inline_style and stop_inline_style commands.
        """
        commands: list["Command"] = []
        for r in block.get("inlineStyleRanges", []):
            data = r["style"]
            start = r["offset"]
            stop = start + r["length"]
            commands.append(Command("start_inline_style", start, data))
            commands.append(Command("stop_inline_style", stop, data))
        return commands
