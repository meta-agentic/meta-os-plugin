# meta-os-plugin

[![CI](https://github.com/meta-agentic/meta-os-plugin/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/meta-agentic/meta-os-plugin/actions/workflows/ci.yml) [![plugin version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fmeta-agentic%2Fmeta-os-plugin%2Fmain%2Fplugin%2F.claude-plugin%2Fplugin.json&query=%24.version&label=plugin&color=blue)](plugin/.claude-plugin/plugin.json) [![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-D97757)](https://code.claude.com/docs/en/plugins) [![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-3776AB)](README.md#try-it) [![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

meta-os is an agentic operating layer for [Claude Code](https://code.claude.com) and Obsidian. An instance is a git repository of your own files only: a project registry, a memory that flows `raw → wiki → output`, automations, note templates and one small config. The framework (skills, the `meta-os` command, later hooks and the pipeline) is delivered as one Claude Code plugin and updated as a plugin, with no merge. This repository builds that plugin: what ships is the `plugin/` folder, and everything else here is tests, continuous integration and development files. It is licensed under MIT.

> **Preview 0.2.** The plugin is a 0.x preview: it works, it is incomplete, and it may change between releases. It carries `/meta-os:init`, `meta-os doctor`, five more skills and the reference documents; the session-start contract, the hooks and the pipeline are not in it yet. Until it is listed in the `meta-agentic` marketplace it is installed from the marketplace file inside this repository, with the lines below; once listed, the plugin is `meta-os@meta-agentic`. The classic meta-os, where an instance is a clone of the framework, is at [meta-agentic/meta-os](https://github.com/meta-agentic/meta-os) and stays as it is until this plugin replaces it.

## Try it

You need Claude Code, git and Python 3.9 or later.

1. Add this repository's marketplace and install the plugin:

   ```
   claude plugin marketplace add meta-agentic/meta-os-plugin
   claude plugin install meta-os@meta-os-preview
   ```

2. Open Claude Code in an empty folder, or in an existing project, and run:

   ```
   /meta-os:init
   ```

`init` introduces itself, shows every default on one screen (the name from the folder, no backlog, the default memory layout, no packs, local scope) and writes the instance after one yes. "Customise" asks only about what you choose to change. It never overwrites an existing file and never touches a root `CLAUDE.md`: the instance contract is `.claude/CLAUDE.md`.

To take a newer release, update the plugin; it takes effect in the next session:

```
claude plugin marketplace update meta-os-preview
claude plugin update meta-os@meta-os-preview
```

## What you get

| Command | What it does |
|---------|--------------|
| `/meta-os:init` | The first-run setup: a short introduction, a quick start with one yes, or a customised setup; writes the instance from the plugin's template. |
| `/meta-os:infoviz` | Chooses the visual form for data before anything is drawn. |
| `/meta-os:multi-engine` | Fans a prompt out to several headless engines through meta-cli and collects the results into `memory/raw/`. |
| `/meta-os:skill-builder` | Authors or revises one skill. |
| `/meta-os:pack-builder` | Authors a pack: a discipline published as a Claude Code plugin. |
| `meta-os doctor` | Checks that a folder is a meta-os instance and says what is missing. Exit 0 healthy, 1 not. |
| `meta-os version` | Prints the plugin's version. |
| `.meta-os/meta-os <command>` | The launcher inside an instance, for git hooks, scheduled jobs and continuous integration. It finds the installed plugin, or the folder named by `META_OS_PLUGIN_ROOT`. |

The reference documents (how memory, configuration, packs, the engine layer and distribution work) are in [plugin/systems/](plugin/systems/_index.md). They stay in the plugin and are not copied into an instance. Origins and licences of the skills are in [plugin/PROVENANCE.md](plugin/PROVENANCE.md).

## Development

```
python3 tests/run.py                      # every test; standard library only
claude plugin validate plugin --strict    # the plugin
claude plugin validate . --strict         # the marketplace file
git config core.hooksPath .githooks       # this repository's public-safe gate, per clone
```

The tests run on Python 3.9 and on the newest Python. The layout and the rules are in [CLAUDE.md](CLAUDE.md).

A pull request that changes anything under `plugin/` must raise `version` in `plugin/.claude-plugin/plugin.json` above the last release; the build refuses it otherwise, because `claude plugin update` does nothing when the version did not move. A release is one manual run of the `release` workflow (`gh workflow run release.yml`): it runs every check, then tags `meta-os--v<version>` and pushes the tag.
