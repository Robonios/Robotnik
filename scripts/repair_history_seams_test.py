#!/usr/bin/env python3
"""
Unit tests for scripts/repair_history_seams.py. Synthetic fixtures only (no vendor data).

Run:  python3 scripts/repair_history_seams_test.py      (verbose: add -v)
"""
import json
import os
import sys
import tempfile
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import repair_history_seams as rh  # noqa: E402


def series(closes, start="2026-09-01"):
    d0 = date.fromisoformat(start)
    return [{"date": (d0 + timedelta(days=i)).isoformat(), "open": c, "high": c, "low": c,
             "close": c, "volume": 100} for i, c in enumerate(closes)]


# A 1-for-5 seam on day 10 (2026-09-11) with a 1.5% fall that day; the split itself on day 20.
SEAMED = [500 + i for i in range(10)] + [101.9 + i for i in range(20)]


class RepairTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.hist = os.path.join(self.dir, "history")
        os.makedirs(self.hist)
        self.reg = os.path.join(self.dir, "repairs.json")
        json.dump({"splits": [{"ticker": "6861 JP", "ex_date": "2026-09-21", "factor": 5}]},
                  open(self.reg, "w"))

    def write(self, closes):
        json.dump({"ticker": "6861 JP", "series": series(closes)},
                  open(os.path.join(self.hist, "6861_JP.json"), "w"))

    def closes(self):
        doc = json.load(open(os.path.join(self.hist, "6861_JP.json")))
        return [r["close"] for r in doc["series"]], doc["series"]

    def run_(self, apply):
        return rh.run(apply=apply, registry=self.reg, history_dir=self.hist)

    def test_dry_run_changes_nothing(self):
        self.write(SEAMED)
        self.assertEqual(self.run_(False), [("6861 JP", "would repair")])
        self.assertEqual(self.closes()[0], SEAMED)

    def test_apply_removes_the_seam_and_keeps_the_days_move(self):
        self.write(SEAMED)
        self.assertEqual(self.run_(True), [("6861 JP", "repaired")])
        closes, rows = self.closes()
        self.assertAlmostEqual(closes[0], 100.0)
        self.assertAlmostEqual(closes[10] / closes[9], 101.9 / (509 / 5))
        self.assertEqual(rows[0]["volume"], 500)
        self.assertEqual(rows[10]["volume"], 100)

    def test_second_run_finds_it_clean(self):
        self.write(SEAMED)
        self.run_(True)
        before = self.closes()[0]
        self.assertEqual(self.run_(True), [("6861 JP", "clean")])
        self.assertEqual(self.closes()[0], before)

    def test_a_reverted_bad_print_is_not_a_seam(self):
        self.write([500 + i for i in range(10)] + [101.0, 511] + [512 + i for i in range(10)])
        self.assertEqual(self.run_(True), [("6861 JP", "clean")])

    def test_two_candidates_are_left_alone(self):
        self.write([2500 + i for i in range(5)] + [501 + i for i in range(5)] + [101.9 + i for i in range(5)])
        self.assertEqual(self.run_(True), [("6861 JP", "ambiguous")])

    def test_steps_outside_the_lookback_are_ignored(self):
        json.dump({"splits": [{"ticker": "6861 JP", "ex_date": "2027-12-01", "factor": 5}]},
                  open(self.reg, "w"))
        self.write(SEAMED)
        self.assertEqual(self.run_(True), [("6861 JP", "clean")])

    def test_missing_history(self):
        self.assertEqual(self.run_(True), [("6861 JP", "no history file")])


if __name__ == "__main__":
    unittest.main()
