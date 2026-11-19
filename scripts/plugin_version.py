#!/usr/bin/env python3
"""The plugin's version against its releases: the check a pull request must pass, and the release's setter.

    plugin_version.py latest              the last released version (from the `meta-os--v*` tags)
    plugin_version.py check --base REF    fail when HEAD changes plugin/ since REF and the manifest's
                                          version is not above the last release
    plugin_version.py set [VERSION]       write VERSION into the manifest (default: keep the manifest's);
                                          fail when it is not above the last release; print it

A release is a tag `meta-os--v<version>`. While no tag exists, the last release is 0.1.0, the first
published version. A user's `claude plugin update` does nothing when the version did not move, so a
change under plugin/ that keeps the released version reaches nobody.

Standard library only, Python 3.9 or later. Exit: 0 fine, 1 the version must move, 2 a usage or git error.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = "plugin/.claude-plugin/plugin.json"
TAG_PREFIX = "meta-os--v"
FIRST_PUBLISHED = (0, 1, 0)
VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


class VersionError(Exception):
    """A git failure or an unreadable version: exit 2, never a pass."""


def parse(text: str) -> tuple[int, int, int] | None:
    match = VERSION_RE.match(text)
    return (int(match.group(1)), int(match.group(2)), int(match.group(3))) if match else None


def dotted(version: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in version)


def git(root: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if done.returncode != 0:
        raise VersionError(f"git {' '.join(args)} failed: {done.stderr.strip()}")
    return done.stdout


def latest_release(root: Path) -> tuple[int, int, int]:
    """The highest version among the release tags; the first published version when there is none."""
    found = [parse(tag[len(TAG_PREFIX):]) for tag in git(root, "tag", "--list", TAG_PREFIX + "*").split()]
    return max([version for version in found if version] or [FIRST_PUBLISHED])


def manifest_version(root: Path) -> tuple[int, int, int]:
    try:
        text = json.loads((root / MANIFEST).read_text(encoding="utf-8"))["version"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise VersionError(f"{MANIFEST}: no readable version ({exc})")
    version = parse(text) if isinstance(text, str) else None
    if version is None:
        raise VersionError(f"{MANIFEST}: version {text!r} is not X.Y.Z")
    return version


def check(root: Path, base: str) -> int:
    changed = [name for name in git(root, "diff", "--name-only", f"{base}...HEAD", "--", "plugin/").splitlines() if name]
    if not changed:
        print("plugin version: nothing under plugin/ changed; no new version is needed")
        return 0
    current, released = manifest_version(root), latest_release(root)
    if current > released:
        print(f"plugin version: {dotted(current)} is above the last release, {dotted(released)}")
        return 0
    print(f"plugin version: {len(changed)} file(s) under plugin/ changed, and the manifest still says "
          f"{dotted(current)} while the last release is {dotted(released)}. Raise `version` in {MANIFEST}: "
          "an update that keeps the released version reaches nobody.", file=sys.stderr)
    return 1


def set_version(root: Path, wanted: str | None) -> int:
    current, released = manifest_version(root), latest_release(root)
    version = current if not wanted else parse(wanted)
    if version is None:
        raise VersionError(f"version {wanted!r} is not X.Y.Z")
    if version <= released:
        print(f"plugin version: {dotted(version)} is not above the last release, {dotted(released)}", file=sys.stderr)
        return 1
    if version != current:
        path = root / MANIFEST
        text = path.read_text(encoding="utf-8")
        new, count = re.subn(r'("version"\s*:\s*")[^"]*(")', lambda m: m.group(1) + dotted(version) + m.group(2),
                             text, count=1)
        if count != 1:
            raise VersionError(f"{MANIFEST}: the version line was not found")
        path.write_text(new, encoding="utf-8")
    print(dotted(version))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("-C", dest="root", default=str(ROOT), help="the repository (default: this one)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("latest")
    sub.add_parser("check").add_argument("--base", required=True, help="the commit the change is compared with")
    sub.add_parser("set").add_argument("version", nargs="?")
    args = parser.parse_args(argv)
    root = Path(args.root)
    try:
        if args.command == "latest":
            print(dotted(latest_release(root)))
            return 0
        if args.command == "check":
            return check(root, args.base)
        return set_version(root, args.version)
    except VersionError as exc:
        print(f"plugin version: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
