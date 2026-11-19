"""Shared set-up of the tests: scratch folders, a clean environment, the command under test."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugin"
TEMPLATE = PLUGIN / "instance-template" / "root"
META_OS = PLUGIN / "bin" / "meta-os"
PLUGIN_VERSION = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]

# The command's own planning code, so a matrix follows the template without being listed by hand.
sys.dont_write_bytecode = True
sys.path.insert(0, str(PLUGIN / "scripts"))
from meta_os import init as init_module  # noqa: E402

LOCAL_SETTINGS = ".claude/settings.local.json"
PROJECT_SETTINGS = ".claude/settings.json"
ALL_FILES = [rel for rel, _ in init_module.plan("scratch", "2000-01-01", [], "default", [], [])]


def add_cases(cls, prefix, cases, body):
    """One test method per case, so each input passes or fails by its own name."""
    for label, case in cases.items():
        def test(self, case=case):
            body(self, case)
        name = prefix + "_" + "".join(c if c.isalnum() else "_" for c in label)
        assert not hasattr(cls, name), name
        setattr(cls, name, test)


class ScratchCase(unittest.TestCase):
    """A temporary folder, and an environment that cannot see the developer's Claude Code."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="meta-os-test-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.target = self.tmp / "scratch"
        self.target.mkdir()
        self.config_dir = self.tmp / "claude-config"
        (self.config_dir / "plugins").mkdir(parents=True)
        keep = ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "SYSTEMROOT")
        self.env = {key: os.environ[key] for key in keep if key in os.environ}
        self.env.update({
            "PATH": str(Path(sys.executable).parent) + os.pathsep + self.env.get("PATH", ""),
            "CLAUDE_CONFIG_DIR": str(self.config_dir),
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
        })

    def run_cmd(self, *command, cwd=None, env=None):
        merged = dict(self.env, **(env or {}))
        return subprocess.run([str(c) for c in command], cwd=str(cwd or self.target), env=merged,
                              capture_output=True, text=True)

    def meta_os(self, *args, cwd=None, env=None):
        return self.run_cmd(META_OS, *args, cwd=cwd, env=env)

    def init(self, *args, **kwargs):
        done = self.meta_os("init", *args, **kwargs)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        return done

    def snapshot(self, root=None):
        root = root or self.target
        return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}

    def read_json(self, rel):
        return json.loads((self.target / rel).read_text(encoding="utf-8"))

    def write_record(self, plugins):
        """Claude Code's install record, as the resolver reads it."""
        path = self.config_dir / "plugins" / "installed_plugins.json"
        path.write_text(json.dumps({"version": 2, "plugins": plugins}), encoding="utf-8")

    def fake_plugin(self, label, version):
        """A folder that looks like an installed meta-os and answers every command with its label."""
        root = self.tmp / "installed" / label
        (root / ".claude-plugin").mkdir(parents=True)
        (root / "bin").mkdir()
        (root / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"name": "meta-os", "version": version}), encoding="utf-8")
        command = root / "bin" / "meta-os"
        command.write_text(f'#!/bin/sh\necho "{label} $*"\n', encoding="utf-8")
        command.chmod(0o755)
        return root
