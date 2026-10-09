#!/usr/bin/env bash
# Runs doctor.sh in a bare environment (no claude, empty config) and checks it
# reports failures with fix hints and still exits 0.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOCTOR="$ROOT/plugins/shipright/skills/doctor/doctor.sh"
tmp="$(mktemp -d)"
out="$(CLAUDE_CONFIG_DIR="$tmp" HOME="$tmp" PATH="/usr/bin:/bin" bash "$DOCTOR" 2>&1)"; rc=$?
fail() { echo "test_doctor: $1"; echo "--- output ---"; echo "$out"; exit 1; }
[ "$rc" -eq 0 ] || fail "expected exit 0, got $rc"
echo "$out" | grep -q '^FAIL  claude CLI' || fail "expected a FAIL line for the claude CLI"
echo "$out" | grep -q '^      fix: ' || fail "expected a fix hint under a FAIL line"
echo "$out" | grep -q '^FAIL  auto-update' || fail "expected a FAIL line for auto-update with empty settings"
echo "$out" | grep -qE '^[0-9]+ passed, [0-9]+ failed$' || fail "expected the summary line"
echo "test_doctor: ok"
