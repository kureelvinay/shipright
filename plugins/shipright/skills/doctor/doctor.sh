#!/usr/bin/env bash
# ShipRight doctor: checks this machine can install and run ShipRight.
# Prints PASS/FAIL per check with a fix for each failure. Always exits 0.
#   bash doctor.sh                      # default repo kureelvinay/shipright
#   SHIPRIGHT_REPO=org/repo bash doctor.sh
set -u
REPO="${SHIPRIGHT_REPO:-kureelvinay/shipright}"
CONFIG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
pass=0; fail=0
ok()  { pass=$((pass + 1)); printf 'PASS  %s\n' "$1"; }
bad() { fail=$((fail + 1)); printf 'FAIL  %s\n      fix: %s\n' "$1" "$2"; }
has() { command -v "$1" >/dev/null 2>&1; }

# --- tools ---
if has claude; then ok "claude CLI on PATH ($(claude --version 2>/dev/null | head -1))"
else bad "claude CLI not on PATH" "npm i -g @anthropic-ai/claude-code   (inside the desktop app you can use /plugin instead)"; fi
if has node; then ok "node $(node --version 2>/dev/null)"; else bad "node missing (ponytail hooks, understand-anything dashboard)" "brew install node"; fi
if has python3; then ok "python3 $(python3 --version 2>&1 | awk '{print $2}')"; else bad "python3 missing (graphify)" "brew install python"; fi
if has uv || (has python3 && python3 -m pip --version >/dev/null 2>&1); then ok "uv or pip available (graphify installs graphifyy on first use)"
else bad "neither uv nor pip found (graphify needs one)" "brew install uv"; fi

# --- git access to the private repo, without prompting ---
if GIT_TERMINAL_PROMPT=0 git ls-remote "https://github.com/$REPO.git" HEAD >/dev/null 2>&1 \
   || GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="ssh -o BatchMode=yes" git ls-remote "git@github.com:$REPO.git" HEAD >/dev/null 2>&1; then
  ok "git reaches github.com/$REPO without prompting"
else
  bad "git cannot reach github.com/$REPO without prompting" "gh auth login && gh auth setup-git   (or add an SSH key at https://github.com/settings/keys); also confirm you have read access to the repo"
fi

# --- plugin state (needs the CLI) ---
if has claude; then
  if claude plugin marketplace list 2>/dev/null | grep -q 'shipright'; then ok "marketplace shipright registered"
  else bad "marketplace shipright not registered" "claude plugin marketplace add $REPO"; fi
  installed="$(claude plugin list 2>/dev/null)"
  missing=""
  for p in shipright superpowers impeccable taste-skill ponytail understand-anything; do
    echo "$installed" | grep -q "$p@shipright" || missing="$missing $p"
  done
  if [ -z "$missing" ]; then ok "all six plugins installed from shipright"
  else bad "not installed from shipright:$missing" "claude plugin install shipright@shipright --scope user"; fi
  dups="$(echo "$installed" | grep -E '(superpowers|impeccable|taste-skill|ponytail|understand-anything)@' | grep -v '@shipright' | sed 's/.*❯ *//' | tr '\n' ' ')"
  if [ -z "$dups" ]; then ok "no duplicate copies of the five dependencies"
  else bad "duplicate copies from other marketplaces: $dups" "claude plugin uninstall <plugin>@<marketplace> for each one listed"; fi
fi

# --- auto-update on for the shipright marketplace ---
if has python3 && python3 - "$CONFIG/settings.json" <<'PY' 2>/dev/null
import json, sys
s = json.load(open(sys.argv[1]))
sys.exit(0 if s.get("extraKnownMarketplaces", {}).get("shipright", {}).get("autoUpdate") else 1)
PY
then ok "auto-update on for marketplace shipright"
else bad "auto-update off for marketplace shipright (pin bumps will not reach this machine)" "in a Claude Code session: /plugin → Marketplaces → shipright → Enable auto-update"; fi

# --- personal copies that would shadow the plugin's skills ---
if [ -e "$CONFIG/skills/ship" ] || [ -e "$CONFIG/skills/graphify" ]; then
  bad "personal copies of ship/graphify under $CONFIG/skills shadow the plugin's" "mkdir -p $CONFIG/backups && mv $CONFIG/skills/ship $CONFIG/skills/graphify $CONFIG/backups/ 2>/dev/null"
else ok "no personal ship/graphify copies shadowing the plugin"; fi

printf '\n%d passed, %d failed\n' "$pass" "$fail"
exit 0
