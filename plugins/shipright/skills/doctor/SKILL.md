---
name: doctor
description: Checks this machine can install and run ShipRight (claude CLI, git access to the private repo, Node/Python, marketplace registration, the six plugins, auto-update, leftover personal skills) and prints a fix for each failure. Use when a ShipRight install fails, a /shipright skill is missing, auto-update seems off, or before onboarding a new machine.
---

# ShipRight doctor

Run the script that sits beside this file and show its output verbatim:

```bash
bash "<this skill's base directory>/doctor.sh"
```

The Skill tool prints the base directory when this skill loads. If the marketplace lives under a different GitHub owner, prefix the command with `SHIPRIGHT_REPO=<owner>/shipright`.

Then, for every `FAIL` line, offer its `fix:` command. Run a fix only when the user says so, and never change credentials or settings unasked. End with the script's one-line summary.
