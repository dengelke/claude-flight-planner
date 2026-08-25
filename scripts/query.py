#!/usr/bin/env python3
"""Quick query helper for the FAC database.

Examples:
    python query.py fuel avgas mogas       # airports with AVGAS AND MOGAS (MOGAS incl. AVPULP)
    python query.py fuel mogas             # all MOGAS/AVPULP airports
    python query.py near -38.27 145.18 50  # airports within 50 km of a lat/lon
    python query.py show YTYA              # full record for one airport
    python query.py pay carnet credit      # airports accepting carnet AND credit card
    python query.py freq YMMB              # radio frequencies + controlled status
    python query.py controlled             # list all towered (controlled) aerodromes
    python query.py runways YSCB           # surfaces (FAC) + declared distances (RDS)
    python query.py sql "SELECT code,name FROM airports WHERE state='TAS' AND jet_a1=1"
"""
import sys, sqlite3, json, math, pathlib

DB = pathlib.Path(__file__).resolve().parent.parent / "data" / "fac_database.sqlite"
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row

def main(argv):
    if not argv: print(__doc__); return
    cmd, *rest = argv
    if cmd == "fuel":
        where = " AND ".join(f"{f.lower()}=1" for f in rest)
        rows = con.execute(f"SELECT code,name,state,fuel_types FROM airports WHERE {where} ORDER BY state,name")
        for r in rows: print(f"{r['code']}  {r['name']:<28} {r['state'] or '':<4} {r['fuel_types']}")
    elif cmd == "pay":
        # filter by payment method(s): carnet credit eftpos cash account app fuelcard
        where = " AND ".join(f"pay_{m.lower()}=1" for m in rest)
        rows = con.execute(f"SELECT code,name,state,fuel_types,payment_methods FROM airports "
                           f"WHERE {where} ORDER BY state,name")
        for r in rows:
            print(f"{r['code']}  {r['name']:<26} {r['state'] or '':<4} [{r['fuel_types'] or '-'}]  {r['payment_methods']}")
    elif cmd == "near":
        lat, lon, km = float(rest[0]), float(rest[1]), float(rest[2] if len(rest) > 2 else 50)
        out = []
        for r in con.execute("SELECT * FROM airports WHERE lat IS NOT NULL"):
            d = 6371 * math.acos(min(1, math.sin(math.radians(lat))*math.sin(math.radians(r["lat"]))
                + math.cos(math.radians(lat))*math.cos(math.radians(r["lat"]))*math.cos(math.radians(lon-r["lon"]))))
            if d <= km: out.append((d, r))
        for d, r in sorted(out):
            print(f"{d:6.1f} km  {r['code']}  {r['name']:<26} {r['fuel_types'] or 'no fuel listed'}")
    elif cmd == "show":
        rec = {x["code"]: x for x in json.load(open(DB.parent/"fac_database.json"))}[rest[0].upper()]
        print(json.dumps(rec, indent=2))
    elif cmd == "freq":
        code = rest[0].upper()
        a = con.execute("SELECT name,state,controlled,airspace_class,ctaf FROM airports WHERE code=?", (code,)).fetchone()
        tag = "CONTROLLED (own tower)" if a and a["controlled"] else "non-towered"
        print(f"{code}  {a['name'] if a else '?'}  {a['state'] if a else ''}  [{tag}]")
        if a and a["airspace_class"]: print(f"  Airspace class: {a['airspace_class']}")
        if a and a["ctaf"]: print(f"  CTAF: {a['ctaf']}")
        print()
        for r in con.execute("SELECT service,callsign,freq FROM frequencies WHERE code=? ORDER BY rowid", (code,)):
            print(f"  {r['service']:<8} {r['callsign']:<22} {r['freq']}")
    elif cmd == "controlled":
        rows = con.execute("SELECT code,name,state,airspace_class,frequencies FROM airports WHERE controlled=1 ORDER BY state,name")
        for r in rows:
            print(f"{r['code']}  {r['name']:<28} {r['state'] or '':<4} class {r['airspace_class'] or '-':<10} {r['frequencies']}")
    elif cmd == "runways":
        code = rest[0].upper()
        name = con.execute("SELECT name,state FROM airports WHERE code=?", (code,)).fetchone()
        print(f"{code}  {name['name'] if name else '?'}  {name['state'] if name else ''}\n")
        print("PHYSICAL (FAC) - direction / length / surface:")
        fac = con.execute("SELECT designator,length_m,surface FROM runways WHERE code=?", (code,)).fetchall()
        for r in fac:
            print(f"  RWY {r['designator']:<9} {(str(r['length_m'])+'M') if r['length_m'] else '':<8} {r['surface'] or ''}")
        if not fac: print("  (none listed)")
        rds = con.execute("SELECT rwy,cn,tora_m,toda_m,asda_m,lda_m,width_m,slope FROM rds WHERE code=?", (code,)).fetchall()
        print("\nDECLARED DISTANCES (RDS) - metres:" if rds else "\nDECLARED DISTANCES (RDS): (no RDS published for this aerodrome)")
        if rds:
            print(f"  {'RWY':<5}{'CN':<5}{'TORA':>6}{'TODA':>6}{'ASDA':>6}{'LDA':>6}{'WID':>5}  SLOPE")
            for r in rds:
                print(f"  {r['rwy']:<5}{str(r['cn']):<5}{r['tora_m']:>6}{r['toda_m']:>6}{r['asda_m']:>6}{r['lda_m']:>6}{(r['width_m'] or ''):>5}  {r['slope'] or ''}")
    elif cmd == "sql":
        for r in con.execute(rest[0]): print(tuple(r))
    else:
        print(__doc__)

if __name__ == "__main__":
    main(sys.argv[1:])
