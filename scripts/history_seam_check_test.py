#!/usr/bin/env python3
"""
Unit tests for the E12 history-seam check in scripts/check_entity_lifecycle.py.
Synthetic fixtures only (no vendor data).

Run:  python3 scripts/history_seam_check_test.py      (verbose: add -v)
"""
import json
import os
import sys
import tempfile
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_entity_lifecycle as lc  # noqa: E402

TODAY = date(2026, 11, 23)


def write(dirname, ticker, closes, start):
    d0 = date.fromisoformat(start)
    rows = [{"date": (d0 + timedelta(days=i)).isoformat(), "close": c} for i, c in enumerate(closes)]
    with open(os.path.join(dirname, ticker.replace(" ", "_") + ".json"), "w") as f:
        json.dump({"ticker": ticker, "series": rows}, f)


class SeamCheckTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.saved = lc.HISTORY_DIR
        lc.HISTORY_DIR = self.dir

    def tearDown(self):
        lc.HISTORY_DIR = self.saved

    def test_recent_split_step_is_found(self):
        write(self.dir, "4062 JP", [100, 101, 50.6, 51], "2026-10-01")
        found = lc.check_seams({"4062 JP"}, today=TODAY)
        self.assertEqual([(f["ticker"], f["date"], f["label"]) for f in found],
                         [("4062 JP", "2026-10-03", "2-for-1 split")])

    def test_consolidation_is_found(self):
        write(self.dir, "MNTS", [1, 1.02, 10.1, 10.2], "2026-10-01")
        self.assertEqual(lc.check_seams({"MNTS"}, today=TODAY)[0]["label"], "1-for-10 consolidation")

    def test_bad_print_undone_next_bar_is_skipped(self):
        write(self.dir, "AAA", [100, 101, 50.5, 101.5], "2026-10-01")
        self.assertEqual(lc.check_seams({"AAA"}, today=TODAY), [])

    def test_ordinary_moves_and_old_steps_are_skipped(self):
        write(self.dir, "BBB", [100, 93, 104, 98], "2026-10-01")
        write(self.dir, "CCC", [100, 101, 50.6, 51], "2025-10-01")
        self.assertEqual(lc.check_seams({"BBB", "CCC"}, today=TODAY), [])

    def test_only_members_are_read(self):
        write(self.dir, "DDD", [100, 101, 50.6, 51], "2026-10-01")
        self.assertEqual(lc.check_seams(set(), today=TODAY), [])

    def test_missing_history_is_skipped(self):
        self.assertEqual(lc.check_seams({"EEE"}, today=TODAY), [])


if __name__ == "__main__":
    unittest.main()
