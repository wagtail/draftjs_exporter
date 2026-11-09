#!/usr/bin/env -S uv run
"""Check the public API for breaking changes since the last release.

The public API is the package root's ``__all__``: everything importable as
``draftjs_exporter.<name>``. Griffe loads the API at the latest git tag and in the
working tree, then reports breaking changes between them -- removed exports,
renamed parameters, changed types, and so on.

Run with ``just api-check``, in ``just lint`` and CI. This is a review aid, not a
gate: a deliberate breaking change is fine, as long as the maintainer sees it and
documents it in the changelog and migration guide.
"""

# ruff: noqa: T201 -- the script's purpose is to report its findings on stdout/stderr.

from __future__ import annotations

import subprocess
import sys

import griffe

PACKAGE = "draftjs_exporter"


def last_tag() -> str | None:
    """Return the most recent version tag, or ``None`` when there is none.

    Returns:
        The tag name, or ``None`` if the repository has no tags.
    """
    # noqa comments for the file: trusted local `git`, run by name from PATH.
    result = subprocess.run(  # noqa: S603
        ["git", "describe", "--tags", "--abbrev=0"],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() or None


def main() -> int:
    """Report breaking changes in the public API since the last release.

    Returns:
        The process exit code: ``0`` if there are none, ``1`` otherwise.
    """
    ref = last_tag()
    if ref is None:
        print("No release tag found, skipping the breaking change check.")
        return 0

    old = griffe.load_git(PACKAGE, ref=ref)
    new = griffe.load(PACKAGE)

    breakages = list(griffe.find_breaking_changes(old, new))
    if not breakages:
        print(f"No breaking changes to the public API since {ref}.")
        return 0

    print(f"Breaking changes to the public API since {ref}:", file=sys.stderr)
    for breakage in breakages:
        print(f"- {breakage.explain()}", file=sys.stderr)
    print(
        "If this is intentional, document it in the changelog and migration guide.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
