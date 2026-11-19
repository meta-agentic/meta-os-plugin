#!/usr/bin/env python3
"""Find the installed meta-os plugin from outside a Claude Code session, and read hook strictness.

    resolver.py root      prints "<plugin folder>\t<version>"; exit 3 when no plugin is found
    resolver.py strict    prints 1 when a hook must refuse without the plugin, else 0

The plugin folder is looked for, in order, in META_OS_PLUGIN_ROOT (continuous integration and
containers), then in Claude Code's install record, where an install for this project wins over
a user-wide one. Run from the instance's root folder. Standard library only, Python 3.9 or later.

This file is framework code kept in the instance: `meta-os doctor` reports a stale copy.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PLUGIN_NAME = "meta-os"
MANIFEST = Path(".claude-plugin") / "plugin.json"
CONFIG = "meta-os.config.json"
NOT_FOUND = 3


def manifest_version(root: Path) -> str | None:
    """The version in a plugin folder's manifest; None when the folder is not this plugin."""
    try:
        data = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("name") != PLUGIN_NAME:
        return None
    return str(data.get("version", "?"))


def record_path() -> Path:
    base = os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
    return Path(base) / "plugins" / "installed_plugins.json"


def installs(name: str, project: Path) -> list[dict]:
    """Installs of plugin `name` that apply to `project`: this project's first, then the user's.

    Each is {"id", "scope", "root", "version"}. An unreadable record is an empty list.
    """
    try:
        plugins = json.loads(record_path().read_text(encoding="utf-8"))["plugins"]
        items = sorted(plugins.items())
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return []
    ranked = []
    for plugin_id, entries in items:
        if plugin_id.split("@", 1)[0] != name or not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("installPath"), str):
                continue
            at = entry.get("projectPath")
            if at is None:
                rank = 1
            elif isinstance(at, str) and Path(at).resolve() == project:
                rank = 0
            else:
                continue
            ranked.append((rank, {
                "id": plugin_id,
                "scope": "project" if rank == 0 else "user",
                "root": entry["installPath"],
                "version": str(entry.get("version", "?")),
            }))
    return [found for _, found in sorted(ranked, key=lambda r: r[0])]


def resolve(project: Path) -> tuple[Path, str] | None:
    """(plugin folder, version) for `project`, or None."""
    explicit = os.environ.get("META_OS_PLUGIN_ROOT")
    if explicit:
        version = manifest_version(Path(explicit))
        return (Path(explicit), version) if version is not None else None
    for found in installs(PLUGIN_NAME, project):
        if manifest_version(Path(found["root"])) is not None:
            return Path(found["root"]), found["version"]
    return None


def strict(project: Path) -> bool:
    """Whether a git hook refuses when the plugin is missing.

    The instance decides (`hooks.strict` in its config, committed); META_OS_HOOK_STRICT=1 makes
    one machine stricter and nothing makes it weaker. A config that cannot be read is strict.
    """
    if os.environ.get("META_OS_HOOK_STRICT") == "1":
        return True
    try:
        value = json.loads((project / CONFIG).read_text(encoding="utf-8"))["hooks"]["strict"]
    except (OSError, ValueError, KeyError, TypeError):
        return True
    return value is not False


def main(argv: list[str]) -> int:
    project = Path.cwd().resolve()
    if argv == ["root"]:
        found = resolve(project)
        if found is None:
            return NOT_FOUND
        print(f"{found[0]}\t{found[1]}")
        return 0
    if argv == ["strict"]:
        print("1" if strict(project) else "0")
        return 0
    print("usage: resolver.py root|strict", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
