"""Utilities for importing classes and functions from dotted module paths."""

from importlib import import_module
from typing import Any


def import_string(dotted_path: str) -> Any:
    """Import a dotted module path and return the last attribute or class.

    Parameters:
        dotted_path: The dotted path to the attribute or class to import.

    Returns:
        The imported attribute or class.

    Raises:
        ImportError: If the path is malformed or the import fails.

    Taken from Django:
    https://github.com/django/django/blob/f6bd00131e687aedf2719ad31e84b097562ca5f2/django/utils/module_loading.py#L7-L24
    """
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as err:
        raise ImportError(f"{dotted_path} doesn't look like a module path") from err

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError(
            f'Module "{module_path}" does not define a "{class_name}" attribute/class'
        ) from err
