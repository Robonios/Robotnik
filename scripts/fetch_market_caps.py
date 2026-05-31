#!/usr/bin/env python3
"""
Robotnik Market Cap Fetcher
============================
Weekly fetcher for market caps — needed for Robotnik Index weighting.
Equities: yfinance (Yahoo Finance, no API key needed)
Tokens:   CoinGecko /simple/price with include_market_cap=true

Usage:
    python scripts/fetch_market_caps.py
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "index"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MCAP_JSON = DATA_DIR / "market_caps.json"
ERROR_LOG = DATA_DIR / "mcap_errors.log"

# ---------------------------------------------------------------------------
# API keys (CoinGecko only — yfinance needs no key)
# ---------------------------------------------------------------------------
def load_env():
    env_path = ROOT / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env()
COINGECKO_KEY = os.environ.get("COINGECKO_API_KEY", "")

# ---------------------------------------------------------------------------
# Import universe from fetch_prices.py
# ---------------------------------------------------------------------------
sys.path.insert(0, str(ROOT / "scripts"))
from fetch_prices import EQUITIES, TOKENS

# ---------------------------------------------------------------------------
# Yahoo Finance ticker mapping
# ---------------------------------------------------------------------------
# Map spreadsheet tickers to Yahoo Finance format
YF_OVERRIDES = {
    # Japan "XXXX JP" -> Yahoo uses XXXX.T
    # Korea "XXXXXX KS" -> Yahoo uses XXXXXX.KS
    # Taiwan -> XXXX.TW
    # HK -> XXXX.HK
    # China Shanghai C1 -> XXXXXX.SS
    # China Shenzhen C2 -> XXXXXX.SZ
    # Germany GR -> TICKER.DE
    # Switzerland SW -> TICKER.SW
    # UK LN -> TICKER.L
    # France FP -> TICKER.PA
    # Finland FH -> TICKER.HE
    # Sweden SS -> TICKER.ST
    # Norway NO -> TICKER.OL
    # Austria AV -> TICKER.VI
    # Canada CN -> TICKER.TO
    "MOG/A": "MOG-A",  # Moog Inc class A
    "HEXAB SS": "HEXA-B.ST",
    "STMPA": "STM",  # STMicro US ADR
    "MELE": "MELE.BR",
    "6488 TT": "6488.TWO",  # GlobalWafers — TPEx (emerging board), not TWSE → .TWO not .TW
    # KOSDAQ names: Bloomberg " KS" defaults to KOSPI (.KS), but these list on KOSDAQ (.KQ).
    # Without these the weekly mcap fetch returns no cap → the name silently drops from the
    # index (the B-sweep gap). Validated px*shares on each at backfill.
    "090360 KS": "090360.KQ",  # Robostar
    "098460 KS": "098460.KQ",  # Koh Young
    "108490 KS": "108490.KQ",  # Robotis
    "189300 KS": "189300.KQ",  # Intellian
    "277810 KS": "277810.KQ",  # Rainbow Robotics
    "455900 KS": "455900.KQ",  # Angel Robotics
}

def ticker_to_yahoo(ticker, country):
    """Map spreadsheet ticker to Yahoo Finance format."""
    t = ticker.strip()

    if t in YF_OVERRIDES:
        return YF_OVERRIDES[t]

    suffix_map = {
        "JP": "T", "KS": "KS", "TT": "TW", "HK": "HK",
        "C1": "SS", "C2": "SZ", "GR": "DE", "LN": "L",
        "SW": "SW", "FP": "PA", "FH": "HE", "SS": "ST",
        "NO": "OL", "AV": "VI", "CN": "TO",
        # added (B-sweep): these suffixes were unmapped → ticker_to_yahoo returned the
        # raw "TICKER CC" string → Yahoo lookup failed → no market cap → the name was
        # silently dropped from the index. AU=Australia, IM=Italy(Milan), NA=Netherlands,
        # IT=Israel(Tel Aviv, NOT Italy). Recovered Lynas/Iluka/Arafura/AMG/Avio.
        "AU": "AX", "IM": "MI", "NA": "AS", "IT": "TA",
    }

    parts = t.split()
    if len(parts) == 2:
        symbol, suffix = parts
        yf_suffix = suffix_map.get(suffix)
        if yf_suffix:
            return "{}.{}".format(symbol, yf_suffix)

    # Bare numeric tickers (TBD country)
    if t.isdigit() and len(t) >= 4:
        if len(t) == 4 and country in ("Japan", "TBD") and int(t) >= 6000:
            return "{}.T".format(t)
        if len(t) == 4 and country == "Taiwan":
            return "{}.TW".format(t)
        if t.startswith("6") or t.startswith("8"):
            return "{}.SS".format(t)  # Shanghai
        if t.startswith("0") or t.startswith("3"):
            return "{}.SZ".format(t)  # Shenzhen
        if country == "China":
            return "{}.HK".format(t)

    # US tickers (no suffix) — use as-is
    return t

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
errors = []

def log_error(ticker, msg):
    errors.append({"ticker": ticker, "error": msg})
    print("  ERROR {}: {}".format(ticker, msg))

def api_get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None

# ---------------------------------------------------------------------------
# yfinance: Fetch market caps in batches
# ---------------------------------------------------------------------------
def fetch_fx_rates():
    """Fetch approximate FX rates to USD using yfinance."""
    import yfinance as yf
    pairs = {
        "JPY": "JPYUSD=X", "KRW": "KRWUSD=X", "TWD": "TWDUSD=X",
        "HKD": "HKDUSD=X", "CNY": "CNYUSD=X", "GBP": "GBPUSD=X",
        "EUR": "EURUSD=X", "CHF": "CHFUSD=X", "SEK": "SEKUSD=X",
        "NOK": "NOKUSD=X", "DKK": "DKKUSD=X", "CAD": "CADUSD=X",
        "ILS": "ILSUSD=X", "GBp": "GBPUSD=X",  # GBp = pence
    }
    rates = {"USD": 1.0}
    for ccy, pair in pairs.items():
        try:
            t = yf.Ticker(pair)
            hist = t.history(period="1d")
            if not hist.empty:
                rate = float(hist["Close"].iloc[-1])
                rates[ccy] = rate
                if ccy == "GBp":
                    rates["GBp"] = rate / 100  # Pence to pounds to USD
        except Exception:
            pass
    print("  FX rates loaded: {}".format(len(rates)))
    return rates

def fetch_equity_mcaps():
    print("=== Fetching equity market caps via yfinance ===")
    import yfinance as yf

    # Get FX rates for currency conversion
    fx_rates = fetch_fx_rates()

    results = []
    total = len(EQUITIES)

    # Build mapping: yahoo_symbol -> (ticker, name, sector)
    yf_map = {}
    for ticker, name, sector, country in EQUITIES:
        yf_sym = ticker_to_yahoo(ticker, country)
        yf_map[yf_sym] = (ticker, name, sector)

    # Fetch in batches of 50
    yf_symbols = list(yf_map.keys())
    batch_size = 50

    for start in range(0, len(yf_symbols), batch_size):
        batch = yf_symbols[start:start + batch_size]
        batch_str = " ".join(batch)
        print("  Fetching batch {}-{} of {}...".format(
            start + 1, min(start + batch_size, len(yf_symbols)), len(yf_symbols)
        ))

        try:
            tickers_obj = yf.Tickers(batch_str)
            for yf_sym in batch:
                ticker, name, sector = yf_map[yf_sym]
                try:
                    info = tickers_obj.tickers[yf_sym].info
                    mcap = info.get("marketCap")
                    currency = info.get("currency", "USD")

                    # Convert to USD if not already.
                    # GBp FIX: Yahoo reports marketCap in the MAJOR unit (GBP
                    # pounds) even when the quote `currency` is the minor unit
                    # "GBp" (pence). Applying the pence price-rate (GBPUSD/100)
                    # to the already-pounds marketCap deflates it 100x — observed
                    # on RPI/IMI/RSW LN. Convert market cap with the major-unit
                    # rate. (Prices stay on the GBp ÷100 rate elsewhere.)
                    if mcap and mcap > 0:
                        conv_ccy = "GBP" if currency == "GBp" else currency
                        rate = fx_rates.get(conv_ccy, None)
                        if rate and conv_ccy != "USD":
                            mcap_usd = mcap * rate
                        else:
                            mcap_usd = mcap

                        results.append({
                            "ticker": ticker,
                            "name": name,
                            "sector": sector,
                            "market_cap_usd": round(mcap_usd),
                            "date_fetched": datetime.utcnow().strftime("%Y-%m-%d"),
                            "source": "Yahoo Finance",
                        })
                    else:
                        log_error(ticker, "No market cap for {} (yf: {})".format(ticker, yf_sym))
                except Exception as e:
                    log_error(ticker, "yfinance error for {}: {}".format(yf_sym, str(e)[:80]))
        except Exception as e:
            print("  Batch error: {}".format(str(e)[:100]))
            for yf_sym in batch:
                ticker, name, sector = yf_map[yf_sym]
                log_error(ticker, "Batch failed")

        time.sleep(1)  # Rate limiting between batches

    print("Equities: {}/{} market caps fetched".format(len(results), total))
    return results

# ---------------------------------------------------------------------------
# CoinGecko: Fetch market caps via /simple/price
# ---------------------------------------------------------------------------
def fetch_token_mcaps():
    print("\n=== Fetching token market caps from CoinGecko ===")
    results = []

    # TOKENS is a dict: ticker -> (coingecko_id, display_name)
    valid_tokens = []
    for ticker, (cg_id, name) in TOKENS.items():
        if cg_id:
            valid_tokens.append((ticker, name, "Token", cg_id))

    if not valid_tokens:
        print("No valid CoinGecko IDs found")
        return results

    batch_size = 50
    for start in range(0, len(valid_tokens), batch_size):
        batch = valid_tokens[start:start + batch_size]
        ids_str = ",".join(t[3] for t in batch)
        url = "https://api.coingecko.com/api/v3/simple/price?ids={}&vs_currencies=usd&include_market_cap=true".format(ids_str)
        headers = {"accept": "application/json"}
        if COINGECKO_KEY:
            headers["x-cg-demo-api-key"] = COINGECKO_KEY

        data = api_get(url, headers)
        if data is None:
            for ticker, name, _, cg_id in batch:
                log_error(ticker, "CoinGecko batch request failed")
            time.sleep(2)
            continue

        for ticker, name, sector, cg_id in batch:
            entry = data.get(cg_id, {})
            mcap = entry.get("usd_market_cap")
            if mcap and mcap > 0:
                results.append({
                    "ticker": ticker,
                    "name": name,
                    "sector": sector,
                    "market_cap_usd": mcap,
                    "date_fetched": datetime.utcnow().strftime("%Y-%m-%d"),
                    "source": "CoinGecko",
                })
            else:
                log_error(ticker, "No market cap from CoinGecko for {}".format(cg_id))

        time.sleep(1.5)

    print("Tokens: {}/{} market caps fetched".format(len(results), len(valid_tokens)))
    return results

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    equity_mcaps = fetch_equity_mcaps()
    token_mcaps = fetch_token_mcaps()
    all_mcaps = equity_mcaps + token_mcaps

    # Sort by market cap descending
    all_mcaps.sort(key=lambda x: x["market_cap_usd"], reverse=True)

    output = {
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "count": len(all_mcaps),
        "market_caps": all_mcaps,
    }

    with open(MCAP_JSON, "w") as f:
        json.dump(output, f, indent=2)
    print("\nSaved {} market caps to {}".format(len(all_mcaps), MCAP_JSON))

    # Write error log
    with open(ERROR_LOG, "w") as f:
        f.write("Market Cap Fetch Errors - {}\n".format(datetime.utcnow().isoformat()))
        f.write("=" * 60 + "\n")
        for err in errors:
            f.write("{}: {}\n".format(err["ticker"], err["error"]))
        f.write("\nTotal errors: {}\n".format(len(errors)))
    print("Errors: {} (logged to {})".format(len(errors), ERROR_LOG))

    # Print top 10
    print("\nTop 10 by market cap:")
    for i, m in enumerate(all_mcaps[:10]):
        print("  {}. {} — ${:,.0f}".format(i + 1, m["ticker"], m["market_cap_usd"]))

if __name__ == "__main__":
    main()
