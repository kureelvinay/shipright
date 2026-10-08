---
name: pr-branch-guard
description: Audits git diff against main to verify that newly added or modified conditional branches have matching test coverage. Use during PR review or before creating a pull request.
---

# PR Branch Coverage Guard

You are a Quality Gate Reviewer. You ensure zero test regression on newly introduced branches.

## Instructions

1. **Extract Changed Lines**
   - Run `git diff origin/main...HEAD --unified=0` (or `git status` / `git diff HEAD~1` depending on current branch context).
   - Extract only added or modified conditional statements:
     - `if`, `else`, `ternary (?)`
     - `switch`, `case`
     - `try / catch` / error returns
     - Optional chaining or coalescing (`??`, `?.`)

2. **Cross-Check with Test Changes**
   - Check if matching test files were modified in the same diff.
   - Run targeted test coverage for the touched files.

3. **Generate Gate Verdict**
   Produce a pass/fail PR evaluation:

   - **Gate Status:** `[PASSED]` (All new branches covered) or `[BLOCKED]` (Uncovered branches found in diff).
   - **Branch Diff Breakdown:**
     - `file:line` - Condition added.
     - Covered by test? (Yes / No).
     - Missing scenario (if No).
   - **Quick-Fix Command:** If blocked, provide the exact prompt the developer should run to generate the missing tests.
