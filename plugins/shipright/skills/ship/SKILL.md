---
name: ship
description: Use when the user wants a requested change fully implemented and delivered as a pull request ready for their review, without being interrupted at each intermediate step — e.g. "ship this", "build and open a PR for X", "implement this end to end and give me a PR"
---

# Ship

## Overview

Chains the existing superpowers pipeline — brainstorm, plan, build, review,
fix, verify — into one run with exactly **one** human checkpoint: plan
approval. Everything after that runs unattended through to a pushed,
tested, reviewed PR. This skill adds no new technique; it sequences
skills that already exist and already enforce their own quality bars.

## When to Use

- The user asks to "ship", "build and PR", or "implement end to end" a
  real feature or fix and wants a finished PR to review, not a running
  commentary.
- Works the same whether the request is typed directly ("ship: add CSV
  export") or names/links a tracker ticket ("ship JIRA-4821", "ship this:
  <Azure DevOps URL>") — the ticket form adds one resolution step at the
  start of Step 1, nothing else changes.
- Not for one-line/trivial edits where the pipeline's overhead exceeds
  the change itself — use judgment, or ask if unsure.
- The user's own project may have a workflow memory (e.g. specific
  branch naming, `gh` auth path) — check for and follow it.

## The One Checkpoint (plus standing exceptions)

Brainstorming's plan-approval gate is the only *routine* pause in this
pipeline. Once the user approves the plan, do not stop again to ask
"should I continue?" or to show intermediate findings — this mirrors
subagent-driven-development's own continuous-execution rule, applied one
level up.

This does not override the platform's own safety rules, which still
apply throughout: stop and ask if a step turns out to be irreversible,
security-sensitive, or a decision only the user can make (e.g. a
security/privacy tradeoff discovered mid-build, not anticipated in the
plan). That is a real stop, not a "should I continue" checkpoint — state
the tradeoff plainly and wait for an answer, the same way plan approval
works.

A platform permission gate (e.g. an auto-mode classifier blocking a merge
or a destructive command) is the same kind of stop, not a pipeline
failure: it can trigger even for an action identical to one it allowed a
moment earlier. When it fires, do not retry the same action through a
different tool or phrasing — confirm nothing partial happened, tell the
user exactly what was attempted and why it's needed, and wait for an
explicit re-ask before repeating it.

## Model per Step

| Step | Model |
|---|---|
| 1. Ideate + plan | Fable |
| 2. Build | Sonnet |
| 3. Branch + PR | Sonnet |
| 4. Code review | Opus |
| 4b. Security review | Opus |
| 5. UI review | Opus |
| 6. Apply fixes | Sonnet |
| 7. Verify | Opus |
| 8. Hand back | Sonnet |

A running session cannot switch its own model — asked directly, the
platform refuses on the grounds that "a session must not silently
re-price its own turns." So a step's model is never set by switching
what this conversation runs on; it's pinned by dispatching that step's
actual work through the `Agent` tool with `model` set explicitly to the
table above, the same explicit-pin discipline this skill already applies
to `/code-review`'s effort level rather than trusting inherited state.
Each numbered step below names its model; do the work for that step via
an `Agent` call on that model rather than inline in whatever model
happens to be running this turn.

Two steps are interactive with the user (Step 1's plan approval, Step
8's handback) and stay that way: the *Agent* call on the pinned model
produces the content — the drafted plan, the drafted handback summary —
and this conversation's own turn is what actually shows it to the user
and, for Step 1, waits for approval. Dispatching the drafting work to
the pinned model is what matters; presenting it and pausing for the
user is inherently this turn's job, not a subagent's, regardless of
which model is orchestrating.

## Steps

1. **Ideate + plan (model: Fable).** If the request names or links a Jira/Azure DevOps
   ticket rather than describing the change directly, resolve it first:
   pull the ticket (via a connected project-tracker MCP if one is
   authenticated; otherwise ask the user to paste the ticket body — don't
   block on the connector), restate the ask in your own words, and pull
   its acceptance criteria as-written. Surface anything genuinely
   ambiguous or missing as a question *before* brainstorming — a wrong
   restatement caught now is cheap; caught after Step 2's build, it isn't.
   Feed the restated ask and acceptance criteria into brainstorming as
   its starting point instead of the raw ticket link.
   Invoke `superpowers:brainstorming` on the requested
   change. Let it hand off to `superpowers:writing-plans`. **The plan
   must include a documentation task** for any change that makes an
   existing README, `docs/**/*.md`, API reference, or other technical
   doc stale, or that warrants a new one (a new subsystem, a changed
   workflow, a new script/command) — written as a normal task with its
   own files-to-touch, not a vague "update docs if needed" footnote. If
   nothing needs documenting, say so explicitly in the plan rather than
   silently omitting the section, so it's a decision, not a gap. If the
   request actually bundles multiple independent changes, decompose
   into separate plans/PRs now (per brainstorming's own scope check) —
   one coherent change per `/ship` run, so the resulting PR stays
   reviewable. **Stop and present the plan for approval — wait for an
   explicit yes.**
2. **Build (model: Sonnet).** Once approved, invoke `superpowers:subagent-driven-development`
   to execute the plan on a feature branch. Let its own continuous
   execution and final whole-branch review run to completion without
   pausing to check in.
3. **Branch + PR (model: Sonnet).** Confirm the base branch (the branch this work forked
   from — usually `main`/`master`, but check git status/history or ask
   if more than one long-lived branch makes it ambiguous). If the
   feature branch isn't already pushed, push it and open a PR against
   that base with `gh pr create` (check memory for a project-specific
   `gh` path/auth note). Write the PR description in the Summary + Test
   Plan format with the generated-by footer, same as any other PR I
   create. End the description with the line `Shipped with ShipRight` on
   its own, so adoption can be counted with a GitHub search. Never push
   directly to the base branch.

   If this PR depends on another not-yet-merged PR (a stacked PR),
   target it at that PR's branch, but treat that as temporary, not a
   place to leave it: say so explicitly in the PR description, and
   re-target it to the real base as soon as its dependency merges. A
   stacked PR left pointed at an intermediate branch that itself never
   merges to the real base strands its content there — a real incident
   left several PRs' work stranded this way, and unwinding it meant
   folding an entire stack into one branch and hand-resolving conflicts
   across every PR downstream of the mistake.

   If this change needs to be verified together with another
   still-unmerged branch (e.g. one fix builds on infrastructure another
   unmerged PR adds), don't wait on that PR to merge just to test: build
   from a disposable local branch that merges both, verify there, and
   publish/test from that combined state. Never push that disposable
   branch or fold it into either PR — it exists only so testing isn't
   blocked on merge order, and each PR still ships its own real diff.
4. **Code review (model: Opus).** Run `/code-review` at `high` effort against the PR
   — pin the level explicitly rather than relying on "reuse the level
   you typed last," which has no prior turn to inherit from in an
   unattended run. If the project has a sweep-style or allowlist-style
   test (one that scans a fixed set of files/fixtures for a pattern,
   rather than the live source tree), explicitly check that the files
   this change touches are actually inside whatever set that test scans.
   A green pass proves nothing about a file the test was never looking
   at — that gap is exactly how two real branding bugs shipped
   undetected in an earlier project despite passing tests, because the
   relevant source files simply weren't in the test's fixture set.
4b. **Security review (model: Opus) — only if the diff touches auth or
   session code, secrets or credential handling, dependency manifests or
   lockfiles, CI workflows, infrastructure or deploy config, or input
   parsing at a trust boundary.** Run the built-in `/security-review`
   against the PR branch. It reports only high-confidence exploitable
   findings (injection, auth bypass, secrets exposure, unsafe
   deserialization, data leakage), so treat every High and Medium finding
   as a fix for Step 6, not a judgment call. When none of those areas
   changed, skip cleanly and say so in one line in the handback.
5. **UI review (model: Opus) — only if the diff touches UI/frontend files.** Run the
   `impeccable` skill against the branch for a visual/UX pass. Skip
   cleanly (don't force it) when nothing UI-facing changed.
6. **Apply fixes (model: Sonnet).** Apply findings from both reviews directly to the
   branch and push.
7. **Verify (model: Opus).** Run the full test suite — unit, and integration/UAT as
   its own explicit check if the project has one (a documented script,
   `Makefile` target, or CI config; don't guess a command). Report unit
   and integration/UAT results separately, not folded into one verdict —
   a partial pass is not "tests pass." If anything fails, check whether
   it also fails on the base branch before concluding this change caused
   it — a pre-existing or flaky failure and a real regression call for
   different next steps, and reporting one as the other sends the fix in
   the wrong direction. Before a production build, stop
   any running dev server first — building into the same output
   directory a dev server is using can corrupt its cache (seen
   first-hand: a live `next dev` plus a `next build` produced
   `Cannot find module` errors that needed a cache wipe and restart to
   fix). Build, then restart the dev server afterward if one was
   running. This is mandatory — never report the PR as ready without
   having actually run these in this pass. For any user-facing or UI
   change, also launch the app and use the actual changed behavior
   end-to-end (not just automated tests) — the empty-dev-database bug,
   the stuck "Saved" indicator, and the disappearing-invite-link bug
   earlier in this project were all the kind of thing only live use
   catches. Also confirm the plan's documentation task actually landed
   in the diff (or that the plan explicitly said none was needed) — a
   docs task that got silently dropped during the build is a gap to fix
   now, not something to notice later.

   If the project ships a packaged artifact (an installer, a compiled
   binary, a container image — anything with its own build/publish
   script separate from the app's source), building and merging the PR
   is not the finish line: build that artifact from the branch and
   confirm the fix is present *inside the compiled output*, not just in
   source (grep the packaged bundle/binary for the changed string, or
   equivalent). If publishing it is part of this request, verify what
   actually landed by re-fetching the published asset and comparing its
   checksum against the local build — an upload that reports success is
   not proof the right bytes are there, and a CI/registry cache can
   silently serve something older than what was just pushed.

   Before trusting any live/manual test of a long-running app, daemon,
   or installed binary, make sure the environment is actually clean:
   confirm there is exactly one running copy, matched by its exact
   binary path (never by process name alone — a stray build-output copy
   or an old install left in a different directory can silently answer
   the test instead of the one just built). Clear any local cache,
   token, or credential file that a previous run could have left behind
   if it might make a stale result look like a fresh one, and say
   explicitly what was checked or cleared. A stale copy or cached
   credential answering a live test can look exactly like the fix not
   working, and telling those apart from the user's side is expensive —
   ruling it out first is cheap.

   The same applies to shared local infrastructure when working in a
   worktree alongside other parallel sessions on the same machine: a
   local database, Docker container, or dev server that several
   worktrees bind to by default (the same fixed port or project ID) will
   have its state clobbered by whichever session touched it last. A
   real incident: 25+ worktrees of one repo sharing a single local
   Supabase instance caused test runs to intermittently see another
   branch's schema mid-test, making a real fix look flaky. If a test
   failure looks flaky specifically in a multi-worktree setup, check
   for a shared service before accepting "flaky" as the explanation —
   an isolated instance per worktree (a distinct project ID/port, or a
   container namespaced per branch) is worth the setup cost once this
   pattern shows up. Before running a full suite against a shared local
   resource, a cheap read-only check (e.g. querying which migrations are
   actually applied) can reveal another session is mid-flight against
   it — in that case, don't race it for a "clean" result; say so and
   skip the live run rather than reporting a false pass or false flake.
   (Sessions on this exact repo have done both: one raced a reset
   against a concurrent session and won by luck; a better one detected
   the conflict first and skipped the run entirely, reporting why. Do
   the latter.)

   Parallel worktree sessions have no shared memory of what earlier
   sessions already found. A pre-existing, unrelated test failure hit
   during verification (see above) may already be known and even fixed
   on another branch — one session, hitting exactly this, had to ask the
   user outright "is this already known?" with no way to check itself.
   If a project uses heavy worktree parallelism, look for (or propose)
   a durable, git-tracked place cross-cutting findings can land where
   every session reads it — a note in the relevant migration/config file
   itself works well, since that recurs with every checkout; a
   `KNOWN_ISSUES.md` or equivalent works too. Either way, when
   encountering a pre-existing failure, check that place before asking
   the user whether it's known.
8. **Hand back (model: Sonnet).** Report the PR URL, a one-line summary, test/build
   status, what each review flagged (code, security when it ran, UI) and
   how it was resolved, and — for
   UI-facing changes — a screenshot or brief description of what you
   actually saw when using it live. If a packaged artifact was built or
   published as part of this run, report its checksum (and release tag,
   if applicable) alongside the PR link, not just "published" — that
   single habit is what actually lets the user confirm they're looking
   at the right build instead of taking it on faith.

## Never Do

- Never merge the PR — the user reviews and merges, always.
- Never push straight to the base branch.
- Never pause between steps 2–8 to ask "should I continue?" — only
  plan approval and a genuine irreversible/security-sensitive/
  user-only decision stop the pipeline (see "standing exceptions"
  above).
- Never skip the Impeccable pass when UI changed, and never run it
  when nothing UI-facing changed.
- Never skip the security pass when the diff touches auth, secrets,
  dependencies, CI, infra, or trust-boundary parsing — and never run it as
  a formality when none of those changed.
- Never omit the `Shipped with ShipRight` footer from a PR this pipeline
  opens — it is how adoption is measured.
- Never run a production build while a dev server is pointed at the
  same output directory — stop it first, build, restart after.
- Never claim the PR is ready without evidence: this run's own test,
  build, and (for UI changes) live-usage output, not a memory of an
  earlier run.
- Never let a plan skip documentation silently — either it has a real
  doc task, or it explicitly states none is needed.
- Never let a `/ship` request quietly become two unrelated changes in
  one PR — decompose at planning time instead.
- Never report a test/integration failure as caused by this change
  without checking whether it's pre-existing on the base branch first.
- Never restate a tracker ticket's ask without surfacing missing or
  ambiguous acceptance criteria as a question — guessing scope from a
  thin ticket is the same mistake as skipping the plan-approval gate.
- Never trust that a packaged artifact carries a fix just because the
  build or upload command exited 0 — verify the fix inside the compiled
  output, and checksum-compare a published asset against the local
  build.
- Never declare a live/manual test conclusive without first confirming
  the environment is clean — one running copy at the exact path just
  built, and no stale cache/credential that could mask the real result.
- Never retry an action a platform permission gate just blocked, through
  another tool, phrasing, or encoding — report it and wait for an
  explicit re-ask (see "standing exceptions").
- Never push or merge a disposable local branch created only to test
  two in-flight changes together — it is scaffolding, not a deliverable.
- Never leave a stacked PR pointed at an intermediate branch once its
  dependency has merged — re-target it to the real base, or its content
  gets stranded.
- Never accept "the test is just flaky" in a multi-worktree setup
  without first checking whether a shared local service (DB, container,
  dev server) is being clobbered by a parallel session.
- Never race a shared local resource for a "clean" test result once a
  concurrent session's activity is detected on it — skip the run and
  report why instead.
- Never ask the user "is this pre-existing failure already known?"
  without first checking the project's own durable record of known
  issues, if one exists (or proposing one, if a worktree-heavy project
  has none).
- Never run a step's actual work on whatever model happens to be
  orchestrating this turn — dispatch it through the `Agent` tool with
  `model` pinned to that step's assigned model (see "Model per Step");
  a session cannot switch its own model, so inline execution silently
  ignores the assignment instead of erroring, which is easy to miss.

## Quick Reference

| Step | Model | Skill/tool | Pauses? |
|---|---|---|---|
| Ideate + plan (ticket resolution if applicable, incl. doc task, scope check) | Fable | brainstorming → writing-plans | Yes — plan approval |
| Build | Sonnet | subagent-driven-development | No* |
| Branch + PR (confirm base, Summary+Test Plan, combined-branch testing if needed) | Sonnet | git / gh | No |
| Code review (incl. test-coverage/fixture-gap check) | Opus | `/code-review` (effort: high) | No |
| Security review | Opus | `/security-review` (if diff touches auth/secrets/deps/CI/infra/trust-boundary parsing) | No |
| UI review | Opus | `impeccable` (if UI changed) | No |
| Apply fixes | Sonnet | — | No |
| Verify | Opus | unit + integration/UAT (separate results, pre-existing-failure check) + build (dev server stopped first) + live use for UI changes + clean-environment check + packaged-artifact/checksum verification if applicable | No |
| Handoff | Sonnet | PR link + screenshot for UI changes + artifact checksum/tag if applicable | Done — awaiting user |

\* Except a genuine irreversible/security-sensitive/user-only decision, or
a platform permission gate blocking a step — see "standing exceptions."
