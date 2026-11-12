#!/usr/bin/env bash
# Save the daily record to the `state` branch (checked out in ./state by the workflow).
# If the main run and the backup run finish together, the second push is rejected.
# Git cannot merge posted.json as text, so we merge it as data (see `state.py merge`).
set -euo pipefail
ROOT="$(pwd)"
cd state
git config user.name "tunespout-bot"
git config user.email "tunespout-bot@users.noreply.github.com"

commit_if_changed() {
  git add -A
  git diff --cached --quiet || git commit -q -m "Record ${DAY:-$(date -u +%F)}"
}

commit_if_changed
if git diff --quiet origin/state HEAD 2>/dev/null; then
  echo "State unchanged."
  exit 0
fi
for attempt in 1 2 3 4; do
  if git push -q origin HEAD:state; then
    echo "State saved."
    exit 0
  fi
  echo "Push rejected (attempt $attempt): another run saved first. Merging both records."
  OURS="$(mktemp -d)"
  cp posted.json "$OURS/posted.json"
  [ -f tiktok_token.enc ] && cp tiktok_token.enc "$OURS/tiktok_token.enc"
  git fetch -q origin state
  git reset -q --hard origin/state
  (cd "$ROOT" && python3 src/state.py merge "$OURS/posted.json")
  [ -f "$OURS/tiktok_token.enc" ] && cp "$OURS/tiktok_token.enc" tiktok_token.enc
  commit_if_changed
done
echo "::error::Could not save the daily record."
exit 1
