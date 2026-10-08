SHIPRIGHT ACTIVE — kureelvinay engineering standard for Claude Code.

Use the standard flow, not ad-hoc edits:
- New feature or bug fix → /shipright:ship  (brainstorm → plan → build → review → verify → PR; one human checkpoint: plan approval)
- Before opening any PR by hand → /shipright:pr-branch-guard
- Writing tests for uncovered paths → /shipright:patch-uncovered-branches
- Release health / test-gap triage → /shipright:branch-audit
- Unfamiliar codebase → /shipright:graphify or /understand-anything:understand
- UI changes → impeccable runs inside /ship; on demand: /impeccable:impeccable audit

Ponytail (lazy senior dev) is on: smallest working diff, no speculative abstractions.
Process guide: https://github.com/kureelvinay/shipright#readme
