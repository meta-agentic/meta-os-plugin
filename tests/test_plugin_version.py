"""The plugin's version against its releases: a change under plugin/ must move the version."""
import json
import unittest

from support import REPO, ScratchCase, add_cases

SCRIPT = REPO / "scripts" / "plugin_version.py"
MANIFEST = "plugin/.claude-plugin/plugin.json"


class VersionCase(ScratchCase):
    """A scratch repository: a base commit on `base`, then one more commit on HEAD."""

    def git(self, *args):
        done = self.run_cmd("git", *args)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stdout

    def write_manifest(self, version):
        path = self.target / MANIFEST
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"name": "meta-os", "version": version}, indent=2) + "\n", encoding="utf-8")

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def repository(self, tags=(), base_version="0.1.0"):
        self.git("init", "-q", "-b", "main")
        self.write_manifest(base_version)
        self.commit("base")
        for tag in tags:
            self.git("tag", tag)
        self.git("branch", "base")

    def change(self, path, version=None):
        if path:
            (self.target / path).parent.mkdir(parents=True, exist_ok=True)
            (self.target / path).write_text("changed\n", encoding="utf-8")
        if version:
            self.write_manifest(version)
        if path or version:
            self.commit("change")

    def script(self, *args):
        import sys
        return self.run_cmd(sys.executable, SCRIPT, "-C", self.target, *args)

    def manifest(self):
        return json.loads((self.target / MANIFEST).read_text(encoding="utf-8"))["version"]


class Check(VersionCase):
    def outcome(self, case):
        tags, base_version, path, version, expected = case
        self.repository(tags, base_version)
        self.change(path, version)
        done = self.script("check", "--base", "base")
        self.assertEqual(done.returncode, expected, done.stdout + done.stderr)

    def test_a_refusal_names_the_manifest(self):
        self.repository()
        self.change("plugin/skills/x/SKILL.md")
        self.assertIn(MANIFEST, self.script("check", "--base", "base").stderr)

    def test_an_unknown_base_is_an_error_not_a_pass(self):
        self.repository()
        self.assertEqual(self.script("check", "--base", "no-such-ref").returncode, 2)


TAG = "meta-os--v"
add_cases(Check, "test_check", {
    # label: (release tags, version at the base, file changed, version after, exit)
    "no tag, plugin changed, version kept at the first published": ((), "0.1.0", "plugin/a.md", None, 1),
    "no tag, plugin changed, version raised": ((), "0.1.0", "plugin/a.md", "0.2.0", 0),
    "no tag, nothing under plugin changed": ((), "0.1.0", "README.md", None, 0),
    "no tag, nothing changed at all": ((), "0.1.0", None, None, 0),
    "tag, plugin changed, version equals the tag": ((TAG + "0.2.0",), "0.2.0", "plugin/a.md", None, 1),
    "tag, plugin changed, version below the tag": ((TAG + "0.3.0",), "0.2.0", "plugin/a.md", None, 1),
    "tag, plugin changed, version above the tag": ((TAG + "0.2.0",), "0.2.0", "plugin/a.md", "0.2.1", 0),
    "tag, only the manifest changed, to the tag's version": ((TAG + "0.3.0",), "0.2.0", None, "0.3.0", 1),
    "tag, tests changed only": ((TAG + "0.2.0",), "0.2.0", "tests/test_a.py", None, 0),
    "the highest tag counts, not the newest": ((TAG + "0.10.0", TAG + "0.9.0"), "0.9.0", "plugin/a.md", "0.9.1", 1),
    "another plugin's tag is not a release": (("other--v9.0.0",), "0.1.0", "plugin/a.md", "0.2.0", 0),
    "a tag that is not a version is ignored": ((TAG + "next",), "0.1.0", "plugin/a.md", "0.2.0", 0),
    "a manifest version that is not a version": ((), "0.1.0", "plugin/a.md", "soon", 2),
}, Check.outcome)


class Latest(VersionCase):
    def latest(self, case):
        tags, expected = case
        self.repository(tags)
        self.assertEqual(self.script("latest").stdout.strip(), expected)


add_cases(Latest, "test_latest", {
    "no tag": ((), "0.1.0"),
    "one tag": ((TAG + "0.2.0",), "0.2.0"),
    "numeric order": ((TAG + "0.9.0", TAG + "0.10.0"), "0.10.0"),
}, Latest.latest)


class Set(VersionCase):
    def outcome(self, case):
        tags, base_version, wanted, expected_exit, expected_version = case
        self.repository(tags, base_version)
        done = self.script("set", *([wanted] if wanted else []))
        self.assertEqual(done.returncode, expected_exit, done.stdout + done.stderr)
        self.assertEqual(self.manifest(), expected_version)

    def test_it_prints_the_version(self):
        self.repository((), "0.2.0")
        self.assertEqual(self.script("set").stdout.strip(), "0.2.0")

    def test_it_changes_only_the_version_line(self):
        self.repository((), "0.2.0")
        before = (self.target / MANIFEST).read_text(encoding="utf-8")
        self.script("set", "0.3.0")
        self.assertEqual((self.target / MANIFEST).read_text(encoding="utf-8"), before.replace("0.2.0", "0.3.0"))


add_cases(Set, "test_set", {
    # label: (release tags, version in the manifest, version asked, exit, version in the manifest after)
    "no version asked keeps the manifest's": ((), "0.2.0", None, 0, "0.2.0"),
    "a higher version is written": ((), "0.2.0", "0.3.0", 0, "0.3.0"),
    "the released version is refused": ((TAG + "0.2.0",), "0.2.0", "0.2.0", 1, "0.2.0"),
    "no version asked, already released": ((TAG + "0.2.0",), "0.2.0", None, 1, "0.2.0"),
    "a lower version is refused": ((TAG + "0.3.0",), "0.3.0", "0.2.5", 1, "0.3.0"),
    "the first published version is refused": ((), "0.1.0", None, 1, "0.1.0"),
    "not a version": ((), "0.2.0", "v0.3", 2, "0.2.0"),
}, Set.outcome)


if __name__ == "__main__":
    unittest.main()
