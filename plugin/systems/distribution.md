---
type: system
tags: [os, system, distribution]
---
# Distribution — one plugin, and an instance that holds only its own files

How meta-os reaches a machine, how a folder becomes an instance, and how both stay current. The classic model, where an instance was a clone of the framework and took updates by merge, is described in the classic repository and is not carried here.

## The invariant

| | The plugin | An instance |
|---|---|---|
| What | The framework: skills, the `meta-os` command, the reference documents in `systems/`, the instance template | A git repository of your own files: `.claude/CLAUDE.md`, `_index.md`, `projects/`, `memory/`, `automations/`, `vaults/`, `templates/`, `meta-os.config.json`, `.packs.yaml` and the launcher folder `.meta-os/` |
| Where | Claude Code's plugin folder on the machine; it changes at every update | Wherever you keep it; private, because it holds estate data |
| Who writes it | A release of the plugin | You, and `init` once |
| Public-safe | Always: it carries no instance data | Not required |

Two rules follow. **The only framework code inside an instance is `.meta-os/`**: a launcher, a resolver and the body of the git hooks, small enough to read. **Nothing outside a session names a path inside the plugin**: git hooks, scheduled jobs and continuous integration call `.meta-os/meta-os`, which finds the installed plugin, or the folder named by `META_OS_PLUGIN_ROOT`.

## First run

1. Install the plugin (the install lines are in the repository's README).
2. In an empty folder or an existing project, run `/meta-os:init`. It introduces itself, shows every default on one screen and writes the instance after one yes; "customise" changes only what you choose.
3. `meta-os doctor` checks the result and names what is missing.

`init` never overwrites, changes or appends to an existing file, and never reads or writes a root `CLAUDE.md`: the instance contract is `.claude/CLAUDE.md`. Run again, it adds only what is missing.

## A second checkout of an instance

Clone the instance, install the plugin once on that machine, and run `meta-os doctor`. With `project` scope the committed `.claude/settings.json` names the plugin and its marketplace; with `local` scope (the default) the new checkout learns what it needs from `meta-os.config.json` and `.packs.yaml`. Each person runs the install once per clone; Claude Code does not download a plugin for them. Git hooks are off until the clone runs `git config core.hooksPath .githooks`.

## Updating

A release reaches a machine with `claude plugin update meta-os@<marketplace>` and takes effect in the next session. Nothing is merged and no instance file changes. Three consequences:

- **Templates are the instance's own.** `init` copies the note templates into `templates/`, where Obsidian's template picker reads them. A template the plugin improves later does not reach a running instance by itself.
- **The launcher is refreshed on request.** `meta-os init --refresh-launcher` rewrites `.meta-os/` from the installed plugin and touches nothing else.
- **The instance acknowledges a version.** `meta-os.config.json` records the plugin version the instance was set up with (`acknowledgedPluginVersion`); a release that changes the process waits for that acknowledgement.

Automatic updates are off by default, as for any marketplace that is not Anthropic's.

## Reference documents stay in the plugin

The `systems/` documents, the skill catalog and the agent roster are not copied into the vault. A skill names the one it needs by its path under the plugin's folder; people read them in the plugin's repository. An instance note with a wikilink into `systems/` therefore shows as unresolved in Obsidian, and the Obsidian graph does not show the framework's documents.

## Packs

A pack is a Claude Code plugin the user chooses, never a dependency of this plugin. `init` records the chosen packs in `.packs.yaml` and prints the install line for each one that is not on the machine yet. See [packs](packs.md).

## The preview and its marketplace

The plugin is a 0.x preview. Until it is listed in the `meta-agentic` marketplace it is installed from the marketplace file inside its build repository. Every release is made by one workflow, which validates the plugin, writes the version into the manifest and tags `meta-os--v<version>`; no release is assembled by hand.

## Where deliverables land (per project)

Default: finished work is filed to the instance's `memory/output/`, namespaced by project when volume warrants (`memory/output/<project>/`). A project that delivers somewhere else — an existing repo, a new empty one, a docs site — declares it in its registry node: the `output:` front-matter field ([ontology.yaml](ontology.yaml) `project` type) holds a repo (`org/repo` or URL) or a path. The delivering skill reads the field and lands results there; the dashboard's registry and output-inbox widgets surface it so the answer to "where does this project deliver?" is always one glance away. `output:` names the *destination*, not a promise — an empty referenced repo is fine; it fills as the project ships.

## Not designed yet

The container layout (an image that installs the plugin, or mounts a checkout and sets `META_OS_PLUGIN_ROOT`), where the config schema is published so `$schema` resolves, and how a running pipeline takes a new version.
