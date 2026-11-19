"""The plugin's content: every skill resolves the files it names, from the plugin and from an instance."""
import os
import re
import unittest

from support import PLUGIN, ScratchCase, add_cases

SKILLS = sorted(p.parent.name for p in (PLUGIN / "skills").glob("*/SKILL.md"))
EXPECTED_SKILLS = ["infoviz", "init", "multi-engine", "pack-builder", "skill-builder"]
# The instance template is the instance's own from the moment it is written: wikilinks are right there.
MARKDOWN = sorted(p for p in PLUGIN.rglob("*.md") if "instance-template" not in p.parts)
ROOT_VARIABLE = "${CLAUDE_PLUGIN_ROOT}/"
ROOT_PATH_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([A-Za-z0-9_./-]+)")
LINK_RE = re.compile(r"(?<!\!)\[[^\]\n]*\]\(([^)\s]+)\)")
LOCAL_FILE_RE = re.compile(r"`((?:references|resources)/[A-Za-z0-9_./-]+)`")
# A wikilink into the framework resolved in a clone, where the framework sat inside the instance.
FRAMEWORK_WIKILINK_RE = re.compile(
    r"\[\[(?:systems|skills|agents|hooks|scripts|pipeline|instance-template|CLAUDE|PROVENANCE)\b")


def rel(path):
    return path.relative_to(PLUGIN).as_posix()


def read(path):
    return path.read_text(encoding="utf-8")


def front_matter(path):
    text = read(path)
    if not text.startswith("---\n"):
        return {}
    block = text[4:text.index("\n---", 4)]
    return {key.strip(): value.strip().strip('"') for key, _, value in
            (line.partition(":") for line in block.splitlines()) if _}


def root_paths():
    """(file, path) for every path a document names under the plugin's folder."""
    return {f"{rel(path)} names {found.rstrip('.')}": found.rstrip(".")
            for path in MARKDOWN for found in ROOT_PATH_RE.findall(read(path))}


def relative_links():
    out = {}
    for path in MARKDOWN:
        for target in LINK_RE.findall(read(path)):
            if "://" in target or target.startswith(("#", "mailto:")) or "<" in target:
                continue                      # a web link, an anchor, or a placeholder of a skeleton
            out[f"{rel(path)} links {target}"] = (path, target.split("#", 1)[0])
    return out


def local_files():
    """(skill file, path) for every `references/…` or `resources/…` a skill names beside itself."""
    out = {}
    for name in SKILLS:
        folder = PLUGIN / "skills" / name
        for path in sorted(folder.rglob("*.md")):
            for found in LOCAL_FILE_RE.findall(read(path)):
                if "<" not in found and "resources/discipline-pack" not in path.as_posix():
                    out[f"{rel(path)} names {found}"] = (folder, found.rstrip("."))
    return out


class Skills(unittest.TestCase):
    def test_the_plugin_ships_exactly_these_skills(self):
        self.assertEqual(SKILLS, EXPECTED_SKILLS)

    def name_is_the_folder(self, name):
        self.assertEqual(front_matter(PLUGIN / "skills" / name / "SKILL.md").get("name"), name)

    def has_a_description(self, name):
        self.assertGreater(len(front_matter(PLUGIN / "skills" / name / "SKILL.md").get("description", "")), 40)

    def is_in_the_catalog(self, name):
        self.assertIn(f"(../skills/{name}/SKILL.md)", read(PLUGIN / "systems" / "skill-catalog.md"))

    def has_a_provenance_row(self, name):
        self.assertIn(f"| `{name}` |", read(PLUGIN / "PROVENANCE.md"))


for check in ("name_is_the_folder", "has_a_description", "is_in_the_catalog", "has_a_provenance_row"):
    add_cases(Skills, "test_" + check, {name: name for name in EXPECTED_SKILLS}, getattr(Skills, check))


class References(unittest.TestCase):
    """What a document names must be there: nothing points into a framework checkout any more."""

    def root_path_exists(self, found):
        self.assertTrue((PLUGIN / found).exists(), found)

    def relative_link_resolves(self, case):
        path, target = case
        self.assertTrue((path.parent / target).exists(), target)

    def local_file_exists(self, case):
        folder, found = case
        self.assertTrue((folder / found).exists(), found)

    def has_no_framework_wikilink(self, path):
        self.assertEqual(FRAMEWORK_WIKILINK_RE.findall(read(path)), [])

    def test_there_is_something_to_check(self):
        self.assertGreater(len(root_paths()), 10)
        self.assertGreater(len(relative_links()), 50)

    def test_a_skill_links_only_inside_its_own_folder(self):
        # Outside its folder a skill names a file by the plugin's variable: a relative path that
        # climbs would depend on where the plugin happens to be installed.
        for name in SKILLS:
            for target in LINK_RE.findall(read(PLUGIN / "skills" / name / "SKILL.md")):
                if "://" not in target:
                    self.assertFalse(target.startswith(("..", "/")), f"{name}: {target}")


add_cases(References, "test_plugin_path", root_paths(), References.root_path_exists)
add_cases(References, "test_link", relative_links(), References.relative_link_resolves)
add_cases(References, "test_local_file", local_files(), References.local_file_exists)
add_cases(References, "test_no_framework_wikilink", {rel(p): p for p in MARKDOWN}, References.has_no_framework_wikilink)


class FromAnInstance(ScratchCase):
    """The scenario: a session in a plugin instance finds the plugin, and under it each file a skill names.

    In a clone the same file was `<instance>/<path>`. Here the instance holds no framework file, so the
    path goes through the plugin's folder, found the way the launcher finds it.
    """

    def setUp(self):
        super().setUp()
        self.init()
        self.env["META_OS_PLUGIN_ROOT"] = str(PLUGIN)
        done = self.run_cmd(self.target / ".meta-os" / "resolver.py", "root")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.root = done.stdout.split("\t")[0]

    def resolves(self, found):
        path = os.path.join(self.root, found)
        self.assertTrue(os.path.exists(path), path)
        self.assertFalse((self.target / found).exists(), "the instance must not hold a framework file")


add_cases(FromAnInstance, "test_resolves", {label: found for label, found in root_paths().items()
                                            if label.startswith("skills/")}, FromAnInstance.resolves)


class ConfigSchema(ScratchCase):
    """The schema the plugin ships describes the config `init` writes."""

    def setUp(self):
        super().setUp()
        import json
        self.schema = json.loads(read(PLUGIN / "systems" / "meta-os.config.schema.json"))
        self.init("--backlog", "abc=../abc", "--memory-layout", "flat")
        self.config = self.read_json("meta-os.config.json")

    def test_every_key_init_writes_is_in_the_schema(self):
        self.assertEqual(set(self.config) - set(self.schema["properties"]), set())

    def test_the_instance_record_has_the_required_keys_and_no_other(self):
        record = self.schema["properties"]["instance"]
        self.assertEqual(sorted(self.config["instance"]), sorted(record["required"]))
        self.assertEqual(set(self.config["instance"]) - set(record["properties"]), set())

    def test_the_acknowledged_version_matches_its_pattern(self):
        self.assertRegex(self.config["acknowledgedPluginVersion"],
                         self.schema["properties"]["acknowledgedPluginVersion"]["pattern"])


if __name__ == "__main__":
    unittest.main()
