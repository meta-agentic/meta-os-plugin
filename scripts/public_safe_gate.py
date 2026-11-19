#!/usr/bin/env python3
"""Public-safe gate of this repository: nothing private in what a public repository receives.

Published history cannot be cleaned, so every commit is checked before it exists and again in
continuous integration.

    public_safe_gate.py tree               the content and names of the files in the git index
    public_safe_gate.py commit-msg FILE    a commit message, from the commit-msg hook
    public_safe_gate.py history [RANGE]    the messages and the author and committer addresses
                                           of the commits in RANGE (default: all of HEAD)

What counts as a finding:
- a tracker key (two to five capitals, a dash, digits), except the standard names listed below;
- a machine path (a home folder of a named user);
- an e-mail address, except a hosting service's no-reply address and documentation domains;
- something shaped like a credential.

It cannot recognise a person's name or a private repository's name: those stay a reviewer's job.

Standard library only, Python 3.9 or later. Exit: 0 clean, 1 a finding, 2 a usage or git error.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TRACKER_KEY_RE = re.compile(r"(?<![A-Za-z0-9])([A-Z]{2,5}-[0-9]+)")
# Exact tokens only, never prefixes: published standard names that merely look like a key.
# A real key is never added here; it is removed from the file.
ALLOWED_TOKENS = frozenset({
    "UTF-8", "UTF-16", "UTF-32",
    "ISO-8601", "ISO-8859",
    "RFC-3339", "RFC-7231",
    "SHA-1", "SHA-256", "SHA-512",
    "AES-128", "AES-256",
    "MIT-0",
})
MACHINE_PATH_RE = re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+")
# The last label is letters only, so a version pin such as `name@v1.2.3` is not an address.
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}(?![A-Za-z0-9-])")
# The last form is the user name of an SSH remote, not a mailbox.
ALLOWED_EMAIL_RE = re.compile(
    r"@(?:users\.noreply\.github\.com|example\.(?:com|org|net))$|^(?:noreply|git)@github\.com$")
CREDENTIAL_RES = (
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[abprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)


class GateError(Exception):
    """A git failure: exit 2, never a pass."""


def findings(text: str, where: str) -> list[str]:
    out = []
    for number, line in enumerate(text.splitlines(), 1):
        for match in TRACKER_KEY_RE.finditer(line):
            if match.group(1) not in ALLOWED_TOKENS:
                out.append(f"{where}:{number}: tracker key {match.group(1)!r}")
        for match in MACHINE_PATH_RE.finditer(line):
            out.append(f"{where}:{number}: machine path {match.group(0)!r}")
        for match in EMAIL_RE.finditer(line):
            if not ALLOWED_EMAIL_RE.search(match.group(0)):
                out.append(f"{where}:{number}: e-mail address {match.group(0)!r}")
        for pattern in CREDENTIAL_RES:
            if pattern.search(line):
                out.append(f"{where}:{number}: something shaped like a credential")
    return out


def git(root: Path, *args: str) -> bytes:
    done = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if done.returncode != 0:
        raise GateError(f"git {' '.join(args)} failed: {done.stderr.decode('utf-8', 'replace').strip()}")
    return done.stdout


def check_tree(root: Path) -> list[str]:
    """The files in the index: what the next commit, or the checked-out commit, holds."""
    out = []
    for name in filter(None, git(root, "ls-files", "-z", "--cached").decode("utf-8").split("\0")):
        out += findings(name, "file name")
        data = git(root, "show", f":{name}")
        if b"\0" in data:
            continue                      # a binary file is not read as text
        out += findings(data.decode("utf-8", "replace"), name)
    return out


def check_history(root: Path, commits: str) -> list[str]:
    out = []
    for sha in git(root, "rev-list", commits).decode().split():
        short = sha[:12]
        out += findings(git(root, "log", "-1", "--format=%B", sha).decode("utf-8", "replace"), f"commit {short}")
        for address in git(root, "log", "-1", "--format=%ae%n%ce", sha).decode().split():
            if not ALLOWED_EMAIL_RE.search(address):
                out.append(f"commit {short}: author or committer address {address!r} is not a no-reply address")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("-C", dest="root", default=str(ROOT), help="the repository (default: this one)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("tree")
    sub.add_parser("commit-msg").add_argument("file")
    sub.add_parser("history").add_argument("commits", nargs="?", default="HEAD")
    args = parser.parse_args(argv)
    root = Path(args.root)
    try:
        if args.command == "tree":
            found = check_tree(root)
        elif args.command == "commit-msg":
            found = findings(Path(args.file).read_text(encoding="utf-8"), "commit message")
        else:
            found = check_history(root, args.commits)
    except (GateError, OSError) as exc:
        print(f"public-safe gate: {exc}", file=sys.stderr)
        return 2
    if found:
        print("public-safe gate: this would publish private data:", file=sys.stderr)
        for line in found:
            print(f"  {line}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
