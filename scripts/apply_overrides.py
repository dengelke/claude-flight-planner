#!/usr/bin/env python3
"""Apply data/fuel_overrides.json to the already-built database artifacts in place.

parse_fac.py applies the same overrides during a full rebuild; this script patches
the committed fac_database.{sqlite,json,csv} directly so the fix lands without
re-downloading/parsing the ERSA source PDFs. Idempotent — safe to re-run.

Usage:  python scripts/apply_overrides.py
"""
import json, csv, sqlite3, pathlib

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
OV = json.loads((DATA / "fuel_overrides.json").read_text())
ENTRIES = {c: o for c, o in OV.items() if not c.startswith("_")}

BOOLS = ("avgas", "mogas", "jet_a1", "jet_b", "f34", "fsii", "jetplus", "has_fuel")


def merged_fuel_types(existing, add):
    types = [t.strip() for t in (existing or "").split(",") if t.strip()]
    for t in add or []:
        if t not in types:
            types.append(t)
    return ", ".join(types)


def apply_to_record(rec):
    """Mutate one flat airport dict/row per its override entry. Returns True if changed."""
    ov = ENTRIES.get(rec["code"])
    if not ov:
        return False
    for k, v in ov.items():
        if k == "add_fuel_types":
            rec["fuel_types"] = merged_fuel_types(rec.get("fuel_types"), v)
        elif k == "override_note":
            continue  # card-only, not stored
        else:
            rec[k] = v
    rec["has_fuel"] = 1 if rec.get("fuel_types") else 0
    return True


def main():
    # ---- SQLite ----
    db = DATA / "fac_database.sqlite"
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    changed = 0
    for code, ov in ENTRIES.items():
        row = con.execute("SELECT * FROM airports WHERE code=?", (code,)).fetchone()
        if row is None:
            print(f"! {code}: not in DB — skipping")
            continue
        rec = dict(row)
        apply_to_record(rec)
        sets = {k: rec[k] for k in ("fuel_types", "has_fuel", *BOOLS) if k in rec}
        con.execute("UPDATE airports SET " + ",".join(f"{k}=?" for k in sets) + " WHERE code=?",
                    [*sets.values(), code])
        changed += 1
    con.commit(); con.close()
    print(f"sqlite: updated {changed} airport(s)")

    # ---- JSON ----
    jpath = DATA / "fac_database.json"
    recs = json.loads(jpath.read_text())
    for rec in recs:
        apply_to_record(rec)
    jpath.write_text(json.dumps(recs, indent=2))
    print("json: patched")

    # ---- CSV ----
    cpath = DATA / "fac_database.csv"
    with open(cpath, newline="") as f:
        rd = csv.DictReader(f)
        cols = rd.fieldnames
        rows = list(rd)
    for r in rows:
        if r["code"] in ENTRIES:
            apply_to_record(r)  # values become strings; fine for the flat CSV
    with open(cpath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    print("csv: patched")


if __name__ == "__main__":
    main()
