# Provenance & Attribution

Origin and licence of every skill the plugin ships. The plugin as a whole is MIT ([LICENSE](LICENSE)); third-party-derived content remains under its original MIT copyright, noted below. Carried over from the classic meta-os repository, whose own `PROVENANCE.md` holds the earlier history (the skills removed in 2026-08 and why).

## Skill provenance

| Skill(s) | Origin | License | Notes |
|----------|--------|---------|-------|
| `init` | **Original** — this project | MIT | Written for the plugin; replaces the classic `bootstrap-instance`. No upstream, no third-party copyright notice. |
| `skill-builder` | **Original** — this project | MIT | Written against this framework's own contract: the trigger-not-summary description, progressive disclosure, the catalog and provenance rows a skill is not finished without, when a skill belongs in a pack instead. No upstream text. |
| `pack-builder` | **Original** — this project | MIT | The pack-authoring meta-discipline; written against `systems/packs.md` and `systems/pack-strategy.md` and ships the `resources/discipline-pack/` skeleton. No upstream, no third-party copyright notice. |
| `infoviz` | **Original** — this project; concept attribution only | MIT | Chooses the visual form before anything is drawn. Synthesised from published literature (Kirk; Cleveland & McGill; Munzner; Bertin; the FT *Visual Vocabulary*; Lima), cited in `references/bibliography.md` — no code or text vendored. Complements Anthropic's `dataviz`, which owns palette and chart chrome. |
| `multi-engine` | **Original** — this project; invokes sibling [meta-cli](https://github.com/meta-agentic/meta-cli) | MIT | Standing multi-provider surface; see `systems/engine.md`. |

## Reference documents, scripts and the instance template

`systems/`, `scripts/`, `bin/` and `instance-template/` are **original** to this project (MIT). The three-layer model follows [chaseAI's Agentic OS](https://www.chaseai.io/blog/agentic-os-skill-backbone-not-dashboard) (concept attribution, no code); the memory flow follows Karpathy's `raw → wiki → output` LLM-wiki pattern. The engine contract in `systems/engine.md` names its own prior art.

## Maintenance rules

- **Adding a skill:** record its origin and licence here in the same commit. No skill enters `skills/` without a provenance row.
- **Prefer a pack to a copy.** If a procedure already exists upstream, the answer is a plugin the user installs, not a vendored file: vendoring buys a maintenance burden and a provenance problem in exchange for a local copy that ages.
- Third-party copyright notices must be preserved in [LICENSE](LICENSE).
