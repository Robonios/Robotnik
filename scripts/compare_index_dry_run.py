#!/usr/bin/env python3
"""Compare a dry run of the index family with what main last published.

index-dry-run.yml recomputes the index family from the pipeline's cached inputs into a
gitignored folder (ROBOTNIK_INDEX_OUT) and checks out main's published files; this
script reports, per series, how far the dry run departs from main: common dates, the
largest absolute difference and its date, the first date that differs, and the two
latest levels. It also lists constituents added to or dropped from weights.json.

Index levels, index differences and tickers only: never a price or a market cap, since
the Actions log of a public repository is public. In GitHub Actions each line is a
notice annotation, which the checks API returns.

Usage:
  python scripts/compare_index_dry_run.py --base base/data/index --dry data/private/dryrun
"""
import argparse
import json
import os
import sys
from pathlib import Path

TOLERANCE = 0.005   # index points; both sides are published to 2 decimals


def say(msg):
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("::notice::" + " ".join(str(msg).split()), flush=True)
    else:
        print(msg)


def series_of(path, key=None):
    doc = json.loads(Path(path).read_text())
    node = doc[key] if key else doc
    return {p["date"]: p["value"] for p in node.get("series") or []}


def compare(name, base, dry):
    common = sorted(set(base) & set(dry))
    if not common:
        say("{}: no common dates (main {}, dry run {})".format(name, len(base), len(dry)))
        return False
    diffs = [(abs(dry[d] - base[d]), d) for d in common]
    worst, at = max(diffs)
    first = next((d for delta, d in sorted(diffs, key=lambda x: x[1]) if delta > TOLERANCE), None)
    last = common[-1]
    say("{}: {} common dates; max |diff| {:.2f} on {}; first difference {}; latest {} main "
        "{:.2f}, dry run {:.2f}; dates only in main {}, only in the dry run {}".format(
            name, len(common), worst, at, first or "none", last, base[last], dry[last],
            len(set(base) - set(dry)), len(set(dry) - set(base))))
    return worst <= TOLERANCE and set(base) == set(dry)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="folder holding main's data/index files")
    ap.add_argument("--dry", required=True, help="folder the dry run wrote to")
    args = ap.parse_args()
    base, dry = Path(args.base), Path(args.dry)

    same = compare("Public Equities", series_of(base / "robotnik_index.json"),
                   series_of(dry / "robotnik_index.json"))
    subs_b = json.loads((base / "sub_indices.json").read_text())
    subs_d = json.loads((dry / "sub_indices.json").read_text())
    for key in sorted(set(subs_b) | set(subs_d)):
        same &= compare("Sub-index " + key, series_of(base / "sub_indices.json", key) if key in subs_b else {},
                        series_of(dry / "sub_indices.json", key) if key in subs_d else {})
    same &= compare("Bottleneck-Weighted", series_of(base / "bottleneck_weighted_composite.json"),
                    series_of(dry / "bottleneck_weighted_composite.json"))

    wb = {w["ticker"] for w in json.loads((base / "weights.json").read_text())["weights"]}
    wd = {w["ticker"] for w in json.loads((dry / "weights.json").read_text())["weights"]}
    say("Constituents: main {}, dry run {}; added {}; dropped {}".format(
        len(wb), len(wd), sorted(wd - wb) or "none", sorted(wb - wd) or "none"))
    same &= wb == wd
    say("Dry run {} main.".format("matches" if same else "differs from"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
