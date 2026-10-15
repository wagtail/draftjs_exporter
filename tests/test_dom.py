import unittest

from draftjs_exporter.dom import DOM, _engine_var
from draftjs_exporter.engines.html5lib import DOM_HTML5LIB
from draftjs_exporter.engines.lxml import DOM_LXML
from draftjs_exporter.engines.string import DOMString
from tests.test_entities import icon


class DOMTestImpl:
    def __init__(self):
        pass


class TestDOM(unittest.TestCase):
    def tearDown(self):
        DOM.use(DOM.HTML5LIB)

    def test_use_custom(self):
        DOM.use("tests.test_dom.DOMTestImpl")
        self.assertEqual(DOM._dom(), DOMTestImpl)

    def test_use_lxml(self):
        DOM.use(DOM.LXML)
        self.assertEqual(DOM._dom(), DOM_LXML)

    def test_use_html5lib(self):
        DOM.use(DOM.HTML5LIB)
        self.assertEqual(DOM._dom(), DOM_HTML5LIB)

    def test_use_string(self):
        DOM.use(DOM.STRING)
        self.assertEqual(DOM._dom(), DOMString)

    def test_engine_context_manager(self):
        DOM.use(DOM.HTML5LIB)
        self.assertEqual(DOM._dom(), DOM_HTML5LIB)
        with DOM.engine(DOM.STRING):
            self.assertEqual(DOM._dom(), DOMString)
        self.assertEqual(DOM._dom(), DOM_HTML5LIB)

    def test_engine_context_manager_restores_on_exception(self):
        DOM.use(DOM.HTML5LIB)
        try:
            with DOM.engine(DOM.STRING):
                raise ValueError("test")
        except ValueError:
            pass
        self.assertEqual(DOM._dom(), DOM_HTML5LIB)

    def test_no_engine_raises(self):
        token = _engine_var.set(None)
        try:
            with self.assertRaises(RuntimeError):
                DOM.create_element("p")
        finally:
            _engine_var.reset(token)

    def test_use_invalid(self):
        with self.assertRaises(ImportError):
            DOM.use("test")

    def test_use_shorthand(self):
        DOM.use("string")
        self.assertEqual(DOM._dom(), DOMString)

    def test_engine_context_manager_shorthand(self):
        DOM.use("html5lib")
        self.assertEqual(DOM._dom(), DOM_HTML5LIB)
        with DOM.engine("string"):
            self.assertEqual(DOM._dom(), DOMString)
        self.assertEqual(DOM._dom(), DOM_HTML5LIB)

    def test_create_element(self):
        self.assertEqual(
            DOM.render_debug(DOM.create_element("p", {"class": "intro"}, "Test test")),
            '<p class="intro">Test test</p>',
        )

    def test_create_element_style_dict(self):
        self.assertEqual(
            DOM.render_debug(
                DOM.create_element(
                    "p",
                    {
                        "style": {
                            "borderColor": "red",
                            "textDecoration": "underline",
                        }
                    },
                    "Test test",
                )
            ),
            '<p style="border-color: red;text-decoration: underline;">Test test</p>',
        )

    def test_create_element_style_str(self):
        self.assertEqual(
            DOM.render_debug(
                DOM.create_element(
                    "p",
                    {"style": "border-color: red;text-decoration: underline;"},
                    "Test test",
                )
            ),
            '<p style="border-color: red;text-decoration: underline;">Test test</p>',
        )

    def test_create_element_empty(self):
        self.assertEqual(
            DOM.render_debug(DOM.create_element()), "<fragment></fragment>"
        )

    def test_create_element_nested(self):
        self.assertEqual(
            DOM.render_debug(
                DOM.create_element(
                    "a",
                    {},
                    DOM.create_element(
                        "span",
                        {"class": "file-info icon-text"},
                        DOM.create_element(
                            "span", {"class": "icon-text__text"}, "Test test"
                        ),
                        DOM.create_element(
                            "svg",
                            {"class": "icon"},
                            DOM.create_element("use", {"xlink:href": "#icon-test"}),
                        ),
                    ),
                )
            ),
            '<a><span class="file-info icon-text"><span class="icon-text__text">Test test</span><svg class="icon"><use xlink:href="#icon-test"></use></svg></span></a>',
        )

    def test_create_element_none(self):
        self.assertEqual(
            DOM.render_debug(
                DOM.create_element(
                    "a", {}, None, DOM.create_element("span", {}, "Test test")
                )
            ),
            "<a><span>Test test</span></a>",
        )

    def test_create_element_entity(self):
        self.assertEqual(
            DOM.render_debug(DOM.create_element(icon, {"name": "rocket"})),
            '<svg class="icon"><use xlink:href="#icon-rocket"></use></svg>',
        )

    def test_parse_html(self):
        self.assertEqual(
            DOM.render_debug(DOM.parse_html("<p><span>Test text</span></p>")),
            "<p><span>Test text</span></p>",
        )

    def test_camel_to_dash(self):
        self.assertEqual(DOM.camel_to_dash("testCamelToDash"), "test-camel-to-dash")
        self.assertEqual(DOM.camel_to_dash("TestCamelToDash"), "test-camel-to-dash")
        self.assertEqual(DOM.camel_to_dash("TestCamelTODash"), "test-camel-to-dash")
        self.assertEqual(DOM.camel_to_dash("TestCamelTODasH"), "test-camel-to-das-h")
        self.assertEqual(DOM.camel_to_dash("testcameltodash"), "testcameltodash")
        self.assertEqual(DOM.camel_to_dash("test-Camel-ToDash"), "test-camel-to-dash")

    def test_append_child(self):
        parent = DOM.create_element("p")
        DOM.append_child(parent, DOM.create_element("span", {}, "Test text"))
        self.assertEqual(DOM.render_debug(parent), "<p><span>Test text</span></p>")

    def test_render_debug(self):
        self.assertEqual(
            DOM.render_debug(
                DOM.create_element(
                    "a",
                    {},
                    DOM.create_element(
                        "span",
                        {"class": "file-info icon-text"},
                        DOM.create_element(
                            "span", {"class": "icon-text__text"}, "Test test"
                        ),
                        DOM.create_element(
                            "svg",
                            {"class": "icon"},
                            DOM.create_element("use", {"xlink:href": "#icon-test"}),
                        ),
                    ),
                )
            ),
            '<a><span class="file-info icon-text"><span class="icon-text__text">Test test</span><svg class="icon"><use xlink:href="#icon-test"></use></svg></span></a>',
        )
