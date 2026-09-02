# Australian Aerodrome FAC Database (ERSA, effective 09 JUL 2026)

Searchable database built by parsing all **749 Facility (FAC) entries** from the
Airservices Australia ERSA (En Route Supplement Australia).

Source index: `https://www.airservicesaustralia.com/aip/aip.asp?pg=40&vdate=09JUL2026&ver=2`
PDF pattern:  `https://www.airservicesaustralia.com/aip/pending/ersa/FAC_<CODE>_09JUL2026.pdf`

## Layout

```
scripts/   pipeline + query CLI (committed)
data/      the parsed database + input code lists (committed);
           source PDFs & caches live here too but are gitignored
```

Committed: everything in `scripts/`, plus the parsed database and code lists in
`data/`. **Not committed** (gitignored in `data/`, ~43 MB / regenerable): `pdfs/`,
`rds/`, `text_cache.json`, `rds_text_cache.json`, `index.html`.

| Path | What it is |
|------|-----------|
| `scripts/query.py` | CLI helper (fuel/pay filters, radius search, `runways`, `freq`, `controlled`, record dump, raw SQL) |
| `scripts/download_all.py` / `download_rds.py` | Download the FAC / RDS PDFs → `data/pdfs/`, `data/rds/` |
| `scripts/extract_text.py` | Cache FAC PDF text → `data/text_cache.json` |
| `scripts/parse_fac.py` | Parse cached FAC text → the FAC database files |
| `scripts/parse_rds.py` | Parse RDS PDFs → `rds` table + `rds_database.*` (caches to `data/rds_text_cache.json`) |
| `data/fac_database.sqlite` | SQLite DB — tables `airports`, `runways` (FAC surfaces), `rds` (declared distances), `frequencies` (radio) |
| `data/fac_database.csv` | Flat one-row-per-airport table (open in Excel/Sheets) |
| `data/fac_database.json` | Full nested records incl. per-runway detail + raw handling text |
| `data/rds_database.csv` / `.json` | One row per runway END: declared distances, width, slope |
| `data/codes.txt` / `rds_codes.txt` | ICAO code lists driving the downloaders |
| `data/pdfs/` `data/rds/` | Source FAC / RDS PDFs (~43 MB, gitignored) |

Reproduce from scratch (run from the repo root; a Python venv with `pdfplumber`
+ `requests` is expected — repo uses `.venv`):

```bash
python scripts/download_all.py && python scripts/download_rds.py   # fetch the ~43 MB of PDFs
python scripts/extract_text.py                                     # PDFs → data/text_cache.json
python scripts/parse_fac.py && python scripts/parse_rds.py         # → data/*_database.*
```

Regenerate just the DB from cached text (PDFs already fetched):
`python scripts/parse_fac.py && python scripts/parse_rds.py`
(run `parse_fac.py` first — `parse_rds.py` merges the `rds` table into the DB it builds).

## Flight-plan tooling (`flightplans/`)

Two helpers turn the database into linkable/inspectable content inside the flight-plan markdown:

| Script | What it does |
|--------|-------------|
| `scripts/aerodrome_card.py` | Emits a per-aerodrome markdown "data card" → `flightplans/aerodromes/<CODE>.md` (position, **verbatim ERSA handling text**, fuel, payment, frequencies, runways + RDS distances, links to the official ERSA FAC/RDS PDFs). The plans link each aerodrome heading to its card. |
| `scripts/route_map.py` | Emits `flightplans/maps/<name>.geojson` (GitHub renders it as an interactive map) **and** `<name>.png` (a static coastline map embedded inline in the plan with `![](…)`). |

```bash
python  scripts/aerodrome_card.py --plan flightplans/YBLN-YAYE_SR20_AVGAS.md   # cards for a whole plan
python  scripts/aerodrome_card.py --all                                        # every aerodrome
.venv/bin/python scripts/route_map.py YBLN-YAYE YBLN YPKG YWBR YAYE            # geojson + png
```

- `aerodrome_card.py` is pure stdlib. `route_map.py` needs **Pillow** for the PNG (`.venv/bin/pip install Pillow`); without it the geojson is still written and the PNG is skipped with a warning.
- `scripts/au_coast.json` is the baked Natural-Earth-50m Australia coastline used to draw the PNG (committed, ~29 KB).
- The ERSA cycle the cards cite is set by `ERSA_CYCLE`/`ERSA_STATE` at the top of `aerodrome_card.py` — update it when the DB is rebuilt from a new cycle.

## `airports` columns

`code, name, state, lat, lon` (decimal degrees), `lat_raw, lon_raw` (DDMMSS as
published), `elevation_ft, mag_var, certification` (CERT/UNCR/MIL), `utc_offset`,
`has_fuel`, `fuel_types`, boolean flags `avgas / mogas / jet_a1 / jet_b /
f34 / fsii / jetplus`, `fuel_caveat`, `fuel_source`, `payment_methods` (summary
string) + payment flags `pay_carnet / pay_credit / pay_eftpos / pay_cash /
pay_account / pay_app / pay_fuelcard`, `controlled` (has own control tower),
`airspace_class` (e.g. `C, D, G`), `ctaf`, `frequencies` (summary string),
`runway_count`, `runway_summary`, `handling_raw` (verbatim fuel/handling text).

- **AVTUR is folded into `jet_a1`** (AVTUR is the ICAO name for Jet A-1).
- **AVPULP (aviation unleaded) is folded into `mogas`** — treated as the same product.
  The exact term used at each field is preserved in `handling_raw`.
- **FSII / JetPlus / F34** are jet-fuel additives / grades and are flagged separately
  in addition to `jet_a1`.
- `fuel_caveat = 1` flags entries whose handling text contains "nil/no fuel" wording
  (e.g. fuel only available elsewhere or on notice) — check `handling_raw`.
- `fuel_source = "line_scan"` marks the 1 airport (YMGD) whose section header was
  unrecoverably scrambled, so fuel was read from a keyword+context line scan.

### Payment methods

Detected within the HANDLING section (same scope as fuel). Flags: `pay_carnet`
(industry fuel carnet accounts), `pay_credit` (credit card / VISA / MasterCard /
"V and MC" / Amex / Diners), `pay_eftpos`, `pay_cash`, `pay_account` (supplier
account / account holders), `pay_app` (mobile payment apps — Fuelcharge, Compac Pay,
smartphone), `pay_fuelcard` (branded aviation fuel cards — Fuel2Sky, UVair, Sterling,
WFS, etc.). `payment_methods` is a readable summary (e.g. `Carnet, Credit card, App`).

- `pay_app` is matched by brand, not bare "APP" — "APP" alone is ambiguous with
  "approach" (e.g. "245 (APP RQ)"), so that would misfire.
- 217 of 411 aerodromes with a handling section list ≥1 payment method. Totals:
  credit 140 · fuel card 63 · app 60 · carnet 95 · account 37 · cash 28 · EFTPOS 16.
  Where none are listed, fuel is often account-only or the FAC just doesn't say —
  check `handling_raw`.

## `runways` columns

`code, designator` (e.g. `17/35`; `(unnamed)` for single unmarked strips),
`length_m, width_m, surface, strength` (PCR/PCN), `raw`.

> Note: for **certified** airports the FAC does not print runway length — length lives
> in the separate RDS documents (see `rds` table). So `length_m` is often null for
> big airports but populated for GA/uncertified strips.

## Radio frequencies & controlled status

Parsed from the ATS AND AERODROME COMMUNICATION FACILITIES section.

- `frequencies` table: one row per (aerodrome, service, frequency) — `code, service,
  callsign, freq` (MHz), `raw` line. Services: `FIA`/`CENTRE` (area/flight-info),
  `TWR` (tower), `SMC`/`GND` (ground), `ATIS`, `APP`/`DEP` (approach/departure),
  `ACD` (clearance delivery), `CTAF`, `UNICOM`, `AFIS`, etc. 1392 freqs / 745 fields.
- Only VHF/airband 108–137 MHz is captured (NDB idents like `398` are skipped).
- `airports.frequencies` is a readable summary, e.g. `FIA 135.7; ATIS 120.9; SMC 134.25; TWR 118.1/123.0`.
- **`controlled = 1`** marks aerodromes with their **own control tower** (46 total:
  the capital-city airports, GA Class-D fields — Jandakot, Archerfield, Moorabbin,
  Bankstown, Parafield, Essendon, Cambridge — regional towers, and military bases).
  - It requires a `TWR` line whose callsign matches the aerodrome name, so offshore
    helidecks that merely sit under another field's tower (e.g. *Charlie One* listing
    *Karratha Tower*) are **not** flagged.
- `airspace_class` lists the classes named in that section (e.g. `C, D, G` — often
  Class D during tower hours reverting to Class G outside them).
- `ctaf` = Common Traffic Advisory Frequency. At towered fields this is the tower
  frequency (used when the tower is closed); at non-towered fields it's the local CTAF.

## `rds` table (per runway END, from Runway Distance Supplements)

`code, rwy` (single direction e.g. `05`, `18L`), `cn` (classification number, or
`MIL`), `tora_m, toda_m, asda_m, lda_m` (declared distances, metres), `width_m`
(pavement width), `slope`. **TORA is effectively the usable runway length.**

- Covers **350 aerodromes / 1077 runway ends** (the busier/certified fields that
  publish an RDS). GA strips without an RDS have their length in `runways.length_m`.
- Surface type is **not** in the RDS — join to `runways.surface` for that.

Combined view for one aerodrome: `query.py runways <CODE>`.

## Coverage / quality

- name **100%**, coordinates **100%**, elevation 98%, state 98%
  (the 13 without a state are external territories — Lord Howe, Cocos, Christmas,
  Norfolk, Wilkins/Antarctica, etc.), certification 97%.
- Fuel: every fuel keyword in every FAC is accounted for (0 unflagged). Detection is
  scoped to the HANDLING SERVICES section to avoid false positives (e.g. "AVGAS
  available 9 NM north").
- Runways: 814 runways across 550 airports. Airports with 0 runways are heliports/HLS,
  seaplane water-alighting areas, or (≈4 cases) unusual military/text-only strips.
- Some PDFs render with scrambled text; coordinates for those were recovered by
  reconstructing character positions (verified against the prior ERSA cycle).

## Fuel totals (this cycle)

AVGAS 277 · Jet A-1 250 · MOGAS 15 (incl. AVPULP) · F34 12 · FSII 8 · JetPlus 5 ·
any fuel 337 of 749.

## Example queries

```bash
.venv/bin/python scripts/query.py fuel avgas mogas          # AVGAS and MOGAS (MOGAS incl. AVPULP)
.venv/bin/python scripts/query.py fuel mogas                # all MOGAS/AVPULP airports
.venv/bin/python scripts/query.py near -38.27 145.18 60     # within 60 km of Tyabb
.venv/bin/python scripts/query.py show YTYA                  # full record
.venv/bin/python scripts/query.py pay carnet credit          # accepts carnet AND credit card
.venv/bin/python scripts/query.py freq YMMB                  # frequencies + controlled status
.venv/bin/python scripts/query.py controlled                 # all towered aerodromes
.venv/bin/python scripts/query.py runways YSCB               # surfaces + declared distances
```

```sql
-- SQLite
SELECT code,name,state,fuel_types FROM airports WHERE mogas=1;
SELECT code,name FROM airports WHERE avgas=1 AND jet_a1=0;         -- AVGAS only
SELECT a.code,a.name,r.designator,r.length_m,r.surface
  FROM airports a JOIN runways r ON r.code=a.code
  WHERE r.surface LIKE '%Sealed%' AND r.length_m>=1500;
-- sealed runways ≥1800 m usable (TORA), from the RDS declared distances
SELECT d.code,a.name,d.rwy,d.tora_m,d.width_m
  FROM rds d JOIN airports a ON a.code=d.code
  WHERE d.tora_m>=1800 ORDER BY d.tora_m DESC;
-- AVGAS airports that DON'T take a credit card (carnet/account only, etc.)
SELECT code,name,state,payment_methods FROM airports
  WHERE avgas=1 AND pay_credit=0 AND payment_methods!='' ORDER BY state,name;
-- every tower frequency in the country
SELECT f.code,a.name,f.freq FROM frequencies f JOIN airports a ON a.code=f.code
  WHERE f.service='TWR' ORDER BY a.name;
-- controlled aerodromes that have AVGAS
SELECT code,name,state,frequencies FROM airports WHERE controlled=1 AND avgas=1;
```
