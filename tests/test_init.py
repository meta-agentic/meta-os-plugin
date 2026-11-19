"""`meta-os init`: writes an instance from the template, and never touches what is already there."""
import os
import unittest

from support import ALL_FILES, LOCAL_SETTINGS, PROJECT_SETTINGS, PLUGIN_VERSION, ScratchCase, TEMPLATE, add_cases, init_module


class InitIntoEmptyFolder(ScratchCase):
    def test_doctor_passes_after_init(self):
        self.init()
        done = self.meta_os("doctor")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("Healthy.", done.stdout)

    def test_writes_exactly_the_planned_files(self):
        self.init()
        self.assertEqual(sorted(self.snapshot()), sorted(ALL_FILES))

    def test_writes_no_root_claude_md(self):
        self.init()
        self.assertFalse((self.target / "CLAUDE.md").exists())

    def test_instance_contract_is_in_dot_claude(self):
        self.init("--name", "acme")
        self.assertIn("# acme", (self.target / ".claude" / "CLAUDE.md").read_text(encoding="utf-8"))

    def test_no_placeholder_of_init_is_left(self):
        self.init("--project", "demo")
        for rel, data in self.snapshot().items():
            for token in ("{{instance-name}}", "{{initialized}}", "{{plugin-version}}", "{{project-rows}}"):
                self.assertNotIn(token.encode(), data, rel)

    def test_name_defaults_to_the_folder_name(self):
        self.init()
        self.assertEqual(self.read_json("meta-os.config.json")["instance"]["name"], "scratch")

    def test_hooks_are_not_strict_by_default(self):
        self.init()
        self.assertIs(self.read_json("meta-os.config.json")["hooks"]["strict"], False)

    def test_acknowledges_the_plugin_version(self):
        self.init()
        self.assertEqual(self.read_json("meta-os.config.json")["acknowledgedPluginVersion"], PLUGIN_VERSION)

    def test_settings_enable_the_plugin(self):
        self.init()
        self.assertIs(self.read_json(LOCAL_SETTINGS)["enabledPlugins"]["meta-os@meta-os-preview"], True)

    def test_settings_name_the_marketplace(self):
        self.init()
        self.assertIn("meta-os-preview", self.read_json(LOCAL_SETTINGS)["extraKnownMarketplaces"])

    def test_gitignore_is_written_under_its_real_name(self):
        self.init()
        self.assertTrue((self.target / ".gitignore").is_file())
        self.assertFalse((self.target / "gitignore").exists())

    def test_dry_run_writes_nothing(self):
        done = self.init("--dry-run")
        self.assertEqual(self.snapshot(), {})
        self.assertIn("would create", done.stdout)

    def test_second_run_changes_nothing(self):
        self.init()
        before = self.snapshot()
        self.init("--name", "other", "--project", "late")
        after = self.snapshot()
        after.pop("projects/late.md")          # a new file may be added; no existing one may change
        self.assertEqual(after, before)

    def test_a_parent_that_is_a_file_blocks_and_fails(self):
        (self.target / "memory").write_text("mine", encoding="utf-8")
        done = self.meta_os("init")
        self.assertEqual(done.returncode, 1)
        self.assertIn("blocked", done.stdout)
        self.assertEqual((self.target / "memory").read_text(encoding="utf-8"), "mine")


class TemplateMatrix(unittest.TestCase):
    def test_every_template_file_is_planned(self):
        on_disk = sum(1 for p in TEMPLATE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
        generated = {"meta-os.config.json", LOCAL_SETTINGS, ".packs.yaml"}
        self.assertEqual(len(ALL_FILES), on_disk + len(generated))

    def test_no_template_file_would_shadow_a_generated_one(self):
        names = {rel for rel, _ in init_module.template_files()}
        self.assertFalse(names & {"meta-os.config.json", LOCAL_SETTINGS, PROJECT_SETTINGS, ".packs.yaml", "CLAUDE.md"})


class ExistingFilesAreKept(ScratchCase):
    """One case per file `init` can write: an existing one keeps its content."""

    def keeps(self, rel):
        path = self.target / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"mine, do not touch\n")
        done = self.init("--name", "acme", "--pack", "some-pack")
        self.assertEqual(path.read_bytes(), b"mine, do not touch\n")
        self.assertIn(f"kept       {rel} (exists)", done.stdout)


add_cases(ExistingFilesAreKept, "test_keeps", {rel: rel for rel in ALL_FILES}, ExistingFilesAreKept.keeps)


class RootClaudeMdIsNotTouched(ScratchCase):
    def test_an_existing_root_claude_md_keeps_its_content(self):
        (self.target / "CLAUDE.md").write_text("# my project\n", encoding="utf-8")
        self.init()
        self.assertEqual((self.target / "CLAUDE.md").read_text(encoding="utf-8"), "# my project\n")

    def test_an_existing_root_claude_md_keeps_its_modification_time(self):
        path = self.target / "CLAUDE.md"
        path.write_text("# my project\n", encoding="utf-8")
        os.utime(path, (1_000_000_000, 1_000_000_000))
        self.init()
        self.assertEqual(path.stat().st_mtime, 1_000_000_000)

    def test_a_symlinked_file_is_kept_even_when_it_dangles(self):
        (self.target / "_index.md").symlink_to(self.tmp / "nowhere.md")
        self.init()
        self.assertTrue((self.target / "_index.md").is_symlink())
        self.assertFalse((self.tmp / "nowhere.md").exists())


class Decisions(ScratchCase):
    def config(self):
        return self.read_json("meta-os.config.json")

    def test_no_backlog_flag_gives_an_empty_list(self):
        self.init()
        self.assertEqual(self.config()["backlogs"], [])

    def test_backlog_none_gives_an_empty_list(self):
        self.init("--backlog", "none")
        self.assertEqual(self.config()["backlogs"], [])

    def test_a_backlog_space_is_recorded(self):
        self.init("--backlog", "abc=../vault/abc")
        self.assertEqual(self.config()["backlogs"], [{"space": "abc", "path": "../vault/abc"}])

    def test_two_backlog_spaces_are_recorded_in_order(self):
        self.init("--backlog", "abc=a", "--backlog", "xyz=b")
        self.assertEqual([b["space"] for b in self.config()["backlogs"]], ["abc", "xyz"])

    def test_default_layout_writes_no_memory_block(self):
        self.init("--memory-layout", "default")
        self.assertNotIn("memory", self.config())

    def layout_is_recorded(self, layout):
        self.init("--memory-layout", layout)
        self.assertEqual(self.config()["memory"]["roots"][0]["layout"], layout)

    def test_a_project_gets_a_node(self):
        self.init("--project", "demo")
        self.assertIn("name: demo", (self.target / "projects" / "demo.md").read_text(encoding="utf-8"))

    def test_a_project_gets_a_row_in_the_registry(self):
        self.init("--project", "demo")
        self.assertIn("| demo | [[projects/demo\\|demo]] | | |",
                      (self.target / "projects" / "_index.md").read_text(encoding="utf-8"))

    def test_no_project_leaves_the_placeholder_row(self):
        self.init()
        self.assertIn("_(none yet)_", (self.target / "projects" / "_index.md").read_text(encoding="utf-8"))

    def test_a_pack_is_recorded_in_the_packs_file(self):
        self.init("--pack", "some-pack")
        self.assertIn("  some-pack:\n    plugin: some-pack@meta-agentic\n",
                      (self.target / ".packs.yaml").read_text(encoding="utf-8"))

    def test_a_pack_is_enabled_in_the_settings(self):
        self.init("--pack", "some-pack")
        self.assertIs(self.read_json(LOCAL_SETTINGS)["enabledPlugins"]["some-pack@meta-agentic"], True)

    def test_a_pack_brings_its_marketplace_into_the_settings(self):
        self.init("--pack", "some-pack")
        self.assertIn("meta-agentic", self.read_json(LOCAL_SETTINGS)["extraKnownMarketplaces"])

    def test_no_pack_writes_an_empty_packs_file(self):
        self.init()
        self.assertIn("packs: {}\n", (self.target / ".packs.yaml").read_text(encoding="utf-8"))

    def test_no_pack_leaves_the_pack_marketplace_out(self):
        self.init()
        self.assertNotIn("meta-agentic", self.read_json(LOCAL_SETTINGS)["extraKnownMarketplaces"])

    def test_answers_for_a_kept_config_are_reported_as_by_hand(self):
        (self.target / "meta-os.config.json").write_text("{}", encoding="utf-8")
        done = self.init("--backlog", "abc=a")
        self.assertIn("Apply your answers by hand in: meta-os.config.json", done.stdout)


add_cases(Decisions, "test_layout_is_recorded", {l: l for l in init_module.LAYOUTS if l != "default"},
          Decisions.layout_is_recorded)


class WrongArguments(ScratchCase):
    """Each wrong value is refused with exit 2 and writes nothing."""

    def refused(self, args):
        done = self.meta_os("init", *args)
        self.assertEqual(done.returncode, 2, done.stdout + done.stderr)
        self.assertEqual(self.snapshot(), {})


add_cases(WrongArguments, "test_refuses", {
    "name with a slash": ["--name", "a/b"],
    "name that climbs": ["--name", ".."],
    "name with a space": ["--name", "a b"],
    "project that climbs": ["--project", "../x"],
    "project with a slash": ["--project", "a/b"],
    "project named _index": ["--project", "_index"],
    "pack with capitals": ["--pack", "Some-Pack"],
    "pack with a marketplace": ["--pack", "some-pack@elsewhere"],
    "pack with a line break": ["--pack", "a\nb"],
    "backlog without a path": ["--backlog", "abc"],
    "backlog with an empty path": ["--backlog", "abc="],
    "backlog with a bad space": ["--backlog", "1abc=x"],
    "backlog none with another": ["--backlog", "none", "--backlog", "abc=x"],
    "backlog space twice": ["--backlog", "abc=x", "--backlog", "abc=y"],
    "unknown layout": ["--memory-layout", "tree"],
    "unknown scope": ["--scope", "everywhere"],
    "target that is not a folder": ["--target", "missing-folder"],
}, WrongArguments.refused)


class PackInstallLines(ScratchCase):
    """`init` installs no second copy: it says where a chosen pack already is."""

    def entry(self, version, project=None):
        found = {"scope": "project" if project else "user", "installPath": str(self.tmp / "p" / version),
                 "version": version}
        if project:
            found["projectPath"] = str(project)
        return found

    def line(self):
        return [l for l in self.init("--pack", "some-pack").stdout.splitlines() if l.startswith("  some-pack:")][0]

    def test_not_installed_prints_the_local_install_command_by_default(self):
        self.assertIn("claude plugin install some-pack@meta-agentic --scope local", self.line())

    def test_not_installed_prints_the_project_install_command_for_project_scope(self):
        line = [l for l in self.init("--pack", "some-pack", "--scope", "project").stdout.splitlines()
                if l.startswith("  some-pack:")][0]
        self.assertIn("claude plugin install some-pack@meta-agentic --scope project", line)

    def test_installed_for_the_user_needs_no_install(self):
        self.write_record({"some-pack@meta-agentic": [self.entry("1.0.0")]})
        self.assertIn("already installed for you on this machine (1.0.0); recorded in .packs.yaml only: "
                      "nothing is installed again and nothing changes", self.line())

    def test_installed_for_this_project_needs_no_install(self):
        self.write_record({"some-pack@meta-agentic": [self.entry("1.1.0", self.target)]})
        self.assertIn("already installed for this project (1.1.0); recorded in .packs.yaml only", self.line())

    def test_installed_at_both_levels_reports_the_project_one(self):
        self.write_record({"some-pack@meta-agentic": [self.entry("1.0.0"), self.entry("1.1.0", self.target)]})
        self.assertIn("installed for this project (1.1.0)", self.line())

    def test_installed_for_another_project_counts_as_not_installed(self):
        self.write_record({"some-pack@meta-agentic": [self.entry("1.0.0", self.tmp / "elsewhere")]})
        self.assertIn("not installed", self.line())

    def test_an_unreadable_record_counts_as_not_installed(self):
        (self.config_dir / "plugins" / "installed_plugins.json").write_text("{ not json", encoding="utf-8")
        self.assertIn("not installed", self.line())


class LauncherFiles(ScratchCase):
    def is_executable(self, rel):
        self.init()
        self.assertTrue(os.access(self.target / rel, os.X_OK), rel)


add_cases(LauncherFiles, "test_is_executable", {rel: rel for rel in sorted(init_module.EXECUTABLE)},
          LauncherFiles.is_executable)


if __name__ == "__main__":
    unittest.main()


class Scope(ScratchCase):
    """`--scope` decides which settings file enables the plugin: one file, never both."""

    def test_local_scope_is_the_default_and_writes_only_the_local_file(self):
        self.init()
        self.assertTrue((self.target / LOCAL_SETTINGS).is_file())
        self.assertFalse((self.target / PROJECT_SETTINGS).exists())

    def test_project_scope_writes_only_the_committed_file(self):
        self.init("--scope", "project")
        self.assertTrue((self.target / PROJECT_SETTINGS).is_file())
        self.assertFalse((self.target / LOCAL_SETTINGS).exists())

    def test_project_scope_enables_the_plugin(self):
        self.init("--scope", "project")
        self.assertIs(self.read_json(PROJECT_SETTINGS)["enabledPlugins"]["meta-os@meta-os-preview"], True)

    def test_the_local_settings_file_is_not_committed(self):
        self.init()
        ignore = (self.target / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".claude/*", ignore)
        self.assertNotIn("!" + LOCAL_SETTINGS, ignore)

    def test_doctor_passes_for_project_scope(self):
        self.init("--scope", "project")
        self.assertEqual(self.meta_os("doctor").returncode, 0)
