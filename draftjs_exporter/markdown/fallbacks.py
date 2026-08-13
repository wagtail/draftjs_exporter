"""Fallback components used when an unknown Draft.js block, entity, or inline style is encountered."""

import logging

from draftjs_exporter.markdown.helpers import md_block
from draftjs_exporter.types import Element, Props

logger = logging.getLogger(__name__)


def md_block_fallback(props: Props) -> Element:
    """Render an unknown block type as plain text.

    Parameters:
        props: Render properties including the unknown block definition.

    Returns:
        The block's children without extra markup.
    """
    type_ = props["block"]["type"]
    logger.warning('Unknown block type "%s". Rendering as plain text.', type_)
    return md_block([props["children"]])


def md_entity_fallback(props: Props) -> Element:
    """Render an unknown entity type as plain text.

    Parameters:
        props: Render properties including the unknown entity definition.

    Returns:
        The entity's children without extra markup.
    """
    type_ = props["entity"]["type"]
    logger.warning('Unknown entity type "%s". Rendering as plain text.', type_)
    return props["children"]


def md_style_fallback(props: Props) -> Element:
    """Render an unknown inline style as plain text.

    Parameters:
        props: Render properties including the unknown inline style range.

    Returns:
        The styled children without extra markup.
    """
    type_ = props["inline_style_range"]["style"]
    logger.warning('Unknown inline style "%s". Rendering as plain text.', type_)
    return props["children"]
