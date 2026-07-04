"""Track inline style ranges and wrap text in nested style elements."""

from draftjs_exporter.command import Command
from draftjs_exporter.constants import INLINE_STYLES
from draftjs_exporter.dom import DOM
from draftjs_exporter.options import Options, OptionsMap
from draftjs_exporter.types import Block, Element


class StyleState:
    """Track active inline styles for the current block and render their wrappers."""

    __slots__ = ("styles", "style_options")

    def __init__(self, style_options: OptionsMap) -> None:
        """Initialize style state with the configured style map.

        Parameters:
            style_options: Normalized configuration for inline styles.
        """
        self.styles: list[str] = []
        self.style_options = style_options

    def apply(self, command: Command) -> None:
        """Update the active style list from a start or stop style command.

        Parameters:
            command: The command to apply.
        """
        match command.name:
            case "start_inline_style":
                self.styles.append(command.data)
            case "stop_inline_style":
                self.styles.remove(command.data)

    def is_empty(self) -> bool:
        """Return whether no inline styles are currently active.

        Returns:
            True when there are no active inline styles.
        """
        return not self.styles

    def render_styles(
        self, decorated_node: Element, block: Block, blocks: list[Block]
    ) -> Element:
        """Wrap the decorated node in nested elements for each active style.

        Parameters:
            decorated_node: The node produced by composite decorators.
            block: The block currently being rendered.
            blocks: All blocks in the content state.

        Returns:
            The styled node, wrapped from innermost to outermost style.
        """
        node = decorated_node
        if not self.is_empty():
            # This will mutate self.styles, but it’s going to be reset after rendering anyway.
            self.styles.sort(reverse=True)

            # Nest the tags.
            for style in self.styles:
                options = Options.get(self.style_options, style, INLINE_STYLES.FALLBACK)
                props = dict(options.props)
                props["block"] = block
                props["blocks"] = blocks
                props["inline_style_range"] = {"style": style}
                node = DOM.create_element(options.element, props, node)

        return node
