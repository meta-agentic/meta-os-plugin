---
name: init
description: First-run setup of a meta-os instance in the current folder. Opens with a short introduction, then offers a quick start that shows every default on one screen and takes one yes, or a customised setup that asks only what the user wants to change (name, backlog, memory layout, first project, packs, scope). Writes the instance from the plugin's template with `meta-os init`, which never overwrites an existing file and never touches the root CLAUDE.md. Use once per new instance, in an empty folder or an existing project.
disable-model-invocation: true
---

# Init — make this folder a meta-os instance

An instance is a git repository that holds only its own files: its contract (`.claude/CLAUDE.md`), `_index.md`, `projects/`, `memory/`, `automations/`, `vaults/`, `templates/`, `meta-os.config.json`, `.packs.yaml` and a small launcher folder, `.meta-os/`. The framework stays in this plugin.

The `meta-os` command writes everything and decides nothing by conversation. This skill holds the conversation: it introduces, shows the command's plan, takes the answers and passes them as flags. Do not write instance files by hand.

If `meta-os` is not found by its bare name, call it as `"${CLAUDE_PLUGIN_ROOT}/bin/meta-os"`.

**Keep it short.** One introduction, one screen, one yes. Never confirm the same thing twice, never ask a question whose answer is already a default the user accepted, and never show a question with more than four choices.

## Step 1 — Introduce, before any question

Say this, in your own words and no longer:

- **What meta-os is.** An operating layer for Claude Code and Obsidian: this folder becomes a repository of your own notes, project registry and memory (captures become refined notes, refined notes become deliverables), and the framework itself (skills, the `meta-os` command) stays in the plugin and updates as a plugin.
- **What init asks and how long it takes.** A quick start needs one yes and takes under a minute. Customising asks only about what you choose to change, out of six settings (name, backlog, memory layout, first project, packs, scope), and takes two or three minutes.
- **What it writes and what it never touches.** It writes about forty small files, all new: the folders above, the config and the launcher. It never overwrites, changes or appends to an existing file, and it never reads or writes a `CLAUDE.md` at the root of the folder.

## Step 2 — Look, then show the plan

1. Run `meta-os doctor`. If it reports a healthy instance, say so and stop: there is nothing to initialise. If the folder already holds a `meta-os.config.json`, it is an instance with something missing: show the doctor's problems and say that `init` adds what is missing and keeps every existing file.
2. Run `meta-os init --plan`. It writes nothing. It prints one screen: the six settings, each marked where it is the default (the name from the folder, no backlog, the default memory layout, no project, no packs, local scope), how many files it would write and where, which existing files it keeps, and the command that writes it. If it refuses the folder's name (a space, for example), ask for a name and run it again with `--name <name>`.
3. Show that screen as it is, then ask **one** question with three choices:
   - **Yes, write it** — the quick start. This yes is the only confirmation: go to Step 4.
   - **Customise** — go to Step 3.
   - **Cancel** — stop; nothing was written.

## Step 3 — Customise: ask only what the user wants to change

First ask which settings to change, as two multi-select questions shown together (a question shows at most four choices): **the instance** — name, backlog, memory layout, first project; and **plugins** — packs, scope. Then ask only about the chosen ones. Everything not chosen keeps the default the plan showed.

- **Name.** Letters, digits, `.`, `_` and `-`.
- **Backlog.** A per-item backlog: one Markdown file per work item in a directory of its own. Ask for its space key (a short name) and its directory. More than one space is allowed.
- **Memory layout.** Put the explanation in the question itself, not only in the choices: notes move through three tiers, `raw` (captures), `wiki` (refined) and `output` (delivered), and a canon root is the one folder that holds them, for example an existing Obsidian vault. The choices: `default`, this instance's own `memory/raw`, `memory/wiki` and `memory/output`; `flat`, one root with `raw/`, `wiki/` and `output/` directly inside; `tier/project`, tier first and then project (`raw/<project>/…`); `project/tier`, project first and then tier (`<project>/raw/…`). For any choice but `default`, ask for the root's path.
- **First project.** The name of the first project to register. One is enough to start.
- **Packs.** Domain skill sets, each a Claude Code plugin from the `meta-agentic` marketplace. Never hide a pack behind the free-text choice: ask two multi-select questions, one for the delivery packs (`meta-discipline-agile`, `meta-discipline-agents`, `meta-discipline-swe`) and one for the science packs (`meta-discipline-math`, `meta-discipline-physics`). Suggest the agile pack when the user chose a backlog. Say in the question that a pack already installed on this machine is only recorded for this instance: nothing is installed again.
- **Scope.** Where the plugin and the packs are enabled. `local`: for this person, in this folder only, written to `.claude/settings.local.json`, which is not committed. `project`: for everyone who clones the instance, written to `.claude/settings.json`, which is committed. Recommend `local` unless the instance is shared with other people.

Then run the plan again with the answers as flags and show the new screen:

```
meta-os init --plan [--name <name>] [--backlog <space>=<directory>]... [--memory-layout <layout>] [--project <name>]... [--pack <plugin name>]... [--scope local|project]
```

Ask once: **Yes, write it**, **Change something else**, or **Cancel**. Showing the plan and the yes to write it are one confirmation, not two.

## Step 4 — Write

1. Run the command the plan printed after "To write it:", unchanged.
2. Report in two or three lines, not file by file: how many files were created and how many were kept. A `kept` line means the file existed and was left alone. When `init` says some answers must be applied by hand, show which file and what to add; change such a file only after the user agrees.
3. For each chosen pack, `init` prints one of two lines. "Already installed …; recorded in .packs.yaml only" means the pack is on this machine already: nothing is installed again; say exactly that. "Not installed. To install it, run: …" gives the command for the chosen scope. Show the commands together and run them after one yes for all of them. Never enable a pack's hooks silently.
4. Run `meta-os doctor`. It must end with `Healthy.`; fix what it names otherwise.

## Step 5 — Wrap up, without a string of questions

Close with one short message: what now exists, and the next steps as a list the user can take or leave. Do not ask about each one, and do none of them without being asked:

- `git init`, if the folder is not a git repository yet.
- `git config core.hooksPath .githooks`, to turn the instance's git hooks on for this clone; they are off until someone runs it.
- The first commit. The repository holds estate data and should be private.
- If a project was registered: filling its node `projects/<name>.md` and its row in `projects/_index.md` from what is really there (the stack from the project's own files, `repo:` from `git -C <path> remote get-url origin`), and the "Instance facts" of `.claude/CLAUDE.md`. Never guess.

## Principles

- **Introduce first, then one screen, then one yes.** Every further question is one the user asked for by choosing to customise.
- **The decisions are the user's.** A default is shown, never applied silently: the plan screen is where the user sees all of them.
- **Read reality before writing it.** Stack and remote come from disk, never from a guess.
- **Existing files win.** If something is already there, `init` keeps it and says so.
