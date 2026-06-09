#!/usr/bin/env python3
"""
Unit tests for scripts/index_dates.py — the shared date-axis rules.
===================================================================
Synthetic fixtures only (NO live data). Exercises the four centralized rules:

  1. Quorum            — a date with >=98/197 eligible is kept; <98 is dropped.
  2. Fixed floor       — resolves to 2021-05-07 and does NOT advance with wall-clock.
  3. Injection gate    — a sub-quorum thin session (the 06-08 case) is gated, not admitted.
  4. Trading-day filter— weekends / holidays are excluded.

Run:  python3 scripts/index_dates_test.py      (verbose: add -v)
Stdlib unittest only — matches the repo's no-build-tools constraint.
"""
import inspect
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import index_dates as ix  # noqa: E402

# ── synthetic eligible universe: 197 names, matching the production size so the
#    50% / 5% / 30% thresholds land on the same integer boundaries as the book. ──
N = 197
ELIG = ["t{:03d}".format(i) for i in range(N)]


def price_matrix(spec):
    """{date: n_traders} -> {date: {ticker: close}} (the first n ELIG names trade)."""
    return {d: {ELIG[i]: 100.0 for i in range(n)} for d, n in spec.items()}


def traded_for(pm):
    """The representation-agnostic predicate the module consumes."""
    return lambda t, d: t in pm.get(d, {})


def snapshot_rows(spec):
    """{date: n_priced} -> list of (ticker, date) priced rows (the snapshot feed)."""
    rows = []
    for d, n in spec.items():
        rows += [(ELIG[i], d) for i in range(n)]
    return rows


class Quorum(unittest.TestCase):
    """Rule 1 — >=50% (98/197) eligible traded keeps the date; below drops it."""

    def test_threshold_is_98(self):
        self.assertEqual(ix.TRADING_COVERAGE, 0.50)
        self.assertEqual(max(1, int(N * ix.TRADING_COVERAGE)), 98)

    def test_98_kept_97_dropped(self):
        pm = price_matrix({
            "2025-01-02": 98,    # == quorum  -> KEEP
            "2025-01-03": 97,    # one short  -> DROP
            "2025-01-06": 197,   # full       -> KEEP
            "2025-01-07": 0,     # empty      -> DROP
        })
        kept = ix.trading_days(sorted(pm), ELIG, traded_for(pm))
        self.assertEqual(kept, ["2025-01-02", "2025-01-06"])

    def test_partial_universe_scales(self):
        # need tracks len(eligible): a 10-name universe needs >=5.
        elig10 = ELIG[:10]
        pm = {"d1": {elig10[i]: 1.0 for i in range(5)},   # 5/10 -> keep
              "d2": {elig10[i]: 1.0 for i in range(4)}}    # 4/10 -> drop
        self.assertEqual(ix.trading_days(["d1", "d2"], elig10, traded_for(pm)), ["d1"])


class FixedFloor(unittest.TestCase):
    """Rule 2 — fixed data floor 2021-05-07, wall-clock-independent."""

    def test_constant_is_fixed_literal(self):
        self.assertEqual(ix.SUB_INDEX_FLOOR, "2021-05-07")

    def test_resolves_to_floor_and_gates_pre_floor_dates(self):
        # Pre-floor dates carry FULL coverage but must not be chosen — the floor
        # is enforced (this is what the old rolling today-1825d window did not do).
        pm = price_matrix({
            "2021-04-30": N, "2021-05-03": N,    # pre-floor, full -> excluded
            "2021-05-07": N, "2021-05-10": N,    # at / after floor
        })
        self.assertEqual(ix.sub_index_base(sorted(pm), ELIG, traded_for(pm)), "2021-05-07")

    def test_skips_thin_first_eligible_day(self):
        # >=30% coverage needed at the base. 197*0.30 = 59.1 -> 59 fails, 60 passes.
        pm = price_matrix({"2021-05-07": 59, "2021-05-10": 60})
        self.assertEqual(ix.sub_index_base(sorted(pm), ELIG, traded_for(pm)), "2021-05-10")

    def test_does_not_advance_with_wall_clock(self):
        # The function takes NO time input and uses no clock, so the floor cannot
        # creep forward day to day (the defect the fixed floor replaced). Prove it:
        #  (a) no `today`-style parameter in the signature,
        #  (b) deterministic across repeated calls.
        params = set(inspect.signature(ix.sub_index_base).parameters)
        self.assertEqual(params & {"today", "today_str", "now", "asof"}, set())
        pm = price_matrix({"2021-04-30": N, "2021-05-07": N, "2024-01-02": N})
        axis = sorted(pm)
        r1 = ix.sub_index_base(axis, ELIG, traded_for(pm))
        r2 = ix.sub_index_base(axis, ELIG, traded_for(pm))
        self.assertEqual(r1, "2021-05-07")
        self.assertEqual(r1, r2)


class InjectionGate(unittest.TestCase):
    """Rule 3 — a thin session present in history but below quorum stays gated."""

    def test_thin_session_in_history_is_gated(self):
        # The 06-08 case: dropped from the axis by the quorum filter, but PRESENT
        # in price_matrix (history carries ~25 bars). It must be returned as the
        # candidate (for caller-side validation) yet NOT re-admitted to the axis.
        all_dates = ["2026-06-04", "2026-06-05"]
        pm = {"2026-06-04": {}, "2026-06-05": {},
              "2026-06-08": {ELIG[i]: 1.0 for i in range(25)}}  # ~25 names, thin
        before = list(all_dates)
        inj = ix.extend_axis_for_snapshot(all_dates, pm, "2026-06-08")
        self.assertEqual(inj, "2026-06-08")     # candidate returned
        self.assertEqual(all_dates, before)      # but axis UNCHANGED
        self.assertNotIn("2026-06-08", all_dates)

    def test_genuinely_new_date_is_admitted(self):
        # A date NOT already in price_matrix is genuinely new -> admitted + sorted in.
        all_dates = ["2026-06-04", "2026-06-05"]
        pm = {"2026-06-04": {}, "2026-06-05": {}}
        inj = ix.extend_axis_for_snapshot(all_dates, pm, "2026-06-09")
        self.assertEqual(inj, "2026-06-09")
        self.assertEqual(all_dates[-1], "2026-06-09")
        self.assertIn("2026-06-09", pm)          # axis key created for it

    def test_not_fresher_than_history_is_noop(self):
        all_dates = ["2026-06-04", "2026-06-05"]
        pm = {"2026-06-04": {}, "2026-06-05": {}}
        before = list(all_dates)
        inj = ix.extend_axis_for_snapshot(all_dates, pm, "2026-06-05")  # == last hist
        self.assertIsNone(inj)
        self.assertEqual(all_dates, before)


class SnapshotDataDate(unittest.TestCase):
    """The snapshot feeder for the injection gate: latest <= today with quorum."""

    def test_quorum_is_10(self):
        self.assertEqual(max(ix.SNAPSHOT_QUORUM_MIN, int(N * ix.SNAPSHOT_QUORUM_PCT)), 10)

    def test_latest_qualifying_snapshot_date(self):
        rows = snapshot_rows({"2026-06-05": 172, "2026-06-08": 25, "2026-06-09": 50})
        # 06-08 has 25 (>= 10) and is the latest <= today -> data_date = 06-08.
        # 06-09 is in the future relative to today_str and is excluded.
        self.assertEqual(
            ix.snapshot_data_date(rows, ELIG, today_str="2026-06-08"), "2026-06-08")

    def test_subquorum_snapshot_date_excluded(self):
        rows = snapshot_rows({"2026-06-05": 172, "2026-06-08": 9})  # 9 < quorum(10)
        self.assertEqual(
            ix.snapshot_data_date(rows, ELIG, today_str="2026-06-08"), "2026-06-05")


class TradingDayFilter(unittest.TestCase):
    """Rule 4 — weekends and holidays (thin, sub-quorum) are excluded."""

    def test_weekend_and_holiday_excluded(self):
        pm = price_matrix({
            "2026-06-05": N,    # Fri  full session             -> KEEP
            "2026-06-06": 5,    # Sat  weekend (5 intl strays)  -> DROP
            "2026-06-08": 30,   # Mon  holiday, thin (30/197)   -> DROP
            "2026-06-09": N,    # Tue  full session             -> KEEP
        })
        self.assertEqual(ix.trading_days(sorted(pm), ELIG, traded_for(pm)),
                         ["2026-06-05", "2026-06-09"])

    def test_quorum_filter_then_floor_compose(self):
        # End-to-end on the axis: filter drops the thin Monday, floor anchors 05-07.
        pm = price_matrix({
            "2021-05-06": N,    # pre-floor full -> kept by filter, gated by floor
            "2021-05-07": N,    # floor day, full
            "2021-05-08": 10,   # thin -> dropped by filter
            "2021-05-10": N,    # full
        })
        axis = ix.trading_days(sorted(pm), ELIG, traded_for(pm))
        self.assertEqual(axis, ["2021-05-06", "2021-05-07", "2021-05-10"])  # 05-08 dropped
        self.assertEqual(ix.sub_index_base(axis, ELIG, traded_for(pm)), "2021-05-07")


if __name__ == "__main__":
    unittest.main(verbosity=2)
