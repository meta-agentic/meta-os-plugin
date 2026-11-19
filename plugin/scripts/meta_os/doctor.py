"""`meta-os doctor`: is this folder a meta-os instance, and what is it missing?

It only reads. A problem makes the instance unhealthy (exit 1); a note is something worth
knowing that does not (exit 0).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from .init import EXECUTABLE, template_files
from .paths import CONFIG, LAUNCHER_DIR, PLUGIN_NAME, plugin_version, version_tuple

INDEXED_FOLDERS = ("projects", "memory", "memory/raw", "memory/wiki", "memory/output",
                   "automations", "vaults", "templates")
HOOK_STUBS = (".githooks/pre-commit", ".githooks/commit-msg")


class Report:
    def __init__(self) -> None:
        self.problems: list[str] = []
        self.notes: list[str] = []

    def problem(self, text: str) -> None:
        self.problems.append(text)

    def note(self, text: str) -> None:
        self.notes.append(text)


def read_json(path: Path) -> tuple[object, str | None]:
    """(value, None), or (None, why it could not be read)."""
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except OSError:
        return None, "missing"
    except ValueError as exc:
        return None, f"not valid JSON ({exc})"


def check_config(target: Path, report: Report) -> None:
    config, error = read_json(target / CONFIG)
    if error:
        report.problem(f"{CONFIG}: {error}")
        return
    if not isinstance(config, dict):
        report.problem(f"{CONFIG}: must be a JSON object")
        return
    instance = config.get("instance")
    if not isinstance(instance, dict) or not isinstance(instance.get("name"), str) or not instance["name"]:
        report.problem(f"{CONFIG}: instance.name is missing")
    hooks = config.get("hooks")
    if not isinstance(hooks, dict) or not isinstance(hooks.get("strict"), bool):
        report.problem(f"{CONFIG}: hooks.strict must be true or false")
    acknowledged = version_tuple(config.get("acknowledgedPluginVersion"))
    if acknowledged is None:
        report.problem(f"{CONFIG}: acknowledgedPluginVersion must be a version such as {plugin_version()}")
        return
    running = version_tuple(plugin_version())
    if running > acknowledged:
        report.note(f"the plugin is {plugin_version()}; this instance acknowledged "
                    f"{config['acknowledgedPluginVersion']}. The acknowledgement is pending.")
    elif running < acknowledged:
        report.problem(f"the plugin here is {plugin_version()}, older than the version this instance "
                       f"acknowledged ({config['acknowledgedPluginVersion']}): update the plugin")


def check_settings(target: Path, report: Report) -> None:
    """The plugin must be enabled in one of the two settings files `init` can write: the local one
    (this person, this folder, not committed) or the project one (everyone who clones it)."""
    present = [rel for rel in (".claude/settings.local.json", ".claude/settings.json") if (target / rel).exists()]
    if not present:
        report.problem(".claude/settings.local.json or .claude/settings.json: neither exists, so nothing "
                       f"enables the {PLUGIN_NAME} plugin here")
        return
    for rel in present:
        settings, error = read_json(target / rel)
        if error:
            report.problem(f"{rel}: {error}")
            return
        enabled = settings.get("enabledPlugins") if isinstance(settings, dict) else None
        ours = [key for key, on in enabled.items() if key.split("@", 1)[0] == PLUGIN_NAME and on is True] \
            if isinstance(enabled, dict) else []
        if not ours:
            continue
        known = settings.get("extraKnownMarketplaces")
        for key in ours:
            marketplace = key.split("@", 1)[1] if "@" in key else ""
            if not isinstance(known, dict) or marketplace not in known:
                report.problem(f"{rel}: extraKnownMarketplaces does not name the marketplace of {key}")
        return
    report.problem(f"{' and '.join(present)}: enabledPlugins does not name the {PLUGIN_NAME} plugin")


def check_files(target: Path, report: Report) -> None:
    if not (target / ".claude" / "CLAUDE.md").is_file():
        report.problem(".claude/CLAUDE.md: the instance contract is missing")
    if not (target / "_index.md").is_file():
        report.problem("_index.md: the vault home is missing")
    for folder in INDEXED_FOLDERS:
        if not (target / folder).is_dir():
            report.problem(f"{folder}/: missing")
        elif not (target / folder / "_index.md").is_file():
            report.problem(f"{folder}/_index.md: missing")
    if not (target / ".packs.yaml").is_file():
        report.problem(".packs.yaml: missing")
    if not (target / ".obsidian").is_dir():
        report.note(".obsidian/ is missing: Obsidian will open this folder with its own defaults")


def check_launcher(target: Path, report: Report) -> None:
    stale = []
    for rel, source in template_files():
        if not rel.startswith(LAUNCHER_DIR + "/"):
            continue
        path = target / rel
        if not path.is_file():
            report.problem(f"{rel}: missing (run `meta-os init --refresh-launcher`)")
        elif rel in EXECUTABLE and not os.access(path, os.X_OK):
            report.problem(f"{rel}: not executable (chmod +x)")
        elif path.read_bytes() != source.read_bytes():
            stale.append(rel)
    if stale:
        report.note("the launcher differs from this plugin's copy (" + ", ".join(stale)
                    + "): run `meta-os init --refresh-launcher`")
    for rel in HOOK_STUBS:
        path = target / rel
        if not path.is_file():
            report.problem(f"{rel}: missing")
        elif not os.access(path, os.X_OK):
            report.problem(f"{rel}: not executable (chmod +x)")


def check_environment(target: Path, report: Report) -> None:
    if sys.version_info[:2] == (3, 9):
        report.note("this is Python 3.9, which works but no longer receives security fixes: "
                    "a supported Python is recommended")
    try:
        inside = subprocess.run(["git", "-C", str(target), "rev-parse", "--show-toplevel"],
                                capture_output=True, text=True)
    except OSError:
        report.note("git was not found")
        return
    if inside.returncode != 0:
        report.note("this folder is not a git repository yet (`git init`)")
        return
    if Path(inside.stdout.strip()).resolve() != target:
        report.note("the instance is not at the root of its git repository, so its git hooks cannot run")
        return
    hooks_path = subprocess.run(["git", "-C", str(target), "config", "core.hooksPath"],
                                capture_output=True, text=True).stdout.strip()
    if hooks_path != ".githooks":
        report.note("git hooks are off in this clone: `git config core.hooksPath .githooks` turns them on")


def run(target: Path) -> int:
    target = target.resolve()
    print(f"meta-os doctor — {target} (plugin {plugin_version()})")
    if not (target / CONFIG).is_file():
        print(f"  problem  not a meta-os instance: there is no {CONFIG}. `/meta-os:init` makes one.")
        print("1 problem.")
        return 1
    report = Report()
    check_config(target, report)
    check_settings(target, report)
    check_files(target, report)
    check_launcher(target, report)
    check_environment(target, report)
    for text in report.problems:
        print(f"  problem  {text}")
    for text in report.notes:
        print(f"  note     {text}")
    if report.problems:
        print(f"{len(report.problems)} problem{'s' if len(report.problems) != 1 else ''}.")
        return 1
    print("Healthy.")
    return 0
