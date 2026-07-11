"""Track inline style ranges and wrap text in nested style elements."""

from draftjs_exporter.command import Command
from draftjs_exporter.constants import INLINE_STYLES
from draftjs_exporter.dom import DOM
from draftjs_exporter.options import Options, OptionsMap
from draftjs_exporter.types import Block, Element


class StyleState:
    """Track active inline styles for the current block and render their wrappers."""

    __slots__ = ("styles", "style_options", "element_stack")

    def __init__(self, style_options: OptionsMap) -> None:
        """Initialize style state with the configured style map.

        Parameters:
            style_options: Normalized configuration for inline styles.
        """
        self.styles: list[str] = []
        self.style_options = style_options
        self.element_stack: list[tuple[str, Element]] = []

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

    def start_segment(
        self, block: Block, blocks: list[Block], content: Element
    ) -> Element:
        """Adjust the element stack to match the current active styles.

        Closes styles that ended, opens styles that started, and returns
        the innermost element where text should be appended.

        Parameters:
            block: The block currently being rendered.
            blocks: All blocks in the content state.
            content: The block's content fragment, used as the root container
                when no styles are active.

        Returns:
            The innermost open element, or ``content`` if no styles are active.
        """
        current = sorted(self.styles)

        match_len = 0
        for i, (style_name, _) in enumerate(self.element_stack):
            if i < len(current) and style_name == current[i]:
                match_len += 1
            else:
                break

        while len(self.element_stack) > match_len:
            self.element_stack.pop()

        innermost = self.element_stack[-1][1] if self.element_stack else content

        for style_name in current[match_len:]:
            options = Options.get(
                self.style_options, style_name, INLINE_STYLES.FALLBACK
            )
            props = dict(options.props)
            props["block"] = block
            props["blocks"] = blocks
            props["inline_style_range"] = {"style": style_name}
            elem = DOM.create_element(options.element, props)
            DOM.append_child(innermost, elem)
            self.element_stack.append((style_name, elem))
            innermost = elem

        return innermost

    def flush(self) -> None:
        """Close all open style elements by clearing the stack."""
        self.element_stack = []

    def uses_components(self, block: Block) -> bool:
        """Return whether any style range in the block uses a callable component.

        Callable components must be invoked once with all children, so they
        cannot be left open across segments. When this returns True, callers
        should fall back to per-segment wrapping via ``render_styles``.

        Parameters:
            block: The block to check.

        Returns:
            True when any style in the block's ranges maps to a callable.
        """
        for r in block.get("inlineStyleRanges", []):
            options = Options.get(
                self.style_options, r["style"], INLINE_STYLES.FALLBACK
            )
            if callable(options.element):
                return True
        return False
