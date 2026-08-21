# Reusing the agent skill

Draft.js exporter ships an agent skill that teaches AI coding agents how to use the library. The skill lives in the package itself (`.agents/skills/draftjs-exporter/SKILL.md`), so it stays in sync with the version of the exporter you install. It follows the open [Agent Skills](https://agentskills.io/) format, and the published documentation exposes it in several machine-readable ways.

This page lists the four ways you can reuse the skill.

| Option                                                     | What you get                                              | Best when                                                      |
| ---------------------------------------------------------- | --------------------------------------------------------- | -------------------------------------------------------------- |
| [Direct link to the skill](#direct-link-to-the-skill)      | The `SKILL.md` file as a URL                              | You want to point one agent at the skill by hand               |
| [Well Known Discovery](#agent-skills-well-known-discovery) | An index listing the skill                                | Your agent supports the Agent Skills discovery format          |
| [AI catalog](#ai-catalog)                                  | A catalog entry describing the skill                      | Your tooling reads AI catalogs                                 |
| [Library Skills](#library-skills)                          | A skill in your project that tracks the installed version | You use an Agent Skills-aware client and installed the library |

## Direct link to the skill

The docs site publishes the skill file directly:

- https://wagtail.github.io/draftjs_exporter/.well-known/agent-skills/draftjs-exporter/SKILL.md

Open the URL to read the skill, point an agent at it, or download it and place it in `.agents/skills/draftjs-exporter/SKILL.md` in your project so tooling that reads local skills picks it up.

## Agent Skills Well Known Discovery

The [Agent Skills discovery](https://agentskills.io/) well-known location publishes an index of the available skills:

- https://wagtail.github.io/draftjs_exporter/.well-known/agent-skills/index.json

The index follows the [Well Known Discovery RFC](https://schemas.agentskills.io/discovery/0.2.0/schema.json). It lists each skill's name, description, URL, and content digest. Agents that support the format can fetch it to discover the skill without loading the whole file up front.

## AI catalog

The docs site also publishes a machine-readable AI catalog:

- https://wagtail.github.io/draftjs_exporter/.well-known/ai-catalog.json

Each entry describes a skill's name, description, URL, version, and publisher. Tooling that reads AI catalogs can use it to present or install the skill.

## Library Skills

Because the skill is bundled inside the exported package, it lands in your environment at `site-packages/draftjs_exporter/.agents/skills/draftjs-exporter/SKILL.md` when you install the exporter. [Library Skills](https://library-skills.io/) scans installed packages for these bundled skills and installs them into your project:

```bash
uvx library-skills
```

Library Skills lists the discovered skills and symlinks `draftjs-exporter` into your project's `.agents/skills/`. Because the link points at the installed package, the skill updates automatically whenever you upgrade the exporter. See [Use Library Skills](https://library-skills.io/use/) for the full workflow.
