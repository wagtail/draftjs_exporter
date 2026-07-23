"""Tests for exporter exception types."""

import unittest

from draftjs_exporter.error import ExporterException, MarkdownParseError


class TestMarkdownParseError(unittest.TestCase):
    def test_message_only(self):
        err = MarkdownParseError("bad input")
        self.assertEqual(str(err), "bad input")
        self.assertEqual(err.message, "bad input")
        self.assertIsNone(err.line)

    def test_with_line(self):
        err = MarkdownParseError("bad input", line=7)
        self.assertEqual(str(err), "line 7: bad input")
        self.assertEqual(err.line, 7)

    def test_is_exporter_exception(self):
        self.assertIsInstance(MarkdownParseError("x"), ExporterException)
