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

If `marketplace add` fails with an SSH or host-key error, use the HTTPS form instead: `claude plugin marketplace add https://github.com/<org>/shipright.git`.

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

Plugins install at the start of each user's next session. `autoUpdate` is locked on by the managed value. If your machines reach GitHub over HTTPS rather than SSH, use `"source": { "source": "url", "url": "https://github.com/<org>/shipright.git" }` as the marketplace source instead.

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
