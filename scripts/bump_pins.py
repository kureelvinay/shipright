#!/usr/bin/env python3
"""Bump pinned third-party plugin SHAs in .claude-plugin/marketplace.json to each
upstream's default-branch HEAD.

    python3 scripts/bump_pins.py          # dry run: print markdown summary of what would change
    python3 scripts/bump_pins.py --write  # also rewrite marketplace.json

Prints nothing when every pin is already current. Exit code is 0 either way.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

MARKETPLACE = Path(__file__).resolve().parent.parent / ".claude-plugin" / "marketplace.json"


def git_url(source):
    """Clone URL for a marketplace `source` object (github / url / git-subdir)."""
    if source["source"] == "github":
        return "https://github.com/%s.git" % source["repo"]
    return source["url"]


def compare_link(url, old, new):
    return "%s/compare/%s...%s" % (re.sub(r"\.git$", "", url), old, new)


def resolve_head(url):
    out = subprocess.run(["git", "ls-remote", url, "HEAD"], capture_output=True, text=True, check=True).stdout
    return out.split()[0]


def bump(marketplace, resolve=resolve_head):
    """Update every pinned entry in place; return one markdown line per changed plugin."""
    lines = []
    for plugin in marketplace["plugins"]:
        source = plugin.get("source")
        if not isinstance(source, dict) or "sha" not in source:
            continue
        url = git_url(source)
        old, new = source["sha"], resolve(url)
        if new != old:
            source["sha"] = new
            lines.append("- **%s**: `%s` → `%s` ([compare](%s))" % (plugin["name"], old[:12], new[:12], compare_link(url, old, new)))
    return lines


def main(argv, marketplace_path=MARKETPLACE, resolve=resolve_head):
    """Run the CLI: bump pins in marketplace_path, write back when --write is given,
    return the markdown summary ("" when nothing moved)."""
    data = json.loads(marketplace_path.read_text())
    changed = bump(data, resolve=resolve)
    if changed and "--write" in argv:
        marketplace_path.write_text(json.dumps(data, indent=2) + "\n")
    return "\n".join(changed)


if __name__ == "__main__":
    summary = main(sys.argv[1:])
    if summary:
        print(summary)
