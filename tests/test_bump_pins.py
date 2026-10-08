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

MARKETPLACE = {
    "name": "shipright",
    "plugins": [
        {"name": "shipright", "source": "./plugins/shipright"},
        {"name": "gh-plugin", "source": {"source": "github", "repo": "o/r", "sha": OLD}},
        {"name": "url-plugin", "source": {"source": "url", "url": "https://github.com/o/u.git", "sha": OLD}},
        {"name": "sub-plugin", "source": {"source": "git-subdir", "url": "https://github.com/o/s.git", "path": "plugin", "sha": OLD}},
    ],
}


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
        lines = bump_pins.bump(m, resolve=lambda url: moved.get(url, OLD))
        self.assertEqual(m["plugins"][1]["source"]["sha"], NEW)
        self.assertEqual(m["plugins"][2]["source"]["sha"], OLD)
        self.assertEqual(m["plugins"][3]["source"]["sha"], OLD)
        self.assertEqual(m["plugins"][0]["source"], "./plugins/shipright")
        self.assertEqual(len(lines), 1)
        self.assertIn("gh-plugin", lines[0])
        self.assertIn(f"/compare/{OLD}...{NEW}", lines[0])

    def test_bump_no_change_returns_empty(self):
        m = copy.deepcopy(MARKETPLACE)
        self.assertEqual(bump_pins.bump(m, resolve=lambda url: OLD), [])
        self.assertEqual(m, MARKETPLACE)

    def test_main_returns_empty_and_leaves_file_when_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "marketplace.json"
            path.write_text(json.dumps(MARKETPLACE))
            out = bump_pins.main(["--write"], marketplace_path=path, resolve=lambda url: OLD)
            self.assertEqual(out, "")
            self.assertEqual(json.loads(path.read_text()), MARKETPLACE)

    def test_main_write_rewrites_file_and_returns_summary(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "marketplace.json"
            path.write_text(json.dumps(MARKETPLACE))
            out = bump_pins.main(["--write"], marketplace_path=path, resolve=lambda url: NEW)
            self.assertIn("gh-plugin", out)
            self.assertEqual(json.loads(path.read_text())["plugins"][1]["source"]["sha"], NEW)
            self.assertTrue(path.read_text().endswith("\n"))

    def test_main_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "marketplace.json"
            path.write_text(json.dumps(MARKETPLACE))
            out = bump_pins.main([], marketplace_path=path, resolve=lambda url: NEW)
            self.assertIn("gh-plugin", out)
            self.assertEqual(json.loads(path.read_text()), MARKETPLACE)


if __name__ == "__main__":
    unittest.main()
