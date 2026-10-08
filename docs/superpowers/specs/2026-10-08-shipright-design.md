# ShipRight — Company-standard Claude Code bundle

**Date:** 2026-10-08
**Status:** Approved in brainstorming, awaiting written-spec review
**Repo:** `github.com/<org>/shipright` (private). `<org>` is a deliberate placeholder: the GitHub org or user handle, to be filled in before first push.

## 1. Goal

Give every engineer who uses Claude Code one thing to install that delivers the
same skills, the same AI-PDLC process, and the same quality bar, so the work they
produce is similar in shape regardless of who ran it. Today the pieces live in
one person's `~/.claude` (the `/ship` skill, `graphify`, three branch-coverage
skills) plus five third-party plugins installed by hand from four different
marketplaces. Nobody else has them, and installing them individually is six-plus
manual steps per machine.

Non-goals: enforcing the process with blocking hooks; vendoring third-party
code; per-repo settings snippets; covering non-engineering plugins (design,
marketing) or product-specific skills (typesafe).

## 2. Decisions already made

| Decision | Choice |
|---|---|
| Packaging | One private marketplace repo containing one bundle plugin that declares the third-party plugins as `dependencies`. |
| Plugin / marketplace name | `shipright` (display name "ShipRight"). Install string `shipright@shipright`. Skills invoke as `/shipright:<skill>`. |
| Bundle contents | Own skills: `ship`, `graphify`, `branch-audit`, `pr-branch-guard`, `patch-uncovered-branches`. Dependencies: `superpowers`, `impeccable`, `taste-skill`, `ponytail`, `understand-anything`. |
| Enforcement | A SessionStart hook that prints a short nudge into context. No blocking hooks. |
| Team setup | Mixed: claude.ai Team/Enterprise members, individual Pro/Max accounts, and API-key/Bedrock users. All use Claude Code. |
| Distribution | Baseline: two CLI commands (works for everyone). Accelerators: claude.ai org-catalog sync and managed settings, both fed from the same repo. |
| Version policy | Third-party plugins pinned by commit SHA. Bumps are deliberate PRs. |
| Spec/repo location | `~/code/shipright`, this repo. |

## 3. Repository layout

```
shipright/
├── .claude-plugin/
│   └── marketplace.json          # six entries: shipright + five third-party, SHA-pinned
├── .github/workflows/
│   ├── validate.yml              # runs `claude plugin validate` on PRs and pushes
│   └── bump-pins.yml             # weekly: opens a PR when any upstream plugin has new commits
├── README.md                     # the education doc: process, install, cheat-sheet, admin, maintainers
├── docs/superpowers/specs/       # this spec (and future ones)
└── plugins/shipright/
    ├── .claude-plugin/
    │   └── plugin.json           # name, version, description, dependencies
    ├── skills/
    │   ├── ship/SKILL.md                      # copied verbatim from ~/.claude/skills/ship
    │   ├── graphify/SKILL.md                  # copied verbatim from ~/.claude/skills/graphify
    │   ├── graphify/references/*.md           #   (8 reference files; SKILL.md resolves them relatively)
    │   ├── branch-audit/SKILL.md              # copied from ~/Downloads/branch-coverage-skills
    │   ├── pr-branch-guard/SKILL.md
    │   └── patch-uncovered-branches/SKILL.md
    └── hooks/
        ├── hooks.json            # SessionStart → cat welcome.md
        └── welcome.md            # the nudge text
```

No SKILL.md content changes. `ship` references `superpowers:brainstorming`,
`superpowers:writing-plans`, `superpowers:subagent-driven-development`,
`/code-review`, and `impeccable` by name; all keep resolving because the
dependency plugins keep their upstream names and `/code-review` is built into
Claude Code. `graphify`'s `.graphify_version` file is copied too.

## 4. Components

### 4.1 `.claude-plugin/marketplace.json`

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
      "description": "ShipRight — /shipright:ship end-to-end delivery pipeline, branch-coverage gates, graphify, plus superpowers, impeccable, taste-skill, ponytail and understand-anything as dependencies.",
      "version": "1.0.0",
      "source": "./plugins/shipright",
      "category": "development"
    },
    {
      "name": "superpowers",
      "description": "Brainstorming, planning, TDD, subagent-driven development, systematic debugging, verification.",
      "source": { "source": "url", "url": "https://github.com/obra/superpowers.git", "sha": "<40-hex, see §6>" }
    },
    {
      "name": "impeccable",
      "description": "Frontend design quality: audit, critique, polish.",
      "source": { "source": "git-subdir", "url": "https://github.com/pbakaus/impeccable.git", "path": "plugin", "sha": "<40-hex, see §6>" }
    },
    {
      "name": "taste-skill",
      "description": "Design-taste skills: minimalist, brutalist, soft, redesign, image-to-code.",
      "source": { "source": "url", "url": "https://github.com/leonxlnx/taste-skill.git", "sha": "<40-hex, see §6>" }
    },
    {
      "name": "ponytail",
      "description": "Lazy-senior-dev mode: YAGNI, stdlib first, shortest working diff.",
      "source": { "source": "url", "url": "https://github.com/DietrichGebert/ponytail.git", "sha": "<40-hex, see §6>" }
    },
    {
      "name": "understand-anything",
      "description": "Codebase knowledge graphs, onboarding tours, diff analysis, dashboard.",
      "source": { "source": "url", "url": "https://github.com/Egonex-AI/Understand-Anything.git", "sha": "<40-hex, see §6>" }
    }
  ]
}
```

Source shapes mirror ones already proven in the official marketplace
(`url` with `sha`; `git-subdir` with full URL, `path`, `sha`). The `github`
shorthand is deliberately not used: during implementation it cloned over SSH
and failed on a machine with no GitHub host key, while HTTPS `url` sources
install with no SSH setup. All five upstreams are public, so HTTPS needs no
credentials.
The `superpowers` plugin manifest lives at the repo root, as do taste-skill,
ponytail and understand-anything; impeccable's lives under `plugin/`, hence
`git-subdir`.

### 4.2 `plugins/shipright/.claude-plugin/plugin.json`

```json
{
  "name": "shipright",
  "version": "1.0.0",
  "description": "ShipRight: the <org> AI-PDLC standard. Ship features end to end with one human checkpoint, gate PRs on branch coverage, and understand any codebase.",
  "author": { "name": "<org> Engineering" },
  "dependencies": ["superpowers", "impeccable", "taste-skill", "ponytail", "understand-anything"]
}
```

Bare dependency names resolve within the same marketplace, so no
`allowCrossMarketplaceDependenciesOn` is needed. Installing `shipright`
installs all five at the same scope.

### 4.3 `plugins/shipright/hooks/hooks.json`

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

`cat` is available on macOS, Linux, and the Git Bash that Claude Code on
Windows already requires. No Node, no script file.

### 4.4 `plugins/shipright/hooks/welcome.md`

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

Ten lines; a few hundred tokens per session. Wording is final and is the only
copy the hook prints; the README expands on it.

### 4.5 `README.md` (the education deliverable)

Sections, in order:

1. **What ShipRight is.** One paragraph. Then the AI-PDLC flow as a numbered
   list mirroring `ship`'s steps: ideate + plan (human approves the plan), build,
   branch + PR, code review, UI review when UI changed, apply fixes, verify, hand
   back. Call out the single checkpoint and the "never merge, never push to
   base" rules.
2. **Install (2 minutes).** Prerequisites: Claude Code, git access to
   `<org>/shipright`, Node.js (ponytail hooks, understand-anything dashboard),
   Python 3 with `uv` or `pip` (graphify installs the `graphifyy` package on
   first use). Then:
   ```bash
   claude plugin marketplace add <org>/shipright
   claude plugin install shipright@shipright --scope user
   ```
   Then, one time, in any Claude Code session: `/plugin` → Marketplaces →
   shipright → **Enable auto-update**. Without this, future pin bumps never
   reach the machine.
   Verify: `claude plugin list` shows six plugins; typing `/shipright:` in a
   session autocompletes `ship`.
3. **Daily cheat-sheet.** Table of job → skill (same mapping as welcome.md,
   plus `/ponytail:ponytail lite|full|ultra`, `/understand-anything:understand-onboard`).
4. **Migrating from individual installs.** If you previously installed any of
   the five dependencies from another marketplace, uninstall those copies so
   skills are not duplicated:
   `claude plugin uninstall superpowers@<old-marketplace>` etc. Also delete
   any personal copies of `ship` or `graphify` under `~/.claude/skills`.
5. **For admins.**
   - *claude.ai Team/Enterprise:* Organization settings → Plugins & skills →
     Add → Sync from GitHub → `<org>/shipright`. Set **all six** plugins to
     "Installed by default" (see §8 risk 1) and turn on **Sync automatically**
     so every push to `main` re-syncs. Members signed in with claude.ai get
     them with no commands, in Claude Code, desktop, and Cowork; Claude Code
     syncs once per launch.
   - *IT-managed machines (API key / Bedrock):* drop this into
     `managed-settings.json` (macOS `/Library/Application Support/ClaudeCode/`,
     Linux `/etc/claude-code/`, Windows `C:\Program Files\ClaudeCode\`):
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
     Installs at the next session start; `autoUpdate` is locked on by the
     managed value. The snippet also sets `"env": {"FORCE_AUTOUPDATE_PLUGINS": "1"}`
     because plugin auto-update is skipped whenever Claude Code's own updater
     is disabled (`DISABLE_AUTOUPDATER`, `DISABLE_UPDATES`, `autoUpdates:
     false`), which managed fleets commonly set. HTTPS-only fleets use
     `{"source": "git", "url": "https://github.com/<org>/shipright.git"}`
     (not `url`, which means "fetch a marketplace.json over HTTP").
6. **For maintainers.** Versioning and pin-bump procedure (§6), release
   checklist (§7).

### 4.6 `.github/workflows/validate.yml`

One job on `pull_request` and `push` to `main`: checkout, setup-node 22,
`npm i -g @anthropic-ai/claude-code`, then
`claude plugin validate . --strict` and
`claude plugin validate plugins/shipright --strict`. Under 20 lines. Validate
needs no API key.

### 4.7 `.github/workflows/bump-pins.yml` (how we learn about upstream updates)

Runs on a weekly cron (Monday 06:00 UTC) and on manual dispatch. One job:

1. Checkout; install Claude Code CLI (same as validate.yml).
2. For each of the five third-party entries in `marketplace.json`, run
   `git ls-remote <upstream-url> HEAD` and compare the result to the entry's
   `sha`.
3. If nothing moved, exit. Otherwise rewrite the changed `sha` values, run
   `claude plugin validate . --strict`, and push to a fixed branch `bump-pins`
   (force-push, so repeated runs refresh one PR instead of piling up).
4. Open or update a PR titled "Bump third-party plugin pins" via `gh pr create`
   with `GITHUB_TOKEN`. Body lists, per plugin, old → new sha and a one-click
   GitHub compare link (`https://github.com/<owner>/<repo>/compare/<old>...<new>`)
   so the reviewer reads the upstream diff before merging.

Validation runs inside this workflow on purpose: PRs opened with
`GITHUB_TOKEN` do not trigger other workflows, so validate.yml would not run
on the bot's PR. Under ~60 lines including the inline Python that edits the
JSON. Merging the PR is the only human action; propagation to machines is
then automatic (§6).

## 5. Distribution summary

| Audience | Mechanism | Engineer effort |
|---|---|---|
| Everyone (baseline) | Two CLI commands from README §2 | 2 minutes, once per machine |
| claude.ai Team/Enterprise members | Org catalog synced from this repo, "Installed by default" | None |
| IT-managed API-key/Bedrock machines | `managed-settings.json` from README §5 | None |

All three read the same repo, so one PR updates every channel.

## 6. Versioning and pinning

- `plugin.json` `version` is semver. Bump it on any change to skills, hook,
  dependency list, or welcome text. Tag the repo with `claude plugin tag`.
- Each third-party entry carries a `sha`. Initial pins are the commits of the
  versions in use today, resolved at implementation time with
  `git ls-remote` against each upstream's tag or default branch:
  superpowers 6.3.0, impeccable 4.1.3, taste-skill 1.0.0, ponytail 4.13.0,
  understand-anything 2.9.4. If no tag exists for a version, pin the current
  default-branch HEAD. Entry descriptions stay version-free; the `sha` is the
  version.
- Bumping a pin: one PR that changes the `sha`,
  after reading the upstream diff, because that code runs on every engineer's
  machine. CI validate must pass. No CHANGELOG file; git log and tags suffice.
- **Update policy: pinned, then pushed.** Upstream changes never reach
  engineers on their own. The weekly bump-pins workflow (§4.7) opens a PR
  whenever any upstream has new commits; a maintainer reviews the compare
  link and merges (or runs the workflow by hand for an urgent security fix).
  Once merged,
  propagation is automatic for every machine whose `shipright` marketplace has
  auto-update on: Claude Code refreshes auto-update marketplaces within ~10
  minutes of a session's first message and updates the installed plugins on
  disk; the new version loads at the next launch or `/reload-plugins`.
  Auto-update is OFF by default for non-official marketplaces, so enabling it
  is part of install (README Install section), of the managed-settings snippet
  (`"autoUpdate": true`), and of the org catalog ("Sync automatically").
- **Propagation is version-gated (verified in CLI 2.1.197 during the final
  review).** Claude Code decides a plugin needs updating by its `version`
  (upstream `plugin.json` first, then the marketplace entry, then the sha).
  A pin bump between upstream releases keeps the same version string, so
  existing installs report "already at the latest version" and keep the old
  commit; only new installs get the new sha. README states this and gives a
  force-refresh loop (uninstall + install per plugin). The lasting fix is an
  open decision (§10): track upstream release tags instead of HEAD.
- Manual fallback: `claude plugin update <plugin>@shipright` for each of the
  six plugins (`update` does not cascade to dependencies), or the
  force-refresh loop above. Org-catalog members: Claude Code syncs once per
  launch. Managed-settings machines: next session start.

## 7. Validation and release checklist

Before tagging any version:

1. `claude plugin validate plugins/shipright --strict` passes.
2. `claude plugin validate . --strict` passes (marketplace file).
3. Clean-profile smoke test:
   ```bash
   export CLAUDE_CONFIG_DIR="$(mktemp -d)"
   claude plugin marketplace add "$PWD"      # local path, before first push
   claude plugin install shipright@shipright --scope user
   claude plugin list                        # expect 6 plugins
   ```
   Then start `claude` in any folder and confirm the first context contains
   the "SHIPRIGHT ACTIVE" text and `/shipright:ship` autocompletes.
4. After pushing: repeat step 3 with `claude plugin marketplace add <org>/shipright`.

The local `claude` CLI is not on PATH on the author's machine (the desktop
app bundles its own); install it once with `npm i -g @anthropic-ai/claude-code`.

## 8. Risks and mitigations

1. **Org-catalog sync may not follow `dependencies`.** Unverified. Mitigation:
   set all six plugins to "Installed by default" in the catalog, not just
   `shipright`. Zero cost.
2. **Duplicate skills** for engineers who keep earlier individual installs.
   Mitigation: README §4 migration section with uninstall commands.
3. **Upstream repo deleted or history rewritten** breaks a SHA pin at install
   time. Mitigation: fork the affected repo under `<org>` and repoint the
   entry. Not done pre-emptively.
4. **Prerequisites missing** (Node.js for ponytail/understand-anything,
   Python for graphify). Mitigation: README §2 lists them; the skills
   themselves report clearly when a tool is absent.
5. **Third-party code runs on every machine.** Mitigation: SHA pins, review
   on bump, private repo with normal PR review.
6. **Background updates fail quietly on a private repo** if git would need to
   prompt for credentials; the last synced copy stays in place. Mitigation:
   README §2 prerequisites require working non-interactive git auth to
   `<org>/shipright` (SSH key or a credential helper), and the smoke test
   in §7 step 4 uses the real remote.

## 9. Author's own migration (one-time, after first successful install)

- Move `~/.claude/skills/ship` and `~/.claude/skills/graphify` into the repo
  (they are copied, not symlinked). After `shipright` is installed, delete the
  originals to avoid duplicate skills.
- Update `~/.claude/CLAUDE.md`: the graphify line points at
  `~/.claude/skills/graphify/SKILL.md`; change it to say `/shipright:graphify`.
- Remove `impeccable` and `taste-skill` from `enabledPlugins` and
  `extraKnownMarketplaces` in `~/.claude/settings.json`; keep `typesafe`.
- Uninstall the desktop-provided copies of superpowers, ponytail and
  understand-anything from the app's plugin pane, or accept duplicates on
  this one machine.

## 10. Items to confirm during implementation (not design gaps)

- Resolved: `claude plugin update shipright@shipright` does not cascade to
  dependencies and is a no-op for pin bumps (§6); README loops over all six.
- To observe during Task 8: whether `claude plugin uninstall <dep>@shipright`
  is refused while `shipright` still depends on it. If so, the README's
  force-refresh loop needs `--prune` or a reinstall of `shipright` instead.
- That `claude plugin validate .` accepts a marketplace root (§7); otherwise
  validate the marketplace via the `/plugin` UI or the schema URL.
- `git ls-remote` results for the five pins (§6).
- **Decision for the owner: track release tags instead of HEAD.** Because
  propagation is version-gated (§6), a HEAD-tracking bump between releases
  never reaches existing installs. Tracking the latest tag (superpowers and
  ponytail tag `vX.Y.Z`; impeccable tags `skill-vX.Y.Z`; taste-skill is
  untagged) makes every merged bump a version change that propagates, at the
  cost of ~15 lines in `bump_pins.py` (tag listing + version sort) and
  leaving untagged upstreams at a fixed pin. Recommended; not implemented.
- Publish ordering: `main` holds only docs until the `build-shipright` PR is
  merged, so the remote smoke test runs after the merge (plan Task 8).
- `bump-pins.yml` needs the repo setting "Allow GitHub Actions to create and
  approve pull requests"; `main` should require a PR but not the `validate`
  check (PRs from `GITHUB_TOKEN` never start workflows).
