#!/usr/bin/env python3
"""Run a command, stream its output, and report a failure as an annotation.

Workflow logs can't be read through the GitHub API from every client, but
annotations can, and they show on the run's summary page. On failure this prints
the command's last lines as one error annotation and exits with the command's
exit code; on success it adds nothing. Stdlib only.

Usage, in a workflow step:
    python scripts/run_step.py -- python scripts/calculate_index.py
"""
import collections
import os
import subprocess
import sys

TAIL_LINES = 15


def annotate(level, msg):
    """One GitHub Actions annotation (outside Actions, a line on stderr)."""
    text = " ".join(str(msg).split()).replace("%", "%25")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("::{}::{}".format(level, text), flush=True)
    else:
        print("{}: {}".format(level.upper(), text), file=sys.stderr)


def main(argv):
    cmd = argv[1:] if argv[:1] == ["--"] else argv
    if not cmd:
        annotate("error", "run_step.py: no command given")
        return 2
    label = " ".join(cmd)
    tail = collections.deque(maxlen=TAIL_LINES)
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                errors="replace", bufsize=1)
    except OSError as exc:
        annotate("error", "{} could not start: {}".format(label, exc))
        return 1
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        if line.strip():
            tail.append(line.strip())
    code = proc.wait()
    if code != 0:
        annotate("error", "{} exited with code {}. Last output: {}".format(
            label, code, " | ".join(tail) or "none"))
        return code if code > 0 else 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
