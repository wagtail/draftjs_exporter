"""Summarize promptfoo eval output JSONs: pass rates per arm, per repeat.

Usage:
    python docs/prompts/graders/summarize_opencode.py <output.json> [<output.json> ...]

Each output file holds one full eval run (four arms over the shared case set).
Rows from a `--repeat N` fan-out are grouped by provider and test index: each
group holds N independent repeats of the same case, so the per-repeat pass
rates and their spread are recoverable even though rows are interleaved.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def repeat_rates(path: str) -> dict[str, list[float]]:
    """Return one pass rate per repeat, per provider label, for one output file."""
    data = json.loads(Path(path).read_text())
    results = data["results"]["results"]
    groups: dict[tuple[str, int], list[bool]] = defaultdict(list)
    for row in results:
        groups[(row["provider"]["label"], row["testIdx"])].append(bool(row["success"]))
    repeats: dict[str, list[list[bool]]] = defaultdict(list)
    for (label, _test_idx), outcomes in groups.items():
        for repeat, success in enumerate(outcomes):
            # Pad shorter groups so a mid-run provider error does not shift
            # repeat indexes: a missing row counts as failed.
            while len(repeats[label]) <= repeat:
                repeats[label].append([])
            repeats[label][repeat].append(success)
    return {
        label: [sum(runs) / len(runs) for runs in runs_per_repeat]
        for label, runs_per_repeat in repeats.items()
    }


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    per_file = {path: repeat_rates(path) for path in sys.argv[1:]}
    labels = sorted(next(iter(per_file.values())))

    for path, by_label in per_file.items():
        cells = "  ".join(
            f"{label}={statistics.mean(rates):6.1%}"
            for label, rates in by_label.items()
        )
        print(f"{Path(path).name}: {cells}")

    if len(per_file) > 1:
        print()
        print("Across runs (mean +/- stddev over repeats):")
        for label in labels:
            all_rates = [
                rate
                for by_label in per_file.values()
                for rate in by_label.get(label, [])
            ]
            spread = (
                f" +/- {statistics.stdev(all_rates):.1%}" if len(all_rates) > 1 else ""
            )
            print(
                f"  {label:10s} {statistics.mean(all_rates):6.1%}{spread} (n={len(all_rates)})"
            )


if __name__ == "__main__":
    main()
