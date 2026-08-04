import unittest

from draftjs_exporter.engines.markdown import DOMMarkdown

M = DOMMarkdown


class TestDOMMarkdown(unittest.TestCase):
    def test_create_tag(self):
        self.assertEqual(
            M.render_debug(M.create_tag("p", {"class": "intro"})),
            '<p class="intro"></p>',
        )

    def test_create_tag_empty(self):
        self.assertEqual(M.render_debug(M.create_tag("p")), "<p></p>")

    def test_parse_html(self):
        self.assertEqual(
            M.render(M.parse_html("<p><span>Test text</span></p>")),
            "<p><span>Test text</span></p>",
        )

    def test_append_child(self):
        parent = M.create_tag("p")
        M.append_child(parent, M.create_tag("span", {}))
        self.assertEqual(M.render_debug(parent), "<p><span></span></p>")

    def test_append_child_identical_text(self):
        parent = M.create_tag("p")
        M.append_child(parent, "test")
        M.append_child(parent, "test")
        self.assertEqual(M.render_debug(parent), "<p>testtest</p>")

    def test_append_child_identical_elements(self):
        parent = M.create_tag("p")
        M.append_child(parent, M.create_tag("br"))
        M.append_child(parent, M.create_tag("br"))
        self.assertEqual(M.render_debug(parent), "<p><br/><br/></p>")

    def test_append_child_same_elements(self):
        elt = M.create_tag("br")
        parent = M.create_tag("p")
        M.append_child(parent, elt)
        M.append_child(parent, elt)
        self.assertEqual(M.render_debug(parent), "<p><br/></p>")

    def test_render_attrs(self):
        self.assertEqual(
            M.render_attrs(
                {
                    "src": "src.png",
                    "alt": "img's alt",
                    "class": "intro",
                }
            ),
            ' alt="img&#x27;s alt" class="intro" src="src.png"',
        )

    def test_render_children(self):
        self.assertEqual(
            M.render_children(
                [
                    "render children",
                    M.create_tag("p", {"class": "intro"}),
                    "test test",
                ]
            ),
            'render children<p class="intro"></p>test test',
        )

    def test_render_children_escapes_text(self):
        """Plain string children are user text and are escaped."""
        self.assertEqual(
            M.render_children(["<strong>not escaped</strong>"]),
            "\\<strong>not escaped\\</strong>",
        )

    def test_render(self):
        self.assertEqual(
            M.render_debug(M.create_tag("p", {"class": "intro"})),
            '<p class="intro"></p>',
        )

    def test_render_debug(self):
        self.assertEqual(
            M.render_debug(M.create_tag("p", {"class": "intro"})),
            '<p class="intro"></p>',
        )


class TestMarkSafe(unittest.TestCase):
    def test_rendered_verbatim(self):
        elt = M.create_tag("mark_safe", {"markup": "# ", "block_prefix": "true"})
        self.assertEqual(M.render(elt), "# ")

    def test_block_prefix_readable(self):
        elt = M.create_tag("mark_safe", {"markup": "- ", "block_prefix": "true"})
        assert elt.attr is not None
        self.assertEqual(elt.attr.get("block_prefix"), "true")


class TestCodeSpanNode(unittest.TestCase):
    def test_content_not_escaped(self):
        elt = M.create_tag("code_span")
        M.append_child(elt, "a*b`c")
        self.assertEqual(M.render(elt), "``a*b`c``")

    def test_plain_content(self):
        elt = M.create_tag("code_span")
        M.append_child(elt, "foo")
        self.assertEqual(M.render(elt), "`foo`")

    def test_leading_backtick_padded(self):
        elt = M.create_tag("code_span")
        M.append_child(elt, "`x")
        self.assertEqual(M.render(elt), "`` `x ``")


class TestCodeBlockNode(unittest.TestCase):
    def test_content_not_escaped(self):
        elt = M.create_tag("code_block", {"fence": "`"})
        M.append_child(elt, "# <script>\n")
        self.assertEqual(M.render(elt), "```\n# <script>\n```\n\n")

    def test_fence_sized_to_content(self):
        elt = M.create_tag("code_block", {"fence": "`"})
        M.append_child(elt, "a```b\n")
        self.assertEqual(M.render(elt), "````\na```b\n````\n\n")

    def test_tilde_fence(self):
        elt = M.create_tag("code_block", {"fence": "~"})
        M.append_child(elt, "x\n")
        self.assertEqual(M.render(elt), "~~~\nx\n~~~\n\n")

    def test_empty_content(self):
        elt = M.create_tag("code_block", {"fence": "`"})
        self.assertEqual(M.render(elt), "```\n```\n\n")


class TestRenderChildrenEscaping(unittest.TestCase):
    def test_metacharacters_escaped(self):
        self.assertEqual(
            M.render_children(["*a* _b_ [c] `d` &e"]),
            "\\*a\\* \\_b\\_ \\[c\\] \\`d\\` \\&e",
        )

    def test_first_string_is_line_start(self):
        self.assertEqual(M.render_children(["# not a heading"]), "\\# not a heading")

    def test_line_start_after_newline(self):
        frag = M.create_tag("fragment")
        M.append_child(frag, M.create_tag("mark_safe", {"markup": "intro\n"}))
        M.append_child(frag, "# b")
        self.assertEqual(M.render(frag), "intro\n\\# b")

    def test_no_line_start_mid_line(self):
        frag = M.create_tag("fragment")
        M.append_child(frag, M.create_tag("mark_safe", {"markup": "# "}))
        M.append_child(frag, "#tag")
        self.assertEqual(M.render(frag), "# #tag")

    def test_line_start_after_block_prefix(self):
        frag = M.create_tag("fragment")
        M.append_child(
            frag, M.create_tag("mark_safe", {"markup": "- ", "block_prefix": "true"})
        )
        M.append_child(frag, "# not a heading")
        self.assertEqual(M.render(frag), "- \\# not a heading")

    def test_no_line_start_after_plain_mark_safe(self):
        frag = M.create_tag("fragment")
        M.append_child(frag, M.create_tag("mark_safe", {"markup": "**"}))
        M.append_child(frag, "#bold")
        self.assertEqual(M.render(frag), "**#bold")

    def test_mark_safe_verbatim_among_text(self):
        frag = M.create_tag("fragment")
        M.append_child(frag, "a")
        M.append_child(frag, M.create_tag("mark_safe", {"markup": "**"}))
        M.append_child(frag, "b")
        self.assertEqual(M.render(frag), "a**b")

    def test_embedded_newline_in_text(self):
        self.assertEqual(M.render_children(["a\n- b"]), "a\n\\- b")

    def test_html_element_children_escaped(self):
        elt = M.create_tag("sup")
        M.append_child(elt, "a<b")
        self.assertEqual(M.render(elt), "<sup>a\\<b</sup>")

    def test_line_start_tracking_across_element(self):
        frag = M.create_tag("fragment")
        M.append_child(frag, M.create_tag("sup"))
        M.append_child(frag, "# x")
        # <sup></sup> does not end with a newline: mid-line, no escape.
        self.assertEqual(M.render(frag), "<sup></sup># x")
