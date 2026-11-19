"""The repository's public-safe gate: what it must catch, what it must let through, and this tree."""
import subprocess
import sys
import unittest

from support import REPO, ScratchCase, add_cases

GATE = REPO / "scripts" / "public_safe_gate.py"
sys.path.insert(0, str(REPO / "scripts"))
import public_safe_gate as gate  # noqa: E402

# Samples are assembled here so that this file holds none of the things it tests for.
KEY = "AB" + "C-" + "123"
HOME = "/" + "Users/" + "someone"
MAIL = "someone" + "@" + "mailhost.io"


class Findings(unittest.TestCase):
    def caught(self, text):
        self.assertEqual(len(gate.findings(text, "sample")), 1, text)

    def clean(self, text):
        self.assertEqual(gate.findings(text, "sample"), [], text)

    def test_a_finding_names_its_line(self):
        self.assertTrue(gate.findings("clean\n" + KEY, "sample")[0].startswith("sample:2: "))


add_cases(Findings, "test_catches", {
    "tracker key": "see " + KEY,
    "tracker key in a branch name": "feat/" + KEY.lower().upper() + "-thing",
    "two letter key": "X" + "Y-" + "7",
    "mac home path": "open " + HOME + "/code",
    "linux home path": "/" + "home/" + "someone/x",
    "e-mail address": "write to " + MAIL,
    "hosting token": "gh" + "p_" + "a" * 36,
    "fine grained token": "github" + "_pat_" + "a" * 30,
    "api key": "s" + "k-" + "a" * 30,
    "cloud key id": "AK" + "IA" + "A" * 16,
    "chat token": "xo" + "xb-" + "1" * 12,
    "private key block": "-----BEGIN OPENSSH " + "PRIVATE KEY-----",
}, Findings.caught)
add_cases(Findings, "test_allows", {
    "plain text": "a normal sentence, version 0.1.0",
    "encoding name": "written as UTF-8",
    "date standard": "an ISO-8601 date",
    "digest name": "its SHA-256",
    "no-reply address": "12345+name@users.noreply.github.com",
    "documentation address": "t@example.com",
    "lower case with digits": "python-3 and abc-12",
    "six capitals": "ABCDEF-1",
    "git remote": "git@github.com:meta-agentic/meta-os-plugin.git",
    "home variable": "${HOME}/code and ~/code",
    "at sign in a plugin id": "meta-os@meta-os-preview",
    "version pin of an action": "uses: actions/checkout@v7.0.1",
    "version pin of a package": "some-package@2.1.328",
}, Findings.clean)


class Commands(ScratchCase):
    def setUp(self):
        super().setUp()
        self.run_cmd("git", "init", "-q", "-b", "main")

    def gate(self, *args):
        return self.run_cmd(sys.executable, GATE, "-C", self.target, *args)

    def stage(self, name, text):
        (self.target / name).write_text(text, encoding="utf-8")
        self.run_cmd("git", "add", "-A")

    def commit(self, message, mail="t@example.com"):
        self.stage("f.txt", message)
        return self.run_cmd("git", "commit", "-q", "-m", message,
                            env={"GIT_AUTHOR_EMAIL": mail, "GIT_COMMITTER_EMAIL": mail})

    def test_tree_passes_clean_content(self):
        self.stage("a.md", "fine\n")
        self.assertEqual(self.gate("tree").returncode, 0)

    def test_tree_fails_on_staged_content(self):
        self.stage("a.md", "see " + KEY + "\n")
        self.assertEqual(self.gate("tree").returncode, 1)

    def test_tree_fails_on_a_file_name(self):
        self.stage(KEY + ".md", "fine\n")
        self.assertEqual(self.gate("tree").returncode, 1)

    def test_tree_ignores_what_is_not_staged(self):
        (self.target / "a.md").write_text(KEY, encoding="utf-8")
        self.assertEqual(self.gate("tree").returncode, 0)

    def test_tree_reads_the_staged_version_not_the_working_one(self):
        self.stage("a.md", KEY)
        (self.target / "a.md").write_text("cleaned later\n", encoding="utf-8")
        self.assertEqual(self.gate("tree").returncode, 1)

    def test_tree_skips_binary_files(self):
        (self.target / "a.bin").write_bytes(b"\0" + KEY.encode())
        self.run_cmd("git", "add", "-A")
        self.assertEqual(self.gate("tree").returncode, 0)

    def test_commit_msg_fails_on_a_key(self):
        (self.tmp / "msg").write_text("fix: " + KEY, encoding="utf-8")
        self.assertEqual(self.gate("commit-msg", self.tmp / "msg").returncode, 1)

    def test_commit_msg_passes_a_clean_message(self):
        (self.tmp / "msg").write_text("fix(init): keep files", encoding="utf-8")
        self.assertEqual(self.gate("commit-msg", self.tmp / "msg").returncode, 0)

    def test_history_passes_clean_commits(self):
        self.commit("feat: one")
        self.assertEqual(self.gate("history").returncode, 0)

    def test_history_fails_on_a_key_in_a_message(self):
        self.commit("feat: " + KEY)
        self.assertEqual(self.gate("history").returncode, 1)

    def test_history_fails_on_a_personal_author_address(self):
        self.commit("feat: one", mail=MAIL)
        self.assertEqual(self.gate("history").returncode, 1)

    def test_outside_a_repository_is_an_error_not_a_pass(self):
        done = self.run_cmd(sys.executable, GATE, "-C", self.tmp, "tree")
        self.assertEqual(done.returncode, 2)


class ThisRepository(unittest.TestCase):
    def test_the_files_git_tracks_or_would_track_are_public_safe(self):
        names = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z", "--cached", "--others",
                                "--exclude-standard"], capture_output=True, text=True, check=True).stdout
        found = []
        for name in filter(None, names.split("\0")):
            path = REPO / name
            if not path.is_file():
                continue
            found += gate.findings(name, "file name")
            data = path.read_bytes()
            if b"\0" not in data:
                found += gate.findings(data.decode("utf-8", "replace"), name)
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
