# Agent skills

Draft.js exporter ships [Agent Skills](https://agentskills.io/) that help users get better results with agentic coding. They’re published in multiple ways so you can reuse them easily with a wide range of tools.

| Option                                                | What you get                                              | Best when                                                      |
| ----------------------------------------------------- | --------------------------------------------------------- | -------------------------------------------------------------- |
| [Direct link to the skill](#direct-link-to-the-skill) | The `SKILL.md` file as a URL                              | You want to point one agent at the skill by hand               |
| [Well Known Discovery](#well-known-discovery)         | An index listing the skill                                | Your agent supports the Agent Skills discovery format          |
| [AI catalog](#ai-catalog)                             | A catalog entry describing the skill                      | Your tooling reads AI catalogs                                 |
| [Library Skills](#library-skills)                     | A skill in your project that tracks the installed version | You use an Agent Skills-aware client and installed the library |

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
