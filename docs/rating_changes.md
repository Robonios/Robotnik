# Bottleneck rating changes

Dated log of bottleneck-rating changes to the equity enrichment store
(`data/markets/enrichment_data.json`). Referenced by the forward-only rule in
[metrics_methodology.md](../data/markets/metrics_methodology.md) §3: each change
takes its new multiplier from the effective date forward, and index history is
not recalculated. The 2026-07-17 entries are the one-off exception noted there
(applied retroactively because the composite is pre-publication and the affected
history is short).

| Effective | Ticker | Old | New | Basis |
|-----------|--------|-----|-----|-------|
| 2026-07-17 | 8035 JP | MEDIUM | HIGH | ~90% global and ~100% EUV-layer share in coater-developer track, an essential lithography step with no leading-edge alternative; peak-position ruling (mid-teens revenue share does not lower the grade). Applied retroactively (one-off). |
| 2026-07-17 | MRVL | LOW | MEDIUM | #2 in the ~95% Broadcom-Marvell custom-ASIC duopoly plus optical-DSP leadership; substitution needs a silicon redesign and requalification cycle; AVGO (#1 in the same duopoly) rates MEDIUM on the same test. Applied retroactively (one-off). |
| 2026-07-25 | 4004 JP | UNRATED | MEDIUM | Genuine grade assignment for the universe's last ungraded constituent (Resonac). Peak position is back-end / advanced-packaging materials: top-three CMP slurry (copper GPX qualified at TSMC), #2 epoxy moulding compound, substitutable at a requalification cost. Forward-only (multiplier 1.0 -> 1.5 from the effective date; history not recalculated). |
