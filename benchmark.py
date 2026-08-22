"""Benchmark the performance of draftjs_exporter."""

import argparse
import cProfile
import logging
import os
import re
from pstats import Stats
from typing import cast

import memray
from markov_draftjs import get_content_sample

from draftjs_exporter import (
    BLOCK_MAP,
    BLOCK_TYPES,
    DOM,
    ENTITY_TYPES,
    HTML,
    STYLE_MAP,
    ContentState,
    Element,
    ExporterConfig,
    Props,
)
from example import br, entity_fallback, image, list_item, ordered_list

parser = argparse.ArgumentParser(description="Run the draftjs_exporter benchmark.")
parser.add_argument(
    "--runs",
    type=int,
    default=int(os.environ.get("BENCHMARK_RUNS", 1)),
    help="Number of times to run the benchmark. Defaults to the BENCHMARK_RUNS environment variable, or 1.",
)
args = parser.parse_args()


def document(props: Props) -> Element:
    """Render a document entity as a link."""
    return DOM.create_element(
        "a",
        {"title": props.get("label"), "href": f"/documents/{props.get('id')}"},
        props["children"],
    )


def link(props: Props) -> Element:
    """Render a link entity as an anchor element."""
    return DOM.create_element("a", {"href": props["url"]}, props["children"])


def block_fallback(props: Props) -> Element:
    """Render a fallback element for an unknown block type."""
    type_ = props["block"]["type"]

    logging.warning(f'Missing config for "{type_}".')
    return DOM.create_element("div", {}, props["children"])


config: ExporterConfig = {
    "block_map": {
        **BLOCK_MAP,
        BLOCK_TYPES.HEADER_TWO: "h2",
        BLOCK_TYPES.HEADER_THREE: {
            "element": "h3",
            "props": {"class": "u-text-center"},
        },
        BLOCK_TYPES.UNORDERED_LIST_ITEM: {
            "element": "li",
            "wrapper": "ul",
            "wrapper_props": {"class": "bullet-list"},
        },
        BLOCK_TYPES.ORDERED_LIST_ITEM: {
            "element": list_item,
            "wrapper": ordered_list,
        },
        BLOCK_TYPES.FALLBACK: block_fallback,
    },
    "style_map": STYLE_MAP,
    "entity_decorators": {
        ENTITY_TYPES.IMAGE: image,
        ENTITY_TYPES.LINK: link,
        ENTITY_TYPES.DOCUMENT: document,
        ENTITY_TYPES.HORIZONTAL_RULE: lambda props: DOM.create_element("hr"),
        ENTITY_TYPES.EMBED: None,
        ENTITY_TYPES.FALLBACK: entity_fallback,
    },
    "composite_decorators": [{"strategy": re.compile(r"\n"), "component": br}],
    "engine": DOM.STRING,
}

exporter = HTML(config)

# markov_draftjs has slightly different type declarations.
content_states = cast(list[ContentState], get_content_sample())

print(f"Exporting {len(content_states)} ContentStates {args.runs} times")  # noqa: T201

pr = cProfile.Profile()
pr.enable()

for i in range(0, args.runs):
    for content_state in content_states:
        exporter.render(content_state)

pr.disable()
p = Stats(pr)

p.strip_dirs().sort_stats("cumulative").print_stats(10)

print("Measuring memory consumption")  # noqa: T201


def memory_consumption_run() -> None:
    """Measure memory consumption while exporting the sample content."""
    with memray.Tracker(
        destination=memray.FileDestination("benchmark.bin", overwrite=True)
    ):
        exporter = HTML(config)

        for content_state in content_states:
            exporter.render(content_state)


memory_consumption_run()
