"""Track entity ranges while rendering a block and wrap content accordingly."""

from draftjs_exporter.command import Command
from draftjs_exporter.constants import ENTITY_TYPES
from draftjs_exporter.dom import DOM
from draftjs_exporter.engines.base import DOMEngine
from draftjs_exporter.error import ExporterException
from draftjs_exporter.options import Options, OptionsMap
from draftjs_exporter.types import Block, Element, Entity, EntityKey, EntityMap


class EntityException(ExporterException):
    """Raised when entity state manipulation is invalid or an entity is missing."""


class EntityState:
    """Track active entities for the current block and render their wrappers."""

    __slots__ = (
        "entity_options",
        "entity_map",
        "entity_stack",
        "completed_entity",
        "element_stack",
    )

    def __init__(self, entity_options: OptionsMap, entity_map: EntityMap) -> None:
        """Initialize entity state with the configured options and entity map.

        Parameters:
            entity_options: Normalized configuration for entity decorators.
            entity_map: Map of entity keys to entity details from the content state.
        """
        self.entity_options = entity_options
        self.entity_map = entity_map

        self.entity_stack: list[EntityKey] = []
        self.completed_entity: EntityKey | None = None
        self.element_stack: list[Element] = []

    def apply(self, command: Command) -> None:
        """Update the entity stack from a start or stop entity command.

        Parameters:
            command: The command to apply.

        Raises:
            EntityException: If a stop command does not match the most recent start.
        """
        match command.name:
            case "start_entity":
                self.entity_stack.append(command.data)
            case "stop_entity":
                expected = self.entity_stack[-1]
                if command.data != expected:
                    raise EntityException(f"Expected {expected}, got {command.data}")

                self.completed_entity = self.entity_stack.pop()

    def has_entity(self) -> list[EntityKey]:
        """Return the stack of currently active entity keys.

        Returns:
            The currently open entity keys, from outermost to innermost.
        """
        return self.entity_stack

    def has_no_entity(self) -> bool:
        """Return whether no entity range is currently active.

        Returns:
            True when there are no open entity ranges.
        """
        return not self.entity_stack

    def get_entity_details(self, entity_key: EntityKey) -> Entity:
        """Fetch entity details from the entity map.

        Parameters:
            entity_key: Key of the entity to look up.

        Returns:
            The entity record.

        Raises:
            EntityException: If the key is missing from the entity map.
        """
        details = self.entity_map.get(entity_key)

        if details is None:
            raise EntityException(
                f'Entity "{entity_key}" does not exist in the entityMap'
            )

        return details

    def render_entities(
        self,
        style_node: Element,
        block: Block,
        blocks: list[Block],
        dom: type[DOMEngine],
    ) -> Element:
        """Wrap the current styled node in any completed or active entity.

        Parameters:
            style_node: The styled node produced by `StyleState`.
            block: The block currently being rendered.
            blocks: All blocks in the content state.
            dom: The active DOM engine.

        Returns:
            The entity node, or the styled node if no entity needs wrapping.
        """
        # We have a complete (start, stop) entity to render.
        if self.completed_entity is not None:
            entity_details = self.get_entity_details(self.completed_entity)
            options = Options.get(
                self.entity_options,
                entity_details["type"],
                ENTITY_TYPES.FALLBACK,
            )
            props = entity_details["data"].copy()
            props["entity"] = {
                "type": entity_details["type"],
                "mutability": entity_details["mutability"]
                if "mutability" in entity_details
                else None,
                "block": block,
                "blocks": blocks,
                "entity_range": {"key": self.completed_entity},
            }

            if len(self.element_stack) == 1:
                children = self.element_stack[0]
            else:
                children = DOM.create_element()

                for n in self.element_stack:
                    dom.append_child(children, n)

            self.completed_entity = None
            self.element_stack = []

            # Is there still another entity? (adjacent) if so add the current style_node for it.
            if self.has_entity():
                self.element_stack.append(style_node)

            return DOM.create_element(options.element, props, children)

        if self.has_entity():
            self.element_stack.append(style_node)
            return None

        return style_node
