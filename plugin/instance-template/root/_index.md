---
type: index
tags: [os, home, moc]
---
# {{instance-name}} — Agentic OS Home

The map of content for this instance. This vault is the layer above every project. The instance contract is `.claude/CLAUDE.md`; the framework (skills, hooks, the `meta-os` command) is the meta-os plugin for Claude Code and is not in this repository.

## The three layers

> **Skill backbone, not dashboard.** Value is bottom-up: skills → memory → interface.

- **Layer 1 — Skills and automation** → the plugin's skills (`/meta-os:…`), this instance's own in `.claude/skills/`, and [[automations/_index|automations/]]
- **Layer 2 — Memory** → [[memory/_index|memory/]] (`raw → wiki → output`)
- **Layer 3 — Interface** → the Obsidian graph (open the graph view)

## Registries

| Registry | What |
|----------|------|
| [[projects/_index\|projects/]] | Every repository this instance covers, as a node: purpose, stack, entry points |
| [[vaults/_index\|vaults/]] | Federated project vaults, symlinked into this graph |
| [[templates/_index\|templates/]] | Note templates, for Obsidian's template picker |

## Quick start

- **Capture something new** → drop it in [[memory/raw/_index|memory/raw/]], promote later
- **Add a project** → copy [[templates/project|the project template]] into [[projects/_index|projects/]]
- **Check the instance** → `meta-os doctor` in a Claude Code session, `.meta-os/meta-os doctor` outside one
- **Take a framework update** → update the plugin in Claude Code

## Where things go

- A repeated workflow → a **skill** in `.claude/skills/`
- A scheduled or triggered routine → an **automation** ([[automations/_index]])
- A capture, note, or Claude output → **memory/raw**, promoted to **memory/wiki**
- A finished artifact → **memory/output**
- A new repository → a node in **projects/**
