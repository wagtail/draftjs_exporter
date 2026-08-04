"""Tests for Markdown escaping primitives."""

import unittest

from draftjs_exporter.markdown.escape import escape_text


class TestEscapeTextAnywhere(unittest.TestCase):
    def test_backslash_escaped_first(self):
        self.assertEqual(escape_text("a\\*b"), "a\\\\\\*b")

    def test_emphasis_chars(self):
        self.assertEqual(escape_text("*em* _em_"), "\\*em\\* \\_em\\_")

    def test_code_backtick(self):
        self.assertEqual(escape_text("a`b"), "a\\`b")

    def test_brackets(self):
        self.assertEqual(escape_text("[x](y)"), "\\[x\\](y)")

    def test_angle_bracket(self):
        self.assertEqual(escape_text("<script>"), "\\<script>")

    def test_ampersand(self):
        self.assertEqual(escape_text("&copy;"), "\\&copy;")

    def test_parentheses_not_escaped(self):
        self.assertEqual(escape_text("(hi)"), "(hi)")

    def test_greater_than_not_escaped_mid_line(self):
        self.assertEqual(escape_text("a > b"), "a > b")


class TestEscapeTextLineStart(unittest.TestCase):
    def test_hash_at_line_start(self):
        self.assertEqual(escape_text("# hi", at_line_start=True), "\\# hi")

    def test_hash_not_at_line_start(self):
        self.assertEqual(escape_text("# hi"), "# hi")

    def test_dash_plus(self):
        self.assertEqual(escape_text("- a", True), "\\- a")
        self.assertEqual(escape_text("+ a", True), "\\+ a")

    def test_blockquote_setext_tilde_pipe(self):
        self.assertEqual(escape_text("> a", True), "\\> a")
        self.assertEqual(escape_text("= a", True), "\\= a")
        self.assertEqual(escape_text("~ a", True), "\\~ a")
        self.assertEqual(escape_text("| a", True), "\\| a")

    def test_ordered_list_marker(self):
        self.assertEqual(escape_text("1. item", True), "1\\. item")
        self.assertEqual(escape_text("12) item", True), "12\\) item")

    def test_ordered_list_marker_ten_digits_not_escaped(self):
        self.assertEqual(escape_text("1234567890. x", True), "1234567890. x")

    def test_no_false_positive_after_anywhere_escape(self):
        # "*" at line start is escaped by the anywhere rule; the line-start
        # rule must not escape the resulting backslash again.
        self.assertEqual(escape_text("* a", True), "\\* a")

    def test_embedded_newline(self):
        self.assertEqual(escape_text("a\n- b"), "a\n\\- b")
        self.assertEqual(escape_text("a\n# b"), "a\n\\# b")

    def test_empty_string(self):
        self.assertEqual(escape_text("", at_line_start=True), "")


if __name__ == "__main__":
    unittest.main()
