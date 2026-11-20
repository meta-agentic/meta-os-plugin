"""`meta-os doctor`: exit 0 on a healthy instance, 1 with the reason otherwise; it only reads."""
import json
import unittest

from support import ALL_FILES, PLUGIN_VERSION, ScratchCase, add_cases

# What an instance may lose and stay healthy. Every other file `init` writes is required, so a
# file added to the template is required by default until it is listed here on purpose.
OPTIONAL = {rel for rel in ALL_FILES if rel.startswith((".obsidian/", "templates/")) and rel != "templates/_index.md"}
OPTIONAL |= {".gitignore", ".githooks.d/README.md"}
REQUIRED = [rel for rel in ALL_FILES if rel not in OPTIONAL]


class Doctor(ScratchCase):
    def doctor(self, *args, **kwargs):
        return self.meta_os("doctor", *args, **kwargs)

    def test_an_empty_folder_is_not_an_instance(self):
        done = self.doctor()
        self.assertEqual(done.returncode, 1)
        self.assertIn("not a meta-os instance", done.stdout)

    def test_a_fresh_instance_is_healthy(self):
        self.init()
        self.assertEqual(self.doctor().returncode, 0)

    def test_target_names_another_folder(self):
        self.init()
        self.assertEqual(self.doctor("--target", self.target, cwd=self.tmp).returncode, 0)

    def test_doctor_writes_nothing(self):
        self.init()
        before = self.snapshot()
        self.doctor()
        self.assertEqual(self.snapshot(), before)

    def missing_file_is_a_problem(self, rel):
        self.init()
        (self.target / rel).unlink()
        done = self.doctor()
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn("problem", done.stdout)

    def missing_file_is_tolerated(self, rel):
        self.init()
        (self.target / rel).unlink()
        self.assertEqual(self.doctor().returncode, 0)

    def change_config(self, change):
        self.init()
        path = self.target / "meta-os.config.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        change(config)
        path.write_text(json.dumps(config), encoding="utf-8")
        return self.doctor()

    def bad_config_is_a_problem(self, change):
        done = self.change_config(change)
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn("meta-os.config.json", done.stdout)

    def test_config_that_is_not_json_is_a_problem(self):
        self.init()
        (self.target / "meta-os.config.json").write_text("{ not json", encoding="utf-8")
        self.assertEqual(self.doctor().returncode, 1)

    def test_config_that_is_not_an_object_is_a_problem(self):
        self.init()
        (self.target / "meta-os.config.json").write_text("[]", encoding="utf-8")
        self.assertEqual(self.doctor().returncode, 1)

    def test_strict_hooks_are_healthy(self):
        self.assertEqual(self.change_config(lambda c: c["hooks"].update(strict=True)).returncode, 0)

    def test_an_older_acknowledged_version_is_a_note(self):
        done = self.change_config(lambda c: c.update(acknowledgedPluginVersion="0.0.1"))
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("acknowledgement is pending", done.stdout)

    def test_a_newer_acknowledged_version_is_a_problem(self):
        done = self.change_config(lambda c: c.update(acknowledgedPluginVersion="99.0.0"))
        self.assertEqual(done.returncode, 1)
        self.assertIn("update the plugin", done.stdout)

    def test_the_acknowledged_version_of_a_fresh_instance_is_the_plugin_s(self):
        self.assertNotIn("pending", self.change_config(lambda c: None).stdout)
        self.assertRegex(PLUGIN_VERSION, r"^\d+\.\d+\.\d+$")

    def change_settings(self, change):
        self.init()
        path = self.target / ".claude" / "settings.local.json"
        settings = json.loads(path.read_text(encoding="utf-8"))
        change(settings)
        path.write_text(json.dumps(settings), encoding="utf-8")
        return self.doctor()

    def bad_settings_are_a_problem(self, change):
        done = self.change_settings(change)
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn(".claude/settings.local.json", done.stdout)

    def test_settings_that_are_a_list_are_a_problem(self):
        self.init()
        (self.target / ".claude" / "settings.local.json").write_text("[]", encoding="utf-8")
        self.assertEqual(self.doctor().returncode, 1)

    def test_settings_with_other_keys_stay_healthy(self):
        self.assertEqual(self.change_settings(lambda s: s.update(permissions={"allow": []})).returncode, 0)

    def test_the_plugin_from_another_marketplace_is_healthy(self):
        def move(settings):
            settings["enabledPlugins"] = {"meta-os@elsewhere": True}
            settings["extraKnownMarketplaces"] = {"elsewhere": {"source": {"source": "github", "repo": "a/b"}}}
        self.assertEqual(self.change_settings(move).returncode, 0)

    def test_no_settings_file_at_all_is_a_problem(self):
        self.init()
        (self.target / ".claude" / "settings.local.json").unlink()
        done = self.doctor()
        self.assertEqual(done.returncode, 1)
        self.assertIn("neither exists", done.stdout)

    def test_a_changed_launcher_is_a_note(self):
        self.init()
        with open(self.target / ".meta-os" / "meta-os", "a", encoding="utf-8") as handle:
            handle.write("# local change\n")
        done = self.doctor()
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("init --refresh-launcher", done.stdout)

    def test_refresh_launcher_clears_the_note(self):
        self.init()
        with open(self.target / ".meta-os" / "meta-os", "a", encoding="utf-8") as handle:
            handle.write("# local change\n")
        self.init("--refresh-launcher")
        self.assertNotIn("refresh-launcher", self.doctor().stdout)

    def test_refresh_launcher_touches_only_the_launcher(self):
        self.init()
        (self.target / "_index.md").write_text("mine\n", encoding="utf-8")
        (self.target / ".meta-os" / "VERSION").write_text("0\n", encoding="utf-8")
        before = self.snapshot()
        self.init("--refresh-launcher")
        changed = {rel for rel, data in self.snapshot().items() if before.get(rel) != data}
        self.assertEqual(changed, {".meta-os/VERSION"})

    def test_refresh_launcher_refuses_a_folder_that_is_not_an_instance(self):
        done = self.meta_os("init", "--refresh-launcher")
        self.assertEqual(done.returncode, 1)
        self.assertEqual(self.snapshot(), {})

    def not_executable_is_a_problem(self, rel):
        self.init()
        (self.target / rel).chmod(0o644)
        done = self.doctor()
        self.assertEqual(done.returncode, 1)
        self.assertIn("not executable", done.stdout)

    def test_a_folder_outside_git_gets_a_note(self):
        self.init()
        self.assertIn("not a git repository", self.doctor().stdout)

    def test_hooks_that_are_off_get_a_note(self):
        self.init()
        self.run_cmd("git", "init", "-q")
        self.assertIn("git hooks are off", self.doctor().stdout)

    def test_hooks_that_are_on_get_no_note(self):
        self.init()
        self.run_cmd("git", "init", "-q")
        self.run_cmd("git", "config", "core.hooksPath", ".githooks")
        self.assertNotIn("git hooks are off", self.doctor().stdout)


add_cases(Doctor, "test_missing_is_a_problem", {rel: rel for rel in REQUIRED}, Doctor.missing_file_is_a_problem)
add_cases(Doctor, "test_missing_is_tolerated", {rel: rel for rel in sorted(OPTIONAL)}, Doctor.missing_file_is_tolerated)
add_cases(Doctor, "test_bad_config", {
    "no instance block": lambda c: c.pop("instance"),
    "empty instance name": lambda c: c["instance"].update(name=""),
    "no hooks block": lambda c: c.pop("hooks"),
    "strict as text": lambda c: c["hooks"].update(strict="false"),
    "no acknowledged version": lambda c: c.pop("acknowledgedPluginVersion"),
    "acknowledged version that is not a version": lambda c: c.update(acknowledgedPluginVersion="latest"),
}, Doctor.bad_config_is_a_problem)
add_cases(Doctor, "test_bad_settings", {
    "no enabled plugins": lambda s: s.pop("enabledPlugins"),
    "plugin switched off": lambda s: s["enabledPlugins"].update({"meta-os@meta-agentic": False}),
    "only another plugin": lambda s: s.update(enabledPlugins={"other@meta-os-preview": True}),
    "no marketplace": lambda s: s.pop("extraKnownMarketplaces"),
    "another marketplace only": lambda s: s.update(extraKnownMarketplaces={"elsewhere": {}}),
}, Doctor.bad_settings_are_a_problem)
add_cases(Doctor, "test_not_executable", {rel: rel for rel in [
    ".meta-os/meta-os", ".meta-os/git-hook", ".githooks/pre-commit", ".githooks/commit-msg",
]}, Doctor.not_executable_is_a_problem)


if __name__ == "__main__":
    unittest.main()
