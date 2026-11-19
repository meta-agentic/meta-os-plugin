---
name: pack-builder
description: "Author a new meta-os skill pack — a parameterised, curated collection of skills, published as a Claude Code plugin, that codifies a discipline (a method + a rigor standard). Use when creating a pack from scratch, extracting skills from a core into a pack, or turning a domain's practice (research, systems engineering, a regulated field, an engineering branch) into a reusable pack. The mechanism and the thesis are in the plugin's reference documents, which the skill names."
---

# Pack Builder

The meta-discipline: how to turn a body of practice into a **pack** — a Claude Code plugin of skills that any instance can install, which carries its method and takes the estate's choices as config. `/meta-os:skill-builder` authors one skill; this authors the *collection + contract* around a discipline. Read `${CLAUDE_PLUGIN_ROOT}/systems/packs.md` (mechanism) and `${CLAUDE_PLUGIN_ROOT}/systems/pack-strategy.md` (what to build and why) before starting.

## Step 0 — Is it a pack? (the three-part test)

Don't build until the candidate passes all three (`${CLAUDE_PLUGIN_ROOT}/systems/pack-strategy.md`):

1. **Recognizable** — a practitioner would call it "how we actually work."
2. **Portable** — parameterizable to any estate, not welded to one shop.
3. **Checkable** — it produces outputs a reviewer can verify against the discipline's own standard.

A pack is a **codified discipline = method + rigor standard + portability**. If it's only a process (steps, no standard of "done right"), it's under-specified — add the rigor. If it's only one estate's config, it's not a pack — it's instance data.

## Step 1 — Scope & name

- Name the **discipline**, not a tool (`research`, `systems-engineering`, `quant-rigor` — not `zotero-helper`). One discipline per pack; one **provenance** per pack (don't mix first-party and vendored — see the curation bar).
- List the skills. Each is a distinct *method or judgment* within the discipline. Keep the pack lean; a skill that isn't recognizable/checkable is a candidate to cut.

## Step 2 — Structure

A pack is a Claude Code plugin (`${CLAUDE_PLUGIN_ROOT}/systems/packs.md`, "What a pack is"). **Start from the skeleton in `${CLAUDE_PLUGIN_ROOT}/skills/pack-builder/resources/discipline-pack/`**, not from memory — it is the shape the shipped first-party packs carry:

```
<pack>/
├── .claude-plugin/plugin.json   ← REQUIRED: the plugin manifest (name, version, description).
│                                  The skeleton carries it as `plugin.json.template`
├── skills/_index.md             ← REQUIRED: the folder's contents —
│                                  Skill | Discipline | Checkable output, one row each
├── skills/<skill>/SKILL.md      ← the discipline's methods & judgments
├── pack.yaml                    ← manifest + config schema; validate against
│                                  ${CLAUDE_PLUGIN_ROOT}/systems/pack.schema.json
├── config.example.yaml          ← the block a user copies into .packs.yaml
├── profiles/<name>.md           ← named rigor bundles — ONLY if the discipline has
│                                  genuine variants; never invent a split to look complete
├── README.md                    ← skills table, the three-part test, configure, install
├── PROVENANCE.md                ← REQUIRED: per-skill origin table, the public-safe
│                                  statement, and why THIS coverage was chosen
├── .gitignore                     (the skeleton carries it as `gitignore`)
└── LICENSE
```

Copy the skeleton, rename `plugin.json.template` to `.claude-plugin/plugin.json` and `gitignore` to `.gitignore`, and fill every `<placeholder>`. Author each skill with `/meta-os:skill-builder`. A pack MAY also carry `agents/` (agent definitions) and `hooks/`; a pack's hooks are never enabled silently.

**Every skill takes the same five-part shape** — see `resources/discipline-pack/skills/SKILL.template.md`: intro (what a practitioner does, and the boundary with sibling skills) → **Method** (numbered steps, config knobs referenced inline) → **The rigor standard** (what to reject) → **Checkable output** → **Anti-patterns**. Target 80–120 lines.

> **The ledger is the load-bearing part.** "Checkable output" means a **named ledger with a concrete, filled-in example** — an estimation ledger, a claims ledger, a generation-constraint ledger. It is what turns the rigor standard from an assertion into something a reviewer can audit, and it must be able to *fail*: name the reading that is a rejection, not only the one that passes. A skill with no ledger has not passed Step 0's checkable test.

## Step 3 — Parameterise (method vs. opinion)

The rule that keeps a pack from being one shop's dogma (`${CLAUDE_PLUGIN_ROOT}/systems/packs.md`, "Parameterisation"):

- **Method** stays in the pack's skills — invariant.
- **Parameters** (names, trackers, cadences) resolve from the instance's `.packs.yaml` `config:` block. Declare them in `pack.yaml` with defaults + `one_of` enums (pipe- separated, comma-free). Skills read config-first and fall back to the defaults `pack.yaml` documents.
- **Conventions** (rules, checklists, formats) ship as data the skills read, with instance overrides winning.
- **Profiles** — if the discipline has genuinely different modes (e.g. the agile pack's `scrum` vs `kanban`), ship each as `profiles/<name>.md` selected by `config: profile:`. "Choose the methodology" becomes one line; "change it" is an edit to instance data, never a fork.

## Step 4 — Declare dependencies (don't duplicate a sibling pack)

When a skill you are about to write already exists in another pack, **depend on it instead of re-deriving it** — a second copy of a discipline diverges, and the divergence is silent. Declare it in `pack.yaml` and say why:

```yaml
depends:
  - name: <other-pack>
    for: [<skill-it-consumes>]     # the names this pack actually calls
    reason: "<what would otherwise be duplicated>"
```

Then cite that skill by its plugin name (`<other-pack>:<skill>`) from the skills that use it, and add the **Dependency** section to `PROVENANCE.md` and `README.md`.

Rules (`${CLAUDE_PLUGIN_ROOT}/systems/packs.md`, "Dependencies between packs"):

- **Names, not version ranges.** The installed plugin version is the version. A range in `pack.yaml` would be a second resolver beside Claude Code's.
- **Anything in `for:` must be listed in the dependency's `provides:`** — that is the dependency's public surface.
- **Depend on packs, not on instances.** If the thing you need is an estate's convention rather than a discipline, it is config — go back to Step 3.

## Step 5 — Provenance & curation

- **First-party** — author it; MIT; a `PROVENANCE`-style note in the README. **Vendored / third-party** — record the real upstream and license; never a silent fork.
- The pack must be **public-safe**: no instance data, ever (the same boundary as the plugin — `${CLAUDE_PLUGIN_ROOT}/systems/distribution.md`).
- To list it among the packs the OS knows by name (`${CLAUDE_PLUGIN_ROOT}/systems/packs.yaml`, changed by pull request to the plugin's repository), meet the bar: provenance named, license known, public-safe.

## Step 6 — Verify

Check the pack against the contract, then install it into a **clean instance** and prove it works before publishing:

- **Plugin validation** — `claude plugin validate <pack-dir> --strict`. It checks the plugin manifest and every skill's front matter.
- **Conformance** — the pack's own repository runs the reusable pack-conformance workflow on every pull request (`${CLAUDE_PLUGIN_ROOT}/systems/packs.md`, "The gate"). It applies both halves of the contract: `pack.yaml` against `${CLAUDE_PLUGIN_ROOT}/systems/pack.schema.json`, and that schema's `required_files` checklist — every required file present, a `profiles/<name>.md` per declared profile, and each skill carrying the front matter and `##` sections the checklist names. The checker needs two Python packages outside the standard library, so it is not run from this plugin yet; until it is, read the pack against the schema's checklist by hand before opening the pull request.
- **Install** — add the pack's marketplace (a local folder works: `claude plugin marketplace add <path>`), then `claude plugin install <pack>@<marketplace> --scope local` in a scratch instance made with `/meta-os:init`. The pack's skills must appear under the pack's name in the next session.
- **Settings** — copy `config.example.yaml` under the pack's name in the scratch instance's `.packs.yaml`; check that a skill reads a changed value and that a non-default profile resolves.
- Exercise one skill end-to-end against a real input; confirm its output is *checkable* against the discipline's standard (Step 0.3). If it isn't, the rigor standard is missing — go back to Step 1.

## Step 7 — Evolve it (a discipline is never finished)

Publishing is not the end state: a discipline earns its rigor standard by surviving contact with real work. The loop — observe in the instance → classify (method · parameter · profile · scope · dependency) → change upstream → re-verify → release, and let instances update — is `${CLAUDE_PLUGIN_ROOT}/systems/packs.md`, "Evolving a discipline". Three authoring rules it implies:

- **The ledger is the feedback channel.** A standard that runs keep waiving, or a ledger field nobody ever fills, is evidence about the *discipline*, not the run — tighten it, cut it, or move it behind a profile.
- **Improvements land in the pack's repository, never in an installed copy** — Claude Code replaces that folder at the next update. If the change only makes sense for one estate, it was config (Step 3), not method.
- **Adding a skill re-runs Step 0.** A pack grows by passing the three-part test again, not by accretion; retiring one keeps a deprecation row for a minor version, because another pack may name it in `depends[].for`.

## Principles

- **Discipline, not dump.** A pack makes an agent behave like a competent practitioner — method *and* rigor, not a prompt pile.
- **Method in the pack, choices in the instance.** If changing a convention means editing the pack, you've hardcoded an opinion — move it to config/profiles.
- **One discipline, one provenance, public-safe.** Clean packs compose; muddy ones rot.
- **Prove it by installing it.** A pack that has not been installed into a clean instance and driven once is unverified.
