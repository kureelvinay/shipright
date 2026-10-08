# ShipRight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `<org>/shipright` repo: a Claude Code marketplace plus one bundle plugin that installs the company-standard skills and process on any engineer's machine with two commands.

**Architecture:** A git repo whose `.claude-plugin/marketplace.json` lists six plugins: `shipright` (local, under `plugins/shipright/`, holding five of our own skills and a SessionStart nudge hook) and five third-party plugins pinned by commit SHA. `shipright` declares the five as `dependencies`, so one install pulls everything. Two GitHub Actions workflows keep it honest: `validate.yml` runs `claude plugin validate` on every PR, and `bump-pins.yml` opens a reviewable PR whenever an upstream repo moves.

**Tech Stack:** Claude Code plugin system (marketplace.json, plugin.json, hooks.json, SKILL.md), Python 3.9+ stdlib (one 40-line script + unittest), GitHub Actions, `gh` CLI.

**Spec:** `docs/superpowers/specs/2026-10-08-shipright-design.md`

## Global Constraints

- Plugin name and marketplace name are both exactly `shipright` (lowercase). Display name "ShipRight" appears only in prose and descriptions.
- `<org>` stays a literal placeholder in every file until Task 8 step 1 replaces it. Never invent an org name.
- SKILL.md files are copied byte-for-byte. No edits to any skill content.
- The hook uses only `cat`. No Node, no scripts, no extra files beyond `hooks.json` and `welcome.md`.
- Third-party entries carry a 40-hex `sha` and no `ref`. Descriptions are version-free.
- All commands run from the repo root `~/code/shipright` unless a step says otherwise.
- The `claude` CLI must be on PATH (Task 1 installs it). Local Python is 3.9: no `match` statements, no `X | Y` type unions.
- Every commit message ends with the trailer `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` (shown in each commit step).
- Never push to GitHub before Task 8, and never merge anything; the user merges.

---

### Task 1: Plugin manifest and CLI prerequisite

**Files:**
- Create: `plugins/shipright/.claude-plugin/plugin.json`

**Interfaces:**
- Consumes: nothing
- Produces: plugin name `shipright`, version `1.0.0`, dependency names `superpowers`, `impeccable`, `taste-skill`, `ponytail`, `understand-anything` (Task 4's marketplace entries must use exactly these names)

- [ ] **Step 1: Install the Claude Code CLI if `claude` is not on PATH**

Run:
```bash
command -v claude || npm i -g @anthropic-ai/claude-code
claude --version
claude plugin validate --help | head -5
```
Expected: a version string, and help text mentioning `validate`.

- [ ] **Step 2: Write the manifest**

Create `plugins/shipright/.claude-plugin/plugin.json`:
```json
{
  "name": "shipright",
  "version": "1.0.0",
  "description": "ShipRight: the <org> AI-PDLC standard. Ship features end to end with one human checkpoint, gate PRs on branch coverage, and understand any codebase.",
  "author": { "name": "<org> Engineering" },
  "dependencies": ["superpowers", "impeccable", "taste-skill", "ponytail", "understand-anything"]
}
```

- [ ] **Step 3: Validate**

Run: `claude plugin validate plugins/shipright --strict`
Expected: output reporting the manifest is valid (no errors). If it warns that `dependencies` cannot be resolved because no marketplace is present, that is expected until Task 4; errors about JSON shape are not.

- [ ] **Step 4: Commit**

```bash
git add plugins/shipright/.claude-plugin/plugin.json
git commit -m "Add shipright plugin manifest with dependencies" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Copy our five skills into the plugin, unchanged

**Files:**
- Create: `plugins/shipright/skills/ship/SKILL.md`
- Create: `plugins/shipright/skills/graphify/SKILL.md`, `plugins/shipright/skills/graphify/.graphify_version`, `plugins/shipright/skills/graphify/references/*.md` (8 files)
- Create: `plugins/shipright/skills/branch-audit/SKILL.md`
- Create: `plugins/shipright/skills/pr-branch-guard/SKILL.md`
- Create: `plugins/shipright/skills/patch-uncovered-branches/SKILL.md`

**Interfaces:**
- Consumes: source skills at `~/.claude/skills/ship`, `~/.claude/skills/graphify`, `~/Downloads/branch-coverage-skills/{branch-audit,pr-branch-guard,patch-uncovered-branches}`
- Produces: skill directories whose names become `/shipright:ship`, `/shipright:graphify`, `/shipright:branch-audit`, `/shipright:pr-branch-guard`, `/shipright:patch-uncovered-branches`

- [ ] **Step 1: Copy**

Run:
```bash
mkdir -p plugins/shipright/skills
cp -R ~/.claude/skills/ship plugins/shipright/skills/ship
cp -R ~/.claude/skills/graphify plugins/shipright/skills/graphify
for s in branch-audit pr-branch-guard patch-uncovered-branches; do
  mkdir -p "plugins/shipright/skills/$s"
  cp ~/Downloads/branch-coverage-skills/$s/SKILL.md "plugins/shipright/skills/$s/SKILL.md"
done
find plugins/shipright/skills -name .DS_Store -delete
```

- [ ] **Step 2: Verify byte-for-byte copies**

Run:
```bash
diff -r ~/.claude/skills/ship plugins/shipright/skills/ship && echo ship OK
diff -r ~/.claude/skills/graphify plugins/shipright/skills/graphify && echo graphify OK
for s in branch-audit pr-branch-guard patch-uncovered-branches; do
  diff ~/Downloads/branch-coverage-skills/$s/SKILL.md plugins/shipright/skills/$s/SKILL.md && echo "$s OK"
done
ls plugins/shipright/skills
```
Expected: five `OK` lines and a listing of exactly `branch-audit graphify patch-uncovered-branches pr-branch-guard ship`.

- [ ] **Step 3: Validate the plugin still passes**

Run: `claude plugin validate plugins/shipright --strict`
Expected: valid, five skills discovered (if the output lists components).

- [ ] **Step 4: Commit**

```bash
git add plugins/shipright/skills
git commit -m "Add ship, graphify and branch-coverage skills to shipright plugin" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: SessionStart nudge hook

**Files:**
- Create: `plugins/shipright/hooks/hooks.json`
- Create: `plugins/shipright/hooks/welcome.md`

**Interfaces:**
- Consumes: `$CLAUDE_PLUGIN_ROOT`, set by Claude Code to the installed plugin directory when it runs the hook
- Produces: the text of `welcome.md` injected into context at session start, resume, `/clear`, and compaction

- [ ] **Step 1: Write the nudge text**

Create `plugins/shipright/hooks/welcome.md`:
```
SHIPRIGHT ACTIVE — <org> engineering standard for Claude Code.

Use the standard flow, not ad-hoc edits:
- New feature or bug fix → /shipright:ship  (brainstorm → plan → build → review → verify → PR; one human checkpoint: plan approval)
- Before opening any PR by hand → /shipright:pr-branch-guard
- Writing tests for uncovered paths → /shipright:patch-uncovered-branches
- Release health / test-gap triage → /shipright:branch-audit
- Unfamiliar codebase → /shipright:graphify or /understand-anything:understand
- UI changes → impeccable runs inside /ship; on demand: /impeccable:impeccable audit

Ponytail (lazy senior dev) is on: smallest working diff, no speculative abstractions.
Process guide: https://github.com/<org>/shipright#readme
```

- [ ] **Step 2: Write the hook config**

Create `plugins/shipright/hooks/hooks.json`:
```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact",
        "hooks": [
          {
            "type": "command",
            "command": "cat \"$CLAUDE_PLUGIN_ROOT/hooks/welcome.md\"",
            "timeout": 5,
            "statusMessage": "Loading ShipRight..."
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 3: Test the hook command exactly as Claude Code will run it**

Run:
```bash
python3 -m json.tool plugins/shipright/hooks/hooks.json >/dev/null && echo JSON OK
CLAUDE_PLUGIN_ROOT="$PWD/plugins/shipright" sh -c "$(python3 -c "import json;print(json.load(open('plugins/shipright/hooks/hooks.json'))['hooks']['SessionStart'][0]['hooks'][0]['command'])")" | head -1
```
Expected: `JSON OK`, then `SHIPRIGHT ACTIVE — <org> engineering standard for Claude Code.`

- [ ] **Step 4: Validate**

Run: `claude plugin validate plugins/shipright --strict`
Expected: valid, hooks discovered.

- [ ] **Step 5: Commit**

```bash
git add plugins/shipright/hooks
git commit -m "Add SessionStart nudge hook" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Marketplace manifest with SHA pins, plus clean-profile install test

**Files:**
- Create: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: plugin name `shipright` and dependency names from Task 1
- Produces: marketplace named `shipright` with six entries; the install string `shipright@shipright` used by README (Task 5) and workflows (Task 7)

- [ ] **Step 1: Resolve the commit to pin for each upstream**

Prefer the tag matching the version in use today; fall back to default-branch HEAD. Run:
```bash
resolve() {  # name url version
  for t in "v$3" "$3"; do
    sha=$(git ls-remote --tags "$2" "refs/tags/$t" "refs/tags/$t^{}" | tail -1 | cut -f1)
    if [ -n "$sha" ]; then echo "$1 tag=$t $sha"; return; fi
  done
  echo "$1 HEAD $(git ls-remote "$2" HEAD | cut -f1)"
}
resolve superpowers         https://github.com/obra/superpowers.git             6.3.0
resolve impeccable          https://github.com/pbakaus/impeccable.git           4.1.3
resolve taste-skill         https://github.com/leonxlnx/taste-skill.git         1.0.0
resolve ponytail            https://github.com/DietrichGebert/ponytail.git      4.13.0
resolve understand-anything https://github.com/Egonex-AI/Understand-Anything.git 2.9.4
```
Expected: five lines, each ending in a 40-hex SHA. Keep them for step 2.

- [ ] **Step 2: Write the marketplace file**

Create `.claude-plugin/marketplace.json`, replacing each `PASTE_SHA_*` with the SHA from step 1:
```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "shipright",
  "metadata": {
    "description": "ShipRight: the <org> AI-PDLC standard for Claude Code. One install, every engineer gets the same skills and process."
  },
  "owner": { "name": "<org> Engineering" },
  "plugins": [
    {
      "name": "shipright",
      "description": "ShipRight: /shipright:ship end-to-end delivery pipeline, branch-coverage gates, graphify, plus superpowers, impeccable, taste-skill, ponytail and understand-anything as dependencies.",
      "version": "1.0.0",
      "source": "./plugins/shipright",
      "category": "development"
    },
    {
      "name": "superpowers",
      "description": "Brainstorming, planning, TDD, subagent-driven development, systematic debugging, verification.",
      "source": { "source": "url", "url": "https://github.com/obra/superpowers.git", "sha": "PASTE_SHA_SUPERPOWERS" }
    },
    {
      "name": "impeccable",
      "description": "Frontend design quality: audit, critique, polish.",
      "source": { "source": "git-subdir", "url": "https://github.com/pbakaus/impeccable.git", "path": "plugin", "sha": "PASTE_SHA_IMPECCABLE" }
    },
    {
      "name": "taste-skill",
      "description": "Design-taste skills: minimalist, brutalist, soft, redesign, image-to-code.",
      "source": { "source": "github", "repo": "leonxlnx/taste-skill", "sha": "PASTE_SHA_TASTE" }
    },
    {
      "name": "ponytail",
      "description": "Lazy-senior-dev mode: YAGNI, stdlib first, shortest working diff.",
      "source": { "source": "github", "repo": "DietrichGebert/ponytail", "sha": "PASTE_SHA_PONYTAIL" }
    },
    {
      "name": "understand-anything",
      "description": "Codebase knowledge graphs, onboarding tours, diff analysis, dashboard.",
      "source": { "source": "github", "repo": "Egonex-AI/Understand-Anything", "sha": "PASTE_SHA_UNDERSTAND" }
    }
  ]
}
```

- [ ] **Step 3: Check no paste tokens remain and the file validates**

Run:
```bash
! grep -n PASTE_SHA .claude-plugin/marketplace.json && echo "no tokens left"
python3 -c "import json,re;m=json.load(open('.claude-plugin/marketplace.json'));bad=[p['name'] for p in m['plugins'] if isinstance(p['source'],dict) and not re.fullmatch(r'[0-9a-f]{40}',p['source']['sha'])];print('bad shas:',bad);assert not bad"
claude plugin validate . --strict || claude plugin validate .claude-plugin/marketplace.json --strict
```
Expected: `no tokens left`, `bad shas: []`, and a valid-marketplace report.

- [ ] **Step 4: Clean-profile install smoke test (needs network; clones five repos)**

Run:
```bash
export CLAUDE_CONFIG_DIR="$(mktemp -d)"
claude plugin marketplace add "$PWD"
claude plugin install shipright@shipright --scope user
claude plugin list
unset CLAUDE_CONFIG_DIR
```
Expected: `claude plugin list` shows six plugins: shipright, superpowers, impeccable, taste-skill, ponytail, understand-anything. If `install` fails on a specific dependency, the failing entry's `source` shape is wrong; fix it and re-run from `marketplace add` with a fresh temp dir.

- [ ] **Step 5: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "Add shipright marketplace with SHA-pinned third-party plugins" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: README (the education doc)

**Files:**
- Create: `README.md`

**Interfaces:**
- Consumes: install string `shipright@shipright` (Task 4), skill names (Task 2), workflow names (Task 7, referenced by filename only)
- Produces: the document the welcome hook links to

- [ ] **Step 1: Write README.md**

Create `README.md` with exactly this content:
````markdown
# ShipRight

ShipRight is <org>'s engineering standard for Claude Code: one plugin that gives every engineer the same skills and the same delivery process, so the work we ship looks the same no matter who ran it.

It bundles:

| Plugin | What it gives you |
|---|---|
| **shipright** (this repo) | `/shipright:ship` end-to-end delivery, branch-coverage gates, `graphify` knowledge graphs, and the session reminder |
| superpowers | brainstorming, planning, TDD, subagent-driven development, systematic debugging, verification |
| impeccable | frontend design audits and polish |
| taste-skill | design-taste references (minimalist, brutalist, soft, redesign) |
| ponytail | lazy-senior-dev mode: smallest working diff, YAGNI |
| understand-anything | codebase knowledge graphs, onboarding tours, diff analysis |

## The AI-PDLC flow

Every feature or bug fix goes through `/shipright:ship`:

1. **Ideate + plan.** Brainstorm the change and write a plan. **You approve the plan.** This is the only routine checkpoint.
2. **Build.** Subagents implement the plan on a feature branch, test-first.
3. **Branch + PR.** Push and open a PR against the base branch. Never push to base directly.
4. **Code review.** `/code-review` at high effort.
5. **UI review.** `impeccable` runs if UI files changed.
6. **Apply fixes.** Review findings land on the branch.
7. **Verify.** Full test suite, build, and live use for UI changes. A partial pass is not a pass.
8. **Hand back.** PR link, test status, what each review flagged and how it was resolved.

Rules that never bend: Claude never merges the PR; the base branch is never pushed to directly; nothing is reported as ready without this run's own test and build output.

## Install (2 minutes)

Prerequisites:

- Claude Code (CLI, desktop app, or IDE extension)
- Git access to `github.com/<org>/shipright` that works without prompting (SSH key or a credential helper)
- Node.js 18+ (ponytail hooks, understand-anything dashboard)
- Python 3 with `uv` or `pip` (graphify installs the `graphifyy` package on first use)

```bash
claude plugin marketplace add <org>/shipright
claude plugin install shipright@shipright --scope user
```

Then, once, inside any Claude Code session: `/plugin` → **Marketplaces** → **shipright** → **Enable auto-update**. Without this step, future updates never reach your machine.

Verify:

- `claude plugin list` shows six plugins: shipright, superpowers, impeccable, taste-skill, ponytail, understand-anything.
- In a new session, typing `/shipright:` autocompletes `ship`, and the session's first context contains "SHIPRIGHT ACTIVE".

## Daily cheat-sheet

| You want to… | Use |
|---|---|
| Build a feature or fix end to end and get a PR | `/shipright:ship <what to build>` or "ship: …" |
| Check that a PR you are opening by hand has tests for its new branches | `/shipright:pr-branch-guard` |
| Write tests for uncovered conditions in a file | `/shipright:patch-uncovered-branches <file>` |
| Triage test gaps before a release | `/shipright:branch-audit` |
| Understand an unfamiliar codebase | `/shipright:graphify` or `/understand-anything:understand` |
| Onboard someone to a repo | `/understand-anything:understand-onboard` |
| Audit or polish UI | `/impeccable:impeccable audit` (also runs inside `/ship` when UI changed) |
| Change how aggressive the minimal-diff mode is | `/ponytail:ponytail lite`, `full` (default), or `ultra` |

## Migrating from individual installs

If you installed any of the bundled plugins yourself before ShipRight existed, remove those copies so skills are not duplicated. Check with `claude plugin list`, then for each duplicate:

```bash
claude plugin uninstall superpowers@claude-plugins-official
claude plugin uninstall impeccable@impeccable
claude plugin uninstall taste-skill@taste-skill
claude plugin uninstall ponytail@<marketplace-you-used>
claude plugin uninstall understand-anything@<marketplace-you-used>
```

Also delete personal copies of `ship` or `graphify` under `~/.claude/skills/`. Plugins installed through the desktop app's plugin pane are removed there.

## Getting updates

Third-party plugins are pinned to exact commits. A weekly job opens a PR when any of them has moved; a maintainer reviews and merges. With auto-update enabled (install step 3), your machine picks the change up within about ten minutes of your next session and loads it on the next launch, or immediately with `/reload-plugins`.

Manual update any time:

```bash
claude plugin update shipright@shipright
```

## For admins

### claude.ai Team / Enterprise

Organization settings → **Plugins & skills** → **Add** → **Sync from GitHub** → `<org>/shipright`. Set all six plugins to **Installed by default** and turn on **Sync automatically**. Members signed in with claude.ai get ShipRight with no commands; Claude Code syncs once per launch.

### IT-managed machines (API key / Bedrock / Vertex)

Add to `managed-settings.json`:

- macOS: `/Library/Application Support/ClaudeCode/managed-settings.json`
- Linux: `/etc/claude-code/managed-settings.json`
- Windows: `C:\Program Files\ClaudeCode\managed-settings.json`

```json
{
  "extraKnownMarketplaces": {
    "shipright": {
      "source": { "source": "github", "repo": "<org>/shipright" },
      "autoUpdate": true
    }
  },
  "enabledPlugins": { "shipright@shipright": true }
}
```

Plugins install at the start of each user's next session. `autoUpdate` is locked on by the managed value.

## For maintainers

- `plugins/shipright/.claude-plugin/plugin.json` carries the version. Bump it on any change to skills, hook, welcome text, or dependencies, then tag with `claude plugin tag`.
- Third-party pins live in `.claude-plugin/marketplace.json` as `sha` values. `.github/workflows/bump-pins.yml` runs every Monday and opens a PR with compare links when any upstream moved. Read the diff, then merge. Run it by hand from the Actions tab for an urgent fix.
- Before tagging a release:

```bash
claude plugin validate . --strict
claude plugin validate plugins/shipright --strict
python3 -m unittest discover -s tests -v
export CLAUDE_CONFIG_DIR="$(mktemp -d)"
claude plugin marketplace add <org>/shipright
claude plugin install shipright@shipright --scope user
claude plugin list   # expect 6 plugins
unset CLAUDE_CONFIG_DIR
```
````

- [ ] **Step 2: Check the README names every skill and both workflows**

Run:
```bash
for n in shipright:ship pr-branch-guard patch-uncovered-branches branch-audit shipright:graphify understand-anything:understand impeccable:impeccable ponytail:ponytail bump-pins.yml 'shipright@shipright' 'Enable auto-update' autoUpdate; do grep -q -- "$n" README.md && echo "ok $n" || echo "MISSING $n"; done
```
Expected: twelve `ok` lines, no `MISSING`.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "Add README: process guide, install, cheat-sheet, admin and maintainer docs" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Pin-bump script with unit test

**Files:**
- Create: `scripts/bump_pins.py`
- Test: `tests/test_bump_pins.py`

**Interfaces:**
- Consumes: `.claude-plugin/marketplace.json` (Task 4)
- Produces: `bump(marketplace: dict, resolve) -> list[str]` (mutates the dict, returns markdown lines), `git_url(source: dict) -> str`, `compare_link(url, old, new) -> str`, `resolve_head(url) -> str`; CLI `python3 scripts/bump_pins.py [--write]` printing the markdown summary (empty when nothing changed). Task 7's workflow calls the CLI.

- [ ] **Step 1: Write the failing test**

Create `tests/test_bump_pins.py`:
```python
import copy
import sys
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python3 -m unittest discover -s tests -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'bump_pins'`.

- [ ] **Step 3: Write the script**

Create `scripts/bump_pins.py`:
```python
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


if __name__ == "__main__":
    data = json.loads(MARKETPLACE.read_text())
    changed = bump(data)
    if changed and "--write" in sys.argv:
        MARKETPLACE.write_text(json.dumps(data, indent=2) + "\n")
    print("\n".join(changed))
```

- [ ] **Step 4: Run the tests to confirm they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: `Ran 4 tests` ... `OK`.

- [ ] **Step 5: Dry-run against the real file**

Run: `python3 scripts/bump_pins.py`
Expected: either no output (all pins current) or one line per upstream that has moved since Task 4, each with a compare link. The file is not modified (no `--write`); confirm with `git status --short` showing nothing under `.claude-plugin/`.

- [ ] **Step 6: Commit**

```bash
git add scripts/bump_pins.py tests/test_bump_pins.py
git commit -m "Add bump_pins script that moves SHA pins to upstream HEAD with compare links" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: GitHub Actions workflows

**Files:**
- Create: `.github/workflows/validate.yml`
- Create: `.github/workflows/bump-pins.yml`

**Interfaces:**
- Consumes: `python3 scripts/bump_pins.py --write` (Task 6), `tests/` (Task 6), marketplace and plugin paths (Tasks 1, 4)
- Produces: CI on PRs and pushes to `main`; a weekly PR on branch `bump-pins`

- [ ] **Step 1: Write validate.yml**

Create `.github/workflows/validate.yml`:
```yaml
name: validate
on:
  pull_request:
  push:
    branches: [main]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - run: npm i -g @anthropic-ai/claude-code
      - run: claude plugin validate . --strict
      - run: claude plugin validate plugins/shipright --strict
      - run: python3 -m unittest discover -s tests -v
```

- [ ] **Step 2: Write bump-pins.yml**

Create `.github/workflows/bump-pins.yml`:
```yaml
name: bump-pins
on:
  schedule:
    - cron: "0 6 * * 1"
  workflow_dispatch:
permissions:
  contents: write
  pull-requests: write
jobs:
  bump:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - run: npm i -g @anthropic-ai/claude-code
      - name: Move pins to upstream HEAD
        id: bump
        run: |
          python3 scripts/bump_pins.py --write > summary.md
          if [ -s summary.md ]; then echo "changed=true" >> "$GITHUB_OUTPUT"; fi
      - name: Validate (PRs opened with GITHUB_TOKEN do not trigger validate.yml)
        if: steps.bump.outputs.changed == 'true'
        run: claude plugin validate . --strict
      - name: Open or refresh the PR
        if: steps.bump.outputs.changed == 'true'
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          git config user.name "shipright-bot"
          git config user.email "shipright-bot@users.noreply.github.com"
          git checkout -B bump-pins
          git add .claude-plugin/marketplace.json
          git commit -m "Bump third-party plugin pins"
          git push --force origin bump-pins
          if gh pr view bump-pins >/dev/null 2>&1; then
            gh pr edit bump-pins --body-file summary.md
          else
            gh pr create --title "Bump third-party plugin pins" --body-file summary.md --base main --head bump-pins
          fi
```

- [ ] **Step 3: Syntax-check both files**

Run:
```bash
ruby -ryaml -e 'ARGV.each { |f| YAML.load_file(f); puts "#{f} OK" }' .github/workflows/validate.yml .github/workflows/bump-pins.yml
```
Expected: two `OK` lines. (macOS ships Ruby; no install needed.)

- [ ] **Step 4: Commit**

```bash
git add .github/workflows
git commit -m "Add validate and weekly bump-pins workflows" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: Publish, verify from the real remote, migrate the author's machine

This task needs two things only the user can supply: the GitHub org/handle, and GitHub credentials. Stop and ask for the org before step 1 if it is not known.

**Files:**
- Modify: every non-`docs/` file containing `<org>` (README.md, marketplace.json, plugin.json, welcome.md)
- Modify (author's machine): `~/.claude/CLAUDE.md`, `~/.claude/settings.json`

**Interfaces:**
- Consumes: everything above
- Produces: `github.com/ORG/shipright` on `main`; ShipRight installed on the author's machine

- [ ] **Step 1: Replace the placeholder (ORG = the real handle)**

Run:
```bash
ORG=REPLACE_ME   # the GitHub org or user handle
grep -rl --exclude-dir=.git --exclude-dir=docs '<org>' . | xargs sed -i '' "s/<org>/$ORG/g"
grep -rn --exclude-dir=.git --exclude-dir=docs '<org>' . ; echo "remaining above (expect none)"
git commit -am "Set org to $ORG" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

- [ ] **Step 2: Create the private repo, push both branches, open the PR**

`main` holds only the spec and plan; the implementation is on `build-shipright`. Push both and open a PR so `validate.yml` runs on it. The user merges; Claude never merges.

`gh` is not installed on the author's machine. Either install it (`brew install gh && gh auth login`) and run:
```bash
gh repo create "$ORG/shipright" --private --source=. --remote=origin
git push -u origin main
git push -u origin build-shipright
gh pr create --base main --head build-shipright --title "ShipRight v1.0.0" --body "Marketplace + bundle plugin, README, bump-pins workflow. See docs/superpowers/specs/2026-10-08-shipright-design.md."
```
or create an empty private repo named `shipright` in the GitHub UI and run:
```bash
git remote add origin "git@github.com:$ORG/shipright.git"
git push -u origin main
git push -u origin build-shipright
```
then open the PR from `build-shipright` into `main` in the UI.
Expected: the `validate` check passes on the PR. The user merges the PR.

- [ ] **Step 2b: Repo settings (once, in the GitHub UI)**

1. Settings → Actions → General → Workflow permissions → enable **Allow GitHub Actions to create and approve pull requests** (for an org repo, the org-level setting of the same name must allow it). Without this, `bump-pins.yml` fails at `gh pr create`.
2. Settings → Branches → add a protection rule for `main` that requires a pull request before merging. Do **not** require the `validate` status check: PRs opened by `GITHUB_TOKEN` never start workflows, so bump PRs would be blocked forever.
Expected: both settings saved.

- [ ] **Step 3: Smoke test from the real remote (after the PR is merged)**

Run:
```bash
export CLAUDE_CONFIG_DIR="$(mktemp -d)"
claude plugin marketplace add "$ORG/shipright"
claude plugin install shipright@shipright --scope user
claude plugin list
unset CLAUDE_CONFIG_DIR
```
Expected: six plugins listed. If `marketplace add` fails with an SSH host-key error, use `https://github.com/$ORG/shipright.git` instead.

- [ ] **Step 4: Install on the author's real profile and check the hook live**

Run:
```bash
claude plugin marketplace add "$ORG/shipright"
claude plugin install shipright@shipright --scope user
claude plugin list
```
Then start `claude` in any folder, run `/plugin` → Marketplaces → shipright → Enable auto-update, and ask: "What does the SHIPRIGHT notice in your context say?"
Expected: the reply quotes the welcome text; `/shipright:` autocompletes `ship`.

- [ ] **Step 5: Remove the author's duplicate copies**

Run:
```bash
mkdir -p ~/.claude/backups/pre-shipright
mv ~/.claude/skills/ship ~/.claude/skills/graphify ~/.claude/backups/pre-shipright/
claude plugin uninstall impeccable@impeccable
claude plugin uninstall taste-skill@taste-skill
python3 - <<'EOF_PY'
import json, pathlib
p = pathlib.Path.home() / ".claude" / "settings.json"
s = json.loads(p.read_text())
for k in ("impeccable@impeccable", "taste-skill@taste-skill"):
    s.get("enabledPlugins", {}).pop(k, None)
for k in ("impeccable", "taste-skill"):
    s.get("extraKnownMarketplaces", {}).pop(k, None)
p.write_text(json.dumps(s, indent=2) + "\n")
print(json.dumps(s, indent=2))
EOF_PY
```
Expected: settings.json still lists `typesafe@typesafe-ai` and its marketplace, nothing for impeccable or taste-skill.

Then edit `~/.claude/CLAUDE.md`: replace the line
`- **graphify** (`~/.claude/skills/graphify/SKILL.md`) - any input to knowledge graph. Trigger: `/graphify``
with
`- **graphify** (`/shipright:graphify`) - any input to knowledge graph. Trigger: `/graphify``.

Desktop-app copies of superpowers, ponytail and understand-anything are removed from the app's plugin pane by hand.

- [ ] **Step 6: Confirm skills are not duplicated**

Start a new `claude` session and type `/ship`. Expected: exactly one `ship` entry (`/shipright:ship`), one `graphify`, one `brainstorming` (`/superpowers:brainstorming`).
