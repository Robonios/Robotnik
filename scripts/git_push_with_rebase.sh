#!/usr/bin/env bash
# Push the current branch's new commits to its upstream. If another workflow pushed in
# the meantime and the push is rejected, rebase onto the upstream and try again, so a
# run never loses its commit to a race. Fails loudly, and pushes nothing, if the rebase
# conflicts or every attempt is rejected.
#
# Usage (in a workflow step, after `git commit`):  bash scripts/git_push_with_rebase.sh [attempts]
set -euo pipefail

attempts="${1:-4}"
for ((i = 1; i <= attempts; i++)); do
  if git push; then
    exit 0
  fi
  if [ "$i" -eq "$attempts" ]; then
    break
  fi
  echo "Push rejected (attempt ${i} of ${attempts}): rebasing onto the upstream and retrying."
  if ! git pull --rebase --autostash; then
    git rebase --abort 2>/dev/null || true
    echo "::error::Rebasing onto the upstream conflicted, so nothing was pushed. Another commit changed the same files; re-run this workflow."
    exit 1
  fi
  sleep $((i * 5))
done
echo "::error::The push was still rejected after ${attempts} attempts, so nothing was pushed. Re-run this workflow."
exit 1
