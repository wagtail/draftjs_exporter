"""Promptfoo assertion: run the model's Python snippet against the real library.

The eval asks the model for a complete, runnable `draftjs_exporter` script. This
grader extracts that script, executes it, and compares stdout against the
expected output recorded in the test case. That turns "the answer looks right"
into "the answer works", which is the only signal that reliably separates a
correct API recollection from a plausible-looking hallucination.

Test cases supply either of these vars (or both):

- `expect_stdout`   — stdout must equal this string, after stripping.
- `expect_contains` — list of substrings that must all appear in stdout.

Caution: this executes model-generated code on the machine running the eval.
Snippets run in a throwaway directory with a short timeout, but they are not
sandboxed. Only run this eval against models and prompts you trust.

Requires `draftjs_exporter` to be importable by the interpreter promptfoo uses
for Python assertions — set `PROMPTFOO_PYTHON` to the project venv (see the
`eval` recipe in the justfile).
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from typing import Any

CODE_BLOCK = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL)
TIMEOUT_SECONDS = 30


def _fail(reason: str) -> dict[str, Any]:
    return {"pass": False, "score": 0, "reason": reason}


def _extract_snippet(output: str) -> str | None:
    """Return the first fenced block that actually uses the library.

    Blocks that never touch `draftjs_exporter` are ignored on purpose. Asked for
    a script, a model that does not know the API sometimes hand-rolls the answer
    with `re` and `json` and prints the expected result, which would otherwise
    pass a stdout comparison without exercising the library at all.
    """
    blocks: list[str] = CODE_BLOCK.findall(output)
    for block in blocks:
        if "draftjs_exporter" in block:
            return block.strip()
    return None


def get_assert(output: str, context: dict[str, Any]) -> dict[str, Any]:
    """Grade one model answer by running the snippet it contains."""
    snippet = _extract_snippet(output)
    if not snippet:
        return _fail("No Python code block using `draftjs_exporter` in the answer.")

    with tempfile.TemporaryDirectory() as workdir:
        try:
            run = subprocess.run(  # noqa: S603 - the eval runs model output on purpose
                [sys.executable, "-c", snippet],
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                cwd=workdir,
            )
        except subprocess.TimeoutExpired:
            return _fail(f"Snippet did not finish within {TIMEOUT_SECONDS}s.")

    if run.returncode != 0:
        error = run.stderr.strip().splitlines()
        last_line = error[-1] if error else f"exit code {run.returncode}"
        return _fail(f"Snippet raised: {last_line}")

    stdout = run.stdout.strip()
    if not stdout:
        return _fail("Snippet ran but printed nothing.")

    variables = context.get("vars", {})

    expected = variables.get("expect_stdout")
    if expected and stdout != expected.strip():
        return _fail(f"Expected stdout {expected.strip()!r}, got {stdout!r}")

    missing = [
        fragment
        for fragment in variables.get("expect_contains", [])
        if fragment not in stdout
    ]
    if missing:
        return _fail(f"stdout {stdout!r} is missing {missing!r}")

    return {"pass": True, "score": 1, "reason": f"Snippet ran, printed {stdout!r}"}
