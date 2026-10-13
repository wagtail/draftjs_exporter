"""Check the Claude skill eval's test cases without calling a model.

Every case in `draftjs_exporter_skills_claude_tests.yaml` and in the held-out
set next to it carries a `reference` answer. This script runs each one through `run_snippet.get_assert`, the same
grader the eval uses, and also feeds the grader answers that must fail: an empty
reply, a refusal, a script that prints nothing, and a script that prints the
expected output without using the library.

A reference that fails means the case, the grader or the library changed. A
null answer that passes means the grader is too lenient for that case. Either
way, the eval's scores for that case cannot be trusted until it is fixed.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import yaml

if TYPE_CHECKING:
    from collections.abc import Callable

# `run_snippet` sits next to this file and is not part of a package, so it is
# only importable when this script is run directly.
get_assert = cast(
    "Callable[[str, dict[str, Any]], dict[str, Any]]",
    importlib.import_module("run_snippet").get_assert,
)

PROMPTS = Path(__file__).parent.parent
TESTS = (
    PROMPTS / "draftjs_exporter_skills_claude_tests.yaml",
    PROMPTS / "draftjs_exporter_skills_claude_heldout.yaml",
)


def _null_answers(variables: dict[str, Any]) -> dict[str, str]:
    """Return answers that a sound grader must reject for this case."""
    expected = variables.get("expect_stdout") or " ".join(
        variables.get("expect_contains", [])
    )
    return {
        "empty": "",
        "refusal": "I don't know.",
        "no output": "```python\nimport draftjs_exporter\n```",
        "hand-rolled": f"```python\nprint({expected!r})\n```",
    }


def check() -> list[str]:
    """Return one message per problem found across all test cases."""
    tests = [
        test
        for path in TESTS
        for test in cast("list[dict[str, Any]]", yaml.safe_load(path.read_text()))
    ]
    problems: list[str] = []
    seen: set[str] = set()

    for test in tests:
        name = str(test["description"])
        variables = cast("dict[str, Any]", test["vars"])
        context = {"vars": variables}

        if name in seen:
            problems.append(f"{name}: duplicate description")
        seen.add(name)

        oracle = get_assert(f"```python\n{variables['reference']}\n```", context)
        if not oracle["pass"]:
            problems.append(f"{name}: reference fails — {oracle['reason']}")

        for label, answer in _null_answers(variables).items():
            if get_assert(answer, context)["pass"]:
                problems.append(f"{name}: {label} answer passes the grader")

    return problems


if __name__ == "__main__":
    found = check()
    sys.stdout.write("".join(f"{problem}\n" for problem in found))
    sys.stdout.write(f"{len(found)} problems found\n")
    sys.exit(1 if found else 0)
