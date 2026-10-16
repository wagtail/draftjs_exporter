---
description: "Skill and docs evals for draftjs_exporter: the 2x2 arms, how answers are graded, repeat counts, and how to run and read results."
---

# Skill and docs evals

We measure whether the `draftjs-exporter` [agent skill](../agent-skills.md) and the published docs actually help a model write working `draftjs_exporter` code. The evals live in `docs/prompts/`, run through [promptfoo](https://promptfoo.dev/), and are how we decide what to change in the skill.

The current results are on the [agent skills](../agent-skills.md#does-the-skill-help) page for users. This page is the method behind them: what an arm is, what counts as a pass, and how to run a suite yourself.

## The four arms

Every eval runs a 2x2 over two questions – can the model load the skill, and can it read the docs:

|          | No docs  | Docs       |
| -------- | -------- | ---------- |
| No skill | baseline | docs       |
| Skill    | skill    | docs+skill |

An arm is a provider entry in the eval config: the same model, the same system prompt, and the same working directory shape, differing only in which tools it may call.

- **baseline** – no tools. The model answers from memory.
- **skill** – the `Skill` loader only, with the skill fixture in its working directory.
- **docs** – `Read`, `Grep`, `Glob` (and `List` on OpenCode) over `llms.txt` and `llms-full.txt`.
- **docs+skill** – all of the above.

Each arm runs in a fixture directory outside the repository, so no arm can read the library source, the eval config, or the reference answers. `just eval-claude-fixtures` and `just eval-opencode-fixtures` build them; `just eval-docs` builds the `llms.txt` / `llms-full.txt` the docs arms read.

> The docs arms also add retrieval tools, so a docs arm that loses may be losing on retrieval rather than on documentation quality. Keep that in mind before concluding the docs are weak.

## What counts as a pass

Most cases ask for a complete, runnable Python script. The grader (`graders/run_snippet.py`) extracts the first fenced Python code block that uses `draftjs_exporter`, runs it against the installed library, and compares stdout:

- **`expect_stdout`** – stdout must equal this string after stripping surrounding whitespace.
- **`expect_contains`** – every listed fragment must appear in stdout.

There is no LLM judge and no partial credit for script cases. An answer passes only if the script runs without error or timeout and the output matches. Explanations around the code are ignored, and a correct script that prints extra output fails an exact-match case. A couple of knowledge-only cases use `llm-rubric` instead, because they have no code answer.

This is what turns "the answer looks right" into "the answer works" – a hallucinated API fails the run even when the prose reads well, which is exactly the failure mode a reference is meant to prevent.

> The grader executes model-generated code on the machine running the eval. Snippets run in a throwaway directory with a short timeout, but they are not sandboxed. Only run evals against models and prompts you trust.

Cases live in `draftjs_exporter_skills_claude_tests.yaml`. `check_references.py` (run by `just eval-claude-check`) validates every case without calling a model: each carries a `reference` answer that must pass the grader, and empty, refusing, no-output, and hand-rolled answers must all fail it. A reference that fails means the case, the grader, or the library changed.

## Repeats and noise

Model runs are noisy: one repeat is one full pass over every case × every arm. The pass rate moves between repeats, so we report the mean of several repeats and their sample standard deviation, and we compare arms **within** a repeat before averaging.

- **One repeat is not enough to act on a gap.** At 35 cases, one repeat has a noise floor of roughly ±17 points on a pass rate, ±10 at three repeats.
- **The recorded Claude results use 7 repeats** for Haiku, Sonnet, and Opus, and 3 for Fable. From 3 to 5 to 7 repeats the conclusions held; the average standard error across the 12 model/arm cells fell from 1.9 to 1.7 to 1.4 points. From 5 to 7 repeats no mean moved by more than 2.0 points.
- **The recorded OpenCode results use 3 repeats** per model, so treat their spreads as wider than the Claude figures.
- The SD across repeats only captures run-to-run variation, not how well the 35 cases represent real questions. Small differences between arms or near-tied models are not meaningful.

Run with `--repeat 3` before trusting a delta, and `--repeat 7` when recording figures for the docs.

## Running the evals

```sh
just eval-init                       # promptfoo + the SDKs (once per Node version)
just init                            # the grader imports draftjs_exporter from the venv

just eval-claude-check               # validate cases, no model calls
just eval-claude                          # Claude Sonnet 5.5
just eval-claude claude-haiku-5-5 --repeat 7
just eval-opencode                        # DeepSeek V4.1 Flash (Neuralwatt)
just eval-opencode glm-5.3-flash --repeat 3

just eval-view                       # dashboard for the latest run
```

`just eval-claude` needs `ANTHROPIC_API_KEY` or a local Claude Code login. `just eval-opencode` takes the Neuralwatt key as its second argument. Use `--no-cache` (the recipes pass it) so a "pass" always reflects a fresh answer.

`docs/prompts/draftjs_exporter_skills_claude_heldout.yaml` holds held-out cases not part of the default run. Keep them out of sight when tuning the skill or the docs against the main cases, then run them to check that a gain carries over to unseen prompts.

## Reading results with care

- **Compare arms at the same repeat count.** A 7-repeat mean and a 3-repeat mean are not directly comparable.
- **The cases flatter the skill.** Many were written from the skill and docs rather than from real user questions, so a skill win is partly a win on coverage of the material the skill was written from.
- **One library version, one harness.** Time and token figures come from one machine running several answers in parallel; they are for comparing arms, not absolute benchmarks.
- **Cost is derived, not measured.** Provider-reported cost exists for the Claude eval. Open-weight costs are computed by applying each model's list rates from [models.dev](https://models.dev/) to the tokens the eval recorded, so they move with those listed rates rather than with what the API actually billed.
- **A lone rubric failure is noise** until a repeat reproduces it; the rubric grader occasionally answers in prose instead of JSON.
- **A provider error is not a model failure.** The configs assert non-empty output first, so an empty answer is labelled rather than graded as wrong.

## Reporting findings

The eval was used to drive the current skill and docs. Data from an eval run belongs on the [agent skills](../agent-skills.md#does-the-skill-help) page when it is user-facing (how much the skill helps, at what cost), and here when it changes the method. When you change the skill or docs from eval findings, mention the eval in the pull request description and link the relevant case.
