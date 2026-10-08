import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import bump_pins  # noqa: E402

OLD = "a" * 40
NEW = "b" * 40
REAL_MARKETPLACE = Path(__file__).resolve().parent.parent / ".claude-plugin" / "marketplace.json"

MARKETPLACE = {
    "name": "shipright",
    "plugins": [
        {"name": "shipright", "source": "./plugins/shipright"},
        {"name": "gh-plugin", "source": {"source": "github", "repo": "o/r", "sha": OLD}},
        {"name": "url-plugin", "source": {"source": "url", "url": "https://github.com/o/u.git", "sha": OLD}},
        {"name": "sub-plugin", "source": {"source": "git-subdir", "url": "https://github.com/o/s.git", "path": "plugin", "sha": OLD}},
        {"name": "tag-plugin", "source": {"source": "url", "url": "https://github.com/o/t.git", "ref": "v1.2.3", "sha": OLD}},
    ],
}

LS_REMOTE_TAGS = "\n".join([
    "1" * 40 + "\trefs/tags/v6.9.0",
    "2" * 40 + "\trefs/tags/v6.10.0",        # annotated tag object
    "3" * 40 + "\trefs/tags/v6.10.0^{}",     # its peeled commit
    "4" * 40 + "\trefs/tags/v7.0.0-rc1",     # prerelease: ignored
    "5" * 40 + "\trefs/tags/cli-v9.0.0",     # other family: ignored
    "6" * 40 + "\trefs/tags/skill-v4.5.1",
])


def every_url_at(sha):
    """Resolver stub: every entry keeps its ref and resolves to `sha`."""
    return lambda url, ref: (ref, sha)


class VersionTests(unittest.TestCase):
    def test_version_of_splits_prefix_and_numbers(self):
        self.assertEqual(bump_pins.version_of("v6.4.2"), ("v", (6, 4, 2)))
        self.assertEqual(bump_pins.version_of("skill-v4.5.1"), ("skill-v", (4, 5, 1)))
        self.assertEqual(bump_pins.version_of("6.3.0"), ("", (6, 3, 0)))

    def test_version_of_rejects_prereleases_and_non_versions(self):
        self.assertIsNone(bump_pins.version_of("v7.0.0-rc1"))
        self.assertIsNone(bump_pins.version_of("latest"))


class LatestTagTests(unittest.TestCase):
    def test_picks_numerically_highest_tag_in_same_family(self):
        name, _ = bump_pins.latest_tag(LS_REMOTE_TAGS, "v6.3.0")
        self.assertEqual(name, "v6.10.0")

    def test_uses_peeled_commit_for_annotated_tags(self):
        self.assertEqual(bump_pins.latest_tag(LS_REMOTE_TAGS, "v6.3.0")[1], "3" * 40)

    def test_prefix_family_is_respected(self):
        self.assertEqual(bump_pins.latest_tag(LS_REMOTE_TAGS, "skill-v4.0.0"), ("skill-v4.5.1", "6" * 40))

    def test_none_when_no_tag_matches_family(self):
        self.assertIsNone(bump_pins.latest_tag(LS_REMOTE_TAGS, "release-1.0.0"))
        self.assertIsNone(bump_pins.latest_tag("", "v1.0.0"))


class ResolveTests(unittest.TestCase):
    def test_head_tracked_entry_asks_for_head(self):
        calls = []

        def git(*args):
            calls.append(args)
            return "9" * 40 + "\tHEAD\n"

        self.assertEqual(bump_pins.resolve("https://x/y.git", None, git=git), (None, "9" * 40))
        self.assertEqual(calls, [("ls-remote", "https://x/y.git", "HEAD")])

    def test_tag_tracked_entry_asks_for_tags(self):
        calls = []

        def git(*args):
            calls.append(args)
            return LS_REMOTE_TAGS

        self.assertEqual(bump_pins.resolve("https://x/y.git", "v6.3.0", git=git), ("v6.10.0", "3" * 40))
        self.assertEqual(calls, [("ls-remote", "--tags", "https://x/y.git")])


class BumpTests(unittest.TestCase):
    def test_git_url_shapes(self):
        self.assertEqual(bump_pins.git_url({"source": "github", "repo": "o/r"}), "https://github.com/o/r.git")
        self.assertEqual(bump_pins.git_url({"source": "url", "url": "https://x/y.git"}), "https://x/y.git")
        self.assertEqual(bump_pins.git_url({"source": "git-subdir", "url": "https://x/z.git", "path": "p"}), "https://x/z.git")

    def test_compare_link_strips_dot_git(self):
        self.assertEqual(
            bump_pins.compare_link("https://github.com/o/r.git", OLD, NEW),
            f"https://github.com/o/r/compare/{OLD}...{NEW}",
        )

    def test_bump_updates_only_moved_entries(self):
        m = copy.deepcopy(MARKETPLACE)
        moved = {"https://github.com/o/r.git": NEW}
        lines = bump_pins.bump(m, resolve=lambda url, ref: (ref, moved.get(url, OLD)))
        self.assertEqual(m["plugins"][1]["source"]["sha"], NEW)
        for i in (2, 3, 4):
            self.assertEqual(m["plugins"][i]["source"]["sha"], OLD)
        self.assertEqual(m["plugins"][0]["source"], "./plugins/shipright")
        self.assertEqual(len(lines), 1)
        self.assertIn("gh-plugin", lines[0])
        self.assertIn(f"/compare/{OLD}...{NEW}", lines[0])

    def test_bump_no_change_returns_empty(self):
        m = copy.deepcopy(MARKETPLACE)
        self.assertEqual(bump_pins.bump(m, resolve=every_url_at(OLD)), [])
        self.assertEqual(m, MARKETPLACE)

    def test_bump_passes_each_entry_ref_to_the_resolver(self):
        seen = []
        bump_pins.bump(copy.deepcopy(MARKETPLACE), resolve=lambda url, ref: seen.append((url, ref)) or (ref, OLD))
        self.assertIn(("https://github.com/o/r.git", None), seen)
        self.assertIn(("https://github.com/o/t.git", "v1.2.3"), seen)

    def test_bump_tag_tracked_entry_updates_ref_and_sha_and_names_versions(self):
        m = copy.deepcopy(MARKETPLACE)
        lines = bump_pins.bump(m, resolve=lambda url, ref: ("v1.3.0", NEW) if ref else (None, OLD))
        self.assertEqual(m["plugins"][4]["source"]["ref"], "v1.3.0")
        self.assertEqual(m["plugins"][4]["source"]["sha"], NEW)
        self.assertEqual(len(lines), 1)
        self.assertIn("`v1.2.3` → `v1.3.0`", lines[0])
        self.assertIn(f"/compare/{OLD}...{NEW}", lines[0])

    def test_bump_never_moves_a_tag_pin_backwards(self):
        m = copy.deepcopy(MARKETPLACE)
        lines = bump_pins.bump(m, resolve=lambda url, ref: ("v1.0.0", NEW) if ref else (None, OLD))
        self.assertEqual(lines, [])
        self.assertEqual(m, MARKETPLACE)

    def test_bump_skips_entry_when_resolver_finds_nothing(self):
        m = copy.deepcopy(MARKETPLACE)
        self.assertEqual(bump_pins.bump(m, resolve=lambda url, ref: None), [])
        self.assertEqual(m, MARKETPLACE)

    def test_main_returns_empty_and_leaves_file_when_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "marketplace.json"
            path.write_text(json.dumps(MARKETPLACE))
            before = path.read_bytes()
            out = bump_pins.main(["--write"], marketplace_path=path, resolve=every_url_at(OLD))
            self.assertEqual(out, "")
            self.assertEqual(path.read_bytes(), before)

    def test_main_write_rewrites_file_and_returns_summary(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "marketplace.json"
            path.write_text(json.dumps(MARKETPLACE))
            out = bump_pins.main(["--write"], marketplace_path=path, resolve=every_url_at(NEW))
            self.assertIn("gh-plugin", out)
            self.assertEqual(json.loads(path.read_text())["plugins"][1]["source"]["sha"], NEW)
            self.assertTrue(path.read_text().endswith("\n"))

    def test_main_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "marketplace.json"
            path.write_text(json.dumps(MARKETPLACE))
            out = bump_pins.main([], marketplace_path=path, resolve=every_url_at(NEW))
            self.assertIn("gh-plugin", out)
            self.assertEqual(json.loads(path.read_text()), MARKETPLACE)

    def test_real_marketplace_is_canonical_json(self):
        raw = REAL_MARKETPLACE.read_text()
        self.assertEqual(json.dumps(json.loads(raw), indent=2) + "\n", raw)


if __name__ == "__main__":
    unittest.main()
