"""The launcher and the git hook stubs an instance carries: they find the plugin from outside a session."""
import json
import unittest

from support import PLUGIN, PLUGIN_VERSION, ScratchCase, add_cases


class Launcher(ScratchCase):
    def setUp(self):
        super().setUp()
        self.init()
        self.launcher = self.target / ".meta-os" / "meta-os"

    def entry(self, root, version, project=None):
        found = {"scope": "project" if project else "user", "installPath": str(root), "version": version}
        if project:
            found["projectPath"] = str(project)
        return found

    def test_the_named_plugin_folder_runs(self):
        done = self.run_cmd(self.launcher, "version", env={"META_OS_PLUGIN_ROOT": str(PLUGIN)})
        self.assertEqual((done.returncode, done.stdout.strip()), (0, PLUGIN_VERSION))

    def test_no_plugin_exits_3(self):
        done = self.run_cmd(self.launcher, "version")
        self.assertEqual(done.returncode, 3)
        self.assertIn("was not found", done.stderr)

    def test_a_named_folder_that_is_not_the_plugin_exits_3(self):
        done = self.run_cmd(self.launcher, "version", env={"META_OS_PLUGIN_ROOT": str(self.tmp)})
        self.assertEqual(done.returncode, 3)

    def test_a_named_folder_wins_over_the_install_record(self):
        self.write_record({"meta-os@any": [self.entry(self.fake_plugin("user", "9.9.9"), "9.9.9")]})
        done = self.run_cmd(self.launcher, "version", env={"META_OS_PLUGIN_ROOT": str(PLUGIN)})
        self.assertEqual(done.stdout.strip(), PLUGIN_VERSION)

    def test_a_user_install_is_found(self):
        self.write_record({"meta-os@any": [self.entry(self.fake_plugin("user", "1.0.0"), "1.0.0")]})
        self.assertEqual(self.run_cmd(self.launcher, "version").stdout.strip(), "user version")

    def test_a_project_install_wins_over_a_user_install(self):
        self.write_record({"meta-os@any": [
            self.entry(self.fake_plugin("user", "1.0.0"), "1.0.0"),
            self.entry(self.fake_plugin("project", "1.1.0"), "1.1.0", self.target),
        ]})
        self.assertEqual(self.run_cmd(self.launcher, "version").stdout.strip(), "project version")

    def test_an_install_for_another_project_is_ignored(self):
        self.write_record({"meta-os@any": [self.entry(self.fake_plugin("other", "1.0.0"), "1.0.0", self.tmp / "x")]})
        self.assertEqual(self.run_cmd(self.launcher, "version").returncode, 3)

    def test_another_plugin_in_the_record_is_ignored(self):
        self.write_record({"meta-os-extra@any": [self.entry(self.fake_plugin("extra", "1.0.0"), "1.0.0")]})
        self.assertEqual(self.run_cmd(self.launcher, "version").returncode, 3)

    def test_an_install_whose_folder_is_gone_is_ignored(self):
        self.write_record({"meta-os@any": [self.entry(self.tmp / "gone", "1.0.0")]})
        self.assertEqual(self.run_cmd(self.launcher, "version").returncode, 3)

    def test_the_command_runs_in_the_instance_from_any_folder(self):
        done = self.run_cmd(self.launcher, "doctor", cwd=self.tmp, env={"META_OS_PLUGIN_ROOT": str(PLUGIN)})
        self.assertIn(f"meta-os doctor — {self.target} ", done.stdout)

    def test_arguments_are_passed_through(self):
        self.write_record({"meta-os@any": [self.entry(self.fake_plugin("user", "1.0.0"), "1.0.0")]})
        self.assertEqual(self.run_cmd(self.launcher, "a", "b c").stdout.strip(), "user a b c")


class GitHook(ScratchCase):
    """The stub in .githooks/: the plugin's check, then the instance's own hooks, by the instance's rule."""

    def setUp(self):
        super().setUp()
        self.init()
        self.run_cmd("git", "init", "-q")
        self.stub = self.target / ".githooks" / "pre-commit"

    def set_strict(self, value):
        path = self.target / "meta-os.config.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        config["hooks"]["strict"] = value
        path.write_text(json.dumps(config), encoding="utf-8")

    def own_hook(self, name, body, hook="pre-commit", mode=0o755):
        path = self.target / ".githooks.d" / hook / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
        path.chmod(mode)

    def test_with_the_plugin_the_hook_passes(self):
        done = self.run_cmd(self.stub, env={"META_OS_PLUGIN_ROOT": str(PLUGIN)})
        self.assertEqual((done.returncode, done.stderr), (0, ""))

    def test_without_the_plugin_a_default_instance_warns_and_passes(self):
        done = self.run_cmd(self.stub)
        self.assertEqual(done.returncode, 0)
        self.assertIn("check was skipped", done.stderr)

    def test_without_the_plugin_a_strict_instance_refuses(self):
        self.set_strict(True)
        done = self.run_cmd(self.stub)
        self.assertEqual(done.returncode, 1)
        self.assertIn("refused", done.stderr)

    def test_the_environment_makes_one_machine_strict(self):
        self.assertEqual(self.run_cmd(self.stub, env={"META_OS_HOOK_STRICT": "1"}).returncode, 1)

    def test_the_environment_cannot_make_a_strict_instance_weaker(self):
        self.set_strict(True)
        self.assertEqual(self.run_cmd(self.stub, env={"META_OS_HOOK_STRICT": "0"}).returncode, 1)

    def unreadable_strictness_refuses(self, content):
        path = self.target / "meta-os.config.json"
        path.unlink() if content is None else path.write_text(content, encoding="utf-8")
        self.assertEqual(self.run_cmd(self.stub).returncode, 1)

    def test_a_strict_instance_with_the_plugin_passes(self):
        self.set_strict(True)
        self.assertEqual(self.run_cmd(self.stub, env={"META_OS_PLUGIN_ROOT": str(PLUGIN)}).returncode, 0)

    def test_a_failing_plugin_check_fails_the_hook(self):
        root = self.fake_plugin("failing", "1.0.0")
        (root / "bin" / "meta-os").write_text("#!/bin/sh\nexit 7\n", encoding="utf-8")
        self.assertEqual(self.run_cmd(self.stub, env={"META_OS_PLUGIN_ROOT": str(root)}).returncode, 7)

    def test_the_plugin_check_is_told_the_hook_name(self):
        root = self.fake_plugin("echo", "1.0.0")
        done = self.run_cmd(self.stub, env={"META_OS_PLUGIN_ROOT": str(root)})
        self.assertEqual(done.stdout.strip(), "echo hook pre-commit")

    def test_the_instance_s_own_hook_runs(self):
        self.own_hook("10-mine", "echo own-hook-ran")
        self.assertIn("own-hook-ran", self.run_cmd(self.stub).stdout)

    def test_the_instance_s_own_hook_runs_without_the_plugin(self):
        self.own_hook("10-mine", "exit 5")
        self.assertEqual(self.run_cmd(self.stub).returncode, 5)

    def test_own_hooks_run_in_name_order(self):
        self.own_hook("20-second", "echo second")
        self.own_hook("10-first", "echo first")
        self.assertEqual(self.run_cmd(self.stub).stdout.split(), ["first", "second"])

    def test_the_first_failing_own_hook_stops_the_rest(self):
        self.own_hook("10-first", "exit 4")
        self.own_hook("20-second", "echo second")
        done = self.run_cmd(self.stub)
        self.assertEqual((done.returncode, done.stdout), (4, ""))

    def skipped_own_hook(self, name):
        self.own_hook(name, "exit 9")
        self.assertEqual(self.run_cmd(self.stub).returncode, 0)

    def test_an_own_hook_that_is_not_executable_is_skipped(self):
        self.own_hook("10-mine", "exit 9", mode=0o644)
        self.assertEqual(self.run_cmd(self.stub).returncode, 0)

    def test_commit_msg_passes_the_message_file_to_own_hooks(self):
        self.own_hook("10-mine", 'echo "got $1"', hook="commit-msg")
        done = self.run_cmd(self.target / ".githooks" / "commit-msg", "MSGFILE")
        self.assertIn("got MSGFILE", done.stdout)

    def test_a_real_commit_goes_through_the_enabled_hooks(self):
        self.own_hook("10-mine", "echo own-hook-ran >&2")
        self.run_cmd("git", "config", "core.hooksPath", ".githooks")
        self.run_cmd("git", "add", "-A")
        done = self.run_cmd("git", "commit", "-q", "-m", "first")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("own-hook-ran", done.stderr)

    def test_a_real_commit_is_refused_by_a_strict_instance_without_the_plugin(self):
        self.set_strict(True)
        self.run_cmd("git", "config", "core.hooksPath", ".githooks")
        self.run_cmd("git", "add", "-A")
        self.assertNotEqual(self.run_cmd("git", "commit", "-q", "-m", "first").returncode, 0)
        self.assertNotEqual(self.run_cmd("git", "rev-parse", "HEAD").returncode, 0)


add_cases(GitHook, "test_unreadable_strictness_refuses", {
    "no config": None, "config that is not json": "{ nope", "config without hooks": "{}",
    "strict as text": '{"hooks": {"strict": "no"}}',
}, GitHook.unreadable_strictness_refuses)
add_cases(GitHook, "test_skips_own_hook_named", {n: n for n in ["10-mine.orig", "10-mine~", ".10-mine.swp"]},
          GitHook.skipped_own_hook)


if __name__ == "__main__":
    unittest.main()
