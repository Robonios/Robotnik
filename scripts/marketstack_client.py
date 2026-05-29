#!/usr/bin/env python3
"""
MarketStack API client — parallel to the EODHD adapter
=======================================================
Stdlib-only client for the MarketStack v1 API (api.marketstack.com).
Mirrors the EODHD fetch interface so downstream callers can be switched
between vendors by import substitution rather than rewriting per-call sites.

Reference: https://marketstack.com/documentation (redirects to docs.apilayer.com)

Auth: query parameter `access_key` (single API key, no expiry header).
Pagination: `?limit=N&offset=N`. Pro tier max limit per call = 1000.
Error envelope: `{"error": {"code": "...", "message": "..."}}` with HTTP 4xx/5xx.

Symbology:
  US tickers       — bare symbol: `AAPL`, `NVDA`
  International    — `SYMBOL.MIC`: `005930.XKRX`, `7203.XTKS`, `ASML.XAMS`
  Indices          — varies; we fall back to ETF proxies (SPY, QQQ, URTH) for
                     consistency with the existing benchmark set.

The MIC table here covers the countries present in our universe and follows
ISO 10383. Unverified entries are flagged so the coverage test surfaces them.

Constraints:
  - The API key MUST be supplied via the MARKETSTACK_API_KEY env var.
    fail_loudly_if_missing() raises at first use if absent.
  - Never log or persist the key. Never write it to disk.
  - Honour MarketStack's call quota — the project budget is the Professional
    100k-calls/month plan, and the call counter helper here lets each driver
    print its own pass-level usage at completion for observability.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Reuse the project-standard .env loader so we don't drift from the established
# pattern (EODHD/COINGECKO fetchers use config.load_env()).
from config import load_env

# ── config ───────────────────────────────────────────────────────────────
API_VERSION = "v1"   # Default. Specific countries override via COUNTRY_TO_API_VERSION.
BASE_URL_FMT = "https://api.marketstack.com/{}"
USER_AGENT = "Robotnik/1.0"
DEFAULT_TIMEOUT = 30
PAGE_LIMIT_MAX = 1000     # Professional tier max per page
INTER_CALL_SLEEP = 0.05   # 50ms ≈ 20 req/sec, comfortably under any tier's burst cap

# Rate-limit retry — MarketStack returns rate_limit_reached when burst-rate
# is hit even within monthly quota. Exponential backoff per attempt.
RATE_LIMIT_RETRY_MAX = 3
RATE_LIMIT_BACKOFF_SECONDS = [1.0, 3.0, 10.0]  # try after 1s, 3s, 10s

# Vendor-driven per-country routing — these are constraints surfaced by live
# probing, NOT design preferences:
#   - Tokyo: V1 returns "data not available, try V2" for ALL Tokyo tickers
#     regardless of suffix. V2 + .T works; V2 + .XTKS does not. So Japan must
#     route to V2 with the .T (Yahoo-style) suffix.
#   - Germany: V1 + .XFRA works; V1 + .XETR fails; V2 + .DE returns close=null.
#     So Germany must stay on V1 with .XFRA. CANNOT migrate full V2.
#   - LSE: V1 + .XLON fails for several names ("data not available"); V2 + .L
#     works. So UK routes to V2 with the .L (Yahoo-style) suffix.
# Full V2 migration is therefore NOT viable — selective routing is forced.
COUNTRY_TO_API_VERSION = {
    "Japan":          "v2",
    "United Kingdom": "v2",
    "Australia":      "v2",   # All 3 ASX tickers (LYC/ILU/ARU) require V2 + .AX (Round 3)
}

# ── ISO 10383 MIC mapping for the Robotnik universe ─────────────────────
# Country tag in fetch_prices.EQUITIES → MarketStack MIC suffix.
# Empty string = bare US symbol with no suffix.
# Entries marked UNVERIFIED haven't been confirmed against the live API and
# are flagged in the coverage test for review.
COUNTRY_TO_MIC = {
    "United States":     "",
    "USA":               "",
    "US":                "",
    "United Kingdom":    "L",        # LSE on V2 — XLON fails on V1 for many names
    "UK":                "L",
    "Germany":           "XFRA",     # Frankfurt Börse — V1+.XFRA works; .XETR and V2 both fail

    "France":            "XPAR",     # Euronext Paris
    "Netherlands":       "XAMS",     # Euronext Amsterdam
    "Switzerland":       "XSWX",     # SIX Swiss Exchange
    "Sweden":            "XSTO",     # Nasdaq Stockholm
    "Norway":            "XOSL",     # Oslo Børs
    "Denmark":           "XCSE",     # Nasdaq Copenhagen
    "Finland":           "XHEL",     # Nasdaq Helsinki
    "Italy":             "XMIL",     # Borsa Italiana
    "Israel":            "XTAE",     # Tel Aviv Stock Exchange
    "Japan":             "T",        # Tokyo — V2 endpoint + Yahoo-style .T suffix (XTKS fails on both V1 and V2)
    "South Korea":       "XKRX",     # Korea Exchange (KOSPI)
    "Korea":             "XKRX",
    "Taiwan":            "XTAI",     # Taiwan Stock Exchange
    "Hong Kong":         "XHKG",
    "China":             "XSHG",     # Shanghai (6xxxxx); ticker_to_marketstack routes 00xxxx/30xxxx to XSHE
    "Australia":         "AX",       # Yahoo-style on V2 — .XASX fails on both v1 and v2 per Round 3 probe
    "Canada":            "XTSE",     # Toronto Stock Exchange — UNVERIFIED
    "Singapore":         "XSES",     # UNVERIFIED
    "India":             "XBOM",     # BSE — UNVERIFIED, may need XNSE for NSE
    "Austria":           "XWBO",     # Wiener Börse — UNVERIFIED
    "Ireland":           "XDUB",     # Euronext Dublin — UNVERIFIED
    "Luxembourg":        "XLUX",     # UNVERIFIED
    "Argentina":         "XBUE",     # Buenos Aires Stock Exchange — UNVERIFIED
    "Chile":             "XSGO",     # Santiago Stock Exchange — UNVERIFIED
    "TBD":               None,       # Sentinel: caller logs and skips (no coverage attempt)
}

# ── error taxonomy ───────────────────────────────────────────────────────
class MarketStackError(Exception):
    """Base — every MarketStack-side failure inherits from this."""


class MissingKeyError(MarketStackError):
    """MARKETSTACK_API_KEY is not present in the environment."""


class AuthError(MarketStackError):
    """API key rejected (invalid, expired, or insufficient tier)."""


class RateLimitError(MarketStackError):
    """Quota exceeded or burst-rate hit."""


class UnknownSymbolError(MarketStackError):
    """Ticker doesn't resolve on MarketStack — caller decides null vs retry."""


class TransportError(MarketStackError):
    """Network/HTTP failure not classified above."""


# ── key handling ─────────────────────────────────────────────────────────
_KEY_CACHE = None


def get_api_key() -> str:
    """Resolve MARKETSTACK_API_KEY from env. Raises MissingKeyError if absent.

    Cached after first lookup. Never logged or persisted by this module.
    """
    global _KEY_CACHE
    if _KEY_CACHE is not None:
        return _KEY_CACHE
    load_env()   # idempotent — config.load_env populates os.environ from .env
    key = os.environ.get("MARKETSTACK_API_KEY", "").strip()
    if not key:
        raise MissingKeyError(
            "MARKETSTACK_API_KEY not set. Export it locally or add to the "
            "GitHub secret of the same name. Never hard-code or commit."
        )
    _KEY_CACHE = key
    return key


# ── call accounting (per-process counter for observability) ──────────────
_CALL_COUNTER = {"count": 0}


def call_count() -> int:
    return _CALL_COUNTER["count"]


def _bump_call_count():
    _CALL_COUNTER["count"] += 1


# ── low-level HTTP ───────────────────────────────────────────────────────
def _api_get(path: str, params: dict, timeout: int = DEFAULT_TIMEOUT,
             version: str = None) -> dict:
    """Make a GET against /{version}/{path} with auth + params.

    Returns the parsed JSON dict (NOT the .data array directly — callers can
    inspect pagination). Raises a typed MarketStackError on any failure.

    `version` defaults to `API_VERSION` (v1); pass "v2" for Tokyo. The country
    routing happens at the caller layer (fetch_eod_latest etc.) — see
    `country_api_version()`.

    Includes automatic exponential-backoff retry on RateLimitError — burst-
    rate limits are common during full-universe sweeps and shouldn't cause
    per-ticker failure when a short wait would clear them.

    Also normalises response symbols to their canonical "SYMBOL.MIC" form
    where MarketStack strips the MIC suffix on output — that quirk would
    otherwise leak into every call site as defensive lookup logic.
    """
    last_rate_limit = None
    for attempt in range(RATE_LIMIT_RETRY_MAX + 1):
        try:
            return _api_get_once(path, params, timeout, version)
        except RateLimitError as e:
            last_rate_limit = e
            if attempt >= RATE_LIMIT_RETRY_MAX:
                break
            delay = RATE_LIMIT_BACKOFF_SECONDS[min(attempt, len(RATE_LIMIT_BACKOFF_SECONDS) - 1)]
            time.sleep(delay)
    # Exhausted retries
    raise last_rate_limit


def _api_get_once(path: str, params: dict, timeout: int, version) -> dict:
    """Single-attempt API call. Wrapped by _api_get for retry-on-rate-limit."""
    params = {**params, "access_key": get_api_key()}
    qs = urllib.parse.urlencode(params, safe=",")
    base = BASE_URL_FMT.format(version or API_VERSION)
    url = "{}/{}?{}".format(base, path.lstrip("/"), qs)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode()
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        _bump_call_count()
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {}
        _raise_for_error_body(e.code, parsed)
    except urllib.error.URLError as e:
        raise TransportError("URL error contacting MarketStack: {}".format(e))
    except Exception as e:  # socket timeout, connection reset, etc.
        raise TransportError("Transport failure: {}".format(e))

    _bump_call_count()
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        raise TransportError("Non-JSON response from MarketStack: {}".format(e))

    if isinstance(data, dict) and "error" in data:
        _raise_for_error_body(200, data)
    return _normalise_response_symbols(data, params.get("symbols"))


def _normalise_response_symbols(data: dict, requested_symbols) -> dict:
    """Stitch MIC suffixes back onto response rows when MarketStack strips them.

    MarketStack returns `symbol` as the bare ticker even when queried with a
    MIC suffix (e.g. requested `005930.XKRX`, returned `005930`). Callers
    expect to look up rows by the symbol they asked for, so we restore the
    canonical form here once instead of at every call site.
    """
    if not isinstance(data, dict) or not data.get("data") or not requested_symbols:
        return data
    requested = {}
    for s in str(requested_symbols).split(","):
        s = s.strip()
        if "." in s:
            requested[s.split(".", 1)[0]] = s
    if not requested:
        return data
    for row in data["data"]:
        bare = row.get("symbol")
        if bare in requested:
            row["symbol"] = requested[bare]
    return data


def _raise_for_error_body(http_code: int, parsed: dict):
    """Classify MarketStack's error envelope into our typed exceptions.

    Error envelope shape (confirmed live against /v1/eod):
        {"error": {"code": "invalid_access_key", "message": "..."}}
    """
    err = (parsed.get("error") if isinstance(parsed, dict) else None) or {}
    code = (err.get("code") or "").lower()
    msg  = err.get("message") or "HTTP {}".format(http_code)
    if code in ("invalid_access_key", "missing_access_key", "inactive_user",
                "invalid_api_function", "https_access_restricted"):
        raise AuthError("{}: {}".format(code, msg))
    if code in ("usage_limit_reached", "rate_limit_reached", "monthly_limit_reached",
                "function_access_restricted"):
        raise RateLimitError("{}: {}".format(code, msg))
    if code in ("no_results_found", "invalid_symbol", "symbol_not_supported"):
        raise UnknownSymbolError("{}: {}".format(code, msg))
    raise TransportError("HTTP {} — {}: {}".format(http_code, code or "unknown", msg))


# ── symbology ────────────────────────────────────────────────────────────
def country_api_version(country: str) -> str:
    """Return the API version a given country must use.

    Vendor-driven routing — see COUNTRY_TO_API_VERSION block above for the
    constraints. Defaults to API_VERSION (v1) when not overridden.

    For ticker-aware routing (per-ticker overrides may force a different
    version than the country default), use `route_for_ticker()` instead.
    """
    return COUNTRY_TO_API_VERSION.get((country or "").strip(), API_VERSION)


def route_for_ticker(ticker: str, country: str):
    """Single-call routing helper that returns (symbol, version, supported).

    Encodes all the routing precedence: unsupported short-circuit → per-ticker
    override (forces V1) → US ADR override → Hong Kong auto-detect → country
    default. Callers should prefer this over calling ticker_to_marketstack()
    and country_api_version() separately when both are needed at once.

    Returns:
        (symbol, version, supported) where:
          - symbol is the MarketStack symbol to query, or "UNAVAILABLE"
          - version is "v1" or "v2"
          - supported is False when the ticker is in MARKETSTACK_UNSUPPORTED
    """
    if ticker in MARKETSTACK_UNSUPPORTED:
        return "UNAVAILABLE", API_VERSION, False
    if ticker in TICKER_OVERRIDES:
        sym, ver = TICKER_OVERRIDES[ticker]
        return sym, ver, True
    sym = ticker_to_marketstack(ticker, country)
    ver = country_api_version(country)
    return sym, ver, sym != "UNAVAILABLE"


# ── per-ticker overrides (live-probe verified — see Round 2 findings) ────
# Sources of these overrides:
#   TICKER_OVERRIDES — primary listing is stale or wrong-instrument on MarketStack;
#                      Frankfurt cross-listing carries fresh data for the same
#                      underlying entity.
#   US_ADR_OVERRIDES — registry tags by parent country but the actual MarketStack
#                      listing is a bare US ADR on NYSE/Nasdaq.
#   MARKETSTACK_UNSUPPORTED — symbol confirmed absent from MarketStack's catalog
#                              (HK post-2023 IPOs, KOSDAQ, TPEx). Route to Yahoo
#                              via data_source_overrides.json instead.

TICKER_OVERRIDES = {
    # Each value is (symbol, api_version). Per-ticker version overrides because
    # the country default doesn't always match the working endpoint — Frankfurt
    # cross-listings stay on V1, while several V2-only symbol formats (.ST, .PA,
    # .BR, .HE, .AX) need to override V1-default countries.

    # Frankfurt cross-listings — V1; native exchange data is stale on MarketStack
    "IMI LN":   ("IMI1.XFRA",  "v1"),  # XLON frozen at 2023-10-18
    "AVIO IM":  ("2ZP.XFRA",   "v1"),  # XMIL frozen at 2023-04-18
    "OVZON SS": ("OVZ.XFRA",   "v1"),  # XSTO frozen at 2023-10-18
    "AMG NA":   ("ADG.XFRA",   "v1"),  # AMG.XAMS silently returns NYSE AMG Inc (wrong instrument)
    "HIAB FH":  ("C1C1.XFRA",  "v1"),  # XHEL not in MS catalogue; Frankfurt cross-listing works
    "SHA":      ("SHA0.XETRA", "v1"),  # Schaeffler — registry mis-tags US; German on Frankfurt
    "MOG.A":    ("MOG-A",      "v1"),  # NYSE convention for class-share — Yahoo-style dash

    # V2 + Yahoo-style suffix on countries that default to V1 — vendor-driven
    "GOMX SS":  ("GOMX.ST",    "v2"),  # GomSpace — Swedish (not Danish per registry); XSTO frozen, .ST on V2 fresh
    "SESG FP":  ("SESG.PA",    "v2"),  # SES SA — Luxembourg-domiciled but Euronext Paris on V2
    "MELE":     ("MELE.BR",    "v2"),  # Melexis — Belgian (registry mis-tags US); Euronext Brussels on V2
    "HEXAB SS": ("HEXA-B.ST",  "v2"),  # Hexagon AB Class B — Yahoo-style dash on V2
    "KALMAR FH":("KALMAR.HE",  "v2"),  # Kalmar Oyj — XHEL fails on V1; .HE on V2 works

    # Per-ticker V1 symbol overrides (no version change vs default)
    "MRSN FP":  ("MRN.XPAR",   "v1"),  # Mersen — Bloomberg legacy ticker; current XPAR is MRN
    "STMPA":    ("STMPA.PA",   "v2"),  # STMicroelectronics N.V. parent — Euronext Paris uses STMPA ticker (5 letters), not STM
}

US_ADR_OVERRIDES = {
    # Tickers tagged by parent country but trade as bare US ADRs
    "TSM", "UMC", "ASX", "ARM", "FTI",
    "NVMI", "GILT", "BIDU", "EH", "HSAI", "XPEV",
    "NXPI",   # NXP Semiconductors — Dutch domicile, Nasdaq-listed
    "STM",    # STMicroelectronics — Swiss/Geneva domicile but NYSE ADR primary
    # Round 3 additions:
    "SATL",   # Satellogic — Cayman/Argentine issuer, NASDAQ-only ADR
    "SQM",    # SQM — Chile parent; NYSE ADR primary (USD-denominated)
    "APTV",   # Aptiv — Jersey-domiciled, NYSE-only
    "CSTM",   # Constellium — registry tags France but NYSE primary
    "CSTM FP",  # Same entity — registry key includes " FP" suffix in fetch_prices.EQUITIES
}

MARKETSTACK_UNSUPPORTED = {
    # KOSDAQ + small-cap Korean names absent from MS catalog
    "090360 KS", "098460 KS", "189300 KS", "455900 KS", "474170 KS",
    # Taiwan TPEx (OTC) — XTAI MIC covers TWSE only
    "6488 TT",
    # Hong Kong: catalog stale at 2023-10-09; post-cutoff IPOs absent
    "1274 HK",  # iMotion (Dec 2023 IPO)
    "2431 HK",  # MiniEye (mid 2024 IPO)
    "2432 HK",  # Shenzhen Dobot (Dec 2024 IPO)
    "2498 HK",  # RoboSense (Jan 2024 IPO)
    "9660 HK",  # Horizon Robotics (Oct 2024 IPO)
    "9880 HK",  # UBTECH (Dec 2023 IPO)
    # HK ticker-slot reissues (MS returns the legacy entity, not the current one)
    "6600 HK",  # MS has Sciclone Pharms; our registry expects OneRobotics/Geek+
    "6680 HK",  # MS has JL Mag; our registry expects China Rare Earth Resources
    # HK working tickers but data frozen at 2023-10-09 (2.5y stale, unusable for live)
    "2121 HK",  # AInnovation — works but stale
    "2252 HK",  # Shanghai MicroPort MedBot — works but stale
    # Round 3 additions:
    "ANDR AV",  # Andritz — Wiener Börse not in MS catalog at all
    "464A JP",  # Tokyo Metro (Oct 2024 IPO) — letter-suffix tickers not in MS catalog
    "290A JP",  # Kioxia Holdings (Dec 2024 IPO)
    "MOG/A",    # Registry duplicate of MOG.A — flag for hygiene, route nothing
}


def is_marketstack_supported(ticker: str) -> bool:
    """Whether a ticker has usable MarketStack coverage.

    Caller should route unsupported tickers to a fallback vendor via
    data/registries/data_source_overrides.json (typically Yahoo).
    """
    return ticker not in MARKETSTACK_UNSUPPORTED


def ticker_to_marketstack(ticker: str, country: str) -> str:
    """Map Robotnik internal ticker → MarketStack symbol.

    The internal universe uses two ticker styles:
      - US tickers as bare symbols ("NVDA")
      - International as "CODE SUFFIX" with a space ("012450 KS", "7203 JP")

    For the international form, we discard the bare-letter suffix (which is
    a Robotnik-internal hint, not an EODHD/MarketStack convention) and apply
    the MIC code from COUNTRY_TO_MIC instead.

    Returns "UNAVAILABLE" if the country isn't mapped — caller handles fallback.
    """
    # Short-circuit: explicitly unsupported tickers route to fallback vendor
    # via data_source_overrides.json. Return UNAVAILABLE so the caller logs and
    # skips rather than burning an API call we know will fail.
    if ticker in MARKETSTACK_UNSUPPORTED:
        return "UNAVAILABLE"

    # Per-ticker override wins (Frankfurt cross-listings + V2-routed singletons).
    # Override value is a (symbol, version) tuple; the version part is consumed
    # in route_for_ticker(), so here we only return the symbol.
    if ticker in TICKER_OVERRIDES:
        return TICKER_OVERRIDES[ticker][0]

    # US ADR override — bare ticker on NYSE/Nasdaq regardless of parent country.
    # Strip any Robotnik-internal exchange-hint suffix (" FP", " AV", etc.) so
    # that registry keys like "CSTM FP" return just "CSTM" (the actual bare US
    # ADR symbol the bare-ticker entries in the set also produce naturally).
    if ticker in US_ADR_OVERRIDES:
        return ticker.split(" ", 1)[0]

    country_key = (country or "").strip()
    # Hong Kong auto-detect: registry tags many HK tickers as "China" with " HK"
    # in the ticker name. Route those to XHKG without requiring a registry fix.
    if ticker.endswith(" HK") and country_key in ("China", "Hong Kong"):
        code = ticker.split(" ", 1)[0]
        return "{}.XHKG".format(code)

    # Missing key OR explicit `None` sentinel both collapse to None via .get(),
    # which means "no MarketStack mapping" in either case. Empty string is the
    # distinct case "bare US symbol, no MIC suffix".
    mic = COUNTRY_TO_MIC.get(country_key)
    if mic is None:
        return "UNAVAILABLE"

    # Strip the Robotnik-internal " XX" / " C1" / " C2" exchange hints. These
    # are internal taxonomy markers, not part of any exchange convention.
    code = ticker.strip().split(" ", 1)[0]

    # China prefix-based MIC selection: Shanghai (6xxxxx) → XSHG, Shenzhen
    # (00xxxx, 30xxxx) → XSHE. Live-probe confirmed XSHE works for both
    # Shenzhen mainboard (002xxx) and ChiNext (300xxx).
    if country_key == "China" and code.isdigit() and len(code) == 6:
        if code.startswith(("00", "30")):
            return "{}.XSHE".format(code)
        # else falls through to XSHG (default)

    return code if mic == "" else "{}.{}".format(code, mic)


# ── EOD endpoints ────────────────────────────────────────────────────────
def fetch_eod_latest(symbols, limit: int = 100, throttle: bool = True,
                     version: str = None) -> list:
    """Latest EOD bars for one or more symbols.

    `symbols` accepts a list of MarketStack symbols (max 100 per call per
    MarketStack docs). Returns the raw .data array — caller maps to its
    internal representation. Throttles between batches if `throttle`.
    Pass `version="v2"` for Tokyo tickers (forced by vendor constraints).
    """
    if isinstance(symbols, str):
        symbols = [symbols]
    out = []
    batch_size = min(100, limit)
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        data = _api_get("eod/latest",
                        {"symbols": ",".join(batch), "limit": limit},
                        version=version)
        out.extend(data.get("data") or [])
        if throttle and i + batch_size < len(symbols):
            time.sleep(INTER_CALL_SLEEP)
    return out


def fetch_eod_historical(symbol: str, date_from: str, date_to: str,
                         throttle: bool = True, version: str = None) -> list:
    """Full daily history for ONE symbol across the date window.

    Single-symbol because pagination caps at 1000 rows/call, and 5Y per
    ticker is ~1,260 rows — at least 2 calls per ticker, kept inside this
    helper to hide pagination from the caller.
    Pass `version="v2"` for Tokyo tickers.
    """
    rows = []
    offset = 0
    while True:
        data = _api_get("eod", {
            "symbols": symbol,
            "date_from": date_from,
            "date_to": date_to,
            "limit": PAGE_LIMIT_MAX,
            "offset": offset,
            "sort": "ASC",
        }, version=version)
        page = data.get("data") or []
        rows.extend(page)
        pag = data.get("pagination") or {}
        total = pag.get("total", 0)
        offset += len(page)
        if not page or offset >= total:
            break
        if throttle:
            time.sleep(INTER_CALL_SLEEP)
    return rows


# ── corporate actions ────────────────────────────────────────────────────
def fetch_splits(symbol: str) -> list:
    data = _api_get("splits", {"symbols": symbol, "limit": PAGE_LIMIT_MAX})
    return data.get("data") or []


def fetch_dividends(symbol: str) -> list:
    data = _api_get("dividends", {"symbols": symbol, "limit": PAGE_LIMIT_MAX})
    return data.get("data") or []


# ── reference data ───────────────────────────────────────────────────────
def search_ticker(query: str, limit: int = 20) -> list:
    """Free-text search across MarketStack's ticker catalogue."""
    data = _api_get("tickers", {"search": query, "limit": limit})
    return data.get("data") or []


def get_exchanges(limit: int = PAGE_LIMIT_MAX) -> list:
    data = _api_get("exchanges", {"limit": limit})
    return data.get("data") or []


# ── self-check (CLI) ─────────────────────────────────────────────────────
if __name__ == "__main__":
    """Quick smoke test: probe auth + sample EOD fetch.

    Usage:
        python scripts/marketstack_client.py
    """
    try:
        key = get_api_key()
        print("API key present (length {} chars).".format(len(key)))
    except MissingKeyError as e:
        print("FAIL: {}".format(e))
        sys.exit(1)

    print("Probing /v1/eod/latest with AAPL …")
    try:
        rows = fetch_eod_latest("AAPL")
        if not rows:
            print("Empty response (auth may have succeeded but no data).")
        else:
            r = rows[0]
            print("OK: AAPL {} close=${} volume={}".format(
                r.get("date"), r.get("close"), r.get("volume")))
    except AuthError as e:
        print("AUTH FAIL: {}".format(e))
        sys.exit(2)
    except MarketStackError as e:
        print("API FAIL ({}): {}".format(type(e).__name__, e))
        sys.exit(3)

    print("Call count this session: {}".format(call_count()))
