#!/usr/bin/env python3
"""
Robotnik Private Capital Index (RPCI)

A monthly composite measuring activity and conviction in private-market
fundraising across the frontier technology stack (semiconductors, robotics,
space, critical materials). Sits alongside the public Robotnik Composite
Index as a structurally different signal: capital deployment flow + conviction,
not mark-to-market valuation.

METHODOLOGY (matches spec)
  Base value:  1,000.00
  Base date:   2025-03-31 (March 2025 reading == 1000.00 exact)
  Periodicity: monthly recalculation; each reading uses a 3-month trailing
               window of round data (May 2026 reading == Mar/Apr/May 2026)
  Series:
    Calibration: 2023-01 to 2023-12 (not published; establishes initial
                                     trailing-12M averages)
    Back-test:   2024-01 to 2025-03 (published as historical context)
    Live:        2025-04 onward
  Components (and weights):
    1. Capital deployed (USD)               30%
    2. Deal count                           20%
    3. Stage-weighted activity              25%
    4. Round size vs trailing 12M average   15%
    5. Investor breadth                     10%
  Stage weights for component 3:
    Pre-seed / Seed   0.7
    Series A          1.0
    Series B          1.3
    Series C+         1.6
    Growth / pre-IPO  2.0

GUARDRAILS
  1. Single-round flag: any round >5x the trailing-12M 99th percentile for
     its stage is flagged (logged + still capped at the 95th percentile)
  2. Currency check: amount_m must be either null (undisclosed) or a positive
     USD number. Per Rule 6 in monthly_ingestion_template.md, all amounts
     are normalised to USD on ingestion. Null is allowed (undisclosed-amount
     rounds still contribute to components 2/3/5).
  3. Stage label check: every round must map to one of the five canonical
     stages OR be explicitly excluded (IPO, M&A, Strategic, Debt, etc.)

Failures of guardrail 2 or 3 exit non-zero. Guardrail 1 is informational.

OUTPUT
  data/index/private_capital_index.json   (the series + components)
  data/index/private_capital_index_guardrails.log   (flagged rows)
"""

import json
import os
import sys
from datetime import datetime, timezone, date, timedelta
from collections import defaultdict, Counter
from statistics import median
import re

# ── paths ────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
ROUNDS_PATH = os.path.join(ROOT_DIR, 'data', 'funding', 'rounds.json')
INDEX_DIR = os.path.join(ROOT_DIR, 'data', 'index')
OUT_PATH = os.path.join(INDEX_DIR, 'private_capital_index.json')
GUARDRAIL_LOG = os.path.join(INDEX_DIR, 'private_capital_index_guardrails.log')

# ── methodology constants ────────────────────────────────────────────────
BASE_VALUE = 1000.0
BASE_MONTH = (2025, 3)  # March 2025; reading at this month == BASE_VALUE
BACK_TEST_START = (2024, 1)  # First published month

WEIGHTS = {
    'capital_deployed': 0.30,
    'deal_count': 0.20,
    'stage_weighted_activity': 0.25,
    'round_size_vs_trailing': 0.15,
    'investor_breadth': 0.10,
}

STAGE_WEIGHTS = {
    'Pre-seed / Seed': 0.7,
    'Series A': 1.0,
    'Series B': 1.3,
    'Series C+': 1.6,
    'Growth / pre-IPO': 2.0,
}

# Map raw round labels (the canonical 37-value enum in the ingestion
# template) to the five RPCI stages. Anything not in this map and not in
# EXCLUDED_ROUNDS triggers guardrail 3.
STAGE_MAP = {
    'Pre-Seed':                'Pre-seed / Seed',
    'Pre-Seed (extension)':    'Pre-seed / Seed',
    'Seed':                    'Pre-seed / Seed',
    'Seed (extension)':        'Pre-seed / Seed',
    'Seed+':                   'Pre-seed / Seed',
    'Seed II':                 'Pre-seed / Seed',
    'Pre-Series A':            'Pre-seed / Seed',
    'Series A':                'Series A',
    'Series A (extension)':    'Series A',
    'Pre-Series B':            'Series A',
    'Series B':                'Series B',
    'Series B2':               'Series B',
    'Series B (extension)':    'Series B',
    'Series B Extension':      'Series B',
    'Pre-Series C':            'Series B',
    'Series C':                'Series C+',
    'Series C (extension)':    'Series C+',
    'Series D':                'Series C+',
    'Series D (extension)':    'Series C+',
    'Series E':                'Series C+',
    'Series E (extension)':    'Series C+',
    'Series E+':               'Series C+',
    'Series F':                'Series C+',
    'Series F (extension)':    'Series C+',
    'Series G':                'Series C+',
    'Series G (extension)':    'Series C+',
    'Series H':                'Series C+',
    'Series H (extension)':    'Series C+',
    'Pre-IPO':                 'Growth / pre-IPO',
    'IPO (filed)':             'Growth / pre-IPO',  # company still private at filing
}

# Rounds explicitly excluded from RPCI (not private equity venture rounds).
# These are flagged-but-expected per guardrail 3 — logged but don't error.
EXCLUDED_ROUNDS = {
    'IPO',                  # listing event (public market)
    'M&A',                  # exit
    'Strategic',            # stage-ambiguous; revisit later
    'Government investment',
    'Government',
    'Grant',
    'Debt Financing',
    'Bridge',               # stage-ambiguous
    'Undisclosed',
    'Other',
    '',                     # blank
}

# Guardrail 1 threshold: any single round >5x the trailing 12M 99th percentile
# at its stage gets flagged (still capped at 95th percentile per methodology).
GUARDRAIL_MULTIPLIER = 5.0
CAP_PERCENTILE = 95

# New-investor multiplier for component 5
NEW_INVESTOR_MULTIPLIER = 1.25
NEW_INVESTOR_LOOKBACK_MONTHS = 24

# ── utilities ────────────────────────────────────────────────────────────

def parse_date(s):
    return datetime.strptime(s, '%Y-%m-%d').date()


def month_tuple(d):
    return (d.year, d.month)


def months_back(year, month, n):
    """Return (year, month) n months before given (year, month)."""
    total = year * 12 + (month - 1) - n
    return total // 12, (total % 12) + 1


def month_end(year, month):
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def window_3m(year, month):
    """3-month window ending at month M (inclusive). Returns (start, end) dates."""
    sy, sm = months_back(year, month, 2)
    return date(sy, sm, 1), month_end(year, month)


def trailing_12m(year, month):
    """12-month window ending immediately BEFORE the 3M window starts.

    Using PRIOR-12M rather than inclusive-of-current-window is required for
    the cap to actually bite: if a mega-round is included in its own
    reference distribution, the 95th-percentile cap moves with the round and
    no longer constrains it. The spec's stated intent — 'prevent single-
    round skew' — is only achieved by an exogenous trailing reference."""
    win_start, _ = window_3m(year, month)
    prior_end = win_start - timedelta(days=1)
    sy, sm = months_back(prior_end.year, prior_end.month, 11)
    return date(sy, sm, 1), prior_end


def prior_24m(year, month):
    """24-month period ending immediately BEFORE the 3-month window's start.
    Used for the investor-freshness check in component 5."""
    win_start, _ = window_3m(year, month)
    lookback_end = win_start - timedelta(days=1)
    sy, sm = months_back(lookback_end.year, lookback_end.month, NEW_INVESTOR_LOOKBACK_MONTHS - 1)
    return date(sy, sm, 1), lookback_end


def percentile(values, pct):
    """Inclusive percentile (pct in [0, 100])."""
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def parse_investors(s):
    """Comma-separated string with paren-depth handling. Matches the
    parsing convention used in js/nav.js + js/funding.js for consistency
    with downstream Top Investor counts."""
    if not s:
        return []
    out, buf, depth = [], '', 0
    for ch in s:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth = max(0, depth - 1)
        if ch == ',' and depth == 0:
            name = buf.strip()
            if name and name.lower() not in {'n/d', 'undisclosed', 'multiple', 'various', 'chinese vcs', 'not disclosed'}:
                out.append(name)
            buf = ''
        else:
            buf += ch
    name = buf.strip()
    if name and name.lower() not in {'n/d', 'undisclosed', 'multiple', 'various', 'chinese vcs', 'not disclosed'}:
        out.append(name)
    return out


def in_range(d, start, end):
    return start <= d <= end


# ── data loading + classification ────────────────────────────────────────

def load_and_classify(rounds_path):
    """Load rounds.json and classify each row.

    Returns (rounds, guardrail_messages) where rounds is a list of dicts
    with: date (datetime.date), amount_m (float|None), stage (str|None),
    investors (list[str]), entity_id (str), company (str), excluded (bool).
    """
    with open(rounds_path) as f:
        data = json.load(f)

    rounds_out = []
    msgs = []
    excluded_count = Counter()
    unmappable_rows = []

    for r in data['rounds']:
        raw_date = r.get('date', '')
        if not raw_date:
            msgs.append(f"  SKIP no-date row: {r.get('entity_id')} / {r.get('company')}")
            continue
        try:
            d = parse_date(raw_date)
        except ValueError:
            msgs.append(f"  SKIP bad-date row: {r.get('entity_id')} date={raw_date}")
            continue

        raw_round = (r.get('round') or '').strip()
        amount_m = r.get('amount_m')
        if amount_m is not None:
            try:
                amount_m = float(amount_m)
                if amount_m < 0:
                    msgs.append(f"  SKIP negative-amount row: {r.get('company')} {raw_date} amount={amount_m}")
                    continue
            except (TypeError, ValueError):
                msgs.append(f"  SKIP non-numeric amount: {r.get('company')} {raw_date} amount={r.get('amount_m')}")
                continue

        # Stage classification
        if raw_round in STAGE_MAP:
            stage = STAGE_MAP[raw_round]
            excluded = False
        elif raw_round in EXCLUDED_ROUNDS:
            stage = None
            excluded = True
            excluded_count[raw_round] += 1
        else:
            # Guardrail 3 violation: unmappable stage
            stage = None
            excluded = True
            unmappable_rows.append((r.get('company'), raw_date, raw_round))

        investors = parse_investors(r.get('lead_investors') or '') + parse_investors(r.get('co_investors') or '')
        # Deduplicate per round (an investor appearing in both lead and co
        # for the same round still counts once, per the funding.js convention)
        investors = list(dict.fromkeys(investors))

        rounds_out.append({
            'date': d,
            'amount_m': amount_m,
            'raw_round': raw_round,
            'stage': stage,
            'excluded': excluded,
            'investors': investors,
            'entity_id': r.get('entity_id'),
            'company': r.get('company'),
        })

    # Guardrail 3 summary
    msgs.append(f"\n[GUARDRAIL 3] Stage-label classification:")
    msgs.append(f"  Total rounds: {len(rounds_out)}")
    msgs.append(f"  Mapped to RPCI stages: {sum(1 for r in rounds_out if not r['excluded'])}")
    msgs.append(f"  Excluded (out-of-scope round types): {sum(excluded_count.values())}")
    for round_name, ct in excluded_count.most_common():
        msgs.append(f"    - {round_name}: {ct}")

    if unmappable_rows:
        msgs.append(f"\n[GUARDRAIL 3 FAILURE] {len(unmappable_rows)} rounds with unmappable stage labels:")
        for c, dt, rnd in unmappable_rows:
            msgs.append(f"    - {c} {dt} round='{rnd}'")
        return rounds_out, msgs, False  # signal failure
    return rounds_out, msgs, True


# ── component calculation ────────────────────────────────────────────────

def compute_components(year, month, all_rounds, msgs):
    """Compute the five raw component values for the monthly reading at
    (year, month) using a 3-month trailing window."""
    w_start, w_end = window_3m(year, month)
    t_start, t_end = trailing_12m(year, month)
    p_start, p_end = prior_24m(year, month)

    window_rounds = [r for r in all_rounds
                     if in_range(r['date'], w_start, w_end) and not r['excluded']]
    trailing_rounds = [r for r in all_rounds
                       if in_range(r['date'], t_start, t_end) and not r['excluded']]
    prior_rounds = [r for r in all_rounds
                    if in_range(r['date'], p_start, p_end) and not r['excluded']]

    # ─── trailing-12M reference values per stage (used by components 1 + 4)
    trailing_by_stage = defaultdict(list)
    for r in trailing_rounds:
        if r['amount_m'] is not None:
            trailing_by_stage[r['stage']].append(r['amount_m'])

    stage_cap = {stage: percentile(amts, CAP_PERCENTILE)
                 for stage, amts in trailing_by_stage.items()}
    stage_99 = {stage: percentile(amts, 99)
                for stage, amts in trailing_by_stage.items()}
    stage_median = {stage: median(amts) if amts else None
                    for stage, amts in trailing_by_stage.items()}

    # ─── 1. Capital deployed (with per-stage 95th-percentile cap)
    capital_deployed = 0.0
    flagged_rows = []
    for r in window_rounds:
        if r['amount_m'] is None:
            continue
        amt = r['amount_m']
        cap = stage_cap.get(r['stage'])
        p99 = stage_99.get(r['stage'])
        # Guardrail 1: flag rounds >5x the 99th percentile for the stage
        if p99 is not None and p99 > 0 and amt > GUARDRAIL_MULTIPLIER * p99:
            flagged_rows.append(
                f"  [GUARDRAIL 1] month={year}-{month:02d} {r['company']} {r['date']} "
                f"stage={r['stage']} amount=${amt:.0f}M trailing-99th=${p99:.0f}M "
                f"({amt/p99:.1f}x); CAPPED at ${cap:.0f}M"
            )
        applied = min(amt, cap) if cap is not None else amt
        capital_deployed += applied
    if flagged_rows:
        msgs.append(f"\n[GUARDRAIL 1] {len(flagged_rows)} round(s) flagged in {year}-{month:02d}:")
        msgs.extend(flagged_rows)

    # ─── 2. Deal count (includes undisclosed-amount rounds)
    deal_count = len(window_rounds)

    # ─── 3. Stage-weighted activity
    stage_weighted = 0.0
    for r in window_rounds:
        stage_weighted += STAGE_WEIGHTS.get(r['stage'], 0)

    # ─── 4. Round size vs trailing 12M median (per-stage), averaged
    ratios = []
    for r in window_rounds:
        if r['amount_m'] is None:
            continue
        median_at_stage = stage_median.get(r['stage'])
        if median_at_stage is None or median_at_stage == 0:
            continue
        ratios.append(r['amount_m'] / median_at_stage)
    avg_ratio = sum(ratios) / len(ratios) if ratios else 0

    # ─── 5. Investor breadth (with new-investor multiplier)
    investors_in_window = set()
    for r in window_rounds:
        investors_in_window.update(r['investors'])
    investors_in_prior_24m = set()
    for r in prior_rounds:
        investors_in_prior_24m.update(r['investors'])

    returning = sum(1 for inv in investors_in_window if inv in investors_in_prior_24m)
    new = sum(1 for inv in investors_in_window if inv not in investors_in_prior_24m)
    investor_breadth = returning + NEW_INVESTOR_MULTIPLIER * new

    return {
        'capital_deployed': capital_deployed,
        'deal_count': float(deal_count),
        'stage_weighted_activity': stage_weighted,
        'round_size_vs_trailing': avg_ratio,
        'investor_breadth': investor_breadth,
        '_raw_dealcount': deal_count,
        '_raw_capital_usd': capital_deployed * 1_000_000,
        '_window': (w_start.isoformat(), w_end.isoformat()),
    }


# ── orchestration ────────────────────────────────────────────────────────

def iter_months(start_y, start_m, end_y, end_m):
    y, m = start_y, start_m
    while (y, m) <= (end_y, end_m):
        yield y, m
        m += 1
        if m > 12:
            m, y = 1, y + 1


def main():
    msgs = [f"Robotnik Private Capital Index — guardrail log",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            f"Source: {os.path.relpath(ROUNDS_PATH, ROOT_DIR)}",
            ""]

    rounds, classification_msgs, ok = load_and_classify(ROUNDS_PATH)
    msgs.extend(classification_msgs)
    if not ok:
        msgs.append("\n*** EXIT NON-ZERO: guardrail 3 (unmappable stages) failed. ***")
        os.makedirs(INDEX_DIR, exist_ok=True)
        with open(GUARDRAIL_LOG, 'w') as f:
            f.write('\n'.join(msgs))
        print('\n'.join(msgs[-20:]))
        sys.exit(1)

    # Determine the latest month present in the data
    max_date = max(r['date'] for r in rounds)
    end_y, end_m = max_date.year, max_date.month

    # Compute raw components for every month in the published range
    raw_series = {}  # (year, month) -> components dict
    for y, m in iter_months(BACK_TEST_START[0], BACK_TEST_START[1], end_y, end_m):
        raw_series[(y, m)] = compute_components(y, m, rounds, msgs)

    # The normalisation reference is March 2025
    if BASE_MONTH not in raw_series:
        msgs.append(f"\n*** EXIT NON-ZERO: base month {BASE_MONTH} missing from series. ***")
        with open(GUARDRAIL_LOG, 'w') as f:
            f.write('\n'.join(msgs))
        sys.exit(1)
    base = raw_series[BASE_MONTH]
    base_for_norm = {k: base[k] for k in WEIGHTS}
    msgs.append(f"\n[BASE] March 2025 raw components used as normalisation reference:")
    for k, v in base_for_norm.items():
        msgs.append(f"  {k}: {v:.4f}")

    # Normalise each component to 1000 at base, weight, sum
    series_out = []
    composite_values = []
    for (y, m) in sorted(raw_series.keys()):
        raw = raw_series[(y, m)]
        normalised = {}
        composite = 0.0
        for comp, w in WEIGHTS.items():
            base_val = base_for_norm[comp]
            if base_val == 0:
                norm = 0.0
            else:
                norm = (raw[comp] / base_val) * BASE_VALUE
            normalised[comp] = round(norm, 4)
            composite += w * norm
        composite_values.append(composite)
        series_out.append({
            'month': f"{y}-{m:02d}",           # spec schema field
            'month_key': f"{y}-{m:02d}",       # backward-compat duplicate
            'year': y,
            'month_num': m,
            'window_start': raw['_window'][0],
            'window_end': raw['_window'][1],
            'value': round(composite, 4),
            'components': normalised,
            'deal_count_raw': raw['_raw_dealcount'],
            'capital_deployed_raw_usd': round(raw['_raw_capital_usd'], 2),
        })

    # 3-month trailing smoothed line
    for i, row in enumerate(series_out):
        recent = composite_values[max(0, i - 2):i + 1]
        row['value_3m_trailing'] = round(sum(recent) / len(recent), 4)

    # Verify March 2025 == 1000.00 exact (acceptance criterion)
    march_2025 = next(r for r in series_out if r['month'] == '2025-03')
    msgs.append(f"\n[ACCEPTANCE] March 2025 composite = {march_2025['value']}")
    if round(march_2025['value'], 2) != 1000.00:
        msgs.append(f"*** FAIL: March 2025 composite is not 1000.00; got {march_2025['value']}.")
        with open(GUARDRAIL_LOG, 'w') as f:
            f.write('\n'.join(msgs))
        sys.exit(1)
    msgs.append("[ACCEPTANCE] OK — March 2025 = 1000.00 exact.")

    # Per-month component decomposition check: weighted sum equals composite
    decomp_errors = []
    for row in series_out:
        check = sum(WEIGHTS[c] * row['components'][c] for c in WEIGHTS)
        if abs(check - row['value']) > 0.01:
            decomp_errors.append(f"  {row['month']}: composite={row['value']} weighted_sum={round(check,4)}")
    if decomp_errors:
        msgs.append(f"\n*** WARN: composite ≠ weighted sum at:")
        msgs.extend(decomp_errors)
    else:
        msgs.append("[ACCEPTANCE] OK — components sum correctly at every month.")

    # Compose output JSON
    latest = series_out[-1]
    out = {
        'index_name': 'Robotnik Private Capital Index',
        'index_code': 'RPCI',
        'base_date': '2025-03-31',
        'base_value': BASE_VALUE,
        'fetched_at': datetime.now(timezone.utc).isoformat(),
        'method': '5-component composite, 3M trailing window, monthly recalc',
        'components': {
            'capital_deployed': {
                'weight': WEIGHTS['capital_deployed'],
                'description': 'USD capital deployed in 3M window, per-round cap at trailing 12M 95th-percentile by stage'
            },
            'deal_count': {
                'weight': WEIGHTS['deal_count'],
                'description': 'Count of all rounds in 3M window (includes undisclosed-amount rounds)'
            },
            'stage_weighted_activity': {
                'weight': WEIGHTS['stage_weighted_activity'],
                'description': 'Sum of (count at stage × stage weight) across 3M window',
                'stage_weights': STAGE_WEIGHTS,
            },
            'round_size_vs_trailing': {
                'weight': WEIGHTS['round_size_vs_trailing'],
                'description': 'Average ratio of (round size / trailing 12M median at same stage) across window'
            },
            'investor_breadth': {
                'weight': WEIGHTS['investor_breadth'],
                'description': f'Unique investor count in 3M window; new-in-{NEW_INVESTOR_LOOKBACK_MONTHS}M investors weighted {NEW_INVESTOR_MULTIPLIER}x'
            },
        },
        'current_month': latest['month_key'],
        'current_value': latest['value'],
        'current_value_3m_trailing': latest['value_3m_trailing'],
        'series': series_out,
    }

    os.makedirs(INDEX_DIR, exist_ok=True)
    with open(OUT_PATH, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"-> {os.path.relpath(OUT_PATH, ROOT_DIR)}")
    print(f"   {len(series_out)} months, base {BASE_VALUE} @ {out['base_date']}, "
          f"current {latest['value']} @ {latest['month_key']}")

    with open(GUARDRAIL_LOG, 'w') as f:
        f.write('\n'.join(msgs))
    print(f"-> {os.path.relpath(GUARDRAIL_LOG, ROOT_DIR)}")


if __name__ == '__main__':
    main()
