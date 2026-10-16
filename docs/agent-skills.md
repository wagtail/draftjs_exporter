---
description: "Agent Skills published by draftjs_exporter for AI coding assistants: direct links, catalogs, and how to install them in your project."
---

# Agent skills

Draft.js exporter ships [Agent Skills](https://agentskills.io/) that help users get better results with agentic coding. They’re published in multiple ways so you can reuse them easily with a wide range of tools.

## Direct link to the skill

Nice and simple - it’s here: <https://wagtail.github.io/draftjs_exporter/.well-known/agent-skills/draftjs-exporter/SKILL.md>.
Open the URL to read the skill, point an agent at it, or download it and place it in `.agents/skills/draftjs-exporter/SKILL.md` in your project so tooling that reads local skills picks it up.

## Well Known Discovery

Machine-readable index of all skills: [/.well-known/agent-skills/](https://wagtail.github.io/draftjs_exporter/.well-known/agent-skills/index.json).
This is per the [Well Known Discovery RFC](https://github.com/cloudflare/agent-skills-discovery-rfc). Agents that support the format can fetch it to discover the skills.

## AI catalog

Machine-readable index that also covers other options than skills: [/.well-known/ai-catalog.json](https://wagtail.github.io/draftjs_exporter/.well-known/ai-catalog.json).
This is per the [AI Catalog](https://ai-catalog.io/) specification.

## Library Skills

Because the skill is bundled inside the exported package, it lands in your environment at `site-packages/draftjs_exporter/.agents/skills/draftjs-exporter/SKILL.md` when you install the exporter.
[Library Skills](https://library-skills.io/) scans installed packages for these bundled skills and installs them into your project. It symlinks to the installed package, so the skill updates automatically whenever you upgrade the exporter.

## Does the skill help

Yes. We evaluate the skill against the published docs on a set of prompts that ask a model to write complete, runnable `draftjs_exporter` code, then run every answer against the real library. The skill improves the pass rate on every model we tested, and helps weaker models the most – with the skill, all Claude models land within 5 points of each other.

These figures are a snapshot from October 2026, against `draftjs_exporter` 7.1.0. They are aggregates over several repeats of 35 prompts, not a guarantee – treat them as an indication of the uplift, not a ranking.

Pass rate on Claude models, skill versus no reference at all:

| Model      | No docs (baseline) | Docs only | Skill only | Docs + skill |
| ---------- | ------------------ | --------- | ---------- | ------------ |
| Haiku 5.5  | 33.5%              | 66.1%     | 89.4%      | 90.6%        |
| Sonnet 5.5 | 49.0%              | 66.1%     | 91.8%      | 94.3%        |
| Opus 5.5   | 77.1%              | 91.8%     | 93.9%      | 95.9%        |
| Fable 5.1  | 58.1%              | 79.0%     | 94.3%      | 93.3%        |

Five open-weight models (DeepSeek V4.1 Flash, DeepSeek V4 Flash Speed, GLM 5.3, GLM 5.3 Flash, Mimo V2.6 Pro) showed the same pattern, with larger uplifts over their weaker baselines:

| Model                   | No docs (baseline) | Docs only | Skill only | Docs + skill |
| ----------------------- | ------------------ | --------- | ---------- | ------------ |
| DeepSeek V4.1 Flash     | 24.8%              | 78.1%     | 87.6%      | 89.5%        |
| DeepSeek V4 Flash Speed | 12.4%              | 74.3%     | 74.3%      | 84.8%        |
| GLM 5.3                 | 8.6%               | 76.2%     | 67.6%      | 85.7%        |
| GLM 5.3 Flash           | 26.7%              | 82.9%     | 74.3%      | 91.4%        |
| Mimo V2.6 Pro           | 10.5%              | 82.9%     | 88.6%      | 93.3%        |

### Skill improvements

How much the skill changes things, compared with the model answering from memory (no docs, no skill). Pass rate is the change in points; duration and cost are the change relative to the baseline, as a percentage.

| Model                   | Pass rate | Duration | Cost  |
| ----------------------- | --------- | -------- | ----- |
| Haiku 5.5               | +55.9 pts | −29%     | +69%  |
| Sonnet 5.5              | +42.9 pts | −32%     | +100% |
| Opus 5.5                | +16.7 pts | −51%     | +26%  |
| Fable 5.1               | +36.2 pts | −69%     | −21%  |
| DeepSeek V4.1 Flash     | +62.9 pts | −66%     | −71%  |
| DeepSeek V4 Flash Speed | +61.9 pts | +85%     | +614% |
| GLM 5.3                 | +59.0 pts | −64%     | −62%  |
| GLM 5.3 Flash           | +47.6 pts | −73%     | −68%  |
| Mimo V2.6 Pro           | +78.1 pts | −57%     | −54%  |

The biggest pass-rate gains are on the weakest baselines: Haiku and the open-weight models gain 48 to 78 points, while Opus, already strong on its own, gains the least. The absolute figures tell that story more honestly than percentages would, since the same finish line looks like a much larger relative jump from a low start.

The open-weight costs are computed from each model's list rates on [models.dev](https://models.dev/) applied to the tokens the eval recorded. Without the skill these models spend most of their budget on reasoning tokens, so the skill usually costs less, not more. The one exception, DeepSeek V4 Flash Speed, has no reasoning lane and its baseline was already so cheap that the skill's larger context is a large relative increase on a very small base.

The skill is usually faster even though it costs a few extra turns to load, because the model stops guessing and spends fewer tokens. The exception is DeepSeek V4 Flash Speed, whose baseline was already very quick but scored low. On Fable and most of the open-weight models the skill is also cheaper, because the no-skill answers spend far more on reasoning or run much longer.

What the results suggest in practice:

- **Use the skill if you use an agent to write `draftjs_exporter` code.** Without any reference, models lean on dated knowledge: they import the old `draftjs_exporter_markdown` package, invent APIs, or claim the library has no Markdown importer. The skill prevents most of that.
- **The skill is usually enough.** Adding the docs on top changes the Claude pass rate by −1 to +2.4 points, within one SD. On the open-weight models the docs help a little more, especially for GLM (+17 to +18 points).
- **The skill is the cheapest and fastest option.** It is the fastest arm on every model (9 to 14 seconds per answer on Claude) and gives the shortest answers, faster than the baseline even though it takes a few extra turns to load.
- **A small model with the skill can beat a large model without it.** Haiku with the skill scores higher than Opus without any reference, at roughly 1/14 of the cost per answer.

A marginal caveat: when both the docs and the skill are available, smaller models sometimes skip the skill and search the docs instead, which measures slightly lower. The skill alone is the simpler setup.

The method behind these numbers – the arms we compare, how answers are graded, and why we repeat runs – is in the [skill and docs evals](contributing/evals.md) guide for contributors.
