"""`meta-os init`: write a meta-os instance into a folder from the template the plugin carries.

The deterministic half of `/meta-os:init`. The skill asks the first-run questions and passes
the answers as flags; this module is the one place that writes them.

Rules it holds:
- an existing file is never overwritten, changed or appended to (`--refresh-launcher` is the one
  exception, and touches only the launcher folder);
- the root `CLAUDE.md` is never read or written: the instance contract is `.claude/CLAUDE.md`;
- every name that becomes a path is checked before anything is written.

`--plan` is the one screen the skill shows before the single yes: every answer, marked where it is
the default, what would be written, and the command that writes it. It writes nothing.

Exit: 0 written (or nothing to write), 1 a path is blocked, 2 a wrong argument.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shlex
import sys
from pathlib import Path

from .paths import (
    CONFIG, LAUNCHER_DIR, MARKETPLACE, MARKETPLACE_SOURCE, PACK_MARKETPLACE, PACK_MARKETPLACE_SOURCE,
    PLUGIN_NAME, TEMPLATE_ROOT, load_resolver, plugin_version,
)

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SPACE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
PACK_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
LAYOUTS = ("default", "flat", "tier/project", "project/tier")

# Template files stored under another name, so they do not act on the plugin's own repository.
STORED_AS = {"gitignore": ".gitignore"}
EXECUTABLE = frozenset({
    ".meta-os/meta-os", ".meta-os/git-hook", ".meta-os/resolver.py",
    ".githooks/pre-commit", ".githooks/commit-msg",
})
NO_PROJECT_ROW = "| _(none yet)_ | | | |"


class UsageError(Exception):
    """A wrong argument: exit 2, nothing written."""


SCOPES = ("local", "project")
# Where the plugin entries go: `local` is this person in this folder only (not committed);
# `project` is everyone who clones the instance (committed).
SETTINGS_FILE = {"local": ".claude/settings.local.json", "project": ".claude/settings.json"}


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target", default=".", help="the folder to write into (default: this folder)")
    parser.add_argument("--name", help="the instance's name (default: the folder's name)")
    parser.add_argument("--backlog", action="append", default=[], metavar="none|SPACE=PATH",
                        help="where the backlog is: none, or a space key and its directory (repeatable)")
    parser.add_argument("--memory-layout", default="default", choices=LAYOUTS,
                        help="the memory topology (default: default)")
    parser.add_argument("--project", action="append", default=[], metavar="NAME",
                        help="a first project node to write (repeatable)")
    parser.add_argument("--pack", action="append", default=[], metavar="NAME",
                        help="a pack to record, by its plugin name (repeatable)")
    parser.add_argument("--scope", default="local", choices=SCOPES,
                        help="where the plugin and its packs are enabled: local (you, this folder, not committed;"
                             " the default) or project (everyone who clones it, committed)")
    parser.add_argument("--plan", action="store_true",
                        help="show the answers and what would be written on one screen; write nothing")
    parser.add_argument("--dry-run", action="store_true", help="list every file that would be written; write nothing")
    parser.add_argument("--refresh-launcher", action="store_true",
                        help="rewrite the launcher folder of an existing instance from this plugin, and nothing else")


def checked_name(value: str, pattern: re.Pattern, what: str) -> str:
    if not pattern.match(value):
        raise UsageError(f"{what} {value!r}: use letters, digits, '-' (and '.', '_' where a file name allows them)")
    return value


def parse_backlogs(specs: list[str]) -> list[dict]:
    if "none" in specs:
        if len(specs) > 1:
            raise UsageError("--backlog none cannot be combined with another --backlog")
        return []
    backlogs, seen = [], set()
    for spec in specs:
        space, sep, path = spec.partition("=")
        if not sep or not path or not SPACE_RE.match(space):
            raise UsageError(f"--backlog {spec!r}: use 'none' or SPACE=PATH, for example abc=../vault/abc")
        if space in seen:
            raise UsageError(f"--backlog: space {space!r} is given twice")
        seen.add(space)
        backlogs.append({"space": space, "path": path})
    return backlogs


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def config_text(name: str, today: str, backlogs: list[dict], layout: str) -> str:
    config = {
        "instance": {"name": name, "initialized": today},
        "acknowledgedPluginVersion": plugin_version(),
        "hooks": {"strict": False},
        "backlogs": backlogs,
    }
    if layout != "default":
        config["memory"] = {"roots": [{"label": "instance", "path": "${instance}/memory", "layout": layout}]}
    return json.dumps(config, indent=2) + "\n"


def settings_text(packs: list[str]) -> str:
    marketplaces = {MARKETPLACE: {"source": MARKETPLACE_SOURCE}}
    enabled = {f"{PLUGIN_NAME}@{MARKETPLACE}": True}
    if packs:
        marketplaces[PACK_MARKETPLACE] = {"source": PACK_MARKETPLACE_SOURCE}
        enabled.update({f"{pack}@{PACK_MARKETPLACE}": True for pack in packs})
    return json.dumps({"extraKnownMarketplaces": marketplaces, "enabledPlugins": enabled}, indent=2) + "\n"


def packs_text(packs: list[str]) -> str:
    head = ("# The packs this instance chose. Each is a Claude Code plugin; a new checkout installs\n"
            "# what is listed here. A pack's own settings go under its name.\n")
    if not packs:
        return head + "packs: {}\n"
    return head + "packs:\n" + "".join(
        f"  {pack}:\n    plugin: {pack}@{PACK_MARKETPLACE}\n" for pack in packs)


def project_node(name: str) -> str:
    text = (TEMPLATE_ROOT / "templates" / "project.md").read_text(encoding="utf-8")
    text = re.sub(r"(?m)^name:.*$", f"name: {name}", text, count=1)
    return text.replace("# {{Project Name}}", f"# {name}")


def template_files() -> list[tuple[str, Path]]:
    """(path in the instance, file in the template), sorted by instance path."""
    found = []
    for path in TEMPLATE_ROOT.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            rel = path.relative_to(TEMPLATE_ROOT).as_posix()
            found.append((STORED_AS.get(rel, rel), path))
    return sorted(found)


def plan(name: str, today: str, backlogs: list[dict], layout: str, projects: list[str],
         packs: list[str], scope: str = "local") -> list[tuple[str, bytes]]:
    """Every file of the instance as (path, content), in writing order."""
    rows = "\n".join(f"| {p} | [[projects/{p}\\|{p}]] | | |" for p in projects) or NO_PROJECT_ROW
    fill = {"{{instance-name}}": name, "{{initialized}}": today,
            "{{plugin-version}}": plugin_version(), "{{project-rows}}": rows}
    files: dict[str, bytes] = {}
    for rel, source in template_files():
        data = source.read_bytes()
        if source.suffix == ".md":
            text = data.decode("utf-8")
            for token, value in fill.items():
                text = text.replace(token, value)
            data = text.encode("utf-8")
        files[rel] = data
    files[CONFIG] = config_text(name, today, backlogs, layout).encode("utf-8")
    files[SETTINGS_FILE[scope]] = settings_text(packs).encode("utf-8")
    files[".packs.yaml"] = packs_text(packs).encode("utf-8")
    for project in projects:
        files[f"projects/{project}.md"] = project_node(project).encode("utf-8")
    return sorted(files.items())


def blocked_by(target: Path, rel: str) -> str | None:
    """The parent of `rel` that exists and is not a folder, if any."""
    current = target
    for part in Path(rel).parts[:-1]:
        current = current / part
        if os.path.lexists(current) and not current.is_dir():
            return current.relative_to(target).as_posix()
    return None


def write_new(target: Path, rel: str, data: bytes) -> None:
    path = target / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "xb") as handle:      # 'x': fails rather than replace a file that appeared meanwhile
        handle.write(data)
    path.chmod(0o755 if rel in EXECUTABLE else 0o644)


def refresh_launcher(target: Path, dry: bool) -> int:
    if not (target / CONFIG).is_file():
        print(f"meta-os init: {target} is not a meta-os instance (no {CONFIG}); nothing refreshed", file=sys.stderr)
        return 1
    for rel, source in template_files():
        if not rel.startswith(LAUNCHER_DIR + "/"):
            continue
        path, data = target / rel, source.read_bytes()
        if path.is_file() and path.read_bytes() == data:
            print(f"  current    {rel}")
            continue
        print(f"  {'would refresh' if dry else 'refreshed'}  {rel}")
        if not dry:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            path.chmod(0o755 if rel in EXECUTABLE else 0o644)
    return 0


def pack_lines(packs: list[str], target: Path, scope: str = "local") -> list[str]:
    """One line per chosen pack: already installed (recorded only, no second copy), or the install command."""
    resolver = load_resolver()
    lines = []
    for pack in packs:
        found = resolver.installs(pack, target)
        if found:
            where = "for this project" if found[0]["scope"] == "project" else "for you on this machine"
            lines.append(f"  {pack}: already installed {where} ({found[0]['version']}); recorded in .packs.yaml "
                         "only: nothing is installed again and nothing changes")
        else:
            lines.append(f"  {pack}: not installed. To install it, run: "
                         f"claude plugin install {pack}@{PACK_MARKETPLACE} --scope {scope}")
    return lines


LAYOUT_WORDS = {
    "default": "memory/raw, memory/wiki and memory/output in this folder",
    "flat": "one root with raw/, wiki/ and output/ inside",
    "tier/project": "tier first, then project (raw/<project>/...)",
    "project/tier": "project first, then tier (<project>/raw/...)",
}
SCOPE_WORDS = {
    "local": "you, in this folder only; .claude/settings.local.json, not committed",
    "project": "everyone who clones it; .claude/settings.json, committed",
}


def by_folder(paths: list[str]) -> str:
    """`.claude/ (2), memory/ (4), 5 at the root`: a file list short enough for one screen."""
    counts: dict[str, int] = {}
    for rel in paths:
        head, sep, _ = rel.partition("/")
        counts[head + "/" if sep else ""] = counts.get(head + "/" if sep else "", 0) + 1
    parts = [f"{folder} ({count})" for folder, count in sorted(counts.items()) if folder]
    if counts.get(""):
        parts.append(f"{counts['']} at the root")
    return ", ".join(parts)


def write_command(args: argparse.Namespace, name: str, backlogs: list[dict], projects: list[str],
                  packs: list[str]) -> str:
    """The command that writes exactly what the plan shows."""
    words = ["meta-os", "init", "--name", name]
    if args.target != ".":
        words += ["--target", args.target]
    for backlog in backlogs:
        words += ["--backlog", f"{backlog['space']}={backlog['path']}"]
    if args.memory_layout != "default":
        words += ["--memory-layout", args.memory_layout]
    for project in projects:
        words += ["--project", project]
    for pack in packs:
        words += ["--pack", pack]
    if args.scope != "local":
        words += ["--scope", args.scope]
    return " ".join(shlex.quote(word) for word in words)


def show_plan(args: argparse.Namespace, target: Path, name: str, backlogs: list[dict], projects: list[str],
              packs: list[str]) -> int:
    """One screen: the answers, what would be written, what is kept, and the command. Writes nothing."""
    def mark(is_default: bool, why: str = "default") -> str:
        return f"   ({why})" if is_default else ""

    created, kept, blocked = [], [], []
    for rel, _ in plan(name, "2000-01-01", backlogs, args.memory_layout, projects, packs, args.scope):
        if os.path.lexists(target / rel):
            kept.append(rel)
        elif blocked_by(target, rel) is not None:
            blocked.append(rel)
        else:
            created.append(rel)
    rows = [
        ("Name", name + mark(not args.name, "default: the folder's name")),
        ("Backlog", (", ".join(f"{b['space']} in {b['path']}" for b in backlogs) or "none") + mark(not backlogs)),
        ("Memory", f"{args.memory_layout}: {LAYOUT_WORDS[args.memory_layout]}" + mark(args.memory_layout == "default")),
        ("Project", (", ".join(projects) or "none") + mark(not projects)),
        ("Packs", (", ".join(packs) or "none") + mark(not packs)),
        ("Scope", f"{args.scope}: {SCOPE_WORDS[args.scope]}" + mark(args.scope == "local")),
        ("Writes", f"{len(created)} new file{'s' if len(created) != 1 else ''}"
                   + (": " + by_folder(created) if created else "")),
        ("Keeps", (f"{len(kept)} existing file{'s' if len(kept) != 1 else ''}, unchanged: "
                   + (", ".join(kept) if len(kept) <= 6 else by_folder(kept)))
                  if kept else "nothing is in the way"),
    ]
    if blocked:
        rows.append(("Blocked", f"{len(blocked)}, because a parent is a file, not a folder: " + ", ".join(blocked)))
    rows.append(("Never", "overwrites, changes or appends to an existing file; never reads or writes ./CLAUDE.md"))
    print(f"meta-os init — the plan for {target} (nothing is written yet)")
    print()
    for label, text in rows:
        print(f"  {label:<8} {text}")
    if packs:
        print()
        print("Packs:")
        for line in pack_lines(packs, target, args.scope):
            print(line)
    print()
    print("To write it: " + write_command(args, name, backlogs, projects, packs))
    return 1 if blocked else 0


def run(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"meta-os init: {target} is not a folder", file=sys.stderr)
        return 2
    if args.refresh_launcher:
        return refresh_launcher(target, args.dry_run)
    try:
        name = checked_name(args.name or target.name, NAME_RE, "instance name")
        backlogs = parse_backlogs(args.backlog)
        projects = [checked_name(p, NAME_RE, "project name") for p in unique(args.project)]
        packs = [checked_name(p, PACK_RE, "pack name") for p in unique(args.pack)]
    except UsageError as exc:
        print(f"meta-os init: {exc}", file=sys.stderr)
        return 2
    if "_index" in projects:
        print("meta-os init: a project cannot be named _index", file=sys.stderr)
        return 2
    if args.plan:
        return show_plan(args, target, name, backlogs, projects, packs)

    dry = args.dry_run
    today = datetime.date.today().isoformat()
    print(f"meta-os init — instance '{name}' in {target}")
    created, kept, blocked = [], [], []
    for rel, data in plan(name, today, backlogs, args.memory_layout, projects, packs, args.scope):
        if os.path.lexists(target / rel):
            kept.append(rel)
            print(f"  kept       {rel} (exists)")
            continue
        parent = blocked_by(target, rel)
        if parent is not None:
            blocked.append(rel)
            print(f"  blocked    {rel} ({parent} is not a folder)")
            continue
        if not dry:
            write_new(target, rel, data)
        created.append(rel)
        print(f"  {'would create' if dry else 'created'}    {rel}")

    print(f"{'Dry run: ' if dry else ''}{len(created)} {'to create' if dry else 'created'}, "
          f"{len(kept)} kept, {len(blocked)} blocked.")
    decided = bool(args.backlog or args.project or args.pack or args.memory_layout != "default" or args.name
                   or args.scope != "local")
    by_hand = [rel for rel in kept if rel in (CONFIG, *SETTINGS_FILE.values(), ".packs.yaml", "projects/_index.md")]
    if by_hand and decided:
        print("Existing files are never changed. Apply your answers by hand in: " + ", ".join(by_hand))
    if packs:
        print("Packs:")
        for line in pack_lines(packs, target, args.scope):
            print(line)
    if not dry:
        print("Next: `meta-os doctor` checks the instance. Git hooks are off until a clone runs "
              "`git config core.hooksPath .githooks`.")
    return 1 if blocked else 0
