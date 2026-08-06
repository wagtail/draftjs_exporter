"""Entity resolvers: map Markdown link and image URLs to Draft.js entities."""

from collections.abc import Callable
from typing import Any, TypeAlias, TypedDict
from urllib.parse import parse_qsl, urlparse

from draftjs_exporter.constants import ENTITY_TYPES
from draftjs_exporter.types import Mutability


class EntityResolution(TypedDict, total=False):
    """How a link or image URL should be converted into a Draft.js entity."""

    type: str
    """The entity type, e.g. ``LINK``, ``IMAGE``, ``DOCUMENT``, ``EMBED``."""

    data: dict[str, Any]
    """The entity data payload."""

    mutability: Mutability
    """The entity mutability. Defaults to ``MUTABLE`` when omitted."""


EntityResolver: TypeAlias = Callable[[str, str], "EntityResolution | None"]
"""Resolve a URL and its label into an entity, or return None to defer."""


def default_link_resolver(url: str, label: str) -> EntityResolution:
    """Resolve any URL into a standard ``LINK`` entity.

    Parameters:
        url: The link URL from the Markdown source.
        label: The link text.

    Returns:
        A ``LINK`` resolution with the URL in its data.
    """
    return {
        "type": ENTITY_TYPES.LINK,
        "data": {"url": url},
        "mutability": "MUTABLE",
    }


def default_image_resolver(url: str, alt: str) -> EntityResolution:
    """Resolve any URL into a standard ``IMAGE`` entity.

    Parameters:
        url: The image URL from the Markdown source.
        alt: The image alt text.

    Returns:
        An ``IMAGE`` resolution with ``src`` and ``alt`` in its data.
    """
    return {
        "type": ENTITY_TYPES.IMAGE,
        "data": {"src": url, "alt": alt},
        "mutability": "IMMUTABLE",
    }


def resolve(
    chain: list[EntityResolver],
    url: str,
    label: str,
    default: Callable[[str, str], EntityResolution],
) -> EntityResolution:
    """Run a resolver chain, falling back to the default resolver.

    Parameters:
        chain: Resolvers tried in order; the first non-None result wins.
        url: The URL to resolve.
        label: The link text or image alt text.
        default: Resolver used when every chain entry defers.

    Returns:
        The winning resolution, or the default resolution.
    """
    for resolver in chain:
        resolution = resolver(url, label)
        if resolution is not None:
            return resolution
    return default(url, label)


def scheme_resolver(
    scheme: str,
    type_map: dict[str, str],
    coerce: dict[str, Callable[[str], Any]] | None = None,
    label_key: str | None = None,
    mutability: Mutability = "MUTABLE",
) -> EntityResolver:
    """Build a resolver for internal URLs like ``scheme://kind?key=value``.

    The URL host selects the entity type via ``type_map``. Query string
    parameters become entity data, optionally converted per key via
    ``coerce``. When a query key repeats, the last value wins (standard
    ``urllib`` dict semantics). When ``label_key`` is set, a non-empty
    Markdown label fills that data key if the query string did not
    provide it.

    Parameters:
        scheme: The URL scheme to match, e.g. ``"wagtail"``.
        type_map: Mapping of URL host to entity type.
        coerce: Optional per-key converters for query string values.
        label_key: Optional data key filled from the Markdown label.
        mutability: Mutability for produced resolutions.

    Returns:
        A resolver that defers (returns None) for non-matching URLs.
    """
    converters = coerce if coerce is not None else {}

    def resolver(url: str, label: str) -> EntityResolution | None:
        parsed = urlparse(url)
        if parsed.scheme != scheme:
            return None
        entity_type = type_map.get(parsed.netloc)
        if entity_type is None:
            return None
        data: dict[str, Any] = {}
        for key, value in parse_qsl(parsed.query, keep_blank_values=True):
            converter = converters.get(key)
            data[key] = converter(value) if converter is not None else value
        if label_key is not None and label and label_key not in data:
            data[label_key] = label
        return {"type": entity_type, "data": data, "mutability": mutability}

    return resolver
