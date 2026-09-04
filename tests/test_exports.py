import cProfile
import json
import os
import unittest
from collections.abc import Callable
from pstats import Stats

from draftjs_exporter import (
    BLOCK_MAP,
    BLOCK_TYPES,
    DOM,
    ENTITY_TYPES,
    HTML,
    MARKDOWN_CONFIG,
    STYLE_MAP,
    ContentState,
    ExporterConfig,
)
from tests.test_composite_decorators import (
    BR_DECORATOR,
    HASHTAG_DECORATOR,
    LINKIFY_DECORATOR,
    LINKIFY_MARKDOWN_DECORATOR,
)
from tests.test_entities import hr, image, link

fixtures_path = os.path.join(os.path.dirname(__file__), "test_exports.json")
with open(fixtures_path) as f:
    fixtures = json.loads(f.read())

ENGINE_MAP = {
    "html5lib": DOM.HTML5LIB,
    "lxml": DOM.LXML,
    "string": DOM.STRING,
    "string_compat": DOM.STRING_COMPAT,
    "markdown": DOM.MARKDOWN,
}


def make_config(engine: str) -> ExporterConfig:
    if engine == DOM.MARKDOWN:
        return {
            **MARKDOWN_CONFIG,
            "style_map": {
                **MARKDOWN_CONFIG["style_map"],
                "KBD": "kbd",
                "HIGHLIGHT": {
                    "element": "strong",
                    "props": {"style": {"textDecoration": "underline"}},
                },
            },
            "entity_decorators": {
                **MARKDOWN_CONFIG["entity_decorators"],
                ENTITY_TYPES.EMBED: None,
            },
            "composite_decorators": [
                LINKIFY_MARKDOWN_DECORATOR,
            ],
        }

    return {
        "entity_decorators": {
            ENTITY_TYPES.LINK: link,
            ENTITY_TYPES.HORIZONTAL_RULE: hr,
            ENTITY_TYPES.IMAGE: image,
            ENTITY_TYPES.EMBED: None,
        },
        "composite_decorators": [
            BR_DECORATOR,
            LINKIFY_DECORATOR,
            HASHTAG_DECORATOR,
        ],
        "block_map": {
            **BLOCK_MAP,
            BLOCK_TYPES.UNORDERED_LIST_ITEM: {
                "element": "li",
                "wrapper": "ul",
                "wrapper_props": {"class": "bullet-list"},
            },
        },
        "style_map": {
            **STYLE_MAP,
            "KBD": "kbd",
            "HIGHLIGHT": {
                "element": "strong",
                "props": {"style": {"textDecoration": "underline"}},
            },
        },
        "engine": engine,
    }


class ExportsTestMeta(type):
    """
    Generates test cases dynamically.
    See http://stackoverflow.com/a/20870875/1798491
    """

    pr: cProfile.Profile = None  # type: ignore

    def __new__(mcs, name, bases, tests):
        engine_key = name.replace("TestExports", "").lower()
        engine_path = ENGINE_MAP.get(engine_key, DOM.STRING)
        exporter = HTML(make_config(engine_path))

        def gen_test(content: ContentState, html: str) -> Callable[[None], None]:
            def test(self):
                self.assertEqual(exporter.render(content), html)

            return test

        for export in fixtures:
            test_label = export["label"].lower().replace(" ", "_")
            test_name = f"test_export_{engine_key}_{test_label}"
            content = export["content_state"]
            html = export["output"][engine_key]
            tests[test_name] = gen_test(content, html)

        return type.__new__(mcs, name, bases, tests)


class TestExportsHTML5LIB(unittest.TestCase, metaclass=ExportsTestMeta):
    @classmethod
    def setUpClass(cls):
        cls.pr = cProfile.Profile()
        cls.pr.enable()
        print("\nhtml5lib")  # noqa: T201

    @classmethod
    def tearDownClass(cls):
        cls.pr.disable()
        Stats(cls.pr).strip_dirs().sort_stats("cumulative").print_stats(0)


class TestExportsLXML(unittest.TestCase, metaclass=ExportsTestMeta):
    @classmethod
    def setUpClass(cls):
        cls.pr = cProfile.Profile()
        cls.pr.enable()
        print("\nlxml")  # noqa: T201

    @classmethod
    def tearDownClass(cls):
        cls.pr.disable()
        Stats(cls.pr).strip_dirs().sort_stats("cumulative").print_stats(0)


class TestExportsString(unittest.TestCase, metaclass=ExportsTestMeta):
    @classmethod
    def setUpClass(cls):
        cls.pr = cProfile.Profile()
        cls.pr.enable()
        print("\nstring")  # noqa: T201

    @classmethod
    def tearDownClass(cls):
        cls.pr.disable()
        Stats(cls.pr).strip_dirs().sort_stats("cumulative").print_stats(0)


class TestExportsString_Compat(unittest.TestCase, metaclass=ExportsTestMeta):
    @classmethod
    def setUpClass(cls):
        cls.pr = cProfile.Profile()
        cls.pr.enable()
        print("\nstring_compat")  # noqa: T201

    @classmethod
    def tearDownClass(cls):
        cls.pr.disable()
        Stats(cls.pr).strip_dirs().sort_stats("cumulative").print_stats(0)


class TestExportsMarkdown(unittest.TestCase, metaclass=ExportsTestMeta):
    @classmethod
    def setUpClass(cls):
        cls.pr = cProfile.Profile()
        cls.pr.enable()
        cls.maxDiff = None
        print("\nmarkdown")  # noqa: T201

    @classmethod
    def tearDownClass(cls):
        cls.pr.disable()
        Stats(cls.pr).strip_dirs().sort_stats("cumulative").print_stats(0)


if __name__ == "__main__":
    unittest.main()
