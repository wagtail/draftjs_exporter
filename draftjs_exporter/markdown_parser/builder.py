"""Accumulates Draft.js blocks and entities into a ContentState."""

from typing import Any

from draftjs_exporter.types import (
    Block,
    ContentState,
    Entity,
    EntityRange,
    InlineStyleRange,
    Mutability,
)


class ContentStateBuilder:
    """Build a ContentState block by block with consistent keys.

    Entity keys are assigned as monotonically increasing integers in
    order of first use. Block keys are deterministic, sequential, and
    unique within the built ContentState.
    """

    __slots__ = ("blocks", "entity_map", "_block_counter")

    def __init__(self) -> None:
        """Initialize an empty builder."""
        self.blocks: list[Block] = []
        self.entity_map: dict[str, Entity] = {}
        self._block_counter = 0

    def add_entity(
        self,
        type_: str,
        data: dict[str, Any],
        mutability: Mutability = "MUTABLE",
    ) -> int:
        """Register an entity and return its integer key.

        Parameters:
            type_: The entity type, e.g. ``LINK``.
            data: The entity data payload.
            mutability: The entity mutability.

        Returns:
            The integer key used in entity ranges.
        """
        key = len(self.entity_map)
        self.entity_map[str(key)] = {
            "type": type_,
            "mutability": mutability,
            "data": data,
        }
        return key

    def add_block(
        self,
        type_: str,
        text: str = "",
        depth: int = 0,
        inline_style_ranges: list[InlineStyleRange] | None = None,
        entity_ranges: list[EntityRange] | None = None,
    ) -> None:
        """Append a block to the ContentState.

        Parameters:
            type_: The Draft.js block type.
            text: The block's plain text.
            depth: Nesting depth for list items.
            inline_style_ranges: Style ranges over the text.
            entity_ranges: Entity ranges over the text.
        """
        self.blocks.append(
            {
                "key": f"{self._block_counter:05d}",
                "text": text,
                "type": type_,
                "depth": depth,
                "inlineStyleRanges": (
                    inline_style_ranges if inline_style_ranges is not None else []
                ),
                "entityRanges": entity_ranges if entity_ranges is not None else [],
            }
        )
        self._block_counter += 1

    def build(self) -> ContentState:
        """Return the accumulated ContentState."""
        return {"blocks": self.blocks, "entityMap": self.entity_map}
