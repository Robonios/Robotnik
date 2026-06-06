#!/usr/bin/env python3
"""
Reject merge-conflict markers — the e4232597 bug class (#55).
=============================================================
On 2026-06-06 a botched merge (the #55 push vs the CI's nightly daily-update)
was committed WITH conflict markers left unresolved in 316 data files and pushed
to the remote — invalid JSON, broken site + pipeline. A trivial grep would have
stopped it. This is that grep, wired two ways:

  • pre-commit hook (`--staged`): blocks the commit locally, before it can reach
    the remote — the primary guard.
  • CI step (default: scan all tracked files): fails the pipeline if markers ever
    do reach the remote, so the bad data is never processed/published — backstop.

Stdlib only; exits 1 (with the offending files) if any marker is found.

Usage:
    python scripts/check_conflict_markers.py            # scan tracked files (CI)
    python scripts/check_conflict_markers.py --staged   # scan staged files (hook)
"""
import re
import subprocess
import sys

# A conflict marker is one of these at the START of a line:
#   <<<<<<< <branch>   |   =======   |   >>>>>>> <branch>
MARKER = re.compile(r"^(<{7} |={7}$|>{7} )")


def _git(args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout.split("\n")


def _files(staged):
    if staged:
        return [f for f in _git(["diff", "--cached", "--name-only", "--diff-filter=ACM"]) if f]
    return [f for f in _git(["ls-files"]) if f]


def main():
    staged = "--staged" in sys.argv
    bad = []
    files = _files(staged)
    for f in files:
        try:
            with open(f, encoding="utf-8", errors="ignore") as fh:
                for i, line in enumerate(fh, 1):
                    if MARKER.match(line):
                        bad.append((f, i, line.rstrip()[:30]))
                        break
        except (IsADirectoryError, FileNotFoundError, PermissionError):
            continue
    if bad:
        print("ERROR: merge-conflict markers present — REJECTED (#55 guard).", file=sys.stderr)
        for f, i, l in bad:
            print("  {}:{}: {}".format(f, i, l), file=sys.stderr)
        print("Resolve the conflict (remove <<<<<<< / ======= / >>>>>>>) before "
              "committing or publishing.", file=sys.stderr)
        sys.exit(1)
    print("conflict-marker check: clean ({} {} files)".format(
        len(files), "staged" if staged else "tracked"))


if __name__ == "__main__":
    main()
