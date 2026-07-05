#!/usr/bin/env python3
"""
One-shot subsector backfill for entities whose registry entry lacks
a subsector field. Uses the existing taxonomy (as surveyed from the
current registry) — no new labels introduced.

Run once; idempotent (only writes if a subsector is missing, never
overwrites an existing one).
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "data" / "registries" / "entity_registry.json"

# Ticker -> subsector. Taxonomy is the set already in use elsewhere in
# the registry: Semiconductors {EDA & IP, Equipment, Fabless Design,
# Foundry, Frontier Compute, IDM, OSAT / Packaging & Test, Power & Analog},
# Materials {Battery Materials, Industrial & Specialty Gases, Packaging &
# Substrates, Process Chemicals, Rare Earths & Critical Minerals, Silicon
# & Substrates, Structural Materials}, Robotics {Autonomous Systems &
# Drones, Collaborative Robots, Humanoid & Service Robots, Industrial
# Robots, Machine Vision & Sensors, Motion Control & Actuators,
# Software & Simulation, Surgical & Medical, Test & Measurement,
# Warehouse & Logistics Automation}, Space {Earth Observation, Ground
# Systems & Antennas, In-Orbit Services, Launch, Satellite Comms,
# Satellite Communications, Space Components}.
MAPPING = {
    # ───── Semiconductors ─────
    "ALAB": "Fabless Design",
    "ALGM": "Power & Analog",
    "AOSL": "Power & Analog",
    "ARM": "EDA & IP",
    "ASX": "OSAT / Packaging & Test",
    "CDNS": "EDA & IP",
    "CEVA": "EDA & IP",
    "CRDO": "Fabless Design",
    "CRUS": "Fabless Design",
    "DIOD": "Power & Analog",
    "IFX GR": "IDM",
    "INDI": "Fabless Design",
    "LASR": "Fabless Design",
    "LSCC": "Fabless Design",
    "MCHP": "IDM",
    "MELE": "Fabless Design",
    "MKSI": "Equipment",
    "MRVL": "Fabless Design",
    "MTSI": "Fabless Design",
    "MXL": "Fabless Design",
    "NVEC": "Fabless Design",
    "NVTS": "Fabless Design",
    "NXPI": "IDM",
    "ON": "IDM",
    "PI": "Fabless Design",
    "QCOM": "Fabless Design",
    "QRVO": "Fabless Design",
    "RMBS": "EDA & IP",
    "SITM": "Fabless Design",
    "SKYT": "Foundry",
    "SLAB": "Fabless Design",
    "SMTC": "Fabless Design",
    "SNPS": "EDA & IP",
    "STM": "IDM",
    "SWKS": "Fabless Design",
    "SYNA": "Fabless Design",
    "TSEM": "Foundry",
    "TXN": "IDM",
    "UMC": "Foundry",
    "WOLF": "IDM",
    "6723": "IDM",  # Renesas (Semi-tagged duplicate)

    # ───── Materials ─────
    "4043 JP": "Industrial & Specialty Gases",
    "4062 JP": "Packaging & Substrates",
    "4091 JP": "Industrial & Specialty Gases",
    "4004 JP": "Process Chemicals",
    "4208 JP": "Process Chemicals",
    "5384 JP": "Process Chemicals",
    "5706 JP": "Rare Earths & Critical Minerals",
    "6680 HK": "Rare Earths & Critical Minerals",
    "AMG NA": "Rare Earths & Critical Minerals",
    "ATI": "Structural Materials",
    "CRS": "Structural Materials",
    "CSTM FP": "Structural Materials",
    "ENTG": "Process Chemicals",
    "HXL": "Structural Materials",
    "ILU AU": "Rare Earths & Critical Minerals",
    "MP": "Rare Earths & Critical Minerals",
    "MTRN": "Process Chemicals",
    "SOI FP": "Silicon & Substrates",
    "WAF GR": "Silicon & Substrates",

    # ───── Robotics ─────
    "388720 KS": "Industrial Robots",
    "454910 KS": "Collaborative Robots",
    "455900 KS": "Humanoid & Service Robots",
    "603009": "Motion Control & Actuators",
    "603662": "Machine Vision & Sensors",
    "6104 JP": "Industrial Robots",
    "6113 JP": "Industrial Robots",
    "6134 JP": "Industrial Robots",
    "6141 JP": "Industrial Robots",
    "6258 JP": "Industrial Robots",
    "6268 JP": "Motion Control & Actuators",
    "6273 JP": "Motion Control & Actuators",
    "6324": "Motion Control & Actuators",
    "6383 JP": "Warehouse & Logistics Automation",
    "6481 JP": "Motion Control & Actuators",
    "6506 JP": "Industrial Robots",
    "6594": "Motion Control & Actuators",
    "6600 HK": "Humanoid & Service Robots",
    "6622 JP": "Industrial Robots",
    "6645 JP": "Industrial Robots",
    "6723 JP": "Motion Control & Actuators",
    "6841 JP": "Test & Measurement",
    "6845 JP": "Industrial Robots",
    "6902 JP": "Industrial Robots",
    "688017": "Motion Control & Actuators",
    "688165 C1": "Industrial Robots",
    "688169 C1": "Humanoid & Service Robots",
    "9880 HK": "Humanoid & Service Robots",
    "ATS CN": "Industrial Robots",
    "AUTO NO": "Warehouse & Logistics Automation",
    "BSL GR": "Machine Vision & Sensors",
    "CGNX": "Machine Vision & Sensors",
    "DUE GR": "Industrial Robots",
    "G1A GR": "Industrial Robots",
    "HEXAB SS": "Machine Vision & Sensors",
    "HIAB FH": "Warehouse & Logistics Automation",
    "HSAI": "Machine Vision & Sensors",
    "INRN SW": "Warehouse & Logistics Automation",
    "IPGP": "Industrial Robots",
    "JBTM": "Industrial Robots",
    "JEN GR": "Machine Vision & Sensors",
    "KARN SW": "Warehouse & Logistics Automation",
    "KGX GR": "Warehouse & Logistics Automation",
    "KRN GR": "Industrial Robots",
    "LECO": "Industrial Robots",
    "MBLY": "Autonomous Systems & Drones",
    "MOG/A": "Motion Control & Actuators",
    "NDSN": "Industrial Robots",
    "NOVT": "Machine Vision & Sensors",
    "OUST": "Machine Vision & Sensors",
    "RR": "Humanoid & Service Robots",
    "RRX": "Motion Control & Actuators",
    "SERV": "Autonomous Systems & Drones",
    "SHA": "Motion Control & Actuators",
    "STMPA": "Motion Control & Actuators",
    "SYM": "Warehouse & Logistics Automation",
    "ZBRA": "Warehouse & Logistics Automation",
    "600111": "Motion Control & Actuators",  # rare-earth feeder into robotics magnets

    # ───── Space ─────
    "474170 KS": "Earth Observation",
    "9348 JP": "In-Orbit Services",
    "AVIO IM": "Launch",
    "DCO": "Space Components",
    "ETL FP": "Satellite Communications",
    "FLY": "Launch",
    "GILT": "Ground Systems & Antennas",
    "GOMX SS": "Space Components",
    "LMT": "Space Components",
    "LUNR": "In-Orbit Services",
    "MDA CN": "In-Orbit Services",
    "MNTS": "In-Orbit Services",
    "MOG.A": "Space Components",
    "NOC": "Space Components",
    "RDW": "Space Components",
    "SATL": "Earth Observation",
    "SCC IT": "Satellite Communications",
    "SESG FP": "Satellite Communications",
    "SIDU": "Earth Observation",
    "SPCE": "Launch",
    "VOYG": "In-Orbit Services",
    "VSAT": "Satellite Communications",

    # ───── Second-sweep: Asian tickers missed in the first pass ─────
    # Robotics (China / Korea / Taiwan / Japan)
    "002008 C2": "Industrial Robots",           # Han's Laser — industrial laser processing
    "002050": "Motion Control & Actuators",     # Zhejiang Sanhua — precision components
    "002472": "Motion Control & Actuators",     # Zhejiang Shuanghuan Driveline — gears
    "002747 C2": "Industrial Robots",           # Estun Automation
    "002979": "Motion Control & Actuators",     # China Leadshine — motion control
    "003021": "Motion Control & Actuators",     # Shenzhen Zhaowei Machinery — micro drives
    "090360 KS": "Industrial Robots",           # Robostar
    "098460 KS": "Machine Vision & Sensors",    # Koh Young — 3D inspection
    "108490 KS": "Humanoid & Service Robots",   # Robotis
    "1590 TT": "Motion Control & Actuators",    # Airtac — pneumatics
    "2049": "Motion Control & Actuators",       # Hiwin — linear motion / ball screws
    "2395 TT": "Industrial Robots",             # Advantech — industrial computing
    "2432 HK": "Collaborative Robots",          # Shenzhen Dobot
    "2498 HK": "Machine Vision & Sensors",      # RoboSense — LiDAR
    "277810 KS": "Humanoid & Service Robots",   # Rainbow Robotics
    "300024 C2": "Industrial Robots",           # Siasun
    "300100": "Motion Control & Actuators",     # Shuanglin
    "300124 C2": "Motion Control & Actuators",  # Inovance — servo / drives
    "300757 C2": "Industrial Robots",           # Robotechnik

    # Materials (Japan / Korea)
    "010060 KS": "Industrial & Specialty Gases",# OCI Holdings — polysilicon + gases
    "2802 JP": "Process Chemicals",             # Ajinomoto — ABF substrate material
    "3401 JP": "Structural Materials",          # Teijin — carbon fibre / aramid
    "3402 JP": "Structural Materials",          # Toray — composites
    "3407 JP": "Process Chemicals",             # Asahi Kasei
    "3436 JP": "Silicon & Substrates",          # SUMCO — silicon wafers

    # Space
    "189300 KS": "Ground Systems & Antennas",   # Intellian — maritime antennas

    # ───── Third-sweep: visible-on-assets entities still unassigned ─────
    "186A JP": "In-Orbit Services",             # Astroscale — debris removal services
    "464A JP": "Earth Observation",             # QPS Holdings — SAR EO constellation
    "290A JP": "Earth Observation",             # Synspective — SAR EO constellation
    "MRSN FP": "Process Chemicals",             # Mersen — electrical / graphite specialty
    "4186 JP": "Process Chemicals",             # Tokyo Ohka Kogyo — photoresists
}


def main():
    with open(REGISTRY) as f:
        reg = json.load(f)

    applied = 0
    skipped_existing = 0
    not_in_registry = 0
    for ticker, subsector in MAPPING.items():
        ent = reg.get(ticker)
        if not isinstance(ent, dict):
            not_in_registry += 1
            print(f"  NOT IN REGISTRY: {ticker}")
            continue
        if ent.get("subsector"):
            skipped_existing += 1
            continue
        ent["subsector"] = subsector
        applied += 1

    with open(REGISTRY, "w") as f:
        json.dump(reg, f, indent=2)

    print(f"\nApplied subsector to {applied} entities")
    print(f"Skipped (already had subsector): {skipped_existing}")
    print(f"Not in registry: {not_in_registry}")


if __name__ == "__main__":
    main()
