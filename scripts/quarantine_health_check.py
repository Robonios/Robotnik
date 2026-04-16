#!/usr/bin/env python3
"""
Robotnik — Weekly Quarantine Health Check
==========================================
Produces a markdown summary of data quality status for the past 7 days.

Output: data/quarantine/weekly_report.md
Usage:  python scripts/quarantine_health_check.py
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
Q_DIR = ROOT / "data" / "quarantine"
INDEX_DIR = ROOT / "data" / "index"
REGISTRY = ROOT / "data" / "registries" / "entity_registry.json"
OUTPUT = Q_DIR / "weekly_report.md"

now = datetime.utcnow()
week_ago = (now - timedelta(days=7)).isoformat()


def load_json(path):
    if path.exists():
        return json.load(open(path))
    return {}


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
            lines.append(f"  - Recent USD values: {info.get('recent_values_usd', [])}")
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
            lines.append(f"- **{ticker}**: {info.get('rejection_count', '?')} rejections, "
                         f"reason: {info.get('latest_reason', 'N/A')}")
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

    lines.append("---")
    lines.append(f"*Report generated by `scripts/quarantine_health_check.py`*")

    report = "\n".join(lines)
    with open(OUTPUT, "w") as f:
        f.write(report)

    print(f"Weekly health report written to {OUTPUT}")
    print(f"  Quarantined: {len(quarantined)}")
    print(f"  Ready for reinstatement: {len(ready)}")
    print(f"  Candidates: {len(candidates)}")


if __name__ == "__main__":
    main()
