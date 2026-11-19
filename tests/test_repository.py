"""The manifest, the marketplace file and the repository's own layout rules."""
import json
import os
import re
import shutil
import subprocess
import unittest

from support import PLUGIN, REPO, ScratchCase, add_cases

MANIFEST = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
MARKETPLACE = json.loads((REPO / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
URL = "https://github.com/meta-agentic/meta-os-plugin"
WORKFLOW = (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
RELEASE = (REPO / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
README = (REPO / "README.md").read_text(encoding="utf-8")


def tracked_or_new():
    out = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                         capture_output=True, text=True, check=True).stdout
    return [name for name in out.split("\0") if name and (REPO / name).is_file()]


class Manifest(unittest.TestCase):
    def field_is(self, case):
        key, value = case
        self.assertEqual(MANIFEST.get(key), value)

    def test_version_is_a_plain_version(self):
        self.assertRegex(MANIFEST["version"], r"^\d+\.\d+\.\d+$")

    def test_it_declares_no_dependency(self):
        self.assertNotIn("dependencies", MANIFEST)

    def test_it_has_a_description(self):
        self.assertGreater(len(MANIFEST.get("description", "")), 40)

    def test_the_marketplace_lists_exactly_this_plugin(self):
        self.assertEqual([p["name"] for p in MARKETPLACE["plugins"]], ["meta-os"])

    def test_the_marketplace_points_at_the_plugin_folder(self):
        self.assertEqual(MARKETPLACE["plugins"][0]["source"], "./plugin")

    def test_the_marketplace_name_is_the_one_init_writes(self):
        from meta_os.paths import MARKETPLACE as written
        self.assertEqual(MARKETPLACE["name"], written)

    def test_the_marketplace_does_not_take_the_organisation_s_name(self):
        self.assertNotEqual(MARKETPLACE["name"], "meta-agentic")


add_cases(Manifest, "test_field", {
    "name": ("name", "meta-os"), "author": ("author", {"name": "meta-agentic"}),
    "homepage": ("homepage", URL), "repository": ("repository", URL), "license": ("license", "MIT"),
}, Manifest.field_is)


class Layout(unittest.TestCase):
    def test_no_claude_md_at_the_plugin_root(self):
        self.assertFalse((PLUGIN / "CLAUDE.md").exists())

    def test_the_repository_has_its_development_contract(self):
        self.assertTrue((REPO / "CLAUDE.md").is_file())

    def test_the_plugin_ships_no_tests(self):
        self.assertEqual([p for p in PLUGIN.rglob("test_*.py")], [])

    def test_the_command_is_executable(self):
        self.assertTrue(os.access(PLUGIN / "bin" / "meta-os", os.X_OK))

    def test_every_file_is_under_1000_lines(self):
        long = [n for n in tracked_or_new() if len((REPO / n).read_bytes().splitlines()) >= 1000]
        self.assertEqual(long, [])

    def test_the_licence_is_mit(self):
        self.assertTrue((REPO / "LICENSE").read_text(encoding="utf-8").startswith("MIT License\n\nCopyright (c) "))

    def test_plugin_code_imports_the_standard_library_only(self):
        allowed = {"__future__", "argparse", "dataclasses", "datetime", "heapq", "importlib", "json", "math", "os", "re",
                   "shlex", "subprocess", "sys", "pathlib", "meta_os"}
        found = set()
        for path in list(PLUGIN.rglob("*.py")):
            for line in path.read_text(encoding="utf-8").splitlines():
                match = re.match(r"\s*(?:from|import)\s+([A-Za-z_][A-Za-z0-9_]*|\.)", line)
                if match and match.group(1) != ".":
                    found.add(match.group(1))
        self.assertEqual(found - allowed, set())


class Workflow(unittest.TestCase):
    """Declared once: the runner label and each version."""

    def test_the_runner_is_named_once(self):
        self.assertEqual(WORKFLOW.count("vars.CI_RUNNER ||"), 1)

    def test_every_job_runs_on_that_runner(self):
        named = re.findall(r"(?m)^\s*runs-on:\s*(\S+)", WORKFLOW)
        self.assertEqual(sorted(set(named)), ["&runner", "*runner"])

    def test_a_pull_request_is_checked_for_a_new_version(self):
        self.assertIn("scripts/plugin_version.py\n          check --base", WORKFLOW)

    def test_the_floor_python_is_tested(self):
        self.assertEqual(WORKFLOW.count('"3.9"'), 1)

    def test_every_action_is_pinned_to_an_exact_release(self):
        uses = re.findall(r"(?m)^\s*-?\s*uses:\s*(\S+)", WORKFLOW)
        self.assertTrue(uses)
        for action in uses:
            self.assertRegex(action, r"@v\d+\.\d+\.\d+$")

    def test_no_action_is_used_twice(self):
        uses = re.findall(r"(?m)^\s*-?\s*uses:\s*(\S+)", WORKFLOW)
        self.assertEqual(len(uses), len(set(uses)))


class Release(unittest.TestCase):
    """One workflow releases, started by hand; its steps and versions are the build's own."""

    def test_it_is_started_by_hand(self):
        self.assertIn("workflow_dispatch:", RELEASE)

    def test_it_is_not_started_by_a_pushed_tag(self):
        self.assertNotIn("tags:", RELEASE)

    def test_it_runs_the_build_workflow(self):
        self.assertEqual(re.findall(r"(?m)^\s*uses:\s*(\S+)", RELEASE), ["./.github/workflows/ci.yml"])

    def test_it_names_no_runner_of_its_own(self):
        self.assertNotIn("runs-on:", RELEASE)

    def test_it_asks_for_a_release(self):
        self.assertIn("release: true", RELEASE)

    def test_the_release_job_waits_for_the_checks(self):
        self.assertRegex(WORKFLOW, r"(?s)\n  release:\n.*?\n    needs: check\n")

    def test_the_release_job_runs_only_when_asked(self):
        self.assertRegex(WORKFLOW, r"(?s)\n  release:\n.*?\n    if: inputs\.release\n")

    def test_the_version_is_set_before_the_tag(self):
        self.assertLess(WORKFLOW.index("plugin_version.py set"), WORKFLOW.index("plugin tag plugin"))

    def test_the_plugin_is_validated_before_the_tag(self):
        job = WORKFLOW[WORKFLOW.index("\n  release:\n"):]
        self.assertLess(job.index("plugin validate plugin --strict"), job.index("plugin tag plugin"))

    def test_the_tag_is_made_by_the_cli_and_pushed(self):
        self.assertRegex(WORKFLOW, r"plugin tag plugin .*--push")

    def test_main_is_never_pushed_to(self):
        self.assertNotIn("git push", WORKFLOW + RELEASE)


class Readme(unittest.TestCase):
    """The preview note names the version a user gets and the lines that install and update it."""

    def test_it_names_the_preview_version(self):
        major, minor, _ = MANIFEST["version"].split(".")
        self.assertIn(f"Preview {major}.{minor}", README)

    def has_the_line(self, line):
        self.assertIn(line, README)


add_cases(Readme, "test_it_has", {
    "the marketplace line": "claude plugin marketplace add meta-agentic/meta-os-plugin",
    "the install line": "claude plugin install meta-os@meta-os-preview",
    "the update line": "claude plugin update meta-os@meta-os-preview",
    "the first command": "/meta-os:init",
}, Readme.has_the_line)


class StrictValidation(ScratchCase):
    """`claude plugin validate --strict`. Skipped without the Claude Code CLI, unless the build requires it."""

    def validate(self, path):
        claude = os.environ.get("CLAUDE_BIN") or shutil.which("claude")
        if not claude:
            if os.environ.get("META_OS_REQUIRE_CLAUDE") == "1":
                self.fail("the Claude Code CLI is required here and was not found")
            self.skipTest("the Claude Code CLI is not installed; set CLAUDE_BIN to run this")
        done = subprocess.run([claude, "plugin", "validate", str(path), "--strict"], capture_output=True, text=True,
                              cwd=str(self.tmp), timeout=120)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)


add_cases(StrictValidation, "test_validates", {"the plugin": PLUGIN, "the marketplace file": REPO},
          StrictValidation.validate)


if __name__ == "__main__":
    unittest.main()
