#!/usr/bin/env python3
"""
Unit tests for scripts/history_rebase.py: a refreshed window merged over stored history.
Synthetic fixtures only (no network, no vendor data).

Run:  python3 scripts/history_rebase_test.py      (verbose: add -v)
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from history_rebase import rebase_factor, rebase_stored  # noqa: E402


def bars(prices, start=1, volume=1000):
    return [{"date": "2026-09-{:02d}".format(start + i), "open": p, "high": p, "low": p,
             "close": p, "volume": volume} for i, p in enumerate(prices)]


# Stored: 20 bars at the old basis. The refreshed window covers days 11-20, split 2-for-1
# from day 16: the vendor halves days 11-15, and days 16-20 trade at the new price.
STORED = bars([100 + i for i in range(15)]) + bars([57.5 + i for i in range(5)], start=16)
WINDOW = bars([(110 + i) / 2 for i in range(5)], start=11) + bars([57.5 + i for i in range(5)], start=16)


def merged(stored, window):
    by = {r["date"]: r for r in stored}
    by.update({r["date"]: r for r in window})
    return [by[d] for d in sorted(by)]


class RebaseTest(unittest.TestCase):
    def test_split_in_window_rebases_older_bars(self):
        out, f = rebase_stored(STORED, WINDOW)
        self.assertAlmostEqual(f, 2.0)
        closes = [r["close"] for r in merged(out, WINDOW)]
        steps = [b / a for a, b in zip(closes, closes[1:])]
        self.assertTrue(all(0.9 < s < 1.1 for s in steps), steps)
        self.assertEqual(out[0]["volume"], 2000)

    def test_bars_after_the_split_keep_their_basis(self):
        out, _ = rebase_stored(STORED, WINDOW)
        self.assertEqual(out[15]["close"], 57.5)
        self.assertEqual(out[14]["close"], 114 / 2)

    def test_second_refresh_changes_nothing(self):
        out, _ = rebase_stored(STORED, WINDOW)
        again, f = rebase_stored(merged(out, WINDOW), WINDOW)
        self.assertIsNone(f)
        self.assertEqual(again, merged(out, WINDOW))

    def test_agreeing_sources_change_nothing(self):
        stored = bars([100 + i for i in range(20)])
        out, f = rebase_stored(stored, bars([110 + i for i in range(10)], start=11))
        self.assertIsNone(f)
        self.assertIs(out, stored)

    def test_disagreeing_probe_changes_nothing(self):
        window = bars([55, 60, 70, 50, 52], start=11)   # no common ratio
        self.assertEqual(rebase_factor(STORED, window), (None, None))

    def test_small_drift_is_left_alone(self):
        window = bars([(110 + i) * 0.99 for i in range(10)], start=11)
        self.assertEqual(rebase_factor(STORED[:15] + bars([115 + i for i in range(5)], start=16), window), (None, None))

    def test_no_shared_dates(self):
        self.assertEqual(rebase_factor([], WINDOW), (None, None))
        self.assertEqual(rebase_factor(STORED, []), (None, None))

    def test_reverse_split(self):
        stored = bars([1.0 + i / 100 for i in range(20)])
        window = bars([(1.10 + i / 100) * 10 for i in range(10)], start=11)
        out, f = rebase_stored(stored, window)
        self.assertAlmostEqual(f, 0.1)
        self.assertAlmostEqual(out[0]["close"], 10.0)


if __name__ == "__main__":
    unittest.main()
