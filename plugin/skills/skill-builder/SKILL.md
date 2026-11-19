---
name: skill-builder
description: "Use when authoring, splitting, or revising a skill — writing a new SKILL.md, deciding whether something should be a skill at all, fixing a skill that never triggers, or folding a learning back into one. Covers the frontmatter contract, progressive disclosure, where a skill is allowed to live, and the registration a skill is not finished without. For a whole collection that codifies a discipline, this hands off to pack-builder."
---

# Skill Builder

A skill is a procedure the OS can load on demand instead of re-deriving. Authoring one is mostly deciding **when it should load** and **what belongs in the file at all** — the prose is the easy part. This skill owns one skill; `/meta-os:pack-builder` owns the collection and the contract around a discipline.

## Method

1. **Check it should exist.** If you have done it more than once, it is a skill. If you have done it once, it is a note. If it encodes *a* process or domain rather than *the* OS, it belongs in a pack, not in the meta-os plugin — the core stays generic by construction (`${CLAUDE_PLUGIN_ROOT}/systems/packs.md`).
2. **Name it for the job, lowercase-kebab, matching its folder.** A skill has one home and never a second copy: `plugin/skills/<name>/SKILL.md` in the plugin's repository for a skill of the OS itself (called as `/meta-os:<name>`), `skills/<name>/SKILL.md` in its pack's repository for a pack skill, and `.claude/skills/<name>/SKILL.md` in the instance for a skill that belongs to one estate only.
3. **Write the description as a trigger, not a summary.** It is the only thing an agent reads when deciding whether to load the file, so it states *when* to use the skill and *what* it does, with the words a user would actually type front-loaded. Name the sibling skill it defers to and the boundary between them; a description that could match three skills routes to none of them reliably.
4. **Keep `SKILL.md` to the procedure.** Target 80–120 lines. Anything a reader needs only sometimes — command catalogues, worked examples, tables, background — goes in `references/<topic>.md`, cited from the procedure. Progressive disclosure is a token budget, not a filing preference: everything in `SKILL.md` is paid for on every load.
5. **Register it, in the same commit.** For a plugin skill: a row in the skill catalog (`${CLAUDE_PLUGIN_ROOT}/systems/skill-catalog.md` shows the shape) and a provenance row (`${CLAUDE_PLUGIN_ROOT}/PROVENANCE.md`) with origin and licence, both edited in the plugin's repository, never in the installed copy. A pack skill gets the same two rows in its pack. A skill nobody can find is not shipped, and no skill is admitted without a recorded origin.

## The rigor standard

- **The trigger is the contract.** A skill that never fires is worse than no skill: the procedure exists, is unused, and drifts. If it does not trigger in practice, the description is wrong — fix that before touching the body.
- **One skill, one job.** When a skill grows a second audience or a second trigger, split it. Two procedures sharing a file means both load whenever either is needed.
- **Cite, never restate, a sibling.** A second copy of a procedure diverges silently. Link it.
- **Instance data never enters a skill here.** Repo names, trackers, paths and business context belong to the instance; a skill carries the method and takes the estate's choices as documented placeholders.
- **A skill inside a discipline owes more** — a rigor standard and a named ledger that can read *reject*, in the five-part shape `${CLAUDE_PLUGIN_ROOT}/systems/pack.schema.json` encodes. Use `/meta-os:pack-builder`'s template for those rather than this procedure.
- **Third-party skills are installed, not copied.** If the procedure already exists upstream, the answer is a plugin the user installs (the packs the OS knows are in `${CLAUDE_PLUGIN_ROOT}/systems/packs.yaml`) — vendoring it here buys a maintenance burden and a provenance problem in exchange for nothing.

## Checkable output

A **skill review record** — five lines per skill, filled before it ships. It is the thing a reviewer can hold you to, and it must be able to fail:

```
SKILL       infoviz
TRIGGER     "which chart should I use" · "visualize this network" · "is this the right chart"
            → fires: yes, tested against 3 phrasings a user would actually type
DISCLOSURE  SKILL.md 89 lines · references/ 5 files (chart-selection, design-layers, …)
BOUNDARY    dataviz owns palette and chart chrome; this owns choosing the form  → stated in §1
REGISTERED  catalog row ✓   PROVENANCE row ✓   origin: original, MIT
VERDICT     ok

SKILL       hooks-automation
TRIGGER     "hooks", "automate coordination" → fires: yes
DISCLOSURE  SKILL.md 1201 lines · references/ none
BOUNDARY    not stated — overlaps the pack hook policy in systems/packs.md
REGISTERED  catalog row ✓   PROVENANCE row ✓   origin: third-party (claude-flow), MIT
VERDICT     REJECT — 1201 lines of upstream CLI reference in a generic framework: it is a
            third-party tool's documentation, so it is a pack of its own or nothing
```

Ship only when every line reads. A row is a **rejection** when the trigger has not been tried, when `SKILL.md` carries reference material that only some readers need, when the boundary with a sibling is unstated, or when the origin is third-party and the answer should have been a pack.

## Anti-patterns

- **A description that summarises instead of triggering.** "Helps with data visualization" matches everything and loads for nothing.
- **The 900-line SKILL.md.** Every reader pays for the command catalogue nobody reads; that is what `references/` is for.
- **Vendoring a third-party skill** to have it locally. It ages, its provenance blurs, and the upstream fix never arrives — install it as a plugin instead.
- **Writing the skill before the second occurrence.** One-off procedures become skills that document a path nobody walks again.
- **Shipping without the catalog and provenance rows**, on the grounds that the file exists. It is undiscoverable and, here, contractually not allowed.
- **Folding an instance-specific rule into the method.** If changing your estate's convention means editing the skill, the convention was config.

## Improving a skill after it ships

Skills improve structurally, not by memory. Per-run skill-notes (`templates/skill-note.md` in the instance) roll into one standing skill-learnings note per skill (`templates/skill-learnings.md`) in the *instance*; when a learning generalises beyond that estate, fold it into the skill's `SKILL.md` in the repository that owns it, by pull request, and delete it from the note. For a pack skill that repository is the pack's — the full loop, including how to tell a method change from one that is really config, is in `${CLAUDE_PLUGIN_ROOT}/systems/packs.md`, "Evolving a discipline". Never edit the installed copy in Claude Code's plugin folder: the next update replaces it.
