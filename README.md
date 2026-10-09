# ShipRight

ShipRight is kureelvinay's engineering standard for Claude Code: one plugin that gives every engineer the same skills and the same delivery process, so the work we ship looks the same no matter who ran it.

It bundles:

| Plugin | What it gives you |
|---|---|
| **shipright** (this repo) | `/shipright:ship` end-to-end delivery, branch-coverage gates, `graphify` knowledge graphs, `/shipright:doctor` setup check, and the session reminder |
| superpowers | brainstorming, planning, TDD, subagent-driven development, systematic debugging, verification |
| impeccable | frontend design audits and polish |
| taste-skill | design-taste references (minimalist, brutalist, soft, redesign) |
| ponytail | lazy-senior-dev mode: smallest working diff, YAGNI |
| understand-anything | codebase knowledge graphs, onboarding tours, diff analysis |

## The AI-PDLC flow

Every feature or bug fix goes through `/shipright:ship`:

1. **Ideate + plan.** Brainstorm the change and write a plan. **You approve the plan.** This is the only routine checkpoint.
2. **Build.** Subagents implement the plan on a feature branch, test-first.
3. **Branch + PR.** Push and open a PR against the base branch, its description ending with `Shipped with ShipRight`. Never push to base directly.
4. **Code review.** `/code-review` at high effort.
5. **Security review.** `/security-review` runs when the diff touches auth, secrets, dependencies, CI, infrastructure, or input parsing at a trust boundary; otherwise it is skipped with a one-line note.
6. **UI review.** `impeccable` runs if UI files changed.
7. **Apply fixes.** Review findings land on the branch.
8. **Verify.** Full test suite, build, and live use for UI changes. A partial pass is not a pass.
9. **Hand back.** PR link, test status, what each review (code, security, UI) flagged and how it was resolved.

Rules that never bend: Claude never merges the PR; the base branch is never pushed to directly; nothing is reported as ready without this run's own test and build output.

## Install (2 minutes)

Prerequisites:

- Claude Code (CLI, desktop app, or IDE extension)
- Git access to `github.com/kureelvinay/shipright` that works without prompting (SSH key or a credential helper)
- Node.js 18+ (ponytail hooks, understand-anything dashboard)
- Python 3 with `uv` or `pip` (graphify installs the `graphifyy` package on first use)

```bash
claude plugin marketplace add kureelvinay/shipright
claude plugin install shipright@shipright --scope user
```

Inside a Claude Code session (desktop app or IDE extension, where the `claude` command may not be on your PATH) the same two steps are `/plugin marketplace add kureelvinay/shipright` and `/plugin install shipright@shipright`.

If `marketplace add` fails with an SSH or host-key error, use the HTTPS form instead: `claude plugin marketplace add https://github.com/kureelvinay/shipright.git`.

Then, once, inside any Claude Code session: `/plugin` → **Marketplaces** → **shipright** → **Enable auto-update**. Without this step, future updates never reach your machine.

Verify:

- `claude plugin list` shows six plugins: shipright, superpowers, impeccable, taste-skill, ponytail, understand-anything.
- In a new session, typing `/shipright:` autocompletes `ship`, and the session's first context contains "SHIPRIGHT ACTIVE".

Check the machine any time with `/shipright:doctor` inside a session. If the install itself failed, run the same checks without the plugin (needs `gh auth login` once):

```bash
gh api -H "Accept: application/vnd.github.raw" repos/kureelvinay/shipright/contents/plugins/shipright/skills/doctor/doctor.sh | bash
```

### Troubleshooting

- **Auto-update silently off** after re-adding the marketplace: `claude plugin marketplace add` rewrites the entry and drops `autoUpdate`. Re-enable it (`/plugin` → **Marketplaces** → **shipright** → **Enable auto-update**) and confirm with `/shipright:doctor`.

- **"Failed to add marketplace"** in the desktop app's plugin pane, with `its source doesn't match its extraKnownMarketplaces entry` in the app log (`~/Library/Logs/Claude/main.log` on macOS): ShipRight is already registered on this machine from a different source form. The CLI shorthand `kureelvinay/shipright` records a `github` source; the pane records the HTTPS URL as a `git` source, and the two are not interchangeable once one exists. Removing the plugin does not remove that entry. Fix: run `claude plugin marketplace list`; if `shipright` is listed, skip the add and run `claude plugin install shipright@shipright --scope user`. To add from the pane anyway, first delete the `shipright` entry under `extraKnownMarketplaces` in `~/.claude/settings.json`, then add again and re-enable auto-update.
- **"Please make sure you have the correct access rights"** or **"unable to get password"**: git cannot authenticate to the private repo without prompting. Run `gh auth login` and then `gh auth setup-git`, or add an SSH key to your GitHub account, and confirm you have read access to `github.com/kureelvinay/shipright`.

## Daily cheat-sheet

| You want to… | Use |
|---|---|
| Check this machine's ShipRight setup | `/shipright:doctor` |
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

Third-party plugins are pinned to exact commits. superpowers, ponytail and impeccable follow their upstream release tags; taste-skill and understand-anything follow the upstream main branch. A weekly job opens a PR when any of them has moved; a maintainer reviews and merges. With auto-update enabled (the **Enable auto-update** step under Install), your machine picks the change up within about ten minutes of your next session and loads it on the next launch, or immediately with `/reload-plugins`.

One limitation to know: Claude Code decides whether a plugin needs updating by its upstream `version` string, not by the pinned commit. Tag-tracked plugins only bump on a release, so those updates always propagate. For the main-branch-tracked ones, a bump that lands between upstream releases (same version, new commit) reaches **new** installs but not machines that already have that version. The weekly PR's compare link shows whether the upstream version changed. To force a machine onto the current pins:

```bash
for p in superpowers impeccable taste-skill ponytail understand-anything; do
  claude plugin uninstall "$p@shipright" && claude plugin install "$p@shipright" --scope user
done
```

Manual update of everything at once (picks up version changes only; `claude plugin update` does not cascade to dependencies):

```bash
for p in shipright superpowers impeccable taste-skill ponytail understand-anything; do
  claude plugin update "$p@shipright"
done
```

## Improving the process

The skills in this bundle are the process. When a step misleads you, sends you down a dead end, or misses a check that would have saved you, do not work around it silently: open a PR that edits the skill text with the lesson (what happened, what to do instead), the way `ship`'s own "Never Do" list was built. The bundled `superpowers:writing-skills` skill helps phrase and test the change. Bump the plugin version in both `plugins/shipright/.claude-plugin/plugin.json` and the `shipright` entry in `.claude-plugin/marketplace.json`, or the change never reaches installed machines.

## For admins

### claude.ai Team / Enterprise

Organization settings → **Plugins & skills** → **Add** → **Sync from GitHub** → `kureelvinay/shipright`. Set all six plugins to **Installed by default** and turn on **Sync automatically**. Members signed in with claude.ai get ShipRight with no commands; Claude Code syncs once per launch.

### IT-managed machines (API key / Bedrock / Vertex)

Add to `managed-settings.json`:

- macOS: `/Library/Application Support/ClaudeCode/managed-settings.json`
- Linux: `/etc/claude-code/managed-settings.json`
- Windows: `C:\Program Files\ClaudeCode\managed-settings.json`

```json
{
  "extraKnownMarketplaces": {
    "shipright": {
      "source": { "source": "github", "repo": "kureelvinay/shipright" },
      "autoUpdate": true
    }
  },
  "enabledPlugins": { "shipright@shipright": true },
  "env": { "FORCE_AUTOUPDATE_PLUGINS": "1" }
}
```

Plugins install at the start of each user's next session. `autoUpdate` is locked on by the managed value, and `FORCE_AUTOUPDATE_PLUGINS` keeps plugin auto-update running on fleets where Claude Code's own updater is disabled (`DISABLE_AUTOUPDATER`, `DISABLE_UPDATES`, or `autoUpdates: false`). If your machines reach GitHub over HTTPS rather than SSH, use `"source": { "source": "git", "url": "https://github.com/kureelvinay/shipright.git" }` as the marketplace source instead.

## For maintainers

- The ShipRight version lives in two places that must match: `plugins/shipright/.claude-plugin/plugin.json` and the `shipright` entry in `.claude-plugin/marketplace.json`. Bump both on any change to skills, hook, welcome text, or dependencies, then tag with `claude plugin tag`.
- Third-party pins live in `.claude-plugin/marketplace.json` as `sha` values. An entry with a `ref` (for example `v6.3.0`) tracks the newest tag of that family: same prefix, strict `X.Y.Z` ending, never backwards. An entry with only `sha` tracks the upstream main branch. To switch a plugin to tag tracking, add `ref` with its current tag and set `sha` to that tag's commit. `.github/workflows/bump-pins.yml` runs every Monday and opens a PR with compare links when any upstream moved. Read the diff, then merge. Run it by hand from the Actions tab for an urgent fix.
- `bump-pins.yml` opens its PR with the built-in `GITHUB_TOKEN`, which GitHub blocks by default. Once, in the repo: **Settings → Actions → General → Workflow permissions → Allow GitHub Actions to create and approve pull requests** (for an org repo, the org-level setting of the same name must allow it too). Without this, the Monday run fails at `gh pr create`.
- Keep `.claude-plugin/marketplace.json` in canonical form: `json.dumps(indent=2)` plus a trailing newline. A test fails CI otherwise. After a hand edit, reformat with `python3 -c "import json;p='.claude-plugin/marketplace.json';d=json.load(open(p));open(p,'w').write(json.dumps(d,indent=2)+'\n')"`.
- If you add required status checks on `main`, bump PRs will never receive them (PRs opened by `GITHUB_TOKEN` do not start workflows). Close and reopen the PR by hand to trigger `validate`, or keep `validate` optional and require only a pull-request review.
- Before tagging a release:

```bash
claude plugin validate . --strict
claude plugin validate plugins/shipright --strict
python3 -m unittest discover -s tests -v
export CLAUDE_CONFIG_DIR="$(mktemp -d)"
claude plugin marketplace add kureelvinay/shipright
claude plugin install shipright@shipright --scope user
claude plugin list   # expect 6 plugins
unset CLAUDE_CONFIG_DIR
```
