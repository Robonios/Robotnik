# History purge plan — PREPARED, NOT EXECUTED

This plan scrubs the **145 inert files** removed at HEAD on 2026-06-29 (see
[DATA_EXPOSURE_REMOVAL.md](DATA_EXPOSURE_REMOVAL.md)) from the **entire git
history**. HEAD removal alone leaves them retrievable from old commits; this is
the step that removes them from history.

> **Claude does NOT run any of this.** History rewrite + force-push are
> deliberate, destructive, and Robert-executed, after the backup in Step 1.

## Honest caveat — what a purge can and cannot do

The repo has been **public**. A history rewrite **cannot** retract anything
already cloned, forked, or cached by GitHub/third parties. It **reduces** future
exposure (no one cloning *after* the purge gets the files); it **cannot guarantee
erasure**. Anything genuinely secret must be treated as already disclosed and
**rotated**, not merely purged. (Secret-scan of this set was clean, so there is
nothing to rotate here.)

## Step 1 — MANDATORY backup first (do not skip)

```bash
# (a) Full mirror clone — a complete, separate copy of all refs/history.
git clone --mirror git@github.com:Robonios/Robotnik.git ~/robotnik-mirror-backup.git

# (b) A dated backup branch on the working clone, pushed to origin.
cd ~/Projects/Robotnik
git branch backup/pre-purge-2026-06-29
git push origin backup/pre-purge-2026-06-29
```
This mirror is **separate** from `~/Robotnik-private-archive/` (the data archive)
— two independent safety nets. Verify the mirror is complete before proceeding.

## Step 2 — Build the path list to purge

The list is exactly the 145 relpaths in the preservation manifest:

```bash
# From the archive manifest, emit one path per line (skip comments/header).
tail -n +5 ~/Robotnik-private-archive/MANIFEST_inert_removal.tsv \
  | cut -f1 > ~/purge-paths.txt
wc -l ~/purge-paths.txt   # expect 145
```
*(Optionally add `js/main.js` and the two retired archive HTML pages if you also
want the legacy dashboard scrubbed — they are low-sensitivity code, so optional.)*

## Step 3 — Rewrite history (git-filter-repo PREFERRED)

`git-filter-repo` is the maintained, recommended tool (BFG is the fallback).

```bash
# Install if needed:  brew install git-filter-repo
cd ~/Projects/Robotnik
git filter-repo --invert-paths --paths-from-file ~/purge-paths.txt
```

<details><summary>BFG fallback</summary>

```bash
# BFG deletes by filename glob, not full path — less precise; prefer filter-repo.
java -jar bfg.jar --delete-files '{investors.json,registry.json,...}' Robotnik.git
git reflog expire --expire=now --all && git gc --prune=now --aggressive
```
</details>

`filter-repo` removes the remote by design; re-add it:
```bash
git remote add origin git@github.com:Robonios/Robotnik.git
```

## Step 4 — Force-push (WRITTEN, do NOT run until Steps 1–3 verified)

```bash
# ⚠️ Destructive. Rewrites public history for every collaborator/fork.
# Pause the data-pipeline cron first so no run collides with the rewrite.
# git push --force --all origin
# git push --force --tags origin
```
Leave these **commented**. Run them only after: backup verified (Step 1), the
local rewrite looks correct (`git log`, repo size dropped), and the cron is
paused. After the push, every collaborator must re-clone; existing clones/forks
are unaffected (the caveat above).

## Step 5 — After the purge

- Confirm the 145 paths are gone from history: `git log --all -- <a-removed-path>`
  returns nothing.
- Repo size should drop materially (most of the 27 MB).
- Re-enable the cron.
- A **second, larger purge** will be needed once the gate-build moves the deferred
  CI substrate (price history etc.) out of the public repo — that is a separate
  future pass, not this one.
