"""Normalize renderer configuration maps into internal option objects."""

from typing import Any, TypeAlias, cast

from draftjs_exporter.constants import BLOCK_TYPES, ENTITY_TYPES, INLINE_STYLES
from draftjs_exporter.error import ConfigException
from draftjs_exporter.types import ConfigMap, Props, RenderableConfig, RenderableType

# Internal equivalent of a ConfigMap.
OptionsMap: TypeAlias = dict[str, "Options"]


class Options:
    """Store and query normalized configuration for a single renderable type."""

    __slots__ = ("type", "element", "props", "wrapper", "wrapper_props")

    def __init__(
        self,
        type_: str,
        element: RenderableType,
        props: Props | None = None,
        wrapper: RenderableType = None,
        wrapper_props: Props | None = None,
    ) -> None:
        """Initialize options for a renderable type.

        Parameters:
            type_: The Draft.js type being configured.
            element: The element or component used to render this type.
            props: Default props to pass to the element.
            wrapper: Optional wrapper element used for nested blocks.
            wrapper_props: Props to pass to the wrapper element.
        """
        self.type = type_
        self.element = element
        self.props = props if props else {}
        self.wrapper = wrapper
        self.wrapper_props = wrapper_props

    def __str__(self) -> str:
        """Return a human-readable representation of the options."""
        return f"<Options {self.type} {self.element} {self.props} {self.wrapper} {self.wrapper_props}>"

    def __repr__(self) -> str:
        """Return the same representation as ``__str__`` for debugging."""
        return str(self)

    def __eq__(self, other: Any) -> bool:
        """Compare options for equality.

        This comparison is intended for test assertions only and should not be
        relied on by the exporter at runtime.

        Parameters:
            other: The other object to compare with.

        Returns:
            True when the string representations match.
        """
        return str(self) == str(other)

    def __ne__(self, other: Any) -> bool:
        """Return whether the options are not equal to another object."""
        return not self == other

    def __hash__(self) -> int:
        """Return a hash based on the string representation."""
        return hash(str(self))

    @staticmethod
    def create(kind_map: ConfigMap, type_: str, fallback_key: str) -> "Options":
        """Create an Options object from a config map.

        Parameters:
            kind_map: The user-provided configuration map.
            type_: The type to look up in the map.
            fallback_key: The key to use when ``type_`` is missing.

        Returns:
            The normalized options.

        Raises:
            ConfigException: If the type and fallback are both missing or the config defines no element.
        """
        if type_ not in kind_map:
            if fallback_key not in kind_map:
                raise ConfigException(
                    f'"{type_}" is not in the config and has no fallback'
                )

            config = kind_map[fallback_key]
        else:
            config = kind_map[type_]

        # TODO Refactor to a TypeGuard when support for those improves.
        if isinstance(config, dict):
            if "element" not in config:
                raise ConfigException(f'"{type_}" does not define an element')

            # TODO Remove cast once ty support improves.
            opts = Options(type_, **cast(RenderableConfig, config))
        else:
            # TODO Remove cast once ty support improves.
            opts = Options(type_, cast(RenderableType, config))

        return opts

    @staticmethod
    def map(kind_map: ConfigMap, fallback_key: str) -> OptionsMap:
        """Create an OptionsMap from each entry in a config map.

        Parameters:
            kind_map: The user-provided configuration map.
            fallback_key: The fallback key passed to ``Options.create``.

        Returns:
            A mapping from type to normalized options.
        """
        options = {}
        for type_ in kind_map:
            options[type_] = Options.create(kind_map, type_, fallback_key)

        return options

    @staticmethod
    def map_blocks(block_map: ConfigMap) -> OptionsMap:
        """Create an OptionsMap from a block configuration map.

        Parameters:
            block_map: The user-provided block map.

        Returns:
            A mapping from block type to normalized options.
        """
        return Options.map(block_map, BLOCK_TYPES.FALLBACK)

    @staticmethod
    def map_styles(style_map: ConfigMap) -> OptionsMap:
        """Create an OptionsMap from a style configuration map.

        Parameters:
            style_map: The user-provided style map.

        Returns:
            A mapping from style name to normalized options.
        """
        return Options.map(style_map, INLINE_STYLES.FALLBACK)

    @staticmethod
    def map_entities(entity_map: ConfigMap) -> OptionsMap:
        """Create an OptionsMap from an entity configuration map.

        Parameters:
            entity_map: The user-provided entity decorators map.

        Returns:
            A mapping from entity type to normalized options.
        """
        return Options.map(entity_map, ENTITY_TYPES.FALLBACK)

    @staticmethod
    def get(options: OptionsMap, type_: str, fallback_key: str) -> "Options":
        """Return existing options from a map, falling back when needed.

        Parameters:
            options: An existing normalized options map.
            type_: The type to look up.
            fallback_key: The key to use when ``type_`` is missing.

        Returns:
            The matching options.

        Raises:
            ConfigException: If neither the type nor the fallback is present.
        """
        try:
            return options[type_]
        except KeyError:
            try:
                return options[fallback_key]
            except KeyError as err:
                raise ConfigException(
                    f'"{type_}" is not in the config and has no fallback'
                ) from err
