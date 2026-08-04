"""Tests for Markdown escaping primitives."""

import unittest

from draftjs_exporter.markdown.escape import (
    code_block_fence,
    code_span_delimiters,
    escape_link_destination,
    escape_text,
)


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


class TestEscapeTextLineEndings(unittest.TestCase):
    def test_crlf_preserved(self):
        self.assertEqual(escape_text("a\r\n- b"), "a\r\n\\- b")
        self.assertEqual(escape_text("a\r\n# b"), "a\r\n\\# b")

    def test_lone_cr_is_line_start(self):
        self.assertEqual(escape_text("a\r# b"), "a\r\\# b")
        self.assertEqual(escape_text("a\r- b"), "a\r\\- b")

    def test_mixed_line_endings_preserved(self):
        self.assertEqual(escape_text("a\rb\r\nc\nd"), "a\rb\r\nc\nd")
        self.assertEqual(escape_text("a\n\r\n# b"), "a\n\r\n\\# b")

    def test_crlf_split_not_doubled(self):
        # A CRLF is a single line ending: the segment after it is at line
        # start, and the CR is not treated as an ending of its own.
        self.assertEqual(escape_text("a\r\n\r\n- b"), "a\r\n\r\n\\- b")


class TestEscapeTextLeadingSpaces(unittest.TestCase):
    def test_hash_after_spaces(self):
        self.assertEqual(escape_text("   # heading", True), "   \\# heading")

    def test_unordered_list_marker_after_spaces(self):
        self.assertEqual(escape_text("  - item", True), "  \\- item")

    def test_blockquote_marker_after_spaces(self):
        self.assertEqual(escape_text(" > quote", True), " \\> quote")

    def test_ordered_list_marker_after_spaces(self):
        self.assertEqual(escape_text("  1. item", True), "  1\\. item")

    def test_setext_underline_after_spaces(self):
        self.assertEqual(escape_text("a\n ---"), "a\n \\---")

    def test_code_fence_after_spaces(self):
        self.assertEqual(escape_text("   ~~~", True), "   \\~~~")

    def test_four_or_more_spaces_still_escaped(self):
        # 4+ spaces render as an indented code block downstream; escaping
        # is harmless there (a visible backslash) and keeps containers safe.
        self.assertEqual(escape_text("     # x", True), "     \\# x")

    def test_tab_not_escaped(self):
        # A leading tab already makes an indented code block; escaping
        # after tabs is out of scope.
        self.assertEqual(escape_text("\t# x", True), "\t# x")

    def test_spaces_not_at_line_start_unchanged(self):
        self.assertEqual(escape_text("  # x"), "  # x")

    def test_line_of_only_spaces(self):
        self.assertEqual(escape_text("   ", True), "   ")


class TestEscapeLinkDestination(unittest.TestCase):
    def test_plain_url_unchanged(self):
        self.assertEqual(
            escape_link_destination("https://example.com/a?b=1&c=2"),
            "https://example.com/a?b=1&c=2",
        )

    def test_parentheses_escaped(self):
        self.assertEqual(
            escape_link_destination("https://example.com/a_(b)"),
            "https://example.com/a_\\(b\\)",
        )

    def test_backslash_escaped(self):
        self.assertEqual(escape_link_destination("a\\b"), "a\\\\b")

    def test_space_percent_encoded(self):
        self.assertEqual(escape_link_destination("a b"), "a%20b")

    def test_control_char_percent_encoded(self):
        self.assertEqual(escape_link_destination("a\nb"), "a%0Ab")

    def test_non_ascii_unchanged(self):
        self.assertEqual(escape_link_destination("/café"), "/café")


class TestCodeSpanDelimiters(unittest.TestCase):
    def test_plain_content(self):
        self.assertEqual(code_span_delimiters("foo"), ("`", "`"))

    def test_backtick_in_content(self):
        self.assertEqual(code_span_delimiters("a`b"), ("``", "``"))

    def test_two_backticks_in_content(self):
        self.assertEqual(code_span_delimiters("a``b"), ("```", "```"))

    def test_leading_backtick_padded(self):
        self.assertEqual(code_span_delimiters("`x"), ("`` ", " ``"))

    def test_trailing_backtick_padded(self):
        self.assertEqual(code_span_delimiters("x`"), ("`` ", " ``"))


class TestCodeBlockFence(unittest.TestCase):
    def test_plain_content(self):
        self.assertEqual(code_block_fence("foo\n", "`"), "```")

    def test_fence_run_in_content(self):
        self.assertEqual(code_block_fence("a```b\n", "`"), "````")

    def test_minimum_length_three(self):
        self.assertEqual(code_block_fence("a`b\n", "`"), "```")

    def test_tilde_fence(self):
        self.assertEqual(code_block_fence("a~~~b\n", "~"), "~~~~")


if __name__ == "__main__":
    unittest.main()
