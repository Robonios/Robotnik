#!/usr/bin/env python3
"""
Shared trading-day axis for the Robotnik index family.
======================================================
ONE definition of the date-axis rules consumed by calculate_index.py,
calculate_bottleneck_composite.py, and verify_index_reconstruction.py:

  - the eligible trading-day quorum (a date is a real session iff >= 50% of
    eligible constituents actually traded — drops weekends/holidays/thin partials),
  - the fixed sub-index floor (2021-05-07, the data floor — first quorum day —
    NOT a rolling today-1825d window),
  - the live-snapshot injection guard: a snapshot date enters the published axis
    ONLY if it is genuinely NEW (not already a price_matrix key). A date that
    exists in history but was dropped by the quorum filter is a thin/partial
    session and stays GATED,
  - admissions not yet in force (pending_entries): a company admitted ahead of
    its index_entry_date stays out of the index until its price history reaches
    the date.

Before this module the rules were re-implemented per script and had drifted:
calculate_bottleneck_composite tested `data_date not in all_dates` for the
injection guard (which RE-ADMITS a quorum-filtered thin session — it published a
spurious 2026-06-08 partial), where calculate_index correctly tested
`inject_date not in price_matrix`. Centralising eliminates that drift class — the
bottleneck now inherits the correct guard by sharing, not by a separate patch.

Representation-agnostic: callers pass a `traded(ticker, date) -> bool` predicate,
so the date-keyed price_matrix (production) and the per-ticker {date: close}
series (the independent reconstruction) drive the SAME rule from their own
representations.
"""

# ── methodology constants (defined ONCE; imported by all three consumers) ──
SUB_INDEX_FLOOR     = "2021-05-07"  # fixed data floor (first >=quorum day), not rolling
TRADING_COVERAGE    = 0.50          # a date is a trading day iff >= this share of eligible traded
SUB_COVERAGE        = 0.30          # min eligible coverage to anchor the sub-index base
SNAPSHOT_QUORUM_MIN = 10            # snapshot data_date needs >= max(MIN, PCT*eligible) priced
SNAPSHOT_QUORUM_PCT = 0.05


def trading_days(all_dates, eligible, traded, coverage=TRADING_COVERAGE):
    """Dates on which >= `coverage` of `eligible` constituents actually traded.

    `traded(ticker, date) -> bool`. Truncating int() on the threshold matches the
    historical per-script behaviour exactly (e.g. 197 * 0.50 -> 98).
    """
    need = max(1, int(len(eligible) * coverage))
    return [d for d in all_dates
            if sum(1 for t in eligible if traded(t, d)) >= need]


def snapshot_data_date(dated_prices, eligible, today_str,
                       quorum_min=SNAPSHOT_QUORUM_MIN, quorum_pct=SNAPSHOT_QUORUM_PCT):
    """Latest genuine trading date in the live snapshot.

    `dated_prices` is an iterable of (ticker, 'YYYY-MM-DD') for priced rows. The
    returned date is the most recent (<= today_str) on which >= max(quorum_min,
    quorum_pct * eligible) eligible names carry a price — so a lone thin session
    (a couple of Sunday-only listings) cannot advance the headline.
    """
    from collections import Counter
    elig = set(eligible)
    counts = Counter(d for t, d in dated_prices
                     if t in elig and d and d <= today_str)
    quorum = max(quorum_min, int(len(eligible) * quorum_pct))
    days = sorted(d for d, c in counts.items() if c >= quorum)
    return days[-1] if days else None


def extend_axis_for_snapshot(all_dates, price_matrix, data_date):
    """Decide whether the live-snapshot `data_date` joins the published trading axis.

    It joins ONLY if it is genuinely NEW — not already a price_matrix key. A date
    present in history but dropped by the quorum filter is a thin/partial session
    and stays GATED; re-adding it publishes a sub-quorum partial (the old
    bottleneck 06-08 bug). Mutates `all_dates` in place when the axis is extended.
    Returns the candidate inject_date (data_date) whenever it is fresher than the
    on-disk history — even when gated — so the caller can still run its own
    price-validation/quarantine against price_matrix[inject_date]; returns None
    when there is no fresher snapshot date.
    """
    last_hist = all_dates[-1] if all_dates else None
    if data_date and (last_hist is None or data_date > last_hist):
        if data_date not in price_matrix:
            price_matrix[data_date] = {}
            all_dates.append(data_date)
            all_dates.sort()
        return data_date
    return None


def sub_index_base(all_dates, eligible, traded,
                   floor=SUB_INDEX_FLOOR, coverage=SUB_COVERAGE):
    """First trading day >= the fixed `floor` with >= `coverage` eligible traded.

    The chain warms up over earlier dates; the sub-index is emitted from here.
    Coverage uses a FLOAT threshold (len(eligible) * coverage), matching the
    historical per-script behaviour. Falls back to all_dates[0] if none qualify.
    """
    need = len(eligible) * coverage
    for d in all_dates:
        if d >= floor and sum(1 for t in eligible if traded(t, d)) >= need:
            return d
    return all_dates[0] if all_dates else None


def last_bar_dates(price_matrix):
    """Ticker -> its latest bar date in a date-keyed {date: {ticker: close}} matrix."""
    last = {}
    for d in sorted(price_matrix):
        for t in price_matrix[d]:
            last[t] = d
    return last


def pending_entries(entry_dates, last_bar):
    """Admissions not yet in force: {ticker: entry date} for each ticker in
    `entry_dates` (ticker -> index_entry_date) whose price history has bars, but
    none on or after its entry date.

    A company can be admitted ahead of its entry date, so the registry change may
    merge on any day before that date. Until its price history reaches the date,
    the company stays out of the run: out of the eligible set, the weights and the
    trading-day quorum, so every output is what it would be without the admission.
    From the first run whose history has a bar on or after the date, it counts from
    that bar, as calculate_index.admission_dates describes.

    `last_bar` maps ticker -> latest bar date in the history before admission
    filtering (index_dates.last_bar_dates). A ticker with no history at all is not
    pending: calculate_index's history-key guard still stops the run for it.
    """
    return {t: d for t, d in entry_dates.items()
            if last_bar.get(t) and last_bar[t] < d}
