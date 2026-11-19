---
type: system
tags: [os, system, distribution, packs]
---
# Skill Packs

The plugin stays **generic by construction**: it ships only the skills that are part of the OS itself (setting up an instance, authoring skills and packs, the graph, the engine surface). Everything that encodes *a* process rather than *the* OS, such as an agile method, a discipline or a third-party skill collection, is a **pack**: a Claude Code plugin of its own, which the user chooses and installs.

Packs are also how the OS stays **domain-agnostic**: a software-delivery estate installs the agile pack, a research instance might install a literature-review pack, a systems-engineering instance a requirements and trade-study pack. The core is the same and the opinions differ. Zero packs is a fully supported install, and the meta-os plugin declares no dependency on any pack.

For *what* makes a good pack and *where* the strategic opportunity is (codified disciplines beyond software), see [pack-strategy](pack-strategy.md). To *author* one, use the [pack-builder](../skills/pack-builder/SKILL.md) skill. How the plugin itself reaches an instance is in [distribution](distribution.md).

## Vocabulary — pack, discipline, plugin name

One thing, two names: **pack** is the *mechanism* (a plugin that carries skills) and **discipline** is what a good one *contains* (a method + a rigor standard + portability — [pack-strategy](pack-strategy.md)). A pack has **one name**, the same everywhere: its Claude Code plugin name, `pack.yaml` `name:`, `depends:`, the key in an instance's `.packs.yaml` and the key in [packs.yaml](packs.yaml). For a first-party discipline that name is `meta-discipline-<x>`, the name of its directory in the disciplines repository (`meta-discipline-agile`, `meta-discipline-math`, `meta-discipline-physics`, `meta-discipline-swe`, `meta-discipline-agents`). The authoring skeleton follows the same rule (`pack-builder/resources/discipline-pack/`). Where these docs say *pack*, read *a discipline packaged as a plugin*.

**Renamed keys.** The first-party packs were keyed by a short discipline name before this rule (`agile`, `advanced-math`, `physics`, `software-engineering`, `agents`). [packs.yaml](packs.yaml) keeps each old key in `renamed-from:` so a settings block written under the old key can still be recognised.

## What a discipline adds to a skill

A skill is one codified workflow — a method, executable, discoverable. A discipline is a *set* of them plus the two things that make an agent a practitioner rather than a step-follower, and both are **per-skill**, not pack-level prose:

| | A plain skill | A skill inside a discipline |
|---|---|---|
| **Method** | numbered steps | the same steps, with `config.<knob>` referenced inline where a choice changes the procedure |
| **Standard of rigor** | usually absent | **required** — what "done right" means, stated as rules that *reject* something |
| **Evidence** | free-form output | **a named ledger** with a concrete filled-in example, able to read *fail* |
| **Boundaries** | implicit | the sibling skill it defers to, named in the intro |
| **Portability** | the author's conventions, welded in | method in the pack, choices in the instance (config · profiles · overrides) |

[pack.schema.json](pack.schema.json)'s `per_skill` block is the checkable form of that right-hand column, and `resources/discipline-pack/skills/SKILL.template.md` in [pack-builder](../skills/pack-builder/SKILL.md) is the shape to copy. The rigor standard and the ledger are what [pack-strategy](pack-strategy.md)'s *checkable* test cashes out to: without them a pack is a prompt pile with a manifest.

## What a pack is

A Claude Code plugin, and nothing else: a folder with `.claude-plugin/plugin.json` and `skills/<name>/SKILL.md` folders, published through a marketplace. Its skills are called by the plugin's name (`meta-discipline-agile:agile-process`). A pack MAY also carry `agents/` (agent definitions) and `hooks/`; a pack's hooks are never enabled silently. A first-party pack also carries `pack.yaml`, the manifest of its settings and of what it provides to other packs (see Conformance below).

A skill collection that is not a plugin cannot be installed through meta-os. It is installed from its own marketplace or kept as the instance's own project skills (`.claude/skills/`).

## Installing a pack

The first-party packs are published through the `meta-agentic` marketplace (repository `meta-agentic/meta-disciplines`):

```text
claude plugin marketplace add meta-agentic/meta-disciplines
claude plugin install meta-discipline-agile@meta-agentic --scope local
```

`/meta-os:init` asks which packs the instance wants and at which scope. For each chosen pack it either says the pack is already installed on this machine and only records it, or prints the install line; it installs nothing by itself. The scope is `local` by default (this person, in this folder, written to `.claude/settings.local.json`, not committed); `project` writes the committed `.claude/settings.json` for an instance shared with other people.

## The instance's record — `.packs.yaml`

`.packs.yaml` at the instance root lists the packs the instance chose, each with its plugin id and, under its name, the pack's own settings. A new checkout learns from it what to install. Each person runs the install once per clone; Claude Code does not download a pack for them.

```yaml
packs:
  meta-discipline-agile:
    plugin: meta-discipline-agile@meta-agentic
    config:
      space: acme
```

## The registry — [packs.yaml](packs.yaml)

The short list of packs the plugin knows by name: the plugin id, what each provides, what it depends on, and the keys it used to have. Curation bar for an entry:

- **Provenance named** — `first-party` or `third-party` with the real upstream repository; never a silent fork or vendored copy.
- **License known.**
- **Public-safe** — a pack carries no instance data; the privacy boundary applies to packs exactly as it does to the plugin.

A plugin outside the registry is still usable as a pack: it is recorded in `.packs.yaml` by its plugin id.

## Lifecycle

| Action | How | Effect |
|--------|-----|--------|
| Choose | `/meta-os:init`, or add an entry to `.packs.yaml` | The pack is recorded for the instance |
| Install | `claude plugin install <pack>@<marketplace> --scope <local or project>` | The pack's skills appear in the next session |
| Update | `claude plugin update <pack>@<marketplace>` | The installed version moves; it takes effect in the next session |
| Remove | `claude plugin uninstall <pack>@<marketplace>`, then delete its `.packs.yaml` entry | The pack's skills are gone; its settings go with the entry |

A plugin cannot be held at a version from inside an instance. An estate that needs a hard pin adds the marketplace at a tag.

## Parameterisation — method vs. opinion

A pack that hardcodes its author's conventions just relocates opinion; the contract is that packs separate three things:

1. **Method (invariant)** — what the pack *is*: the ceremony structure, the lane model, the review discipline. Lives in the pack's skills, versioned with the pack.
2. **Parameters (chosen per instance)** — names, trackers, cadences, repos. A pack documents its knobs in its README; the instance sets them in `.packs.yaml` under the pack's `config:` block (it's the one desired-state file packs already own):

   ```yaml
   packs:
     meta-discipline-agile:
       config:
         space: acme
         tracker: jira          # jira | local | none
         mirror-repo: you/scrum-mirror
   ```

   Skills read config-first and fall back to their documented defaults; placeholders in a pack's docs (`<SPACE>`-style) name the keys that resolve from this block.
3. **Conventions (overridable)** — branch rules, DoR lists, commit formats. Packs ship them as *data* (files the skills read) with instance-side overrides winning, additive merge — the same template-chain semantics the OS uses elsewhere. Hooks remain opt-in per hook, always, regardless of configuration.

Packs MAY ship **profiles** — named convention bundles (e.g. a Scrum-with-tracker profile vs. a lightweight Kanban profile) selected via `config: profile: <name>` — so "choose a methodology" is a one-line decision, and "change it" is an edit to instance data, never a fork of the pack.

## Conformance — the manifest contract

[pack.schema.json](pack.schema.json) is the machine-readable contract for a pack's `pack.yaml`: required keys, the `config` key shape (`default` / `one_of` / `doc`), `depends` / `provides`, and — in its `required_files` block — the files a conformant pack ships. [pack-builder](../skills/pack-builder/SKILL.md) carries the matching skeleton at `resources/discipline-pack/`.

The convention is deliberately checkable rather than prose-only, because prose drifts: the structure documented before this contract existed had already fallen behind what the shipped packs carried, and a pack authored from the doc came out wrong. **Validate the manifest, then install it** — reading another pack by eye is how the drift propagates.

**Config keys are written in block form**, one key per block with `default:` / `one_of:` / `doc:` beneath it — *not* as an inline `{ … }` map. `doc:` is required and its prose contains commas, which a comma-split inline map cannot carry, so the inline shape cannot express a conformant key at all. 

Three rules the schema encodes that are easy to get wrong from examples alone:

- **Every skill emits a named ledger** with a filled-in example, and the ledger must be able to say *no* — a rigor standard with no failing reading is decoration.
- **Profiles are optional.** Ship them only for genuine methodology variants; a pack with one mode says so instead of inventing a split to look like its siblings.

### The gate — who actually checks this

The contract above is enforced by a program, on every pull request, in every pack's own repository. That matters more than it sounds: a checklist applied once by a reviewer at merge time establishes conformance for one commit and never again, so a pack drifts and nothing says so.

**One checker, one home.** `validate_pack.py` is the only pack conformance checker in the estate. Today it lives in the classic meta-os repository (`scripts/validate_pack.py`), which pack repositories reach through the reusable workflow below; it moves into this plugin together with the plugin's own Python environment, because it needs two packages outside the standard library. It validates `pack.yaml` against [pack.schema.json](pack.schema.json), applies the `required_files` checklist (including the per-skill shape), validates any `meta-os.config.json`, and runs the **estate-neutral scan** — a pack is published on its own, so it must carry no tracker key, no absolute machine path, and no name of whoever authored it. A pack never vendors a copy of the checker.

**The LICENSE exemption.** A copyright holder's name in `LICENSE` is *not* an instance identifier — that is the ratified reading, and it lives in the checker rather than in a review comment. The gate reads the holder out of the pack's own `LICENSE` and then hunts that exact string through every other file, so the exemption is narrow in both directions: the holder in `LICENSE` passes, the same holder in a skill file fails, and a tracker key inside `LICENSE` fails like anywhere else.

**Adopting it costs one file.** A pack repository adds `.github/workflows/pack-conformance.yml` containing nothing but a call:

```yaml
name: pack conformance
"on":
  pull_request:
  push:
    branches: [main]
jobs:
  conformance:
    uses: meta-agentic/meta-os/.github/workflows/pack-conformance.yml@main
```

Make that job a required check and the pack's acceptance criteria are re-checked on every change. The reusable workflow takes `pack-path` (for a pack that is not at the repository root), `framework-ref` (pin a tag or SHA to decide for yourself when the contract moves), `python-version` and `strict`.

The gate's own fixture packs — one conforming, one deliberately violating — live beside the checker's tests, so a change that weakens the contract fails that build rather than passing quietly.

## Dependencies between packs

Packs reuse each other: the physics pack consumes the math pack's `dimensional-analysis` rather than redefining units, π-groups and uncertainty. That relationship is declared in the depending pack's `pack.yaml` and mirrored in its [packs.yaml](packs.yaml) entry:

```yaml
depends:
  - name: meta-discipline-math
    for: [dimensional-analysis]
    reason: "units homogeneity, Buckingham π, uncertainty propagation — not duplicated here"
```

The dependency's own manifest declares the other side of the contract:

```yaml
provides: [dimensional-analysis, mathematical-rigor]   # the public surface
```

| Concern | Rule | Why |
|---------|------|-----|
| Version | **Names only; no ranges.** | The installed plugin version is the version. A range inside `pack.yaml` would be a second resolver beside Claude Code's. |
| Missing | The depending pack names what is missing and the install line for it. | A pack whose dependency is absent is not degraded, it is broken. |
| Cycles | Rejected at validate time. | Two packs that need each other are one pack. |
| Optional | `optional: true` dependencies are **reported, never installed for the user** — for a skill only reachable under a non-default profile. | Installing for a profile the estate does not use is unrequested surface. |
| Surface | Anything in `for:` must be listed in the dependency's `provides:`. | That list is the dependency's public surface. |

## Evolving a discipline — the improvement loop

The lifecycle table above is the *consumption* side (how an instance takes a new version); this is how the discipline itself gets better. Skills improve **structurally, not by memory** ([the skill catalog](skill-catalog.md)) — a discipline adds one thing to that loop: **the ledger is the evidence stream.** A rigor standard runs keep waiving, or a ledger column that is always empty, is a finding about the discipline, not about the run.

1. **Observe in the instance.** Per-run `templates/skill-note.md` roll into the one standing `templates/skill-learnings.md` note per skill (`memory/wiki/skills/<skill>-learnings.md`). Learnings never live in a pack repo — they are instance experience, and packs are public-safe by construction.
2. **Classify before editing** — which layer is actually wrong decides where the change goes, and getting this wrong is how a pack turns back into one shop's dogma:

   | Symptom | Layer | Where the fix lands |
   |---------|-------|---------------------|
   | Every estate practising this discipline would want it | **method** | edit the skill in the pack |
   | Only this estate wants it | **parameter** | a `config:` knob (or a knob that already exists) |
   | A coherent *other* way to practise the discipline | **profile** | a new `profiles/<name>.md` — never a fork |
   | A distinct method the pack doesn't cover | **scope** | a new skill; re-run the three-part test first |
   | Another pack already codifies it | **dependency** | `depends:` + cite the skill by name, never a second copy |
3. **Change it upstream.** Fold the generalized learning into the pack repo as a reviewed change, then delete it from the instance note. Editing the installed copy in Claude Code's plugin folder is lost at the next update.
4. **Re-verify before publishing.** `pack.yaml` still validates against [pack.schema.json](pack.schema.json); the changed skill still emits its named ledger and can still say *no*; `skills/_index.md` gained its row; the skill was driven once end-to-end in a clean instance ([pack-builder](../skills/pack-builder/SKILL.md) Step 6).
5. **Adopt deliberately.** Instances take the improvement with `claude plugin update <pack>@<marketplace>`. With automatic updates off, which is the default for a marketplace that is not Anthropic's, nothing improves ambiently: the estate chooses when the discipline changes under it.

Retiring or renaming a skill runs the same loop in reverse, and keeps a deprecation row for one minor version naming what supersedes it — another pack may name that skill in `depends[].for`, where a silent disappearance becomes an agent improvising the discipline it was meant to defer to.

## Not packs, still worth knowing

Some widely used resources are not packs and should not be forced into the model: **awesome-lists** (skill *directories*: browse them to find pack candidates), **anthropics/claude-cookbooks** (notebooks and patterns, not skill folders), **modelcontextprotocol/servers** (MCP servers: connect them through the engine's own configuration), **ccusage** (a command-line utility; the dashboard's usage widget covers the same logs natively), and **claude-flow / Ruflo** (a command-line ecosystem with its own installer, `npx @claude-flow/cli@latest init`; install it upstream, opt-in, outside meta-os).

The general rule: **check what a candidate's plugin manifest actually declares before listing it.** A plugin that declares only MCP servers and no skills is not a skill collection.
