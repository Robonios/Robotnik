# MarketStack Coverage Test

Generated: `2026-05-29T15:32:42.030256Z`

## Headline

| Check | Result |
|---|---|
| Universe size | 309 |
| Resolved on MarketStack | **274 / 309 (88.7%)** |
| History sample success | 12 / 12 |
| Splits endpoint works | 6 / 6 sampled tickers |
| Dividends endpoint works | 6 / 6 sampled tickers |
| Benchmarks resolved | 6 / 6 |
| Price disagreements >2% vs EODHD | 189 |
| Total API calls used | 305 |

## Resolution by country

| Country | Resolved | Unresolved |
|---|---:|---:|
| Argentina | 1 | 0 |
| Australia | 3 | 0 |
| Austria | 0 | 1 |
| Canada | 3 | 0 |
| Chile | 1 | 0 |
| China | 13 | 10 |
| Denmark | 1 | 0 |
| Finland | 3 | 0 |
| France | 7 | 0 |
| Germany | 13 | 0 |
| Ireland | 1 | 0 |
| Israel | 3 | 0 |
| Italy | 1 | 0 |
| Japan | 43 | 2 |
| Luxembourg | 1 | 0 |
| Netherlands | 3 | 0 |
| Norway | 1 | 0 |
| South Korea | 6 | 5 |
| Sweden | 2 | 0 |
| Switzerland | 5 | 0 |
| TBD | 0 | 14 |
| Taiwan | 10 | 1 |
| United Kingdom | 5 | 0 |
| United States | 148 | 2 |

## Unresolved tickers

| Ticker | Country | MS symbol attempt | Reason |
|---|---|---|---|
| 2121 HK | China | — | marketstack_unsupported |
| 455900 KS | South Korea | — | marketstack_unsupported |
| ANDR AV | Austria | — | marketstack_unsupported |
| 9660 HK | China | — | marketstack_unsupported |
| 1274 HK | China | — | marketstack_unsupported |
| 098460 KS | South Korea | — | marketstack_unsupported |
| 2431 HK | China | — | marketstack_unsupported |
| 6600 HK | China | — | marketstack_unsupported |
| 2498 HK | China | — | marketstack_unsupported |
| 090360 KS | South Korea | — | marketstack_unsupported |
| 9880 HK | China | — | marketstack_unsupported |
| 2432 HK | China | — | marketstack_unsupported |
| 2252 HK | China | — | marketstack_unsupported |
| MOG/A | United States | — | marketstack_unsupported |
| STMPA | United States | STMPA | no_row_in_batch_response |
| 002979 | TBD | — | marketstack_unsupported |
| 600111 | TBD | — | marketstack_unsupported |
| 601100 | TBD | — | marketstack_unsupported |
| 603662 | TBD | — | marketstack_unsupported |
| 688017 | TBD | — | marketstack_unsupported |
| 6594 | TBD | — | marketstack_unsupported |
| 601689 | TBD | — | marketstack_unsupported |
| 6723 | TBD | — | marketstack_unsupported |
| 603009 | TBD | — | marketstack_unsupported |
| 003021 | TBD | — | marketstack_unsupported |
| 300100 | TBD | — | marketstack_unsupported |
| 9868 | TBD | — | marketstack_unsupported |
| 002050 | TBD | — | marketstack_unsupported |
| 002472 | TBD | — | marketstack_unsupported |
| 189300 KS | South Korea | — | marketstack_unsupported |
| 474170 KS | South Korea | — | marketstack_unsupported |
| 464A JP | Japan | — | marketstack_unsupported |
| 290A JP | Japan | — | marketstack_unsupported |
| 6488 TT | Taiwan | — | marketstack_unsupported |
| 6680 HK | China | — | marketstack_unsupported |

## Price disagreements >2% vs EODHD
These likely indicate symbology mismatches pulling the wrong instrument.

| Ticker | MS symbol | MS close | EODHD close | Delta % |
|---|---|---:|---:|---:|
| AOSL | AOSL | 49.34 | 47.89 | +3.03% |
| ARM | ARM | 335.27 | 321.22 | +4.37% |
| ASX | ASX | 40.6 | 38.95 | +4.24% |
| ALAB | ALAB | 349.17 | 318.72 | +9.55% |
| AEIS | AEIS | 317.08 | 339.65 | -6.65% |
| AMKR | AMKR | 70.58 | 73.46 | -3.92% |
| CRUS | CRUS | 174.33 | 178.3 | -2.23% |
| ENTG | ENTG | 138.44 | 142.12 | -2.59% |
| FSLR | FSLR | 303.38 | 269.95 | +12.38% |
| FORM | FORM | 130.22 | 136.48 | -4.59% |
| INDI | INDI | 5.34 | 5.07 | +5.33% |
| INTC | INTC | 120.89 | 123.52 | -2.13% |
| KOPN | KOPN | 6.05 | 5.61 | +7.84% |
| KLIC | KLIC | 104.75 | 108.57 | -3.52% |
| MTSI | MTSI | 391.09 | 409.68 | -4.54% |
| MU | MU | 923.52 | 895.88 | +3.09% |
| MKSI | MKSI | 323.41 | 334.11 | -3.20% |
| NVTS | NVTS | 28.51 | 31.79 | -10.32% |
| NVEC | NVEC | 100.865 | 96.76 | +4.24% |
| PENG | PENG | 53.21 | 54.95 | -3.17% |
| POWI | POWI | 87.07 | 84.09 | +3.54% |
| PLAB | PLAB | 34.02 | 54.44 | -37.51% |
| RMBS | RMBS | 148.02 | 157.23 | -5.86% |
| RGTI | RGTI | 27.03 | 25.065 | +7.84% |
| SKYT | SKYT | 38.97 | 37.37 | +4.28% |
| SWKS | SWKS | 81.41 | 83.42 | -2.41% |
| SYNA | SYNA | 143.26 | 147.57 | -2.92% |
| TSEM | TSEM | 275.5 | 288.53 | -4.52% |
| UMC | UMC | 22.68 | 21.08 | +7.59% |
| LASR | LASR | 79.15 | 81.57 | -2.97% |

## History sample (180-day window)

| Ticker | Country | MS symbol | Rows | First | Last |
|---|---|---|---:|---|---|
| NVDA | United States | NVDA | 123 | 2025-12-01 | 2026-05-28 |
| AAPL | United States | AAPL | 123 | 2025-12-01 | 2026-05-28 |
| LIN | United States | LIN | 123 | 2025-12-01 | 2026-05-28 |
| ASML | Netherlands | ASML.XAMS | 125 | 2025-12-01 | 2026-05-28 |
| SIE | Germany | SIE.XFRA | 117 | 2025-12-01 | 2026-05-22 |
| ABBN | Switzerland | ABBN.XSWX | 115 | 2025-12-01 | 2026-05-22 |
| 2330 | Taiwan | 2330.XTAI | 108 | 2025-12-01 | 2026-05-22 |
| 6594 | Japan | 6594.T | 116 | 2025-12-01 | 2026-05-28 |
| 012450 | South Korea | 012450.XKRX | 115 | 2025-12-01 | 2026-05-22 |
| 0700 | Hong Kong | 0700.XHKG | FAIL | — | — |
| BARC | United Kingdom | BARC.L | 116 | 2025-12-01 | 2026-05-28 |
| 000660 | South Korea | 000660.XKRX | 114 | 2025-12-01 | 2026-05-22 |

## Splits + dividends sample

| Ticker | Splits count | Dividends count |
|---|---:|---:|
| NVDA | 7 | 56 |
| AAPL | 5 | 92 |
| TSM | 14 | 45 |
| AVGO | 1 | 67 |
| AMD | 6 | 1 |
| INTC | 12 | 129 |

## Benchmarks

| Symbol | Resolved | Close | Date | Exchange |
|---|---|---:|---|---|
| SPY | yes | 754.6 | 2026-05-28 | ARCX |
| IXIC | yes | 26343.9707 | 2026-05-22 | INDX |
| URTH | yes | 204.8 | 2026-05-28 | ARCX |
| QQQ | yes | 735.58 | 2026-05-28 | XNAS |
| SOXX | yes | 569.47 | 2026-05-28 | XNAS |
| ROBO | yes | 88.92 | 2026-05-28 | ARCX |

## Errors seen

- `TRANSPORT` × 1
