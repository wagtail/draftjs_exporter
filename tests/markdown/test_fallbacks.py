import pytest

from draftjs_exporter.dom import DOM
from draftjs_exporter.error import ConfigException
from draftjs_exporter.html import HTML
from draftjs_exporter.markdown import CONFIG, build_markdown_config
from draftjs_exporter.markdown.fallbacks import (
    md_block_fallback,
    md_entity_fallback,
    md_style_fallback,
)
from draftjs_exporter.markdown.helpers import md_block
from draftjs_exporter.types import ContentState, Element, Props

LOGGER = "draftjs_exporter.markdown.fallbacks"


# -- Unit tests: each fallback renders plain text and logs a warning ----------

UNIT_CASES = [
    (
        "block",
        md_block_fallback,
        {"block": {"type": "custom-block"}, "children": "content"},
        "custom-block",
        "content\n\n",
        True,
    ),
    (
        "entity",
        md_entity_fallback,
        {"entity": {"type": "CUSTOM_ENTITY"}, "children": "link text"},
        "CUSTOM_ENTITY",
        "link text",
        False,
    ),
    (
        "style",
        md_style_fallback,
        {"inline_style_range": {"style": "CUSTOM_STYLE"}, "children": "styled"},
        "CUSTOM_STYLE",
        "styled",
        False,
    ),
]


@pytest.mark.parametrize(
    "fallback_fn, props, expected_log, expected_output, needs_render",
    [c[1:] for c in UNIT_CASES],
    ids=[c[0] for c in UNIT_CASES],
)
def test_fallback_renders_plain_text(
    fallback_fn, props, expected_log, expected_output, needs_render
):
    result = fallback_fn(props)
    output = DOM.render(result) if needs_render else result
    assert output == expected_output


@pytest.mark.parametrize(
    "fallback_fn, props, expected_log, expected_output, needs_render",
    [c[1:] for c in UNIT_CASES],
    ids=[c[0] for c in UNIT_CASES],
)
def test_fallback_logs_warning(
    fallback_fn, props, expected_log, expected_output, needs_render, caplog
):
    with caplog.at_level("WARNING", logger=LOGGER):
        fallback_fn(props)
    assert len(caplog.records) == 1
    assert expected_log in caplog.records[0].message


# -- Integration: fallbacks work end-to-end via build_markdown_config ---------

exporter = HTML(build_markdown_config())

INTEGRATION_CASES = [
    (
        "unknown_block",
        {
            "entityMap": {},
            "blocks": [
                {
                    "key": "a",
                    "text": "fallback content",
                    "type": "custom-unknown-block",
                    "depth": 0,
                    "inlineStyleRanges": [],
                    "entityRanges": [],
                }
            ],
        },
        "fallback content\n\n",
        None,
    ),
    (
        "unknown_entity",
        {
            "entityMap": {
                "0": {"type": "CUSTOM_ENTITY", "mutability": "MUTABLE", "data": {}}
            },
            "blocks": [
                {
                    "key": "a",
                    "text": "entity text",
                    "type": "unstyled",
                    "depth": 0,
                    "inlineStyleRanges": [],
                    "entityRanges": [{"offset": 0, "length": 11, "key": 0}],
                }
            ],
        },
        "entity text\n\n",
        None,
    ),
    (
        "unknown_style",
        {
            "entityMap": {},
            "blocks": [
                {
                    "key": "a",
                    "text": "styled text",
                    "type": "unstyled",
                    "depth": 0,
                    "inlineStyleRanges": [
                        {"offset": 0, "length": 11, "style": "CUSTOM_STYLE"}
                    ],
                    "entityRanges": [],
                }
            ],
        },
        "styled text\n\n",
        None,
    ),
]


@pytest.mark.parametrize(
    "content_state, expected_output, expected_log_substring",
    [c[1:] for c in INTEGRATION_CASES],
    ids=[c[0] for c in INTEGRATION_CASES],
)
def test_fallback_integration(
    content_state, expected_output, expected_log_substring, caplog
):
    with caplog.at_level("WARNING", logger=LOGGER):
        result = exporter.render(content_state)
    assert result == expected_output
    assert len(caplog.records) >= 1
    if expected_log_substring:
        assert expected_log_substring in caplog.records[0].message


# -- CONFIG includes default fallbacks ----------------------------------------


def test_config_has_block_fallback():
    assert "fallback" in CONFIG["block_map"]


def test_config_has_style_fallback():
    assert "FALLBACK" in CONFIG["style_map"]


def test_config_has_entity_fallback():
    assert "FALLBACK" in CONFIG["entity_decorators"]


# -- Custom fallbacks via MarkdownOptions -------------------------------------

UNKNOWN_STYLE_CONTENT: ContentState = {
    "entityMap": {},
    "blocks": [
        {
            "key": "a",
            "text": "text",
            "type": "unstyled",
            "depth": 0,
            "inlineStyleRanges": [{"offset": 0, "length": 4, "style": "UNKNOWN"}],
            "entityRanges": [],
        }
    ],
}

UNKNOWN_BLOCK_CONTENT: ContentState = {
    "entityMap": {},
    "blocks": [
        {
            "key": "a",
            "text": "text",
            "type": "custom-block",
            "depth": 0,
            "inlineStyleRanges": [],
            "entityRanges": [],
        }
    ],
}

UNKNOWN_ENTITY_CONTENT: ContentState = {
    "entityMap": {"0": {"type": "CUSTOM", "mutability": "MUTABLE", "data": {}}},
    "blocks": [
        {
            "key": "a",
            "text": "text",
            "type": "unstyled",
            "depth": 0,
            "inlineStyleRanges": [],
            "entityRanges": [{"offset": 0, "length": 4, "key": 0}],
        }
    ],
}


def test_custom_style_fallback():
    def custom_style(props: Props) -> Element:
        return props["children"]

    config = build_markdown_config({"style_fallback": custom_style})
    result = HTML(config).render(UNKNOWN_STYLE_CONTENT)
    assert result == "text\n\n"


def test_custom_block_fallback():
    def custom_block(props: Props) -> Element:
        return md_block(["[UNKNOWN] ", props["children"]])

    config = build_markdown_config({"block_fallback": custom_block})
    result = HTML(config).render(UNKNOWN_BLOCK_CONTENT)
    assert result == "\\[UNKNOWN\\] text\n\n"


def test_custom_entity_fallback():
    def custom_entity(props: Props) -> Element:
        return props["children"]

    config = build_markdown_config({"entity_fallback": custom_entity})
    result = HTML(config).render(UNKNOWN_ENTITY_CONTENT)
    assert result == "text\n\n"


def test_disable_style_fallback():
    config = build_markdown_config({"style_fallback": None})
    assert "FALLBACK" not in config["style_map"]
    with pytest.raises(ConfigException, match="UNKNOWN"):
        HTML(config).render(UNKNOWN_STYLE_CONTENT)


def test_disable_block_fallback():
    config = build_markdown_config({"block_fallback": None})
    assert "fallback" not in config["block_map"]
    with pytest.raises(ConfigException, match="custom-block"):
        HTML(config).render(UNKNOWN_BLOCK_CONTENT)


def test_disable_entity_fallback():
    config = build_markdown_config({"entity_fallback": None})
    assert "FALLBACK" not in config["entity_decorators"]
    with pytest.raises(ConfigException, match="CUSTOM"):
        HTML(config).render(UNKNOWN_ENTITY_CONTENT)


def test_default_fallbacks_present():
    config = build_markdown_config()
    assert "fallback" in config["block_map"]
    assert "FALLBACK" in config["style_map"]
    assert "FALLBACK" in config["entity_decorators"]


def test_html_style_map_inherited():
    """Known HTML styles like UNDERLINE render as HTML, not as fallback."""
    result = exporter.render(
        {
            "entityMap": {},
            "blocks": [
                {
                    "key": "a",
                    "text": "underlined",
                    "type": "unstyled",
                    "depth": 0,
                    "inlineStyleRanges": [
                        {"offset": 0, "length": 10, "style": "UNDERLINE"}
                    ],
                    "entityRanges": [],
                }
            ],
        }
    )
    assert result == "<u>underlined</u>\n\n"
