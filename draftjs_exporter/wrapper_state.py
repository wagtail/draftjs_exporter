"""Build block-level elements and manage nesting of wrapper elements."""

from draftjs_exporter.constants import BLOCK_TYPES
from draftjs_exporter.dom import DOM
from draftjs_exporter.engines.base import DOMEngine
from draftjs_exporter.options import Options, OptionsMap
from draftjs_exporter.types import Block, Element, Props, RenderableType


class Wrapper:
    """Represent a single wrapper element that nests blocks at a given depth."""

    __slots__ = ("depth", "last_child", "type", "props", "elt")

    def __init__(self, depth: int, options: Options | None = None) -> None:
        """Initialize a wrapper at the given depth.

        Parameters:
            depth: The nesting depth this wrapper represents.
            options: Block options defining the wrapper element, or None for a placeholder.
        """
        self.depth = depth
        self.last_child = None

        if options:
            self.type = options.wrapper
            self.props = options.wrapper_props

            wrapper_props = dict(self.props) if self.props else {}
            wrapper_props["block"] = {"type": options.type, "depth": depth}

            self.elt = DOM.create_element(self.type, wrapper_props)
        else:
            self.type = None
            self.props = None
            self.elt = DOM.create_element()

    def is_different(
        self, depth: int, type_: RenderableType, props: Props | None
    ) -> bool:
        """Return whether the requested wrapper differs from this one.

        Parameters:
            depth: The depth to compare.
            type_: The wrapper element type to compare.
            props: The wrapper props to compare.

        Returns:
            True when the depth, wrapper type, or props do not match.
        """
        return depth > self.depth or type_ != self.type or props != self.props


class WrapperStack:
    """Track nested wrapper elements from the page body to the most nested node."""

    __slots__ = "stack"

    def __init__(self) -> None:
        """Initialize an empty wrapper stack."""
        self.stack: list[Wrapper] = []

    def __str__(self) -> str:
        """Return a string representation of the wrapper stack."""
        return str(self.stack)

    def length(self) -> int:
        """Return the number of wrappers on the stack.

        Returns:
            The current stack depth.
        """
        return len(self.stack)

    def append(self, wrapper: Wrapper) -> None:
        """Push a wrapper onto the top of the stack.

        Parameters:
            wrapper: The wrapper to append.
        """
        return self.stack.append(wrapper)

    def get(self, index: int) -> Wrapper:
        """Return the wrapper at the given index.

        Parameters:
            index: The zero-based index into the stack.

        Returns:
            The wrapper at that index.
        """
        return self.stack[index]

    def slice(self, length: int) -> None:
        """Truncate the stack to the given length.

        Parameters:
            length: The desired stack length.
        """
        self.stack = self.stack[:length]

    def head(self) -> Wrapper:
        """Return the topmost wrapper, or a placeholder if the stack is empty.

        Returns:
            The most nested wrapper, or a depth -1 placeholder when empty.
        """
        if self.stack:
            wrapper = self.stack[-1]
        else:
            wrapper = Wrapper(-1)

        return wrapper

    def tail(self) -> Wrapper:
        """Return the bottommost wrapper.

        Returns:
            The wrapper closest to the page body.
        """
        return self.stack[0]


class WrapperState:
    """Build block-level elements and add wrapper elements where required."""

    __slots__ = ("block_options", "blocks", "dom", "stack")

    def __init__(
        self, block_options: OptionsMap, blocks: list[Block], dom: type[DOMEngine]
    ) -> None:
        """Initialize wrapper state for the given blocks and DOM engine.

        Parameters:
            block_options: Normalized configuration for block rendering.
            blocks: All blocks in the content state.
            dom: The active DOM engine.
        """
        self.block_options = block_options
        self.blocks = blocks
        self.dom = dom
        self.stack = WrapperStack()

    def __str__(self) -> str:
        """Return a string representation of the wrapper state."""
        return f"<WrapperState: {self.stack}>"

    def element_for(
        self, block: Block, block_content: Element | list[Element]
    ) -> Element:
        """Create the wrapped element for a block.

        Parameters:
            block: The block to render.
            block_content: The rendered content of the block.

        Returns:
            The block element, nested inside any required wrapper elements.
        """
        type_ = block.get("type", "unstyled")
        depth = block.get("depth", 0)
        options = Options.get(self.block_options, type_, BLOCK_TYPES.FALLBACK)
        props = dict(options.props)
        props["block"] = block
        props["blocks"] = self.blocks

        # Make an element from the options specified in the block map.
        elt = DOM.create_element(options.element, props, block_content)

        parent = self.parent_for(options, depth, elt)

        return parent

    def parent_for(self, options: Options, depth: int, elt: Element) -> Element:
        """Return the parent element for the given block element.

        Parameters:
            options: The block options.
            depth: The block depth.
            elt: The block element.

        Returns:
            The wrapped parent element, or the element itself if no wrapper is used.
        """
        if options.wrapper:
            parent = self.get_wrapper_elt(options, depth)
            self.dom.append_child(parent, elt)
            self.stack.stack[-1].last_child = elt
        else:
            # Reset the stack if there is no wrapper.
            if self.stack.stack:
                self.stack = WrapperStack()
            parent = elt

        return parent

    def get_wrapper_elt(self, options: Options, depth: int) -> Element:
        """Return the wrapper element for the given options and depth.

        Parameters:
            options: The block options defining the wrapper.
            depth: The block depth.

        Returns:
            The wrapper element at the requested depth.
        """
        head = self.stack.head()
        if head.is_different(depth, options.wrapper, options.wrapper_props):
            self.update_stack(options, depth)

        # If depth is lower than the maximum, we cut the stack.
        if depth < head.depth:
            self.stack.slice(depth + 1)

        return self.stack.get(depth).elt

    def update_stack(self, options: Options, depth: int) -> None:
        """Ensure the wrapper stack matches the requested depth.

        Parameters:
            options: The block options defining the wrapper.
            depth: The requested depth.
        """
        if depth >= self.stack.length():
            # If the depth is gte the stack length, we need more wrappers.
            depth_levels = range(self.stack.length(), depth + 1)

            for level in depth_levels:
                new_wrapper = Wrapper(level, options)

                # Determine where to append the new wrapper.
                if self.stack.head().last_child is None:
                    # If there is no content in the current wrapper, we need
                    # to add an intermediary node.
                    props = dict(options.props)
                    props["block"] = {
                        "type": options.type,
                        "depth": depth,
                        "data": {},
                    }
                    props["blocks"] = self.blocks

                    wrapper_parent = DOM.create_element(options.element, props, "")
                    self.dom.append_child(self.stack.head().elt, wrapper_parent)
                else:
                    # Otherwise we can append at the end of the last child.
                    wrapper_parent = self.stack.head().last_child

                self.dom.append_child(wrapper_parent, new_wrapper.elt)

                self.stack.append(new_wrapper)
        else:
            # Cut the stack to where it now stops, and add new wrapper.
            self.stack.slice(depth)
            self.stack.append(Wrapper(depth, options))
