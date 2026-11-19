---
type: index
tags: [os, agents]
---
# Agent Roster

Who the OS can spawn and how they coordinate. Agents are the *runtime* of the skill backbone — skills say **what**, agents do **it**.

## Coordination model — SendMessage-first

Named agents message each other directly rather than polling shared state. Spawn a whole team in one message, each knowing who to message next. See the canonical pattern in [agentic-operating-model](agentic-operating-model.md), [swarm-harness](swarm-harness.md), and the agile pack's `meta-discipline-agile:agile-swarm` skill.

```
Lead ←→ architect ←→ coder ←→ tester ←→ reviewer
```

| Pattern | Flow | Use when |
|---------|------|----------|
| Pipeline | A → B → C → D | Sequential dependencies (feature dev) |
| Fan-out | Lead → A,B,C → Lead | Independent parallel work (research) |
| Supervisor | Lead ↔ workers | Ongoing coordination (complex refactor) |

## Standing roles

| Role | Comes from | Used in |
|------|-----------|---------|
| researcher / Explore | built-in | recon, code search |
| architect / system-architect | built-in | design, API contracts |
| coder | built-in | implementation |
| tester | built-in | tests |
| reviewer / code-reviewer | built-in | quality + security gate |
| swarm lead (per lane) | `meta-discipline-agile:agile-swarm` | parallel sprint lanes, worktree-isolated |

The full catalog of installed agent types is large (consensus, github, sparc, flow-nexus families). Register a role here only when it's part of our standing operating model.

## Adding an agent role

Define it where it runs (the instance's `.claude/agents/`, or a plugin's `agents/` folder), then add a row above with a link to the skill or system document that drives it. This roster is a reference document: it is deliberately not in the plugin's `agents/` folder, where every Markdown file is read as an agent definition.
