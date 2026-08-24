import json, re, pathlib, csv, sqlite3, pdfplumber

CTX = pathlib.Path(__file__).parent
cache = json.loads((CTX/"text_cache.json").read_text())

CORE_RE = re.compile(r'(\d{5,6}(?:\.\d+)?)([NS])(\d{6,7}(?:\.\d+)?)([EW])')
def recon_header(code):
    """Rebuild the header region from individual char positions (for PDFs whose text flow
    is scrambled). Chars are grouped into rows by y and ordered left-to-right within each row."""
    with pdfplumber.open(CTX/f"pdfs/FAC_{code}.pdf") as pdf:
        chars=pdf.pages[0].chars
    rows={}
    for ch in chars:
        if ch['top']>280: continue
        rows.setdefault(round(ch['top']/2),[]).append(ch)
    lines=["".join(c['text'] for c in sorted(r,key=lambda c:c['x0'])) for _,r in sorted(rows.items())]
    return "\n".join(CID_RE.sub("",l) for l in lines)

SECTION_HEADERS = {
 "CHARTS RELATED TO THE AERODROME","ATS AND AERODROME COMMUNICATION FACILITIES",
 "PHYSICAL CHARACTERISTICS","ADDITIONAL INFORMATION","REMARKS",
 "AERODROME AND APPROACH LIGHTING","HANDLING SERVICES AND FACILITIES",
 "AERODROME OBSTACLES","LOCAL TRAFFIC REGULATIONS","PASSENGER FACILITIES",
 "OTHER LIGHTING","FLIGHT PROCEDURES","METEOROLOGICAL INFORMATION PROVIDED",
 "RADIO NAVIGATION AND LANDING AIDS","APRONS AND TAXIWAYS",
 "NOISE ABATEMENT PROCEDURES","RESCUE AND FIREFIGHTING SERVICES",
 "SURFACE MOVEMENT GUIDANCE","ARRESTING GEAR",
}
STATES = {"NSW","VIC","QLD","SA","WA","TAS","NT","ACT"}
SURFACES = ["Grooved","Sealed","Bitumen","Asphalt","Concrete","Gravel","Grass",
            "Clay","Loam","Earth","Dirt","Natural surface","Natural","Coral","Sand"]

def header_of(line):
    """Return the section header this line represents, tolerating margin-noise prefixes/suffixes
    (page numbers, bearings, stray letters/glyphs bleeding in from diagrams)."""
    s = clean(line)
    for h in SECTION_HEADERS:
        if s == h or s.startswith(h) or s.endswith(h):
            return h
    return None

def get_section(text, name):
    """Return lines of a section until the next known section header/footer."""
    lines = text.split("\n"); out=[]; on=False
    for l in lines:
        h = header_of(l)
        if not on:
            if h == name: on=True
            continue
        if h and h != name: break        # next section reached
        s = clean(l)
        if re.match(r'\d{2} \w{3} \d{2} Information may be continued', s): continue
        if re.match(r'AIP Australia .* FAC \w+ - \d+', s): continue
        out.append(s)
    return out

def dms_to_dd(raw, hemi):
    # raw = [D]DMMSS[.s]: seconds = last 2 int digits (+ optional decimal), then MM, then degrees
    ip, fp = (raw.split(".") + [None])[:2]
    sec = int(ip[-2:]) + (float("0."+fp) if fp else 0.0)
    mins = int(ip[-4:-2]); deg = int(ip[:-4])
    dd = deg + mins/60 + sec/3600
    return round(-dd if hemi in ("S","W") else dd, 6)

COORD_RE = re.compile(r'(\d{5,6}(?:\.\d+)?)([NS])\s+(\d{6,7}(?:\.\d+)?)([EW])'
                      r'(?:\s+VAR\s+(\d+)\s+DEG\s+([EW]))?\s*(CERT|UNCR|MIL)?', re.I)
REGION_RE = re.compile(r'\b(NSW|VIC|QLD|SA|WA|TAS|NT|ACT)\s+UTC\s+([+\-][\d:]+)\s+(Y[A-Z0-9]{3})\b')
NAME_RE   = re.compile(r'^(.+?)\s+ELEV\s+(-?\d+)\s*$')
CID_RE    = re.compile(r'\(cid:\d+\)')
def clean(s): return CID_RE.sub("", s).replace("  "," ").strip()
# a runway dimension line starts with a *paired* designator (e.g. 17/35, 01L/19R),
# optionally after list numbering ("1. ") or an "RWY " prefix
DESIG_RE  = re.compile(r'^(?:\d+\.\s*)?(?:RWY\s+)?([0-9]{2}[LRCT]?/[0-9]{2}[LRCT]?)(?![\d/])\s*(.*)$', re.I)

FUELS = [
 ("avgas",  re.compile(r'\bAVGAS\b|\b100\s?LL\b', re.I)),
 ("mogas",  re.compile(r'\bMOGAS\b|\bAVPUL\w*\b', re.I)),  # AVPULP (aviation unleaded) = MOGAS
 ("jet_a1", re.compile(r'\bJET\s*A-?\s*1\b|\bJETA1\b|\bJET\s?A1\b|\bAVTUR\b', re.I)),  # AVTUR = Jet A-1
 ("jet_b",  re.compile(r'\bJET\s*B\b', re.I)),
 ("f34",    re.compile(r'\bF-?34\b', re.I)),
 ("fsii",   re.compile(r'\bFSII\b|JET/FSII', re.I)),
 ("jetplus",re.compile(r'\bJET\s?PLUS\b|\bJETPLUS\b', re.I)),
]
NEG_RE = re.compile(r'\bNIL FUEL\b|\bNO FUEL\b|\bFUEL NOT AVBL\b|\bNil fuel\b', re.I)

# Fuel payment methods, detected within the HANDLING SERVICES section (same scope as fuel).
# App is matched by brand (Fuelcharge/Compac Pay/smartphone) — bare "APP" is ambiguous with
# "approach" (e.g. "245 (APP RQ)"). handling_raw is retained for auditing.
PAY = [
 ("pay_carnet",  "Carnet",     re.compile(r'\bcarnet\b', re.I)),
 ("pay_credit",  "Credit card",re.compile(r'credit\s+card|\bVISA\b|\bMaster\s?card\b|\bV\s+and\s+MC\b|\bV\s*/\s*MC\b|\bV\s*&\s*MC\b|\bAMEX\b|\bDiners\b', re.I)),
 ("pay_eftpos",  "EFTPOS",     re.compile(r'\bEFTPOS\b', re.I)),
 ("pay_cash",    "Cash",       re.compile(r'\bcash\b', re.I)),
 ("pay_account", "Account",    re.compile(r'\baccount\b', re.I)),
 ("pay_app",     "App",        re.compile(r'Fuelcharge|Compac\s?Pay|smartphone|mobile\s+app|phone\s+app', re.I)),
 ("pay_fuelcard","Fuel card",  re.compile(r'fuel\s?card|Fuel2Sky|UVair|Sterling\s+Card|\bWFS\b|World Fuel Services|Multi[- ]?Card', re.I)),
]

# --- Radio frequencies (ATS AND AERODROME COMMUNICATION FACILITIES section) ---
# A frequency line looks like: <SERVICE> <CALLSIGN...> <FREQ> [<FREQ2>] [notes]
# Services seen: FIA CTAF ATIS TWR APP DEP UNICOM SMC(V) ACD ACC AFIS CENTRE APP/DEP ...
FREQ_RE = re.compile(r'\b(1[0-3]\d\.\d{1,3})\b')            # airband/VOR-voice 108-137 MHz
SVC_RE  = re.compile(r'^([A-Z][A-Z/]{1,7})\b')             # leading service token
CTAF_RE = re.compile(r'\bCTAF\b(?:\s*[-/]\s*AFRU)?\s*(?:on\s+)?(1[0-3]\d\.\d{1,3})', re.I)
CLASS_RE= re.compile(r'\bClass\s+([A-G])\b')
GENERIC_TOK={"TOWER","INTL","AIRPORT","AERODROME","FIELD","CENTRE","GROUND","APPROACH"}
def _toks(s): return [w for w in re.split(r'[^A-Za-z]+', (s or "").upper()) if len(w)>=4 and w not in GENERIC_TOK]
def own_tower(name, callsign):
    """True if a TWR callsign belongs to THIS aerodrome (shares a name word), so we
    don't flag offshore helidecks/helipads that merely sit under another field's tower
    (e.g. 'CHARLIE ONE' listing 'KARRATHA TOWER')."""
    nt=_toks(name)
    return any(a[:4]==b[:4] for a in nt for b in _toks(callsign))
def parse_freqs(ats_lines):
    entries=[]
    for l in ats_lines:
        freqs=[f for f in FREQ_RE.findall(l) if 108.0 <= float(f) <= 137.0]
        if not freqs: continue
        m=SVC_RE.match(l)
        if not m: continue
        svc=m.group(1)
        callsign=l[m.end():l.find(freqs[0])].strip(" -")
        entries.append({"service":svc,"callsign":callsign,"freqs":freqs,"raw":l})
    return entries

def surface_of(txt):
    found=[s for s in SURFACES if re.search(r'\b'+re.escape(s)+r'\b', txt, re.I)]
    # collapse "Natural surface"/"Natural" dup
    if "Natural surface" in found and "Natural" in found: found.remove("Natural")
    return ", ".join(dict.fromkeys(found))

def parse(code, text):
    rec={"code":code}
    lines=[clean(l) for l in text.split("\n")]
    head=lines[1:14]
    # name + elevation (line may lack ELEV)
    rec["name"]=None; rec["elevation_ft"]=None
    for l in head:
        m=NAME_RE.match(l)
        if m: rec["name"]=m.group(1).strip(); rec["elevation_ft"]=int(m.group(2)); break
    if not rec["name"]:
        # fallback: first plausible line after the AIP header
        SKIP=("AVFAX","FULL NOTAM","AIP Australia")
        for l in head:
            if not l or any(l.startswith(s) for s in SKIP): continue
            if REGION_RE.search(l) or COORD_RE.search(l) or l in SECTION_HEADERS: continue
            rec["name"]=l.strip(); break
    for l in head:
        m=REGION_RE.search(l)
        if m: rec["state"]=m.group(1); rec["utc_offset"]=m.group(2); break
    # coords may be on one line, or split lat/lon across two lines -> search joined head text
    m=COORD_RE.search(" ".join(head))
    if m:
        rec["lat_raw"]=m.group(1)+m.group(2); rec["lon_raw"]=m.group(3)+m.group(4)
        rec["lat"]=dms_to_dd(m.group(1),m.group(2)); rec["lon"]=dms_to_dd(m.group(3),m.group(4))
        if m.group(5): rec["mag_var"]=f"{m.group(5)} {m.group(6)}"
        rec["certification"]=m.group(7) or ""
    else:
        # fallback: reconstruct scrambled header from word positions
        rh=recon_header(code)
        m=COORD_RE.search(rh) or CORE_RE.search(re.sub(r'\s+','',rh))
        if m:
            rec["lat_raw"]=m.group(1)+m.group(2); rec["lon_raw"]=m.group(3)+m.group(4)
            rec["lat"]=dms_to_dd(m.group(1),m.group(2)); rec["lon"]=dms_to_dd(m.group(3),m.group(4))
            if m.re is COORD_RE and m.group(5): rec["mag_var"]=f"{m.group(5)} {m.group(6)}"
            if m.re is COORD_RE: rec["certification"]=m.group(7) or ""
    # fuel
    hs=get_section(text,"HANDLING SERVICES AND FACILITIES")
    hs_txt="\n".join(hs).strip()
    rec["fuel_source"]="handling_section"
    if not hs_txt:
        # No handling section parsed (rare scrambled PDFs): recover fuel from lines that
        # pair a fuel token with a refuelling-context word, to avoid false positives.
        ctx=re.compile(r'\bFUEL\b|REFUEL|BOWSER|SELF.?SERVE|CARNET|TANKER|\bIOR\b|AIR ?BP|VIVA|MOBIL|FUELCHARGE|\bWFS\b', re.I)
        fl=[l for l in lines if ctx.search(l) and any(rx.search(l) for _,rx in FUELS)]
        if fl:
            hs_txt="\n".join(fl); rec["fuel_source"]="line_scan"
    rec["handling_raw"]=hs_txt
    fuel_types=[]
    for key,rx in FUELS:
        present=bool(rx.search(hs_txt))
        rec[key]=present
        if present: fuel_types.append(key.upper().replace("_"," "))
    rec["fuel_types"]=", ".join(fuel_types)
    rec["has_fuel"]=bool(fuel_types)
    rec["fuel_caveat"]=bool(NEG_RE.search(hs_txt)) if hs_txt else False
    # fuel payment methods (scoped to the handling section, like fuel)
    pay_labels=[]
    for key,label,rx in PAY:
        present=bool(rx.search(hs_txt))
        rec[key]=present
        if present: pay_labels.append(label)
    rec["payment_methods"]=", ".join(pay_labels)
    # runways: within PHYSICAL CHARACTERISTICS, group lines by paired runway designator
    # (e.g. 17/35). Handles GA ("RWY 17/35 1,000M. Grass"), certified table
    # ("05/23 043 56a PCR .../... Sealed. WID 45"), and text/list styles.
    pc=get_section(text,"PHYSICAL CHARACTERISTICS")
    order=[]; group={}; cur=None
    for l in pc:
        m=DESIG_RE.match(l.strip())
        if m:
            cur=m.group(1)
            if cur not in group: group[cur]=[]; order.append(cur)
            group[cur].append(m.group(2))
        elif cur is not None:
            group[cur].append(l.strip())
    rwys=[]
    for d in order:
        blob=" ".join(group[d])
        lens=[int(x.replace(",","")) for x in re.findall(r'LEN\s+([\d,]+)\s*M\b', blob, re.I)]
        if not lens:
            lens=[int(x.replace(",","")) for x in re.findall(r'([\d,]+)\s*M\b', group[d][0])
                  if int(x.replace(",",""))>=100]
        wid=re.search(r'\bWID\s+(\d+)', blob)
        pcr=re.search(r'\b(PC[RN][ /]\S+)', blob)
        rwys.append({"designator":d,"length_m":max(lens) if lens else None,
                     "width_m":int(wid.group(1)) if wid else None,
                     "surface":surface_of(blob),
                     "strength":pcr.group(1) if pcr else None,
                     "raw":(d+" "+group[d][0]).strip()})
    # fallback: a runway described without a paired designator (single unmarked strip)
    if not rwys and pc:
        blob=" ".join(pc)
        if not re.search(r'HELIPAD|\bHLS\b|alighting area|FATO', blob, re.I):
            lens=[int(x.replace(",","")) for x in re.findall(r'([\d,]+)\s*M\b', blob)
                  if int(x.replace(",",""))>=100]
            surf=surface_of(blob)
            if lens or surf:
                wid=re.search(r'\bWID\s+(\d+)', blob)
                rwys.append({"designator":"(unnamed)","length_m":max(lens) if lens else None,
                             "width_m":int(wid.group(1)) if wid else None,"surface":surf,
                             "strength":None,"raw":blob[:120]})
    # radio frequencies + controlled status
    ats=get_section(text,"ATS AND AERODROME COMMUNICATION FACILITIES")
    freqs=parse_freqs(ats)
    rec["frequencies_list"]=freqs
    rec["frequencies"]="; ".join(f"{e['service']} {'/'.join(e['freqs'])}" for e in freqs)
    rec["controlled"]=any(e["service"].startswith("TWR") and own_tower(rec.get("name"), e["callsign"])
                          for e in freqs)
    classes=sorted(set(CLASS_RE.findall("\n".join(ats))))
    rec["airspace_class"]=", ".join(classes)
    # CTAF (Common Traffic Advisory Frequency) can appear outside the ATS section too
    cm=CTAF_RE.search(text)
    ctaf=cm.group(1) if cm else next((e["freqs"][0] for e in freqs if e["service"]=="CTAF"), None)
    rec["ctaf"]=ctaf
    rec["runways"]=rwys
    rec["runway_count"]=len(rwys)
    rec["runway_summary"]="; ".join(
        f"{r['designator']} " + (f"{r['length_m']}M " if r['length_m'] else "") + (r['surface'] or "")
        for r in rwys).strip()
    return rec

records=[parse(c,t) for c,t in sorted(cache.items())]

# ---- JSON ----
(CTX/"fac_database.json").write_text(json.dumps(records,indent=2))

# ---- CSV (flat, one row per airport) ----
cols=["code","name","state","lat","lon","lat_raw","lon_raw","elevation_ft","mag_var",
      "certification","utc_offset","has_fuel","fuel_types","avgas","mogas",
      "jet_a1","jet_b","f34","fsii","jetplus","fuel_caveat","fuel_source",
      "payment_methods","pay_carnet","pay_credit","pay_eftpos","pay_cash",
      "pay_account","pay_app","pay_fuelcard",
      "controlled","airspace_class","ctaf","frequencies",
      "runway_count","runway_summary","handling_raw"]
BOOLCOLS=("has_fuel","avgas","mogas","jet_a1","jet_b","f34","fsii","jetplus","fuel_caveat",
          "pay_carnet","pay_credit","pay_eftpos","pay_cash","pay_account","pay_app","pay_fuelcard",
          "controlled")
with open(CTX/"fac_database.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore"); w.writeheader()
    for r in records: w.writerow(r)

# ---- SQLite ----
db=CTX/"fac_database.sqlite"
if db.exists(): db.unlink()
con=sqlite3.connect(db); cur=con.cursor()
cur.execute("""CREATE TABLE airports(code TEXT PRIMARY KEY,name TEXT,state TEXT,lat REAL,lon REAL,
  lat_raw TEXT,lon_raw TEXT,elevation_ft INT,mag_var TEXT,certification TEXT,utc_offset TEXT,
  has_fuel INT,fuel_types TEXT,avgas INT,mogas INT,jet_a1 INT,jet_b INT,
  f34 INT,fsii INT,jetplus INT,fuel_caveat INT,fuel_source TEXT,
  payment_methods TEXT,pay_carnet INT,pay_credit INT,pay_eftpos INT,pay_cash INT,
  pay_account INT,pay_app INT,pay_fuelcard INT,
  controlled INT,airspace_class TEXT,ctaf TEXT,frequencies TEXT,
  runway_count INT,runway_summary TEXT,handling_raw TEXT)""")
cur.execute("""CREATE TABLE runways(code TEXT,designator TEXT,length_m INT,width_m INT,
  surface TEXT,strength TEXT,raw TEXT)""")
cur.execute("""CREATE TABLE frequencies(code TEXT,service TEXT,callsign TEXT,freq TEXT,raw TEXT)""")
for r in records:
    cur.execute("INSERT INTO airports VALUES(%s)"%",".join("?"*len(cols)),
                [ (1 if r.get(c) else 0) if c in BOOLCOLS else r.get(c) for c in cols])
    for rw in r["runways"]:
        cur.execute("INSERT INTO runways VALUES(?,?,?,?,?,?,?)",
                    (r["code"],rw["designator"],rw["length_m"],rw["width_m"],
                     rw["surface"],rw.get("strength"),rw["raw"]))
    for e in r["frequencies_list"]:
        for f in e["freqs"]:
            cur.execute("INSERT INTO frequencies VALUES(?,?,?,?,?)",
                        (r["code"],e["service"],e["callsign"],f,e["raw"]))
con.commit(); con.close()
print("Wrote fac_database.json / .csv / .sqlite with",len(records),"airports")
