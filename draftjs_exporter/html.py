"""Convert Draft.js content state into HTML using configurable maps.

The ``HTML`` exporter is the main entry point. It coordinates block,
inline style, entity, and decorator rendering over a pluggable DOM
engine.
"""

from operator import attrgetter
from typing import TypedDict

from draftjs_exporter.command import Command
from draftjs_exporter.composite_decorators import (
    render_decorators,
    should_render_decorators,
)
from draftjs_exporter.defaults import BLOCK_MAP, STYLE_MAP
from draftjs_exporter.dom import DOM
from draftjs_exporter.engines.base import DOMEngine
from draftjs_exporter.entity_state import EntityState
from draftjs_exporter.options import Options
from draftjs_exporter.style_state import StyleState
from draftjs_exporter.types import (
    Block,
    CompositeDecorators,
    ConfigMap,
    ContentState,
    Element,
    EntityMap,
)
from draftjs_exporter.wrapper_state import WrapperState


class ExporterConfig(TypedDict, total=False):
    """Available options when configuring an HTML exporter."""

    block_map: ConfigMap
    style_map: ConfigMap
    entity_decorators: ConfigMap
    composite_decorators: CompositeDecorators
    engine: str


class HTML:
    """Combine entity, wrapper, and style state to render Draft.js content.

    This is the main entry point for converting a Draft.js content state
    into an HTML string.
    """

    __slots__ = (
        "composite_decorators",
        "entity_options",
        "block_options",
        "style_options",
        "_engine",
    )

    def __init__(self, config: ExporterConfig | None = None) -> None:
        """Initialize the exporter with the given configuration.

        Parameters:
            config: Exporter options. Missing values use the default block
                and style maps and the string DOM engine.
        """
        if config is None:
            config = {}

        self.composite_decorators = config.get("composite_decorators", [])

        self.entity_options = Options.map_entities(config.get("entity_decorators", {}))
        self.block_options = Options.map_blocks(config.get("block_map", BLOCK_MAP))
        self.style_options = Options.map_styles(config.get("style_map", STYLE_MAP))

        self._engine = config.get("engine", DOM.STRING)

    def render(self, content_state: ContentState | None = None) -> str:
        """Render the given Draft.js content state as HTML."""
        with DOM.engine(self._engine):
            dom = DOM._dom()

            if content_state is None:
                content_state = {}

            blocks = content_state.get("blocks", [])
            wrapper_state = WrapperState(self.block_options, blocks, dom)
            document = DOM.create_element()
            entity_map = content_state.get("entityMap", {})
            min_depth = 0

            for block in blocks:
                # Assume a depth of 0 if it's not specified, like Draft.js would.
                depth = block.get("depth", 0)
                elt = self.render_block(block, entity_map, wrapper_state, dom)

                if depth > min_depth:
                    min_depth = depth

                # At level 0, append the element to the document.
                if depth == 0:
                    dom.append_child(document, elt)

            # If there is no block at depth 0, we need to add the wrapper that contains the whole tree to the document.
            if min_depth > 0 and wrapper_state.stack.length() != 0:
                dom.append_child(document, wrapper_state.stack.tail().elt)

            return dom.render(document)

    def render_block(
        self,
        block: Block,
        entity_map: EntityMap,
        wrapper_state: WrapperState,
        dom: type[DOMEngine],
    ) -> Element:
        """Render a single block to an element.

        Parameters:
            block: The Draft.js block to render.
            entity_map: Map of entity keys to entity definitions.
            wrapper_state: Stateful wrapper that handles nesting of list items.
            dom: Active DOM engine used to create elements.

        Returns:
            The rendered block element.
        """
        text = block.get("text", "")
        has_styles = bool(block.get("inlineStyleRanges"))
        has_entities = bool(block.get("entityRanges"))
        has_decorators = should_render_decorators(self.composite_decorators, text)

        if has_styles or has_entities:
            content = DOM.create_element()
            entity_state = EntityState(self.entity_options, entity_map)
            style_state = StyleState(self.style_options) if has_styles else None

            use_continuation = not (
                style_state is None or style_state.uses_components(block)
            )

            for text, commands in self.build_command_groups(block):
                for command in commands:
                    entity_state.apply(command)
                    if style_state:
                        style_state.apply(command)

                # Decorators are not rendered inside entities.
                if has_decorators and entity_state.has_no_entity():
                    decorated_node = render_decorators(
                        self.composite_decorators,
                        text,
                        block,
                        wrapper_state.blocks,
                        dom,
                    )
                else:
                    decorated_node = text

                entity_active = (
                    bool(entity_state.has_entity())
                    or entity_state.completed_entity is not None
                )

                if style_state is not None and use_continuation and not entity_active:
                    innermost = style_state.start_segment(
                        block, wrapper_state.blocks, content
                    )
                    if decorated_node not in (None, ""):
                        dom.append_child(innermost, decorated_node)
                else:
                    if style_state is not None and use_continuation:
                        style_state.flush()

                    if style_state:
                        styled_node = style_state.render_styles(
                            decorated_node, block, wrapper_state.blocks
                        )
                    else:
                        styled_node = decorated_node
                    entity_node = entity_state.render_entities(
                        styled_node, block, wrapper_state.blocks, dom
                    )

                    if entity_node is not None:
                        dom.append_child(content, entity_node)

                        # Check whether there actually are two different nodes, confirming we are not inserting an upcoming entity.
                        if styled_node != entity_node and entity_state.has_no_entity():
                            dom.append_child(content, styled_node)
        # Fast track for blocks which do not contain styles nor entities, which is very common.
        elif has_decorators:
            content = render_decorators(
                self.composite_decorators,
                text,
                block,
                wrapper_state.blocks,
                dom,
            )
        else:
            content = text

        return wrapper_state.element_for(block, content)

    def build_command_groups(self, block: Block) -> list[tuple[str, list[Command]]]:
        """Group block modification commands by start index.

        Each group is paired with the slice of text the commands apply to.

        Parameters:
            block: The Draft.js block whose commands are grouped.

        Returns:
            Tuples of ``(text slice, commands applied to the slice)``.
        """
        text = block.get("text", "")

        commands = self.build_commands(block)
        sliced = []

        start = 0
        command_count = len(commands)

        # Manual groupby on command index. build_commands sorts by index, so
        # consecutive commands with the same index form a group. Avoids
        # itertools.groupby and the extra list allocations it would create.
        while start < command_count:
            start_index = commands[start].index
            end = start + 1

            while end < command_count and commands[end].index == start_index:
                end += 1

            if end < command_count:
                stop_index = commands[end].index
                sliced.append((text[start_index:stop_index], commands[start:end]))
            else:
                sliced.append(("", commands[start:end]))

            start = end

        return sliced

    def build_commands(self, block: Block) -> list[Command]:
        """Build all manipulation commands for a block.

        The returned commands include a start and stop text marker plus one
        command for each inline style and entity range.

        Parameters:
            block: The Draft.js block to build commands from.

        Returns:
            The ordered list of manipulation commands.
        """
        style_commands = Command.from_style_ranges(block)
        entity_commands = Command.from_entity_ranges(block)
        styles_and_entities = style_commands + entity_commands
        styles_and_entities.sort(key=attrgetter("index"))

        return (
            [Command("start_text", 0)]
            + styles_and_entities
            + [Command("stop_text", len(block.get("text", "")))]
        )
