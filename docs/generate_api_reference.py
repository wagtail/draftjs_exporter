#!/usr/bin/env -S uv run
"""Generate the API reference page from the package's public API.

The page is derived from ``draftjs_exporter.__all__`` so the reference cannot
drift from the public API. Run with ``just docs-generate``, or pass ``--check`` to
verify the committed page is up to date, for CI.
"""

# ruff: noqa: T201 -- the script's purpose is to report its progress on stdout/stderr.

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import draftjs_exporter

REPO_ROOT = Path(__file__).resolve().parent.parent
PAGE = REPO_ROOT / "docs" / "reference" / "api.md"

# Fixed Markdown prepended to the generated page: frontmatter, an intro given
# the page is generated, and the mkdocstrings directive whose member list is
# built from __all__.
PREFIX = """---
description: "API reference for draftjs_exporter: the HTML exporter, DOM, constants, types, and the Markdown toolchain."
---

# API reference

This reference is generated from the package's public API, so it always matches what `draftjs_exporter` exports. Everything documented here is importable from the package root:

```python
from draftjs_exporter import HTML, DOM, BLOCK_TYPES
```

::: draftjs_exporter

    options:
      show_source: false
      members:
"""


def render() -> str:
    """Render the reference page from the package's ``__all__``.

    Returns:
        The page's Markdown.
    """
    # Skip dunder metadata like __version__ and __author__: they are not API.
    members = dict.fromkeys(
        name for name in draftjs_exporter.__all__ if not name.startswith("__")
    )
    body = "".join(f"        - {name}\n" for name in members)
    return PREFIX + body


def main() -> int:
    """Generate the reference page, or verify it, and report the result.

    Returns:
        The process exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the page is up to date instead of writing it.",
    )
    args = parser.parse_args()

    content = render()
    up_to_date = PAGE.exists() and PAGE.read_text(encoding="utf-8") == content

    if args.check:
        if up_to_date:
            print("API reference is up to date.")
            return 0
        print(
            "API reference is out of date. Run `just docs-generate` to regenerate it.",
            file=sys.stderr,
        )
        return 1

    PAGE.write_text(content, encoding="utf-8")
    print(f"Wrote {PAGE.relative_to(REPO_ROOT)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
