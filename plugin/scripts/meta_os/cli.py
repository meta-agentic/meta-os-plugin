"""Command line of `meta-os`: version, doctor, init, hook."""
from __future__ import annotations

import argparse
from pathlib import Path

from . import doctor, init
from .paths import plugin_version


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="meta-os", description="The meta-os command.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("version", help="print the plugin's version")

    p_doctor = sub.add_parser("doctor", help="check that a folder is a healthy meta-os instance")
    p_doctor.add_argument("--target", default=".", help="the instance folder (default: this folder)")

    p_init = sub.add_parser("init", help="write a meta-os instance into a folder; never overwrites a file")
    init.add_arguments(p_init)

    p_hook = sub.add_parser("hook", help="the plugin's part of a git hook (called by the instance's stubs)")
    p_hook.add_argument("name", choices=["pre-commit", "commit-msg"])
    p_hook.add_argument("arguments", nargs="*")

    args = parser.parse_args(argv)
    if args.command == "version":
        print(plugin_version())
        return 0
    if args.command == "doctor":
        return doctor.run(Path(args.target))
    if args.command == "init":
        return init.run(args)
    # hook: no instance check exists yet, so the plugin's part passes and the stub goes on to
    # the instance's own hooks.
    return 0
