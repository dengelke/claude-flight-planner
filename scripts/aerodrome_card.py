#!/usr/bin/env python3
"""Generate a per-aerodrome markdown "data card" from the FAC/RDS database.

Cards are written to `flightplans/aerodromes/<CODE>.md` and are meant to be linked
from the flight-plan markdown so each aerodrome heading can drill into the full
parsed ERSA record (fuel + handling verbatim, frequencies, runways, RDS distances)
plus a link to the official Airservices ERSA source PDF.

Usage:
    python scripts/aerodrome_card.py YAYE YWBR YPKG      # named aerodromes
    python scripts/aerodrome_card.py --plan flightplans/YBLN-YAYE_SR20_AVGAS.md
    python scripts/aerodrome_card.py --all               # every aerodrome in the DB
"""
import sys, re, sqlite3, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "fac_database.sqlite"
OUT = ROOT / "flightplans" / "aerodromes"

# ERSA cycle the committed database was parsed from. Update alongside a DB rebuild.
ERSA_CYCLE = "09JUL2026"
ERSA_STATE = "pending"  # "pending" or "current" path on the Airservices AIP site
FAC_URL = "https://www.airservicesaustralia.com/aip/{state}/ersa/FAC_{code}_{cycle}.pdf"
RDS_URL = "https://www.airservicesaustralia.com/aip/{state}/ersa/RDS_{code}_{cycle}.pdf"
ERSA_INDEX = "https://www.airservicesaustralia.com/aip/aip.asp?pg=40"

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

# Curated fuel overrides (see data/fuel_overrides.json) — surface any override_note on the card.
import json as _json
_ov_path = ROOT / "data" / "fuel_overrides.json"
OVERRIDES = {c: o for c, o in _json.loads(_ov_path.read_text()).items()
             if not c.startswith("_")} if _ov_path.exists() else {}


def card(code: str) -> str | None:
    a = con.execute("SELECT * FROM airports WHERE code=?", (code,)).fetchone()
    if a is None:
        return None
    L = []
    L.append(f"# {a['code']} — {a['name']} ({a['state'] or '?'})\n")
    L.append(f"> Parsed from ERSA **{ERSA_CYCLE}**. Always re-verify against current "
             f"ERSA + NOTAMs before flight.\n")

    # Position / basics
    L.append("## Position & basics\n")
    L.append(f"- **Coordinates:** {a['lat']:.5f}, {a['lon']:.5f}  "
             f"([map](https://www.openstreetmap.org/?mlat={a['lat']}&mlon={a['lon']}&zoom=12))")
    if a["elevation_ft"] is not None:
        L.append(f"- **Elevation:** {a['elevation_ft']} ft")
    if a["mag_var"]:
        L.append(f"- **Mag var:** {a['mag_var']}")
    if a["certification"]:
        L.append(f"- **Certification:** {a['certification']}")
    if a["utc_offset"]:
        L.append(f"- **UTC offset:** {a['utc_offset']}")
    L.append("")

    # Fuel — handling_raw is the authoritative cross-check field
    L.append("## Fuel & handling\n")
    L.append(f"- **Fuel types (parsed):** {a['fuel_types'] or 'none listed'}"
             + ("  ⚠️ *caveat flagged — read handling text*" if a["fuel_caveat"] else ""))
    note = OVERRIDES.get(code, {}).get("override_note")
    if note:
        L.append(f"- **⚠️ Fuel override (local knowledge, not ERSA):** {note}")
    if a["payment_methods"]:
        L.append(f"- **Payment:** {a['payment_methods']}")
    if a["handling_raw"]:
        L.append("\n**HANDLING (verbatim from ERSA — the source of truth):**\n")
        L.append("```")
        L.append(a["handling_raw"].strip())
        L.append("```")
    L.append("")

    # Communications
    freqs = con.execute(
        "SELECT service,callsign,freq FROM frequencies WHERE code=? ORDER BY rowid", (code,)
    ).fetchall()
    if a["controlled"] or a["ctaf"] or freqs:
        L.append("## Communications\n")
        tag = "CONTROLLED (own tower)" if a["controlled"] else "non-towered"
        L.append(f"- **Status:** {tag}"
                 + (f" · class {a['airspace_class']}" if a["airspace_class"] else ""))
        if a["ctaf"]:
            L.append(f"- **CTAF:** {a['ctaf']}")
        if freqs:
            L.append("\n| Service | Callsign | Freq |")
            L.append("|---------|----------|------|")
            for f in freqs:
                L.append(f"| {f['service'] or ''} | {f['callsign'] or ''} | {f['freq'] or ''} |")
        L.append("")

    # Runways (physical) + RDS declared distances
    rwy = con.execute(
        "SELECT designator,length_m,width_m,surface,strength FROM runways WHERE code=?", (code,)
    ).fetchall()
    rds = con.execute(
        "SELECT rwy,cn,tora_m,toda_m,asda_m,lda_m,width_m,slope FROM rds WHERE code=?", (code,)
    ).fetchall()
    if rwy or rds:
        L.append("## Runways\n")
        if rwy:
            L.append("**Physical (FAC):**\n")
            L.append("| RWY | Length | Width | Surface | Strength |")
            L.append("|-----|-------:|------:|---------|----------|")
            for r in rwy:
                L.append(f"| {r['designator'] or ''} | "
                         f"{(str(r['length_m'])+' m') if r['length_m'] else ''} | "
                         f"{(str(r['width_m'])+' m') if r['width_m'] else ''} | "
                         f"{r['surface'] or ''} | {r['strength'] or ''} |")
        if rds:
            L.append("\n**Declared distances (RDS), metres:**\n")
            L.append("| RWY | CN | TORA | TODA | ASDA | LDA | Width | Slope |")
            L.append("|-----|----|-----:|-----:|-----:|----:|------:|-------|")
            for r in rds:
                L.append(f"| {r['rwy'] or ''} | {r['cn'] or ''} | {r['tora_m'] or ''} | "
                         f"{r['toda_m'] or ''} | {r['asda_m'] or ''} | {r['lda_m'] or ''} | "
                         f"{(r['width_m'] or '')} | {r['slope'] or ''} |")
        L.append("")

    # Source links
    fac = FAC_URL.format(state=ERSA_STATE, code=code, cycle=ERSA_CYCLE)
    rds_link = RDS_URL.format(state=ERSA_STATE, code=code, cycle=ERSA_CYCLE)
    L.append("## Official source\n")
    L.append(f"- ERSA FAC PDF: [{code} FAC]({fac})")
    if rds:
        L.append(f"- ERSA RDS PDF: [{code} RDS]({rds_link})")
    L.append(f"- ERSA index (current cycle may differ): [{ERSA_INDEX}]({ERSA_INDEX})")
    L.append("")
    L.append("*Generated by `scripts/aerodrome_card.py` from the parsed ERSA database. "
             "PDF links point at the cycle the DB was built from and will rot as cycles roll — "
             "use the ERSA index for the live document.*")
    return "\n".join(L) + "\n"


def codes_from_plan(path: str) -> list[str]:
    text = pathlib.Path(path).read_text()
    seen, out = set(), []
    for m in re.finditer(r"\bY[A-Z]{3}\b", text):
        c = m.group(0)
        if c not in seen:
            seen.add(c); out.append(c)
    return out


def main(argv):
    if not argv:
        print(__doc__); return
    if argv[0] == "--all":
        codes = [r["code"] for r in con.execute("SELECT code FROM airports ORDER BY code")]
    elif argv[0] == "--plan":
        codes = codes_from_plan(argv[1])
    else:
        codes = [c.upper() for c in argv]
    OUT.mkdir(parents=True, exist_ok=True)
    written, missing = 0, []
    for code in codes:
        c = card(code)
        if c is None:
            missing.append(code); continue
        (OUT / f"{code}.md").write_text(c)
        written += 1
    print(f"Wrote {written} card(s) to {OUT.relative_to(ROOT)}/")
    if missing:
        print(f"Not in DB (skipped): {', '.join(missing)}")


if __name__ == "__main__":
    main(sys.argv[1:])
