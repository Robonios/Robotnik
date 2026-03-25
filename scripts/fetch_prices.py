#!/usr/bin/env python3
"""
Robotnik Price Fetcher
======================
Daily fetcher for 219 equities (EODHD) + 43 crypto tokens (CoinGecko).
Outputs: data/prices/equities.json, data/prices/tokens.json, data/prices/all_prices.json
Errors:  data/prices/errors.log

Usage:
    python scripts/fetch_prices.py
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, date
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "prices"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EQUITIES_JSON = DATA_DIR / "equities.json"
TOKENS_JSON = DATA_DIR / "tokens.json"
ALL_JSON = DATA_DIR / "all_prices.json"
ERROR_LOG = DATA_DIR / "errors.log"

# ---------------------------------------------------------------------------
# API keys
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
EODHD_KEY = os.environ.get("EODHD_API_KEY", "")
COINGECKO_KEY = os.environ.get("COINGECKO_API_KEY", "")

# ---------------------------------------------------------------------------
# Robotnik Universe — 219 equities
# (ticker, company, sector, country) — direct from spreadsheet
# ---------------------------------------------------------------------------
EQUITIES = [
    ("ALGM", "Allegro MicroSystems", "Semiconductor", "United States"),
    ("AOSL", "Alpha + Omega Semiconductor", "Semiconductor", "United States"),
    ("ARM", "ARM Holdings ADR", "Semiconductor", "United Kingdom"),
    ("ASX", "ASE Technology Holding ADR", "Semiconductor", "Taiwan"),
    ("ALAB", "Astera Labs", "Semiconductor", "United States"),
    ("AEIS", "Advanced Energy Industries", "Semiconductor", "United States"),
    ("AMKR", "Amkor Technology", "Semiconductor", "United States"),
    ("CEVA", "CEVA Inc", "Semiconductor", "United States"),
    ("CAMT", "Camtek Ltd", "Semiconductor", "United States"),
    ("CRUS", "Cirrus Logic", "Semiconductor", "United States"),
    ("DVLT", "DataVault AI", "Semiconductor", "United States"),
    ("DIOD", "Diodes Inc", "Semiconductor", "United States"),
    ("ENTG", "Entegris", "Semiconductor", "United States"),
    ("FSLR", "First Solar", "Semiconductor", "United States"),
    ("FORM", "FormFactor", "Semiconductor", "United States"),
    ("PI", "Impinj", "Semiconductor", "United States"),
    ("INDI", "Indie Semiconductor", "Semiconductor", "United States"),
    ("INTC", "Intel", "Semiconductor", "United States"),
    ("AGPXX", "Invesco Govt & Agency Portfolio", "Semiconductor", "United States"),
    ("KOPN", "Kopin Corp", "Semiconductor", "United States"),
    ("KLIC", "Kulicke & Soffa Industries", "Semiconductor", "United States"),
    ("MTSI", "MACOM Technology Solutions", "Semiconductor", "United States"),
    ("MRVL", "Marvell Technology", "Semiconductor", "United States"),
    ("MU", "Micron Technology", "Semiconductor", "United States"),
    ("MKSI", "MKS Instruments", "Semiconductor", "United States"),
    ("MPWR", "Monolithic Power Systems", "Semiconductor", "United States"),
    ("MXL", "MaxLinear", "Semiconductor", "United States"),
    ("NVTS", "Navitas Semiconductor", "Semiconductor", "United States"),
    ("NVEC", "NVE Corp", "Semiconductor", "United States"),
    ("PENG", "Penguin Solutions", "Semiconductor", "United States"),
    ("POWI", "Power Integrations", "Semiconductor", "United States"),
    ("PLAB", "Photronics", "Semiconductor", "United States"),
    ("QRVO", "Qorvo", "Semiconductor", "United States"),
    ("RMBS", "Rambus", "Semiconductor", "United States"),
    ("RGTI", "Rigetti Computing", "Semiconductor", "United States"),
    ("SLAB", "Silicon Laboratories", "Semiconductor", "United States"),
    ("SKYT", "SkyWater Technology", "Semiconductor", "United States"),
    ("SWKS", "Skyworks Solutions", "Semiconductor", "United States"),
    ("SYNA", "Synaptics", "Semiconductor", "United States"),
    ("SMTC", "Semtech Corp", "Semiconductor", "United States"),
    ("SITM", "SiTime Corp", "Semiconductor", "United States"),
    ("TSEM", "Tower Semiconductor", "Semiconductor", "United States"),
    ("UMC", "United Microelectronics ADR", "Semiconductor", "Taiwan"),
    ("OLED", "Universal Display Corp", "Semiconductor", "United States"),
    ("LASR", "nLIGHT", "Semiconductor", "United States"),
    # Cross-stack
    ("AMD", "Advanced Micro Devices", "Cross-stack", "United States"),
    ("AMBA", "Ambarella", "Cross-stack", "United States"),
    ("ADI", "Analog Devices", "Cross-stack", "United States"),
    ("AMAT", "Applied Materials", "Cross-stack", "United States"),
    ("ASML", "ASML Holding ADR", "Cross-stack", "Netherlands"),
    ("AVGO", "Broadcom", "Cross-stack", "United States"),
    ("CRDO", "Credo Technology Group", "Cross-stack", "United States"),
    ("CDNS", "Cadence Design Systems", "Cross-stack", "United States"),
    ("KLAC", "KLA Corp", "Cross-stack", "United States"),
    ("LRCX", "Lam Research", "Cross-stack", "United States"),
    ("LSCC", "Lattice Semiconductor", "Cross-stack", "United States"),
    ("MCHP", "Microchip Technology", "Cross-stack", "United States"),
    ("NVMI", "Nova Ltd", "Cross-stack", "Israel"),
    ("NVDA", "NVIDIA", "Cross-stack", "United States"),
    ("NXPI", "NXP Semiconductors", "Cross-stack", "Netherlands"),
    ("ON", "ON Semiconductor", "Cross-stack", "United States"),
    ("QCOM", "Qualcomm", "Cross-stack", "United States"),
    ("STM", "STMicroelectronics ADR", "Cross-stack", "Switzerland"),
    ("SNPS", "Synopsys", "Cross-stack", "United States"),
    ("TSM", "TSMC ADR", "Cross-stack", "Taiwan"),
    ("TER", "Teradyne", "Cross-stack", "United States"),
    ("TXN", "Texas Instruments", "Cross-stack", "United States"),
    # Robotics — international (with exchange suffixes)
    ("ABBN SW", "ABB Ltd", "Robotics", "Switzerland"),
    ("2395 TT", "Advantech Co", "Robotics", "Taiwan"),
    ("2121 HK", "AInnovation Technology", "Robotics", "China"),
    ("1590 TT", "Airtac International", "Robotics", "Taiwan"),
    ("455900 KS", "Angel Robotics", "Robotics", "South Korea"),
    ("AUTO NO", "AutoStore Holdings", "Robotics", "Norway"),
    ("688297 C1", "AVIC Chengdu UAS", "Robotics", "China"),
    ("6857 JP", "Advantest Corp", "Robotics", "Japan"),
    ("6113 JP", "Amada Co", "Robotics", "Japan"),
    ("ANDR AV", "Andritz AG", "Robotics", "Austria"),
    ("6845 JP", "Azbil Corp", "Robotics", "Japan"),
    ("688169 C1", "Beijing Roborock Technology", "Robotics", "China"),
    ("BSL GR", "Basler AG", "Robotics", "Germany"),
    ("6383 JP", "Daifuku Co", "Robotics", "Japan"),
    ("6622 JP", "Daihen Corp", "Robotics", "Japan"),
    ("2308 TT", "Delta Electronics", "Robotics", "Taiwan"),
    ("454910 KS", "Doosan Robotics", "Robotics", "South Korea"),
    ("DUE GR", "Duerr AG", "Robotics", "Germany"),
    ("6902 JP", "Denso Corp", "Robotics", "Japan"),
    ("6141 JP", "DMG Mori Co", "Robotics", "Japan"),
    ("688165 C1", "EFORT Intelligent Robot", "Robotics", "China"),
    ("002747 C2", "Estun Automation", "Robotics", "China"),
    ("EXA FP", "Exail Technologies", "Robotics", "France"),
    ("6954 JP", "Fanuc Corp", "Robotics", "Japan"),
    ("6134 JP", "Fuji Corporation", "Robotics", "Japan"),
    ("G1A GR", "GEA Group", "Robotics", "Germany"),
    ("002008 C2", "Han's Laser Technology", "Robotics", "China"),
    ("6324", "Harmonic Drive Systems", "Robotics", "Japan"),
    ("HEXAB SS", "Hexagon AB", "Robotics", "Sweden"),
    ("HIAB FH", "Hiab Oyj", "Robotics", "Finland"),
    ("6258 JP", "Hirata Corp", "Robotics", "Japan"),
    ("2049", "Hiwin Technologies", "Robotics", "Taiwan"),
    ("2317 TT", "Hon Hai Precision (Foxconn)", "Robotics", "Taiwan"),
    ("9660 HK", "Horizon Robotics", "Robotics", "China"),
    ("1274 HK", "iMotion Automotive", "Robotics", "China"),
    ("IFX GR", "Infineon Technologies", "Robotics", "Germany"),
    ("IMI LN", "IMI PLC", "Robotics", "United Kingdom"),
    ("INRN SW", "Interroll Holding", "Robotics", "Switzerland"),
    ("JEN GR", "Jenoptik AG", "Robotics", "Germany"),
    ("KALMAR FH", "Kalmar Oyj", "Robotics", "Finland"),
    ("KARN SW", "Kardex Holding", "Robotics", "Switzerland"),
    ("6861 JP", "Keyence Corp", "Robotics", "Japan"),
    ("KGX GR", "Kion Group", "Robotics", "Germany"),
    ("098460 KS", "Koh Young Technology", "Robotics", "South Korea"),
    ("KRN GR", "Krones AG", "Robotics", "Germany"),
    ("KCR FH", "Konecranes Oyj", "Robotics", "Finland"),
    ("6920 JP", "Lasertec Corp", "Robotics", "Japan"),
    ("2431 HK", "MiniEye Technology", "Robotics", "China"),
    ("6503 JP", "Mitsubishi Electric", "Robotics", "Japan"),
    ("6268 JP", "Nabtesco Corp", "Robotics", "Japan"),
    ("6645 JP", "Omron Corp", "Robotics", "Japan"),
    ("6600 HK", "OneRobotics Shenzhen", "Robotics", "China"),
    ("6914 JP", "Optex Group", "Robotics", "Japan"),
    ("277810 KS", "Rainbow Robotics", "Robotics", "South Korea"),
    ("RPI LN", "Raspberry Pi Holdings", "Robotics", "United Kingdom"),
    ("6723 JP", "Renesas Electronics", "Robotics", "Japan"),
    ("RSW LN", "Renishaw PLC", "Robotics", "United Kingdom"),
    ("2498 HK", "RoboSense Technology", "Robotics", "China"),
    ("090360 KS", "Robostar Co", "Robotics", "South Korea"),
    ("300757 C2", "Robotechnik Intelligent", "Robotics", "China"),
    ("108490 KS", "Robotis Co", "Robotics", "South Korea"),
    ("SU FP", "Schneider Electric", "Robotics", "France"),
    ("300124 C2", "Shenzhen Inovance Technology", "Robotics", "China"),
    ("6104 JP", "Shibaura Machine Co", "Robotics", "Japan"),
    ("300024 C2", "Siasun Robot & Automation", "Robotics", "China"),
    ("SIE GR", "Siemens AG", "Robotics", "Germany"),
    ("6273 JP", "SMC Corp", "Robotics", "Japan"),
    ("TECN SW", "Tecan Group", "Robotics", "Switzerland"),
    ("6481 JP", "THK Co", "Robotics", "Japan"),
    ("FTI", "TechnipFMC", "Robotics", "United Kingdom"),
    ("8035 JP", "Tokyo Electron", "Robotics", "Japan"),
    ("9880 HK", "UBTECH Robotics", "Robotics", "China"),
    ("6506 JP", "Yaskawa Electric", "Robotics", "Japan"),
    ("6841 JP", "Yokogawa Electric", "Robotics", "Japan"),
    ("388720 KS", "Yuil Robotics", "Robotics", "South Korea"),
    ("2432 HK", "Shenzhen Dobot Corp", "Robotics", "China"),
    ("2252 HK", "Shanghai MicroPort MedBot", "Robotics", "China"),
    # Robotics — US-listed
    ("AVAV", "AeroVironment", "Robotics", "United States"),
    ("GOOG", "Alphabet", "Robotics", "United States"),
    ("AMZN", "Amazon", "Robotics", "United States"),
    ("APH", "Amphenol", "Robotics", "United States"),
    ("APTV", "Aptiv PLC", "Robotics", "Ireland"),
    ("ATS CN", "ATS Corp", "Robotics", "Canada"),
    ("BIDU", "Baidu ADR", "Robotics", "China"),
    ("BWXT", "BWX Technologies", "Robotics", "United States"),
    ("BYDDY", "BYD Co ADR", "Robotics", "United States"),
    ("CCJ", "Cameco Corp", "Robotics", "United States"),
    ("CAT", "Caterpillar", "Robotics", "United States"),
    ("CLS CN", "Celestica", "Robotics", "Canada"),
    ("CGNX", "Cognex", "Robotics", "United States"),
    ("COHR", "Coherent Corp", "Robotics", "United States"),
    ("DASH", "DoorDash", "Robotics", "United States"),
    ("EH", "EHang Holdings ADR", "Robotics", "China"),
    ("ESLT", "Elbit Systems", "Robotics", "United States"),
    ("EMR", "Emerson Electric", "Robotics", "United States"),
    ("GMED", "Globus Medical", "Robotics", "United States"),
    ("HSAI", "Hesai Group", "Robotics", "China"),
    ("LUNR", "Intuitive Machines", "Space", "United States"),
    ("ISRG", "Intuitive Surgical", "Robotics", "United States"),
    ("IPGP", "IPG Photonics", "Robotics", "United States"),
    ("IRDM", "Iridium Communications", "Space", "United States"),
    ("JBL", "Jabil", "Robotics", "United States"),
    ("JBTM", "JBT Marel Corp", "Robotics", "United States"),
    ("KAI", "Kadant", "Robotics", "United States"),
    ("KDK", "Kodiak AI", "Robotics", "United States"),
    ("KMTUY", "Komatsu ADR", "Robotics", "United States"),
    ("KTOS", "Kratos Defense & Security", "Space", "United States"),
    ("LECO", "Lincoln Electric Holdings", "Robotics", "United States"),
    ("LHX", "L3Harris Technologies", "Space", "United States"),
    ("MG", "Magna International", "Robotics", "United States"),
    ("MBLY", "Mobileye Global", "Robotics", "United States"),
    ("MELE", "Melexis NV", "Robotics", "United States"),
    ("MOG/A", "Moog Inc Class A", "Robotics", "United States"),
    ("MP", "MP Materials", "Robotics", "United States"),
    ("NDSN", "Nordson Corp", "Robotics", "United States"),
    ("NOVT", "Novanta", "Robotics", "United States"),
    ("OKLO", "Oklo", "Robotics", "United States"),
    ("ONDS", "Ondas Inc", "Robotics", "United States"),
    ("ONTO", "Onto Innovation", "Robotics", "United States"),
    ("OUST", "Ouster", "Robotics", "United States"),
    ("PLTR", "Palantir Technologies", "Robotics", "United States"),
    ("PRCT", "PROCEPT BioRobotics", "Robotics", "United States"),
    ("RBC", "RBC Bearings", "Robotics", "United States"),
    ("RR", "Richtech Robotics", "Robotics", "United States"),
    ("RRX", "Regal Rexnord", "Robotics", "United States"),
    ("ROK", "Rockwell Automation", "Robotics", "United States"),
    ("SHA", "Schaeffler AG", "Robotics", "United States"),
    ("SERV", "Serve Robotics", "Robotics", "United States"),
    ("SRTA", "Strata Critical Medical", "Robotics", "United States"),
    ("STMPA", "STMicroelectronics NV", "Robotics", "United States"),
    ("ST", "Sensata Technologies", "Robotics", "United States"),
    ("SYM", "Symbotic", "Robotics", "United States"),
    ("TEL", "TE Connectivity", "Robotics", "United States"),
    ("TDY", "Teledyne Technologies", "Robotics", "United States"),
    ("TSLA", "Tesla", "Robotics", "United States"),
    ("TRMB", "Trimble", "Robotics", "United States"),
    ("XPEV", "XPeng ADR", "Robotics", "China"),
    ("ZBRA", "Zebra Technologies", "Robotics", "United States"),
    # Bare numeric tickers (TBD country — mapped manually)
    ("002979", "China Leadshine Technology", "Robotics", "TBD"),
    ("600111", "China Northern Rare Earth", "Robotics", "TBD"),
    ("601100", "Jiangsu Hengli Hydraulic", "Robotics", "TBD"),
    ("603662", "Keli Sensing Technology", "Robotics", "TBD"),
    ("688017", "Leader Harmonious Drive Systems", "Robotics", "TBD"),
    ("6594", "Nidec Corp", "Robotics", "TBD"),
    ("601689", "Ningbo Tuopu Group", "Robotics", "TBD"),
    ("6723", "Renesas Electronics", "Robotics", "TBD"),
    ("603009", "Shanghai Beite Technology", "Robotics", "TBD"),
    ("003021", "Shenzhen Zhaowei Machinery", "Robotics", "TBD"),
    ("300100", "Shuanglin Co", "Robotics", "TBD"),
    ("9868", "XPeng Inc Class A", "Robotics", "TBD"),
    ("002050", "Zhejiang Sanhua Intelligent", "Robotics", "TBD"),
    ("002472", "Zhejiang Shuanghuan Driveline", "Robotics", "TBD"),
    # ── Space ────────────────────────────────────────────────────
    ("RKLB", "Rocket Lab USA", "Space", "United States"),
    ("ASTS", "AST SpaceMobile", "Space", "United States"),
    ("HEI", "HEICO Corp", "Space", "United States"),
    ("VSAT", "Viasat Inc", "Space", "United States"),
    ("PL", "Planet Labs PBC", "Space", "United States"),
    ("RDW", "Redwire Corp", "Space", "United States"),
    ("SPIR", "Spire Global", "Space", "United States"),
    ("BKSY", "BlackSky Technology", "Space", "United States"),
    ("GSAT", "Globalstar Inc", "Space", "United States"),
    ("TSAT", "Telesat Corp", "Space", "United States"),
    ("SATS", "EchoStar Corp", "Space", "United States"),
    ("BA", "Boeing Co", "Space", "United States"),
    ("LMT", "Lockheed Martin", "Space", "United States"),
    ("RTX", "RTX Corp", "Space", "United States"),
    ("NOC", "Northrop Grumman", "Space", "United States"),
    ("GD", "General Dynamics", "Space", "United States"),
    ("SPCE", "Virgin Galactic", "Space", "United States"),
    # --- Space companies added from Universe v4 ---
    ("186A JP", "Astroscale Holdings", "Space", "Japan"),
    ("AVIO IM", "Avio SpA", "Space", "Italy"),
    ("DCO", "Ducommun", "Space", "United States"),
    ("ESE", "ESCO Technologies", "Space", "United States"),
    ("ETL FP", "Eutelsat Communications", "Space", "France"),
    ("FLY", "Firefly Aerospace", "Space", "United States"),
    ("GILT", "Gilat Satellite Networks", "Space", "Israel"),
    ("GOGO", "Gogo Inc", "Space", "United States"),
    ("GOMX SS", "GomSpace", "Space", "Denmark"),
    ("012450 KS", "Hanwha Aerospace", "Space", "South Korea"),
    ("HXL", "Hexcel Corp", "Space", "United States"),
    ("189300 KS", "Intellian Technologies", "Space", "South Korea"),
    ("KRMN", "Karman Holdings", "Space", "United States"),
    ("474170 KS", "Lumir Inc", "Space", "South Korea"),
    ("MDA CN", "MDA Space", "Space", "Canada"),
    ("MNTS", "Momentus", "Space", "United States"),
    ("MOG.A", "Moog Inc", "Space", "United States"),
    ("NN", "NextNav", "Space", "United States"),
    ("OVZON SS", "Ovzon AB", "Space", "Sweden"),
    ("PSN", "Parsons Corp", "Space", "United States"),
    ("464A JP", "QPS Holdings", "Space", "Japan"),
    ("SESG FP", "SES SA", "Space", "Luxembourg"),
    ("SATL", "Satellogic", "Space", "Argentina"),
    ("SIDU", "Sidus Space", "Space", "United States"),
    ("SCC IT", "Space Communication", "Space", "Israel"),
    ("290A JP", "Synspective", "Space", "Japan"),
    ("TTMI", "TTM Technologies", "Space", "United States"),
    ("VOYG", "Voyager Technologies", "Space", "United States"),
    ("9348 JP", "ispace Inc", "Space", "Japan"),
    # ── Materials & Inputs (44 companies) ──
    ("4063 JP", "Shin-Etsu Chemical", "Materials", "Japan"),
    ("3436 JP", "SUMCO Corp", "Materials", "Japan"),
    ("6488 TT", "GlobalWafers", "Materials", "Taiwan"),
    ("WAF GR", "Siltronic", "Materials", "Germany"),
    ("010060 KS", "OCI Holdings", "Materials", "South Korea"),
    ("4043 JP", "Tokuyama Corp", "Materials", "Japan"),
    ("WCH GR", "Wacker Chemie", "Materials", "Germany"),
    ("SOI FP", "Soitec", "Materials", "France"),
    ("6153 TT", "Coretronic", "Materials", "Taiwan"),
    ("WOLF", "Wolfspeed", "Materials", "United States"),
    ("LIN", "Linde plc", "Materials", "United States"),
    ("AI FP", "Air Liquide", "Materials", "France"),
    ("APD", "Air Products", "Materials", "United States"),
    ("4091 JP", "Nippon Sanso", "Materials", "Japan"),
    ("4186 JP", "Tokyo Ohka Kogyo", "Materials", "Japan"),
    ("MRK GR", "Merck KGaA", "Materials", "Germany"),
    ("BAS GR", "BASF", "Materials", "Germany"),
    ("4112 JP", "Daicel Corp", "Materials", "Japan"),
    ("4005 JP", "Sumitomo Chemical", "Materials", "Japan"),
    ("4208 JP", "UBE Corp", "Materials", "Japan"),
    ("3407 JP", "Asahi Kasei", "Materials", "Japan"),
    ("5384 JP", "Fujimi Inc", "Materials", "Japan"),
    ("5706 JP", "Mitsui Mining", "Materials", "Japan"),
    ("MTRN", "Materion Corp", "Materials", "United States"),
    ("4062 JP", "Ibiden", "Materials", "Japan"),
    ("3037 TT", "Unimicron", "Materials", "Taiwan"),
    ("2802 JP", "Ajinomoto Co", "Materials", "Japan"),
    ("6971 JP", "Kyocera", "Materials", "Japan"),
    ("LYC AU", "Lynas Rare Earths", "Materials", "Australia"),
    ("ILU AU", "Iluka Resources", "Materials", "Australia"),
    ("ARU AU", "Arafura Rare Earths", "Materials", "Australia"),
    ("600111 C1", "Northern Rare Earth", "Materials", "China"),
    ("6680 HK", "China Rare Earth Resources", "Materials", "China"),
    ("ALB", "Albemarle Corp", "Materials", "United States"),
    ("SQM", "Sociedad Quimica y Minera", "Materials", "Chile"),
    ("AMG NA", "AMG Critical Materials", "Materials", "Netherlands"),
    ("3402 JP", "Toray Industries", "Materials", "Japan"),
    ("3401 JP", "Teijin Ltd", "Materials", "Japan"),
    ("4188 JP", "Mitsubishi Chemical", "Materials", "Japan"),
    ("SGL GR", "SGL Carbon", "Materials", "Germany"),
    ("ATI", "ATI Inc", "Materials", "United States"),
    ("CRS", "Carpenter Technology", "Materials", "United States"),
    ("CSTM FP", "Constellium", "Materials", "France"),
    ("MRSN FP", "Mersen", "Materials", "France"),
]


def ticker_to_eodhd(ticker, country):
    """Map spreadsheet ticker to EODHD format: SYMBOL.EXCHANGE

    Note: EODHD has no Tokyo Stock Exchange (TSE). Japanese stocks are
    mapped to their US OTC/ADR equivalents where available.
    Stocks without US OTC tickers will fail and be logged in errors.log.
    """
    t = ticker.strip()

    # Japan "XXXX JP" -> US OTC ADR (EODHD has no TSE exchange)
    JP_TO_US_OTC = {
        "6857": "ATEYY", "6113": "AMDLY", "6383": "DFKCY",
        "6902": "DNZOY", "6954": "FANUY", "6861": "KYCCF",
        "6268": "NCTKY", "6594": "NJDCY", "6645": "OMRNY",
        "6723": "RNECY", "6481": "THKLY", "6506": "YASKY",
        "6920": "LSRCY", "8035": "TOELY", "6503": "MIELY",
        "6273": "SMCAY", "6841": "YOKEY", "6762": "TTDKY",
        "6971": "KYOCY",
        # No US OTC: use Frankfurt (.F) as fallback via JP_FRANKFURT
    }

    # Japan tickers without US OTC — use Frankfurt exchange
    JP_FRANKFURT = {
        "6845": "YMK",    # Azbil Corp
        "6622": "6NV",    # Daihen Corp
        "6141": "GIL",    # DMG Mori (listed as German on EODHD)
        "6134": "F5M",    # Fuji Corporation
        "6258": "1ZM",    # Hirata Corp
        "6104": "TOA",    # Shibaura Machine
        "6324": "HSYDF",  # Harmonic Drive Systems (US OTC, not Frankfurt)
    }

    # Hardcoded overrides for ambiguous or special tickers
    bare_overrides = {
        "9868": "9868.HK",     # XPeng HK listing
        "HEXAB SS": "HEXA-B.ST",  # Hexagon AB class B (Sweden)
        "MELE": "MELE.BR",        # Melexis NV (Euronext Brussels)
        "STMPA": "STMPA.PA",      # STMicroelectronics (Paris)
    }
    if t in bare_overrides:
        return bare_overrides[t]

    # Korean tickers on KOSDAQ (not KOSPI) — use .KQ instead of .KO
    KOSDAQ_TICKERS = {"455900", "098460", "090360"}

    suffix_map = {
        "KS": "KO", "TT": "TW", "HK": "HK",
        "C1": "SHG", "C2": "SHE", "GR": "XETRA", "LN": "LSE",
        "SW": "SW", "FP": "PA", "FH": "HE", "SS": "ST",
        "NO": "OL", "AV": "VI", "CN": "TO",
    }

    parts = t.split()
    if len(parts) == 2:
        symbol, suffix = parts
        # Japan: use US OTC mapping, then Frankfurt fallback
        if suffix == "JP":
            otc = JP_TO_US_OTC.get(symbol)
            if otc:
                return "{}.US".format(otc)
            ffm = JP_FRANKFURT.get(symbol)
            if ffm:
                if ffm == "HSYDF":
                    return "HSYDF.US"  # US OTC, not Frankfurt
                if ffm == "GIL":
                    return "GIL.XETRA"  # DMG Mori primary listing
                return "{}.F".format(ffm)
            return "{}.US".format(symbol)  # Will fail, logged as error
        # Korean KOSDAQ override
        if suffix == "KS" and symbol in KOSDAQ_TICKERS:
            return "{}.KQ".format(symbol)
        exchange = suffix_map.get(suffix)
        if exchange:
            return "{}.{}".format(symbol, exchange)

    # Bare numeric tickers
    if t.isdigit() and len(t) >= 4:
        # Japan bare (TBD country, 4-digit >= 6000)
        if len(t) == 4 and country in ("Japan", "TBD") and int(t) >= 6000:
            otc = JP_TO_US_OTC.get(t)
            if otc:
                return "{}.US".format(otc)
            ffm = JP_FRANKFURT.get(t)
            if ffm:
                if ffm == "HSYDF":
                    return "HSYDF.US"
                if ffm == "GIL":
                    return "GIL.XETRA"
                return "{}.F".format(ffm)
            return "{}.US".format(t)  # Will fail, logged as error
        # Taiwan 4-digit
        if len(t) == 4 and country in ("Taiwan",):
            return "{}.TW".format(t)
        # China Shanghai: starts with 6
        if t.startswith("6"):
            return "{}.SHG".format(t)
        # China Shenzhen: starts with 0 or 3
        if t.startswith("0") or t.startswith("3"):
            return "{}.SHE".format(t)

    # MOG/A -> MOG-A.US
    if "/" in t:
        t = t.replace("/", "-")

    return "{}.US".format(t)


def guess_currency(eodhd_ticker):
    """Guess currency from exchange suffix."""
    exchange = eodhd_ticker.split(".")[-1] if "." in eodhd_ticker else "US"
    currency_map = {
        "US": "USD", "TSE": "JPY", "KO": "KRW", "KQ": "KRW",
        "TW": "TWD", "HK": "HKD", "SHG": "CNY", "SHE": "CNY",
        "XETRA": "EUR", "F": "EUR", "BR": "EUR",
        "LSE": "GBp", "SW": "CHF", "PA": "EUR", "HE": "EUR",
        "ST": "SEK", "OL": "NOK", "VI": "EUR", "TO": "CAD",
    }
    return currency_map.get(exchange, "USD")


# ---------------------------------------------------------------------------
# CoinGecko token mapping (43 tokens)
# ticker -> (coingecko_id, display_name)
# ---------------------------------------------------------------------------
TOKENS = {
    "ANIMUS": ("animus", "Animus"),
    "AUKI": ("auki-labs", "Auki"),
    "ATNM": ("autonoma-network", "Autonoma Network"),
    "EVAL": ("chromia-eval-by-virtuals", "Chromia EVAL"),  # Not on CoinGecko yet
    "CODEC": ("codec-flow", "Codec Flow"),
    "DPTX": ("deeptics", "DEEPTICS"),
    "EDGE": ("edge-token", "Edge"),  # Not on CoinGecko yet
    "$CPT": ("empulser-enterprises", "Empulser Enterprises"),
    "ROBO": ("robo-token-2", "Fabric Protocol"),
    "FORMA": ("forma-robotics", "Forma Robotics"),
    "GEOD": ("geodnet", "Geodnet"),
    "BREW": ("homebrew-robotics-club", "Homebrew Robotics Club"),
    "IOTX": ("iotex", "IoTeX"),
    "JOJO": ("jojoworld", "JojoWorld"),
    "KAGE": ("kage-network", "KAGE Network"),
    "MECHA": ("mechaos", "MechaOs"),
    "EMDR": ("modulr", "Modulr"),
    "NATIX": ("natix-network", "NATIX Network"),
    "NRN": ("neuron-ai", "Neuron"),  # Not on CoinGecko yet
    "OP": ("one-path", "One Path"),
    "ONO": ("onocoy-token", "Onocoy Token"),
    "OPAN": ("opanarchy", "Opanarchy"),
    "OPUS": ("opus-2", "Opus Genesis"),
    "OVR": ("ovr", "Ovr"),
    "QACE": ("qace-dynamics", "Qace Dynamics"),
    "ROBA": ("roba", "ROBA"),
    "ROVR": ("rovr-network", "ROVR Network"),
    "RICE": ("rice-ai", "Rice AI"),
    "ROBCO": ("robco-network", "RobCo Network"),
    "ROBOT": ("robostack", "RoboStack"),
    "XRT": ("robonomics-network", "Robonomics Network"),
    "RBR": ("robora", "Robora"),
    "ROX": ("robotexon", "Robotexon"),
    "ROKO": ("roko-network", "Roko Network"),
    "SLC": ("silencio", "Silencio"),
    "SMPL": ("simple-ai", "Simple AI"),
    "SPAWN": ("spawn", "Spawn"),
    "TSMON": ("ondo-tsm", "TSMC Ondo Tokenized"),  # Not on CoinGecko yet
    "VADER": ("vaderai-by-virtuals", "Vader"),
    "VIRTUAL": ("virtual-protocol", "Virtuals Protocol"),
    "SHOW": ("vitanova", "VitaNova"),
    "DEUS": ("xmaquina", "XMAQUINA"),
    "PEAQ": ("peaq-2", "peaq"),
}


# ---------------------------------------------------------------------------
# EODHD fetcher
# ---------------------------------------------------------------------------
def fetch_eodhd_price(eodhd_ticker):
    url = "https://eodhd.com/api/eod/{}?api_token={}&fmt=json&order=d&limit=2".format(
        eodhd_ticker, EODHD_KEY
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Robotnik/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        if not data or not isinstance(data, list) or len(data) == 0:
            return None
        latest = data[0]
        prev_close = data[1]["close"] if len(data) > 1 else None
        change_pct = None
        if prev_close and prev_close != 0:
            change_pct = round((latest["close"] - prev_close) / prev_close * 100, 2)
        return {
            "price": latest["close"],
            "date": latest["date"],
            "volume": latest.get("volume"),
            "change_pct": change_pct,
            "currency": guess_currency(eodhd_ticker),
        }
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError):
        return None


def load_eodhd_mapping():
    """Load explicit ticker mapping from data/mappings/eodhd_tickers.json if available."""
    mapping_path = ROOT / "data" / "mappings" / "eodhd_tickers.json"
    if mapping_path.exists():
        with open(mapping_path) as f:
            return json.load(f)
    return None

_EODHD_MAP = None
_PENDING_TICKERS = None

def load_pending_tickers():
    """Load list of tickers with pending EODHD coverage (new IPOs etc)."""
    path = ROOT / "data" / "mappings" / "pending_tickers.json"
    if path.exists():
        with open(path) as f:
            return set(json.load(f))
    return set()

def fetch_all_equities():
    global _EODHD_MAP, _PENDING_TICKERS
    if _EODHD_MAP is None:
        _EODHD_MAP = load_eodhd_mapping()
    if _PENDING_TICKERS is None:
        _PENDING_TICKERS = load_pending_tickers()
    if _EODHD_MAP:
        print("  Using explicit EODHD ticker mapping ({} entries)".format(len(_EODHD_MAP)))
    if _PENDING_TICKERS:
        print("  Pending coverage tickers: {}".format(len(_PENDING_TICKERS)))

    results = []
    errors = []
    total = len(EQUITIES)

    for i, (ticker, company, sector, country) in enumerate(EQUITIES):
        # Use explicit mapping if available, fall back to rule-based
        if _EODHD_MAP and ticker in _EODHD_MAP:
            eodhd_sym = _EODHD_MAP[ticker]
        else:
            eodhd_sym = ticker_to_eodhd(ticker, country)

        # Skip unavailable tickers
        if eodhd_sym == "UNAVAILABLE":
            errors.append("{} ({}) — Not available on EODHD (expected)".format(ticker, company))
            print("[{}/{}] {} -> UNAVAILABLE (skipped)".format(i + 1, total, ticker))
            continue

        print("[{}/{}] {} -> {} ...".format(i + 1, total, ticker, eodhd_sym), end=" ")

        data = fetch_eodhd_price(eodhd_sym)
        if data:
            results.append({
                "ticker": ticker,
                "eodhd_symbol": eodhd_sym,
                "name": company,
                "sector": sector,
                "price": data["price"],
                "currency": data["currency"],
                "change_pct": data["change_pct"],
                "volume": data["volume"],
                "date": data["date"],
                "source": "EODHD",
            })
            print("{} ({})".format(data["price"], data["currency"]))
        else:
            if _PENDING_TICKERS and eodhd_sym in _PENDING_TICKERS:
                print("PENDING (new IPO)")
                # Don't count as error — just info
            else:
                errors.append("{} ({}) — EODHD: {}".format(ticker, company, eodhd_sym))
                print("FAILED")

        time.sleep(0.2)

    return results, errors


# ---------------------------------------------------------------------------
# CoinGecko fetcher
# ---------------------------------------------------------------------------
def load_coingecko_mapping():
    """Load explicit CoinGecko ID mapping from data/mappings/coingecko_ids.json if available."""
    mapping_path = ROOT / "data" / "mappings" / "coingecko_ids.json"
    if mapping_path.exists():
        with open(mapping_path) as f:
            return json.load(f)
    return None

def fetch_coingecko_prices():
    results = []
    errors = []

    cg_mapping = load_coingecko_mapping()

    cg_ids = []
    id_to_ticker = {}
    for ticker, (cg_id_default, name) in TOKENS.items():
        # Use explicit mapping if available
        if cg_mapping and ticker in cg_mapping:
            cg_id = cg_mapping[ticker]
            if cg_id == "not_found":
                errors.append("{} ({}) — CoinGecko: not_found (expected)".format(ticker, name))
                print("[Token] {} -> SKIPPED (not on CoinGecko)".format(ticker))
                continue
        else:
            cg_id = cg_id_default
        cg_ids.append(cg_id)
        id_to_ticker[cg_id] = (ticker, name)

    if cg_mapping:
        print("  Using explicit CoinGecko ID mapping")

    ids_str = ",".join(cg_ids)
    url = "https://api.coingecko.com/api/v3/simple/price?ids={}&vs_currencies=usd&include_24hr_change=true".format(
        ids_str
    )

    headers = {
        "User-Agent": "Robotnik/1.0",
        "accept": "application/json",
        "x-cg-demo-api-key": COINGECKO_KEY,
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
        print("CoinGecko API error: {}".format(e))
        for ticker, (cg_id, name) in TOKENS.items():
            errors.append("{} ({}) — CoinGecko: {}".format(ticker, name, cg_id))
        return results, errors

    today = date.today().isoformat()
    for cg_id, (ticker, name) in id_to_ticker.items():
        if cg_id in data:
            price_data = data[cg_id]
            price = price_data.get("usd")
            change = price_data.get("usd_24h_change")
            if change is not None:
                change = round(change, 2)
            results.append({
                "ticker": ticker,
                "coingecko_id": cg_id,
                "name": name,
                "sector": "Token",
                "price": price,
                "currency": "USD",
                "change_pct": change,
                "volume": None,
                "date": today,
                "source": "CoinGecko",
            })
            print("[Token] {} -> ${} ({}%)".format(ticker, price, change))
        else:
            errors.append("{} ({}) — CoinGecko ID: {} not found".format(ticker, name, cg_id))
            print("[Token] {} -> NOT FOUND (tried: {})".format(ticker, cg_id))

    return results, errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if not EODHD_KEY:
        print("ERROR: EODHD_API_KEY not set")
        sys.exit(1)
    if not COINGECKO_KEY:
        print("ERROR: COINGECKO_API_KEY not set")
        sys.exit(1)

    print("=" * 60)
    print("ROBOTNIK PRICE FETCHER")
    print("=" * 60)
    ts = datetime.utcnow().isoformat() + "Z"

    print("\n--- Fetching {} equities (EODHD) ---\n".format(len(EQUITIES)))
    eq_results, eq_errors = fetch_all_equities()

    eq_output = {
        "fetched_at": ts,
        "count": len(eq_results),
        "source": "EODHD (eodhd.com)",
        "equities": eq_results,
    }
    with open(EQUITIES_JSON, "w") as f:
        json.dump(eq_output, f, indent=2)
    print("\nEquities: {}/{} succeeded -> {}".format(len(eq_results), len(EQUITIES), EQUITIES_JSON))

    print("\n--- Fetching {} tokens (CoinGecko) ---\n".format(len(TOKENS)))
    tk_results, tk_errors = fetch_coingecko_prices()

    tk_output = {
        "fetched_at": ts,
        "count": len(tk_results),
        "source": "CoinGecko (coingecko.com)",
        "attribution": "Data provided by CoinGecko",
        "tokens": tk_results,
    }
    with open(TOKENS_JSON, "w") as f:
        json.dump(tk_output, f, indent=2)
    print("\nTokens: {}/{} succeeded -> {}".format(len(tk_results), len(TOKENS), TOKENS_JSON))

    all_prices = eq_results + tk_results
    all_output = {
        "fetched_at": ts,
        "count": len(all_prices),
        "sources": ["EODHD (eodhd.com)", "CoinGecko (coingecko.com)"],
        "attribution": "Data provided by CoinGecko",
        "prices": sorted(all_prices, key=lambda x: x["ticker"]),
    }
    with open(ALL_JSON, "w") as f:
        json.dump(all_output, f, indent=2)
    print("\nCombined: {} prices -> {}".format(len(all_prices), ALL_JSON))

    all_errors = eq_errors + tk_errors
    with open(ERROR_LOG, "w") as f:
        f.write("Robotnik Price Fetcher - Error Log\n")
        f.write("Run: {}\n".format(ts))
        f.write("=" * 50 + "\n\n")
        if all_errors:
            for e in all_errors:
                f.write(e + "\n")
        else:
            f.write("No errors.\n")
    print("\n{} errors logged -> {}".format(len(all_errors), ERROR_LOG))

    print("\n" + "=" * 60)
    print("DONE: {} equities, {} tokens, {} errors".format(
        len(eq_results), len(tk_results), len(all_errors)
    ))
    print("=" * 60)


if __name__ == "__main__":
    main()
