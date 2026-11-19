---
type: index
tags: [os, systems]
---
# Systems — How the OS Operates

The *how* behind the contract. The instance's contract (`.claude/CLAUDE.md`) states the invariants; these documents hold the procedure. They stay in the plugin: a skill names the one it needs by its path under the plugin's folder, and people read them in the plugin's repository. Load the one you need.

> **Preview.** These documents were carried over from the classic meta-os, where an instance was a clone of the framework. [distribution](distribution.md), [packs](packs.md) and [packs.yaml](packs.yaml) are rewritten for the plugin. The others are as ported: where one names `scripts/…`, `pipeline/…` or `hooks/…`, it describes machinery (the pipeline, the opt-in hooks, the pack checker, the public-repository gate) that reaches the plugin in a later release.

| System | Covers |
|--------|--------|
| [agentic-operating-model](agentic-operating-model.md) | How work flows through the OS: skills → agents → memory; the SendMessage coordination model; when to swarm |
| [engine](engine.md) | Pluggable headless runtimes: Claude is the default adapter; meta-cli fan-out; run artifacts → `memory/raw/` |
| [memory-layer](memory-layer.md) | The `raw → wiki → output` discipline, promotion, and federation with project vaults |
| [config](config.md) | The three config levels (framework schema · instance estate `meta-os.config.json` · deployment) and the `meta-os.` namespace; [meta-os.config.schema.json](meta-os.config.schema.json) is the machine-readable contract |
| [scrum-harness](scrum-harness.md) | The agile process: backlog↔Jira, ceremonies, sprint lifecycle (driven by `meta-discipline-agile:agile-process`) |
| [swarm-harness](swarm-harness.md) | Parallel multi-lane execution model (driven by `meta-discipline-agile:agile-swarm`) |
| [pipeline](pipeline.md) | The swarm as an autonomous closed loop, model and specification in one: one meaning for *lane*; the five stations under one WIP cap, pooling with fairness and the sizing rules; the PO's stories and the envelope; admission and planning; lane and pipe states with their controls; the two usage windows and the lane cap; screens, commands and gauges; the watchdog; the record repository; configuration; the acceptance examples. Numbers marked *(proposal)* until the PO decides |
| [pipeline/](pipeline/_index.md) | The evidence behind it, dated and kept as written: the queueing analysis ([queueing-model.py](pipeline/queueing-model.py) reproduces its tables) and the control spike with its prototype |
| [ontology](ontology.md) | The vault's type system made explicit: note types, tags, relations ([ontology.yaml](ontology.yaml) is the machine-readable contract) |
| [interface-layer](interface-layer.md) | Layer 3 contract: what the dashboard reads, how it triggers runs, ontology-driven rendering |
| [interface-extensions](interface-extensions.md) | Layer 3 roadmap: the common agentic-dashboard widget set evaluated against the contract — verdicts, new read surfaces, phasing |
| [repo-docs](repo-docs.md) | Entry READMEs as a distributed knowledge base: the one-home rule, graduated onboarding structure, one runnable example per procedure, public/private link boundary; decision-record naming, numbering and index |
| [distribution](distribution.md) | How meta-os reaches a machine and an instance: one Claude Code plugin; an instance that holds only its own files, written by `/meta-os:init`; the launcher for everything outside a session; updates as plugin updates; the preview and its marketplace; per-project delivery targets |
| [packs](packs.md) | Skill packs: the plugin stays generic; a domain skill set is a Claude Code plugin the user chooses, recorded in the instance's `.packs.yaml` ([packs.yaml](packs.yaml) lists the ones the plugin knows); the pack and discipline vocabulary and what a discipline adds to a plain skill (rigor standard + ledger); pack conformance and dependencies between packs ([pack.schema.json](pack.schema.json) is the machine-readable manifest contract); the improvement loop by which a discipline evolves |
| [pack-strategy](pack-strategy.md) | The thesis behind packs: a pack = a codified discipline (method + rigor + portability); the evidence-disciplined-work niche the coding-born ecosystem leaves open, and why meta-os is built to fill it |
| [skill-catalog](skill-catalog.md) | The skills the plugin ships, the ones packs provide, and how a skill is added |
| [agent-roster](agent-roster.md) | Who the OS can spawn and how they coordinate: the SendMessage-first model and the standing roles |
