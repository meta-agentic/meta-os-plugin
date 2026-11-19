# {{instance-name}} — Agentic OS instance

<!-- Written by /meta-os:init on {{initialized}} with the meta-os plugin {{plugin-version}}. This file is yours: fill in "Instance facts" and delete the TODO comments. -->

This repository is a meta-os instance. It holds only its own files; the framework is the meta-os plugin for Claude Code, installed outside this repository and updated as a plugin. The root `CLAUDE.md`, if there is one, is not part of the instance.

```
{{instance-name}}/                 ← open this folder as the Obsidian vault
├── .claude/CLAUDE.md              ← this file, the instance contract
├── .claude/settings.json          ← names the plugin and its marketplace
├── .claude/skills/                ← this instance's own skills
├── _index.md                      ← the vault home
├── projects/                      ← estate registry (repositories, paths)
├── memory/                        ← raw → wiki → output, the knowledge
├── automations/                   ← live routine rows
├── vaults/                        ← symlinks to federated project vaults
├── templates/                     ← note templates (yours since init)
├── meta-os.config.json            ← estate config, hook strictness, acknowledged plugin version
├── .packs.yaml                    ← the packs this instance chose
├── .githooks/  .githooks.d/       ← hook stubs, and this instance's own hooks
└── .meta-os/                      ← the launcher: the only framework code kept here
```

## Instance facts

<!-- TODO: fill these in as the estate grows; delete this comment once populated. -->

- **Estate:** (list the projects, one node each in [[projects/_index|projects/]])
- **Authority order (process and backlog):** (which source wins when two disagree; skip this line without a backlog)
- **Packs:** declared in `.packs.yaml`; each is a Claude Code plugin installed for this project.
- **Updates:** a plugin update. A release that changes the process waits until this instance acknowledges it; the acknowledged version is in `meta-os.config.json`.

## Rules

- `_index.md` discipline: every folder that holds notes has an `_index.md`, kept current when a note is added, moved or removed.
- Memory promotion: a capture lands in `memory/raw/` and is trusted only after it is cleaned, linked and moved to `memory/wiki/`.
- Projects are nodes, not clones. Federated vault notes are edited in their own conventions.
- Outside a Claude Code session, call framework code only through `.meta-os/meta-os`, never by a path inside the plugin's folder: that folder moves at every update.
- This repository holds estate data. Keep it private, and keep its data out of public repositories.
