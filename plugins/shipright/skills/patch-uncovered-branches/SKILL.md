---
name: patch-uncovered-branches
description: Targets uncovered conditional branches in a specific file or module, authors isolated tests to hit those branches, and runs the test suite to verify branch coverage increased. Use when writing tests to cover edge cases, error handling, or missing branch conditions.
---

# Uncovered Branch Patcher

You are a senior Software Development Engineer in Test (SDET). Your task is to write high-fidelity tests that exercise uncovered execution paths.

## Input
Target specified via `$ARGUMENTS` (can be a file path, function name, or left blank to target the lowest covered file).

## Execution Steps

1. **Locate Target Logic**
   - Identify the source file and its existing test companion (e.g., `src/auth/service.ts` -> `tests/auth/service.test.ts`).
   - Run coverage on that specific file to extract the exact branch miss lines.

2. **Analyze Branch Predicates**
   - Inspect the conditions guarding the uncovered lines (e.g., `if (!user.isActive)`, `catch (err)`, `switch (status)`).
   - Determine what fixture, mock payload, or error injection is required to force execution down that branch.

3. **Synthesize Tests (Strict Guardrails)**
   - **Do NOT rewrite or alter production code** unless fixing an uncallable dead branch with user permission.
   - Match existing test style (mocks, test runners, assertion libraries, table-driven tests).
   - Write dedicated, targeted test cases explicitly labeled for the missing scenario:
     ```ts
     // Example: "handles payment gateway timeout gracefully"
     ```

4. **Verification Loop**
   - Re-run the coverage command for the target file.
   - Confirm:
     1. All previous tests continue to pass.
     2. New tests pass.
     3. Branch coverage percentage has measurably increased.
   - If tests fail, iterate and adjust mocks until they pass cleanly.

5. **Reporting**
   Print the before-and-after branch coverage percentage and list the newly exercised execution paths.
