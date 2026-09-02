#!/usr/bin/env python3
"""Generate a route map (GeoJSON) from an ordered list of aerodrome codes.

Emits two artefacts under `flightplans/maps/`:
  <name>.geojson  — GitHub renders this as an interactive Leaflet map.
  <name>.png      — a static coastline map that embeds inline in the plan
                    markdown (`![](maps/<name>.png)`), so the route is visible
                    without opening the geojson. Needs Pillow (in .venv); if
                    Pillow is missing the PNG step is skipped with a warning.

Also prints a Great Circle Mapper URL for a quick browser view.

Each ordered stop is either an aerodrome code (looked up in the FAC DB) or a
free-form visual waypoint written `LABEL@lat,lon` — e.g. `Mandurah@-32.53,115.72`.
Waypoints are drawn as small hollow markers and the legs route through them, so a
coastal track can follow visual features that aren't aerodromes.

Usage:
    .venv/bin/python scripts/route_map.py YBLN-YAYE YBLN YPKG YWBR YAYE
    #                                      ^name    ^ordered aerodrome codes (>=2)
    .venv/bin/python scripts/route_map.py YBLN-YSHK YBLN Mandurah@-32.53,115.72 \
        Fremantle@-32.06,115.75 YGEL YSHK
    #    aerodrome codes and LABEL@lat,lon waypoints can be mixed, in order
"""
import sys, json, math, sqlite3, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "fac_database.sqlite"
OUT = ROOT / "flightplans" / "maps"
COAST = pathlib.Path(__file__).resolve().parent / "au_coast.json"

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row


def great_circle(lat1, lon1, lat2, lon2, n=48):
    """Interpolate n points along the great circle so the leg curves correctly."""
    p1 = (math.radians(lat1), math.radians(lon1))
    p2 = (math.radians(lat2), math.radians(lon2))
    d = 2 * math.asin(math.sqrt(
        math.sin((p2[0]-p1[0])/2)**2
        + math.cos(p1[0])*math.cos(p2[0])*math.sin((p2[1]-p1[1])/2)**2))
    if d == 0:
        return [[lon1, lat1], [lon2, lat2]]
    pts = []
    for i in range(n+1):
        f = i/n
        a = math.sin((1-f)*d)/math.sin(d)
        b = math.sin(f*d)/math.sin(d)
        x = a*math.cos(p1[0])*math.cos(p1[1]) + b*math.cos(p2[0])*math.cos(p2[1])
        y = a*math.cos(p1[0])*math.sin(p1[1]) + b*math.cos(p2[0])*math.sin(p2[1])
        z = a*math.sin(p1[0]) + b*math.sin(p2[0])
        lat = math.degrees(math.atan2(z, math.sqrt(x*x+y*y)))
        lon = math.degrees(math.atan2(y, x))
        pts.append([round(lon, 5), round(lat, 5)])
    return pts


def nm(lat1, lon1, lat2, lon2):
    r = 3440.065  # nautical miles
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2-lat1), math.radians(lon2-lon1)
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return r*2*math.asin(math.sqrt(h))


def render_png(name, pts, total_nm):
    """Draw a static coastline map with the route. Returns the dest path or None."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("! Pillow not installed — skipping PNG (run: .venv/bin/pip install Pillow)")
        return None

    lats = [p["lat"] for p in pts]
    lons = [p["lon"] for p in pts]
    # Pad the route bbox for context; enforce a sensible minimum span.
    pad = max(2.0, (max(lats) - min(lats)) * 0.18, (max(lons) - min(lons)) * 0.18)
    lat0, lat1 = min(lats) - pad, max(lats) + pad
    lon0, lon1 = min(lons) - pad, max(lons) + pad
    mean_lat = (lat0 + lat1) / 2
    kx = math.cos(math.radians(mean_lat))  # lon compression at this latitude

    INNER_W = 1000
    span_x = (lon1 - lon0) * kx
    span_y = (lat1 - lat0)
    INNER_H = max(300, min(1400, round(INNER_W * span_y / span_x)))
    M_L, M_R, M_T, M_B = 20, 20, 54, 20  # margins (top holds the title)
    W, H = INNER_W + M_L + M_R, INNER_H + M_T + M_B

    def xy(lon, lat):
        x = M_L + (lon - lon0) * kx / span_x * INNER_W
        y = M_T + (lat1 - lat) / span_y * INNER_H
        return (x, y)

    img = Image.new("RGB", (W, H), "#eaf2f8")           # sea
    d = ImageDraw.Draw(img)
    d.rectangle([M_L, M_T, M_L + INNER_W, M_T + INNER_H], fill="#f7f4ec", outline="#c9d6e0")

    # Coastline
    try:
        coast = json.loads(COAST.read_text())["lines"]
        for seg in coast:
            d.line([xy(lon, lat) for lon, lat in seg], fill="#9bb0bf", width=1)
    except FileNotFoundError:
        print(f"! {COAST.name} missing — map drawn without coastline")

    # Great-circle legs
    for a, b in zip(pts, pts[1:]):
        gc = great_circle(a["lat"], a["lon"], b["lat"], b["lon"])
        d.line([xy(lon, lat) for lon, lat in gc], fill="#0055aa", width=3)

    def font(sz):
        try:
            return ImageFont.load_default(sz)
        except TypeError:
            return ImageFont.load_default()

    # Markers + labels
    for i, p in enumerate(pts):
        x, y = xy(p["lon"], p["lat"])
        if p.get("is_waypoint"):
            # Small hollow marker for non-aerodrome visual waypoints.
            r = 4
            d.ellipse([x - r, y - r, x + r, y + r],
                      fill="#eaf2f8", outline="#6a7b88", width=2)
            d.text((x + 8, y - 6), p["code"], fill="#4a5a66", font=font(13))
            continue
        end = i in (0, len(pts) - 1)
        r = 6
        d.ellipse([x - r, y - r, x + r, y + r],
                  fill="#1f7a1f" if end else "#b36b00", outline="white", width=2)
        label = f"{p['code']}"
        d.text((x + 9, y - 7), label, fill="#11334d", font=font(16))

    stops = [p["code"] for p in pts if not p.get("is_waypoint")]
    title = f"{'  >  '.join(stops)}    |    {round(total_nm)} nm"
    d.text((M_L, 16), title, fill="#11334d", font=font(20))

    dest = OUT / f"{name}.png"
    img.save(dest)
    return dest


def parse_waypoint(token):
    """Parse a `LABEL@lat,lon` visual waypoint into a pts dict, or None."""
    if "@" not in token:
        return None
    label, _, coords = token.partition("@")
    try:
        lat_s, lon_s = coords.split(",")
        lat, lon = float(lat_s), float(lon_s)
    except ValueError:
        print(f"! {token}: bad waypoint (expected LABEL@lat,lon) — skipping")
        return None
    return {"code": label, "name": label, "lat": lat, "lon": lon,
            "elevation_ft": None, "fuel_types": None, "is_waypoint": True}


def main(argv):
    if len(argv) < 3:
        print(__doc__); return
    name = argv[0]
    pts = []
    for token in argv[1:]:
        wp = parse_waypoint(token)
        if wp is not None:
            pts.append(wp); continue
        code = token.upper()
        r = con.execute("SELECT code,name,state,lat,lon,elevation_ft,fuel_types "
                        "FROM airports WHERE code=?", (code,)).fetchone()
        if r is None or r["lat"] is None:
            print(f"! {code}: not in DB or no coordinates — skipping"); continue
        pts.append({"code": r["code"], "name": r["name"], "lat": r["lat"],
                    "lon": r["lon"], "elevation_ft": r["elevation_ft"],
                    "fuel_types": r["fuel_types"], "is_waypoint": False})
    if len([p for p in pts if not p["is_waypoint"]]) < 2:
        print("Need at least 2 aerodromes with coordinates."); return

    features = []
    for i, r in enumerate(pts):
        if r["is_waypoint"]:
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
                "properties": {
                    "code": r["code"], "name": r["name"], "role": "waypoint",
                    # marker-* keys are honoured by GitHub's GeoJSON renderer
                    "marker-color": "#6a7b88", "marker-symbol": "triangle",
                    "marker-size": "small",
                },
            })
            continue
        role = "departure" if i == 0 else "arrival" if i == len(pts)-1 else "stop"
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
            "properties": {
                "code": r["code"], "name": r["name"], "role": role,
                "fuel": r["fuel_types"] or "none listed",
                "elevation_ft": r["elevation_ft"],
                # marker-* keys are honoured by GitHub's GeoJSON renderer
                "marker-color": "#1f7a1f" if i in (0, len(pts)-1) else "#b36b00",
                "marker-symbol": "airport",
            },
        })
    total = 0.0
    for a, b in zip(pts, pts[1:]):
        leg = nm(a["lat"], a["lon"], b["lat"], b["lon"])
        total += leg
        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString",
                         "coordinates": great_circle(a["lat"], a["lon"], b["lat"], b["lon"])},
            "properties": {"leg": f"{a['code']}→{b['code']}",
                           "distance_nm": round(leg),
                           "stroke": "#0055aa", "stroke-width": 3},
        })
    fc = {"type": "FeatureCollection",
          "properties": {"route": " → ".join(p["code"] for p in pts),
                         "total_nm": round(total)},
          "features": features}

    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / f"{name}.geojson"
    dest.write_text(json.dumps(fc, indent=1))
    png = render_png(name, pts, total)
    gcmap = "https://www.gcmap.com/mapui?P=" + "-".join(p["code"] for p in pts)
    print(f"Wrote {dest.relative_to(ROOT)}  ({round(total)} nm total)")
    if png:
        print(f"Wrote {png.relative_to(ROOT)}")
    print(f"Great Circle Mapper: {gcmap}")


if __name__ == "__main__":
    main(sys.argv[1:])
