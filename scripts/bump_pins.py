#!/usr/bin/env python3
"""Bump pinned third-party plugin SHAs in .claude-plugin/marketplace.json.

An entry with a `ref` (e.g. "v6.3.0") is tag-tracked: it moves to the newest tag of
the same family (same prefix, strict X.Y.Z ending) and never backwards. An entry
with only a `sha` is HEAD-tracked: it moves to the upstream default branch.

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
VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)$")


def git_url(source):
    """Clone URL for a marketplace `source` object (github / url / git-subdir)."""
    if source["source"] == "github":
        return "https://github.com/%s.git" % source["repo"]
    return source["url"]


def compare_link(url, old, new):
    return "%s/compare/%s...%s" % (re.sub(r"\.git$", "", url), old, new)


def version_of(tag):
    """(prefix, (major, minor, patch)) for a tag ending in X.Y.Z; None otherwise.
    'skill-v4.5.1' -> ('skill-v', (4, 5, 1)). Prereleases like 'v7.0.0-rc1' are None."""
    m = VERSION_RE.search(tag)
    if not m:
        return None
    return tag[: m.start()], tuple(int(x) for x in m.groups())


def latest_tag(ls_remote_output, current_ref):
    """Newest tag in current_ref's family from `git ls-remote --tags` output, as
    (name, commit sha); annotated tags use their peeled commit. None when no tag matches."""
    prefix = version_of(current_ref)[0]
    peeled, best = {}, None
    for line in ls_remote_output.splitlines():
        sha, _, ref = line.partition("\t")
        name = ref[len("refs/tags/"):]
        if name.endswith("^{}"):
            peeled[name[:-3]] = sha
            continue
        parsed = version_of(name)
        if parsed and parsed[0] == prefix and (best is None or parsed[1] > best[0]):
            best = (parsed[1], name, sha)
    if best is None:
        return None
    _, name, sha = best
    return name, peeled.get(name, sha)


def git_output(*args):
    # stderr is left alone so a failing ls-remote shows git's reason in CI logs
    return subprocess.run(["git", *args], stdout=subprocess.PIPE, text=True, check=True).stdout


def resolve(url, current_ref, git=git_output):
    """What to pin: (tag, sha) for a tag-tracked entry, (None, HEAD sha) for a HEAD-tracked one.
    None when a tag-tracked entry's family has no tags."""
    if current_ref is None:
        return None, git("ls-remote", url, "HEAD").split()[0]
    return latest_tag(git("ls-remote", "--tags", url), current_ref)


def bump(marketplace, resolve=resolve):
    """Update every pinned entry in place; return one markdown line per changed plugin."""
    lines = []
    for plugin in marketplace["plugins"]:
        source = plugin.get("source")
        if not isinstance(source, dict) or "sha" not in source:
            continue
        url, old_ref, old = git_url(source), source.get("ref"), source["sha"]
        found = resolve(url, old_ref)
        if not found or found[1] == old:
            continue
        new_ref, new = found
        if old_ref:
            if version_of(new_ref)[1] < version_of(old_ref)[1]:
                continue
            source["ref"] = new_ref
            change = "`%s` → `%s`" % (old_ref, new_ref)
        else:
            change = "`%s` → `%s`" % (old[:12], new[:12])
        source["sha"] = new
        lines.append("- **%s**: %s ([compare](%s))" % (plugin["name"], change, compare_link(url, old, new)))
    return lines


def main(argv, marketplace_path=MARKETPLACE, resolve=resolve):
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
