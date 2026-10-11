#!/usr/bin/env python3
"""Nil-wind nav log for an ordered route, computed from the FAC database.

For each leg: distance, true track, mag var (from the ERSA FAC of the two ends),
magnetic heading (nil wind, so HDG = track), a VFR hemispherical cruise level,
the climb allowance (1 min per 2,000 ft from the departure field elevation),
leg time, leg fuel and the cumulative time. Then lists ERSA-registered
aerodromes within `--near` nm of each leg that publish an ADDITIONAL
INFORMATION section, so the en-route hazards come from ERSA, not guesswork.

Stops are aerodrome codes or `LABEL@lat,lon` visual waypoints (same syntax as
route_map.py); add a third number, `LABEL@lat,lon,elev`, for an unlisted strip
you land at (e.g. a Shire ALA). A visual waypoint continues the leg: the climb is only charged
on the first segment out of an aerodrome, and the leg's time/fuel are summed
until the next aerodrome.

Usage:
    python scripts/nav_log.py YBLN YPKG YWBR YAYE                       # SR20 defaults
    python scripts/nav_log.py YBLN Mandurah@-32.53,115.72 YGEL --alt 1500,8500
    python scripts/nav_log.py YBLN YWGN YKOJ@-33.7503,117.1358,915 YBLN --tas 100 --burn 20 --unit L

Options:
    --tas KT        true airspeed (default 150, SR20 planning)
    --burn N        fuel flow per hour (default 12.5)
    --unit U        fuel unit label (default USG)
    --alt A,B,..    cruise altitude per segment (overrides the default level)
    --east FT       level for magnetic tracks 000-179 (default 7500)
    --west FT       level for magnetic tracks 180-359 (default 8500)
    --near NM       hazard search radius either side of track (default 10)
"""
import sys, math, sqlite3, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "fac_database.sqlite"
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
R_NM = 3440.065


def opt(argv, name, default, cast=str):
    if name in argv:
        i = argv.index(name)
        val = argv[i + 1]
        del argv[i:i + 2]
        return cast(val)
    return default


def var_deg(text):
    """'3 W' -> -3.0, '11 E' -> 11.0 (east positive), None if unparsable."""
    if not text:
        return None
    parts = text.split()
    try:
        v = float(parts[0])
    except (ValueError, IndexError):
        return None
    return -v if len(parts) > 1 and parts[1].upper().startswith("W") else v


def nearest_var(lat, lon):
    """Mag var of the nearest aerodrome that publishes one."""
    best = None
    for r in con.execute("SELECT lat, lon, mag_var FROM airports WHERE mag_var != ''"):
        v = var_deg(r["mag_var"])
        if v is None:
            continue
        d = dist(lat, lon, r["lat"], r["lon"])
        if best is None or d < best[0]:
            best = (d, v)
    return best[1] if best else 0.0


def stop(token):
    if "@" in token:
        label, _, coords = token.partition("@")
        nums = [float(x) for x in coords.split(",")]
        lat, lon = nums[0], nums[1]
        # a third number (field elevation, ft) marks an unlisted landing strip, not a waypoint
        landing = len(nums) > 2
        return dict(code=label, name=label, lat=lat, lon=lon, elev=nums[2] if landing else None,
                    var=nearest_var(lat, lon), wpt=not landing)
    a = con.execute("SELECT * FROM airports WHERE code=?", (token.upper(),)).fetchone()
    if a is None:
        sys.exit(f"unknown aerodrome {token}")
    v = var_deg(a["mag_var"])
    return dict(code=a["code"], name=a["name"].title(), lat=a["lat"], lon=a["lon"],
                elev=a["elevation_ft"] or 0,
                var=v if v is not None else nearest_var(a["lat"], a["lon"]), wpt=False)


def dist(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R_NM * 2 * math.asin(math.sqrt(h))


def bearing(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def off_track(a, b, p):
    """(cross-track nm, along-track nm) of point p from segment a→b, or None if abeam outside it."""
    d13 = dist(a["lat"], a["lon"], p["lat"], p["lon"]) / R_NM
    t13 = math.radians(bearing(a["lat"], a["lon"], p["lat"], p["lon"]))
    t12 = math.radians(bearing(a["lat"], a["lon"], b["lat"], b["lon"]))
    xt = math.asin(math.sin(d13) * math.sin(t13 - t12))
    at = math.acos(max(-1, min(1, math.cos(d13) / math.cos(xt))))
    if math.cos(t13 - t12) < 0:
        at = -at
    leg = dist(a["lat"], a["lon"], b["lat"], b["lon"])
    at_nm, xt_nm = at * R_NM, abs(xt) * R_NM
    if at_nm < 0 or at_nm > leg:
        # past an end: use the distance to that end instead
        end = a if at_nm < 0 else b
        return dist(end["lat"], end["lon"], p["lat"], p["lon"]), max(0, min(leg, at_nm))
    return xt_nm, at_nm


def hm(minutes):
    """Whole-minute 'H h MM m' (rounds first, so 59.6 min prints as 1 h 00 m)."""
    h, m = divmod(round(minutes), 60)
    return f"{h} h {m:02d} m"


def main(argv):
    tas = opt(argv, "--tas", 150.0, float)
    burn = opt(argv, "--burn", 12.5, float)
    unit = opt(argv, "--unit", "USG")
    alts = opt(argv, "--alt", None)
    east = opt(argv, "--east", 7500, int)
    west = opt(argv, "--west", 8500, int)
    near = opt(argv, "--near", 10.0, float)
    if len(argv) < 2:
        sys.exit(__doc__)
    stops = [stop(t) for t in argv]
    alts = [int(x) for x in alts.split(",")] if alts else None

    print(f"Nil wind · {tas:g} KTAS · {burn:g} {unit}/hr · climb +1 min / 2,000 ft\n")
    print("| Seg | From → To | Dist (nm) | Track °T | Var | HDG °M | Cruise | Climb | Time | Fuel |")
    print("|----:|-----------|----------:|---------:|----:|-------:|-------:|------:|-----:|-----:|")
    legs, cur, cum = [], None, 0.0
    for i, (a, b) in enumerate(zip(stops, stops[1:])):
        d = dist(a["lat"], a["lon"], b["lat"], b["lon"])
        trk = bearing(a["lat"], a["lon"], b["lat"], b["lon"])
        var = (a["var"] + b["var"]) / 2
        mag = (trk - var) % 360
        alt = alts[i] if alts else (east if mag < 180 else west)
        climb_min = 0
        if not a["wpt"]:
            climb_min = round(max(0, alt - a["elev"]) / 2000)
        t = d / tas * 60 + climb_min
        f = t / 60 * burn
        cum += t
        vs = f"{abs(var):g}{'E' if var >= 0 else 'W'}"
        print(f"| {i+1} | {a['code']} → {b['code']} | {d:.1f} | {trk:03.0f} | {vs} | "
              f"{mag:03.0f} | {alt:,} | +{climb_min} | {t:.0f} m | {f:.1f} |")
        if cur is None:
            cur = dict(frm=a["code"], d=0.0, t=0.0, f=0.0, segs=[])
        cur["d"] += d; cur["t"] += t; cur["f"] += f; cur["segs"].append((a, b))
        if not b["wpt"]:
            cur["to"] = b["code"]
            legs.append(cur)
            cur = None

    print(f"\nLegs (aerodrome to aerodrome):\n")
    print(f"| Leg | From → To | Dist (nm) | Time | Fuel ({unit}) | Cum. time |")
    print("|----:|-----------|----------:|-----:|------:|----------:|")
    cum = 0.0
    for i, L in enumerate(legs):
        cum += L["t"]
        print(f"| {i+1} | {L['frm']} → {L['to']} | {L['d']:.0f} | {L['t']:.0f} m | "
              f"{L['f']:.1f} | {hm(cum)} |")
    tot_d = sum(L["d"] for L in legs)
    tot_f = sum(L["f"] for L in legs)
    print(f"| | **Total** | **{tot_d:.0f}** | **{hm(cum)}** | "
          f"**{tot_f:.1f}** | |")

    print(f"\nERSA aerodromes within {near:g} nm of track that publish ADDITIONAL INFORMATION:\n")
    on_route = {s["code"] for s in stops}
    rows = con.execute("SELECT code, name, lat, lon, additional_info FROM airports "
                       "WHERE additional_info IS NOT NULL AND additional_info != ''").fetchall()
    for i, L in enumerate(legs):
        hits = []
        offset = 0.0
        for a, b in L["segs"]:
            for r in rows:
                if r["code"] in on_route:
                    continue
                xt, at = off_track(a, b, r)
                if xt <= near:
                    hits.append((offset + at, xt, r))
            offset += dist(a["lat"], a["lon"], b["lat"], b["lon"])
        # a field can be near several segments of one leg; keep its closest approach
        closest = {}
        for at, xt, r in hits:
            if r["code"] not in closest or xt < closest[r["code"]][1]:
                closest[r["code"]] = (at, xt, r)
        seen = set(closest)
        print(f"Leg {i+1} {L['frm']} → {L['to']}:")
        for at, xt, r in sorted(closest.values(), key=lambda h: h[0]):
            info = " ".join(r["additional_info"].split())
            print(f"  - {r['code']} {r['name'].title()} — {at:.0f} nm along, {xt:.1f} nm off track")
            print(f"      {info}")
        if not seen:
            print("  (none)")


if __name__ == "__main__":
    main(sys.argv[1:])
