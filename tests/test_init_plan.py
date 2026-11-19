"""`meta-os init --plan`: one screen with every answer and what would be written; it writes nothing."""
import shlex
import unittest

from support import ALL_FILES, ScratchCase, add_cases

SETTINGS = ("Name", "Backlog", "Memory", "Project", "Packs", "Scope")
ANSWERS = {
    # label: (flags, the row it changes, what that row must say)
    "name": (["--name", "acme"], "Name", "acme"),
    "backlog": (["--backlog", "abc=../vault/abc"], "Backlog", "abc in ../vault/abc"),
    "memory layout": (["--memory-layout", "flat"], "Memory", "flat:"),
    "project": (["--project", "demo"], "Project", "demo"),
    "pack": (["--pack", "some-pack"], "Packs", "some-pack"),
    "scope": (["--scope", "project"], "Scope", "project:"),
}


class Plan(ScratchCase):
    def plan(self, *args):
        done = self.meta_os("init", "--plan", *args)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        return done.stdout

    def row(self, text, label):
        rows = [line for line in text.splitlines() if line.startswith(f"  {label} ")]
        self.assertEqual(len(rows), 1, text)
        return rows[0]

    def command(self, text):
        lines = [line for line in text.splitlines() if line.startswith("To write it: ")]
        self.assertEqual(len(lines), 1, text)
        return shlex.split(lines[0][len("To write it: "):])

    def test_it_writes_nothing(self):
        self.plan("--name", "acme", "--project", "demo", "--pack", "some-pack")
        self.assertEqual(self.snapshot(), {})

    def test_it_fits_one_screen(self):
        self.assertLessEqual(len(self.plan().splitlines()), 20)

    def test_it_says_nothing_is_written_yet(self):
        self.assertIn("nothing is written yet", self.plan().splitlines()[0])

    def test_the_name_defaults_to_the_folder(self):
        self.assertIn("scratch   (default: the folder's name)", self.row(self.plan(), "Name"))

    def test_it_counts_the_files_it_would_write(self):
        self.assertIn(f"{len(ALL_FILES)} new files", self.row(self.plan(), "Writes"))

    def test_it_says_what_it_never_touches(self):
        self.assertIn("./CLAUDE.md", self.row(self.plan(), "Never"))

    def test_an_existing_file_is_named_as_kept(self):
        (self.target / "_index.md").write_text("mine\n", encoding="utf-8")
        self.assertIn("1 existing file, unchanged: _index.md", self.row(self.plan(), "Keeps"))

    def test_an_existing_file_is_not_counted_as_written(self):
        (self.target / "_index.md").write_text("mine\n", encoding="utf-8")
        self.assertIn(f"{len(ALL_FILES) - 1} new files", self.row(self.plan(), "Writes"))

    def test_a_blocked_path_is_named_and_fails(self):
        (self.target / "memory").write_text("mine", encoding="utf-8")
        done = self.meta_os("init", "--plan")
        self.assertEqual(done.returncode, 1)
        self.assertIn("memory/_index.md", self.row(done.stdout, "Blocked"))

    def test_a_wrong_answer_is_refused_before_any_plan(self):
        done = self.meta_os("init", "--plan", "--name", "../escape")
        self.assertEqual((done.returncode, done.stdout), (2, ""))

    def test_a_chosen_pack_gets_its_install_line(self):
        self.assertIn("claude plugin install some-pack@meta-agentic --scope local", self.plan("--pack", "some-pack"))

    def test_the_printed_command_writes_what_the_plan_counted(self):
        text = self.plan("--project", "demo", "--backlog", "abc=../vault/abc")
        done = self.meta_os(*self.command(text)[1:])
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn(f"{len(self.snapshot())} new files", self.row(text, "Writes"))

    def default_is_marked(self, label):
        self.assertIn("(default", self.row(self.plan(), label))

    def answer_is_shown(self, case):
        flags, label, expected = case
        self.assertIn(expected, self.row(self.plan(*flags), label))

    def answer_is_not_marked_default(self, case):
        flags, label, _ = case
        self.assertNotIn("(default", self.row(self.plan(*flags), label))

    def answer_is_in_the_command(self, case):
        flags, _, _ = case
        command = self.command(self.plan(*flags))
        self.assertEqual(command[:2], ["meta-os", "init"])
        self.assertIn(" ".join(flags), " ".join(command))

    def default_is_not_in_the_command(self, case):
        flags, _, _ = case
        if flags[0] != "--name":              # the name is always passed: the plan fixed it
            self.assertNotIn(flags[0], self.command(self.plan()))


add_cases(Plan, "test_default_is_marked", {label: label for label in SETTINGS}, Plan.default_is_marked)
add_cases(Plan, "test_answer_is_shown", ANSWERS, Plan.answer_is_shown)
add_cases(Plan, "test_answer_is_not_marked_default", ANSWERS, Plan.answer_is_not_marked_default)
add_cases(Plan, "test_answer_is_in_the_command", ANSWERS, Plan.answer_is_in_the_command)
add_cases(Plan, "test_default_is_not_in_the_command", ANSWERS, Plan.default_is_not_in_the_command)


if __name__ == "__main__":
    unittest.main()
