#!/usr/bin/env python3
"""
Robotnik — Weekly Quarantine Health Check
==========================================
Produces a markdown summary of data quality status for the past 7 days.

Output: data/quarantine/weekly_report.md
Usage:  python scripts/quarantine_health_check.py

The report is committed and served, so it lists tickers, dates, counts and
statuses only: never a fetched value, and never a rejection reason (those quote
the rejected raw value). CLAUDE.md served-data rule.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
Q_DIR = ROOT / "data" / "quarantine"
INDEX_DIR = ROOT / "data" / "index"
REGISTRY = ROOT / "data" / "registries" / "entity_registry.json"
HISTORY_DIR = ROOT / "data" / "prices" / "history"
OUTPUT = Q_DIR / "weekly_report.md"

# Threshold for the price-history staleness monitor (section 7 of the report).
# More than this many days between "yesterday" and the newest price-history
# date is flagged as a WARNING. Aligned with the 3-day freshness gate on the
# 24H return override in calculate_metrics.py so the report surfaces the
# exact condition that would start nulling 24H columns on the live page.
PRICE_HISTORY_STALENESS_DAYS = 3

now = datetime.utcnow()
week_ago = (now - timedelta(days=7)).isoformat()


def load_json(path):
    if path.exists():
        return json.load(open(path))
    return {}


def audit_price_history_staleness(threshold_days=PRICE_HISTORY_STALENESS_DAYS):
    """Scan data/prices/history/*.json and flag files whose last date is older
    than `threshold_days` before yesterday. Returns (stale_entries, summary).

    Rationale: the 24H column on the Frontier Assets page relies on a freshness
    gate in scripts/calculate_metrics.py that only fires the override when the
    last close is within 3 days of yesterday. If history goes stale beyond
    that, 24H silently nulls site-wide. This audit surfaces the condition a
    week in advance of users seeing empty columns.
    """
    if not HISTORY_DIR.exists():
        return [], {"files": 0, "stale": 0, "newest": None, "oldest": None}

    yesterday = (now.date() - timedelta(days=1))
    stale = []
    newest_seen = None
    oldest_seen = None
    count = 0

    for path in HISTORY_DIR.glob("*.json"):
        count += 1
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception:
            continue

        to_date = data.get("to")
        if not to_date:
            series = data.get("series") or []
            if series:
                to_date = max((s.get("date") for s in series if s.get("date")),
                              default=None)
        if not to_date:
            continue

        try:
            last_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
        except ValueError:
            continue

        if newest_seen is None or last_dt > newest_seen:
            newest_seen = last_dt
        if oldest_seen is None or last_dt < oldest_seen:
            oldest_seen = last_dt

        days_stale = (yesterday - last_dt).days
        if days_stale > threshold_days:
            stale.append({
                "ticker": data.get("ticker") or path.stem,
                "name": data.get("name", ""),
                "sector": data.get("sector", ""),
                "last_date": to_date,
                "days_stale": days_stale,
            })

    stale.sort(key=lambda r: (-r["days_stale"], r["ticker"]))
    summary = {
        "files": count,
        "stale": len(stale),
        "newest": newest_seen.isoformat() if newest_seen else None,
        "oldest": oldest_seen.isoformat() if oldest_seen else None,
        "yesterday": yesterday.isoformat(),
        "threshold_days": threshold_days,
    }
    return stale, summary


def main():
    lines = []
    lines.append(f"# Robotnik Data Quality — Weekly Report")
    lines.append(f"**Generated:** {now.strftime('%d-%b-%Y %H:%M UTC')}")
    lines.append(f"**Period:** {(now - timedelta(days=7)).strftime('%d-%b')} to {now.strftime('%d-%b-%Y')}")
    lines.append("")

    # ── 1. Ready for reinstatement ──
    ready = load_json(Q_DIR / "ready_for_reinstatement.json")
    lines.append("## 🟢 Ready for Reinstatement")
    if ready:
        for ticker, info in ready.items():
            lines.append(f"- **{ticker}** ({info.get('name', '')})")
            lines.append(f"  - Quarantined: {info.get('quarantine_date')}")
            lines.append(f"  - Clean fetches: {info.get('consecutive_clean_fetches')}")
            lines.append(f"  - Command: `python scripts/reinstate_quarantined.py '{ticker}'`")
    else:
        lines.append("No entities ready for reinstatement.")
    lines.append("")

    # ── 2. Reinstatement watch ──
    watch = load_json(Q_DIR / "reinstatement_watch.json")
    lines.append("## 🟡 Reinstatement Watch")
    watch_active = {k: v for k, v in watch.items() if 0 < v.get("consecutive_clean_fetches", 0) < 5}
    if watch_active:
        for ticker, info in watch_active.items():
            lines.append(f"- **{ticker}** ({info.get('name', '')}): "
                         f"{info.get('consecutive_clean_fetches')}/5 clean fetches")
    else:
        lines.append("No entities in progress toward reinstatement.")
    lines.append("")

    # ── 3. Currently quarantined (no recovery) ──
    reg = load_json(REGISTRY)
    quarantined = [(k, v) for k, v in reg.items()
                   if isinstance(v, dict) and v.get("status") == "data_quarantine"]
    lines.append("## 🔴 Currently Quarantined (No Recovery Yet)")
    if quarantined:
        for ticker, entity in quarantined:
            w = watch.get(ticker, {})
            clean = w.get("consecutive_clean_fetches", 0)
            last_status = w.get("last_fetch_status", "unknown")
            lines.append(f"- **{ticker}** ({entity.get('name', '')})")
            lines.append(f"  - Reason: {entity.get('quarantine_reason', 'N/A')}")
            lines.append(f"  - Since: {entity.get('quarantine_date', 'N/A')}")
            lines.append(f"  - Clean fetches: {clean}, last status: {last_status}")
    else:
        lines.append("No entities quarantined.")
    lines.append("")

    # ── 4. Auto-quarantine candidates ──
    candidates = load_json(Q_DIR / "auto_quarantine_candidates.json")
    lines.append("## ⚠️ Quarantine Candidates (3+ Consecutive Rejections)")
    if candidates:
        for ticker, info in candidates.items():
            # Count and status only: rejection reasons quote the rejected raw value.
            lines.append(f"- **{ticker}**: {info.get('rejection_count', '?')} rejections "
                         f"({info.get('signal') or 'rejected'})")
    else:
        lines.append("No new candidates this week.")
    lines.append("")

    # ── 5. Index-side quarantine events ──
    idx_q = load_json(Path(INDEX_DIR) / "quarantine.json")
    recent_events = [e for e in idx_q.get("history", []) if e.get("date", "") >= week_ago[:10]]
    lines.append("## 📊 Index-Side Quarantine Events This Week")
    if recent_events:
        for e in recent_events:
            lines.append(f"- {e.get('date')}: **{e.get('ticker')}** — {e.get('reason')}")
    else:
        lines.append("No index-side quarantine events this week.")
    lines.append("")

    # ── 6. Fetcher rejection summary ──
    rejections_path = Q_DIR / "fetcher_rejections.jsonl"
    lines.append("## 📋 Fetcher Rejection Summary (7 days)")
    if rejections_path.exists():
        from collections import Counter
        rejection_counts = Counter()
        with open(rejections_path) as f:
            for line in f:
                try:
                    r = json.loads(line.strip())
                    if r.get("timestamp", "") >= week_ago:
                        rejection_counts[r["ticker"]] += 1
                except:
                    continue
        if rejection_counts:
            for ticker, count in rejection_counts.most_common(20):
                lines.append(f"- **{ticker}**: {count} rejections")
        else:
            lines.append("No fetcher rejections in the past 7 days.")
    else:
        lines.append("No rejection log found.")
    lines.append("")

    # ── 7. Price-history staleness monitor ──
    stale, st_summary = audit_price_history_staleness()
    lines.append("## ⏱ Price History Staleness")
    if st_summary["files"] == 0:
        lines.append("No history files found on disk.")
    else:
        lines.append(
            f"Scanned **{st_summary['files']}** history files. "
            f"Newest last-close: **{st_summary['newest']}**. "
            f"Yesterday (UTC): **{st_summary['yesterday']}**. "
            f"Threshold: **>{st_summary['threshold_days']} days stale** (aligned "
            f"with the 24H freshness gate in `calculate_metrics.py`)."
        )
        if not stale:
            lines.append("🟢 All history files are within threshold. 24H column will render normally.")
        else:
            lines.append(
                f"🟠 **{st_summary['stale']} file(s) stale** beyond threshold. "
                f"Each of these will show `—` in the 24H column and may degrade "
                f"the 7D column if the staleness exceeds the 5-day lookback window."
            )
            # Cap output at 25 worst to keep the report readable
            for r in stale[:25]:
                lines.append(
                    f"- **{r['ticker']}** ({r['name']}) — last close "
                    f"`{r['last_date']}`, **{r['days_stale']}d stale** "
                    f"[{r['sector']}]"
                )
            if len(stale) > 25:
                lines.append(f"- _…and {len(stale) - 25} more. Run "
                             f"`python scripts/fetch_price_history.py --refresh` "
                             f"to catch up._")
    lines.append("")

    lines.append("---")
    lines.append(f"*Report generated by `scripts/quarantine_health_check.py`*")

    report = "\n".join(lines)
    with open(OUTPUT, "w") as f:
        f.write(report)

    print(f"Weekly health report written to {OUTPUT}")
    print(f"  Quarantined: {len(quarantined)}")
    print(f"  Ready for reinstatement: {len(ready)}")
    print(f"  Candidates: {len(candidates)}")
    print(f"  Stale price history files: {st_summary['stale']}/{st_summary['files']}")


if __name__ == "__main__":
    main()
