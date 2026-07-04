import unittest
from collections.abc import Callable
from typing import Any

import pytest

from draftjs_exporter.html import HTML
from draftjs_exporter.markdown import CONFIG, build_markdown_config
from draftjs_exporter.types import Block, ContentState


def _text_block(text: str, block_type: str = "unstyled", **kwargs: Any) -> Block:
    return {
        "key": kwargs.get("key", "a"),
        "text": text,
        "type": block_type,
        "depth": kwargs.get("depth", 0),
        "inlineStyleRanges": kwargs.get("inlineStyleRanges", []),
        "entityRanges": kwargs.get("entityRanges", []),
    }


def _styled_content(text: str, style: str) -> ContentState:
    return {
        "entityMap": {},
        "blocks": [
            _text_block(
                text,
                inlineStyleRanges=[{"offset": 0, "length": len(text), "style": style}],
            )
        ],
    }


def _block_content(text: str, block_type: str, **kwargs: Any) -> ContentState:
    return {
        "entityMap": {},
        "blocks": [_text_block(text, block_type, **kwargs)],
    }


def _ol_content() -> ContentState:
    return {
        "entityMap": {},
        "blocks": [
            _text_block("first", "ordered-list-item", key="a"),
            _text_block("second", "ordered-list-item", key="b"),
        ],
    }


def _hr_content() -> ContentState:
    return {
        "entityMap": {
            "0": {
                "type": "HORIZONTAL_RULE",
                "mutability": "IMMUTABLE",
                "data": {},
            }
        },
        "blocks": [
            _text_block(
                " ",
                "atomic",
                entityRanges=[{"offset": 0, "length": 1, "key": 0}],
            )
        ],
    }


def _render(options: Any, content_state: ContentState) -> str:
    return HTML(build_markdown_config(options)).render(content_state)


class TestBuildMarkdownConfig(unittest.TestCase):
    """Tests for the build_markdown_config API."""

    def test_no_options_matches_config(self):
        """Calling with no options produces output identical to the default CONFIG."""
        content_state = _block_content("hello", "unstyled")
        self.assertEqual(
            HTML(build_markdown_config()).render(content_state),
            HTML(CONFIG).render(content_state),
        )

    def test_none_options(self):
        config = build_markdown_config(None)
        self.assertIn("block_map", config)
        self.assertIn("style_map", config)
        self.assertIn("entity_decorators", config)
        self.assertIn("engine", config)

    def test_empty_options(self):
        config = build_markdown_config({})
        self.assertIn("block_map", config)


# -- Inline style options ----------------------------------------------------

STYLE_CASES = [
    # (option_key, option_value, style_name, text, expected)
    ("bold", "__", "BOLD", "bold", "__bold__\n\n"),
    ("bold", "**", "BOLD", "bold", "**bold**\n\n"),
    ("italic", "*", "ITALIC", "italic", "*italic*\n\n"),
    ("italic", "_", "ITALIC", "italic", "_italic_\n\n"),
    ("strikethrough", "~~", "STRIKETHROUGH", "struck", "~~struck~~\n\n"),
    ("strikethrough", "~", "STRIKETHROUGH", "struck", "~struck~\n\n"),
]


@pytest.mark.parametrize(
    "option_key, option_value, style, text, expected",
    STYLE_CASES,
    ids=[f"{k}={v}" for k, v, *_ in STYLE_CASES],
)
def test_style_option(
    option_key: str, option_value: str, style: str, text: str, expected: str
) -> None:
    assert _render({option_key: option_value}, _styled_content(text, style)) == expected


def test_style_defaults():
    """Omitted style options use the documented defaults."""
    assert _render({}, _styled_content("bold", "BOLD")) == "**bold**\n\n"
    assert _render({}, _styled_content("italic", "ITALIC")) == "_italic_\n\n"
    assert _render({}, _styled_content("struck", "STRIKETHROUGH")) == "~struck~\n\n"


# -- Block-level options ------------------------------------------------------

# fmt: off
BLOCK_CASES = [
    # (option_key, option_value, content_state_factory, expected)
    ("unordered_list_marker", "-", lambda: _block_content("item", "unordered-list-item"), "- item\n\n"),
    ("unordered_list_marker", "*", lambda: _block_content("item", "unordered-list-item"), "* item\n\n"),
    ("ordered_list_delimiter", ".", _ol_content, "1. first\n2. second\n\n"),
    ("ordered_list_delimiter", ")", _ol_content, "1) first\n2) second\n\n"),
    ("horizontal_rule", "---", _hr_content, "---\n\n"),
    ("horizontal_rule", "***", _hr_content, "***\n\n"),
    ("code_fence", "```", lambda: _block_content("code", "code-block"), "```\ncode\n```\n\n"),
    ("code_fence", "~~~", lambda: _block_content("code", "code-block"), "~~~\ncode\n~~~\n\n"),
]


@pytest.mark.parametrize(
    "option_key, option_value, content_factory, expected",
    BLOCK_CASES,
    ids=[f"{k}={v}" for k, v, *_ in BLOCK_CASES],
)
def test_block_option(option_key: str, option_value: str, content_factory: Callable[[], ContentState], expected: str) -> None:
    assert _render({option_key: option_value}, content_factory()) == expected


def test_block_defaults():
    """Omitted block options use the documented defaults."""
    assert _render({}, _block_content("item", "unordered-list-item")) == "- item\n\n"
    assert _render({}, _block_content("first", "ordered-list-item")) == "1. first\n\n"
    assert _render({}, _hr_content()) == "---\n\n"
    assert _render({}, _block_content("code", "code-block")) == "```\ncode\n```\n\n"


# -- Combined options ---------------------------------------------------------


def test_all_options_combined():
    config = build_markdown_config(
        {
            "bold": "__",
            "italic": "*",
            "strikethrough": "~~",
            "unordered_list_marker": "+",
            "ordered_list_delimiter": ")",
            "horizontal_rule": "***",
            "code_fence": "~~~",
        }
    )
    content: ContentState = {
        "entityMap": {},
        "blocks": [
            _text_block(
                "bold and italic",
                inlineStyleRanges=[
                    {"offset": 0, "length": 4, "style": "BOLD"},
                    {"offset": 9, "length": 6, "style": "ITALIC"},
                ],
            ),
            _text_block("item", "unordered-list-item", key="b"),
        ],
    }
    assert HTML(config).render(content) == "__bold__ and *italic*\n\n+ item\n\n"
