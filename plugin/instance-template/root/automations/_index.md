---
type: index
tags: [os, automations, layer1]
---
# Automations

The scheduled or triggered half of Layer 1. A skill is invoked on demand; an automation runs itself, on a **schedule** (cron, launchd, a cloud routine) or on an **event** (git hook, session start, file change).

| Automation | Trigger | Cadence | Runs | Status |
|------------|---------|---------|------|--------|
| Instance check | schedule (weekly) | @weekly | `.meta-os/meta-os doctor` — reports what this instance is missing, changes nothing | candidate |

Executions append one JSON line to `automations/runs.jsonl` (`{"automation": "<table name>", "ts": "<ISO-8601>", "outcome": "ok|fail", "note": "…"}`). The log is machine-local and ignored by git.

## Two kinds

- **Local** — cron, git hooks, Claude Code hooks on this machine. A job that needs framework code names `.meta-os/meta-os`, the launcher, and never a path inside the plugin.
- **Remote** — cloud scheduler routines, which survive machine sleep.

## Classifying a workflow

When a workflow becomes a skill, decide: on demand (it stays a skill) or scheduled or triggered (it also gets a row here). Record the trigger, the cadence, what it runs, and its status.
