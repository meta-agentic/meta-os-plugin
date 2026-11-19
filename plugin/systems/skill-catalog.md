---
type: index
tags: [os, skills, layer1]
---
# Layer 1 — Skill Backbone

Codified, executable workflows. The plugin's `skills/` folder is the single authoritative home of the skills below; each is called as `/meta-os:<name>`.

> If you do it more than once, it should be a skill. Author new ones with [skill-builder](../skills/skill-builder/SKILL.md).

## Core backbone — the skills the plugin ships

| Skill | Domain | Use for |
|-------|--------|---------|
| [init](../skills/init/SKILL.md) | Meta | First-run setup of an instance in the current folder: a short introduction, a quick start with every default on one screen, or a customised setup |
| [infoviz](../skills/infoviz/SKILL.md) | Interface | Choose the visual *form* for data before drawing it — chart and encoding selection from data and task, method choice for complex data (network, hierarchy, flow, temporal, geospatial), trust gate; hands off to styling |
| [skill-builder](../skills/skill-builder/SKILL.md) | Meta | Author one skill: the trigger contract, progressive disclosure, and the registration a skill is not finished without |
| [pack-builder](../skills/pack-builder/SKILL.md) | Meta | Author a new pack: apply the is-it-a-pack test, structure (plugin manifest, `pack.yaml`, profiles), parameterise, provenance, verify by installing — see [pack-strategy](pack-strategy.md) |
| [multi-engine](../skills/multi-engine/SKILL.md) | Meta | Cross-provider headless fan-out via meta-cli (`claude`/`gemini`/`grok`/…); collect → `memory/raw/` — see [engine](engine.md) |

## Pack-provided skills

Skills a pack ships rather than this plugin, catalogued here because the core shipped them until they moved. Each resolves from the `provides:` list of its pack in [the registry](packs.yaml); see [packs](packs.md).

| Skill | Pack | Plugin | Use for |
|-------|------|--------|---------|
| `agile-process` | [meta-discipline-agile](https://github.com/meta-agentic/meta-disciplines/tree/main/plugins/meta-discipline-agile) | `meta-discipline-agile@meta-agentic` | Backlog of record, ceremonies, transitions — transition ledger |
| `agile-swarm` | [meta-discipline-agile](https://github.com/meta-agentic/meta-disciplines/tree/main/plugins/meta-discipline-agile) | `meta-discipline-agile@meta-agentic` | Multi-lane sprint execution — lane ledger |

## What is deliberately not here

The core ships only what is part of the OS itself: setting up an instance, skill and pack authoring, the graph, the engine surface. Two categories live elsewhere on purpose:

- **Domain and process skill sets are packs.** An agile method, a discipline, a third-party collection: a Claude Code plugin the user chooses, recorded in the instance's `.packs.yaml`, never vendored here. See [packs](packs.md).
- **Third-party tooling is installed by its own installer.** The claude-flow / Ruflo skill library the classic repository once vendored was removed in 2026-08. That upstream is a command-line ecosystem rather than a skill collection, so the supported path is its own installer, opt-in, outside meta-os. The history is in [PROVENANCE.md](../PROVENANCE.md).

## Skill learnings — the improvement loop

Skills self-improve structurally, not by memory: each skill in active use gets **one standing skill-learnings note** in the *instance* (`memory/wiki/skills/<skill>-learnings.md`, from `templates/skill-learnings.md`). Per-run skill-notes (`templates/skill-note.md`) feed it; when a learning generalizes beyond the instance, fold it into the skill's `SKILL.md` in the plugin's repository, by pull request, via [skill-builder](../skills/skill-builder/SKILL.md), and remove it from the note. Learnings never live in the plugin: they are instance experience, and the plugin stays public-safe.

**For a skill that came from a pack, the fold-back goes to the pack's repository, not here:** change it upstream, then take it with `claude plugin update <pack>@<marketplace>`. Editing the installed copy in Claude Code's plugin folder is lost at the next update. The full loop — including how to tell a *method* change from one that is really a config knob, a profile, or a new skill — is in [packs](packs.md), "Evolving a discipline".

## Adding a skill to the plugin

1. Build it with [skill-builder](../skills/skill-builder/SKILL.md).
2. Put the authoritative version in `plugin/skills/<name>/SKILL.md` of the plugin's repository.
3. Add it to the core table above **and** a row in [PROVENANCE.md](../PROVENANCE.md) with its origin and licence, in the same commit — no skill enters the plugin without a recorded origin.
4. Discovery needs nothing more: Claude Code lists every skill of an enabled plugin. A skill that belongs to one instance only goes in that instance's `.claude/skills/<name>/` instead.
