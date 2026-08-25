#!/usr/bin/env python3
"""Parse RDS (Runway Distance Supplement) PDFs into structured per-runway-end
declared distances, and merge them into the FAC database (sqlite/json/csv).

Each RDS row gives, per runway END (direction):
  RWY, CN (classification number), TORA, TODA, ASDA, LDA  (metres)
plus RWY WID (pavement width, m) and slope, taken from the pair's summary line.
Surface type is NOT in the RDS -- it comes from the FAC (runways table).
"""
import pdfplumber, pathlib, re, json, csv, sqlite3, sys

CTX = pathlib.Path(__file__).resolve().parent.parent / "data"
RDS_DIR = CTX/"rds"
CACHE = CTX/"rds_text_cache.json"

# data row: <RWY> (<CN>) <TORA> (ft) <TODA> (ft) [(<grad%>)] <ASDA> (ft) <LDA> (ft)
ROW = re.compile(
    r'^(\d{2}[LRCT]?)\s+\(([^)]+)\)\s+'  # CN: a number, or "MIL" at military bases
    r'(\d+)\s+\(\d+\)\s+'                 # TORA
    r'(\d+)\s+\(\d+\)(?:\s+(?:\([\d.]+%\)|NIL))?\s+'  # TODA (+ optional grad% or NIL)
    r'(\d+)\s+\(\d+\)\s+'                 # ASDA
    r'(\d+)\s+\(\d+\)')                   # LDA
WID = re.compile(r'RWY WID\s+(\d+)')
SLOPE = re.compile(r'Slope\s+(.+?)\.(?!\d)')  # end at a period NOT inside a decimal

def load_text():
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    cache={}
    files=sorted(RDS_DIR.glob("RDS_*.pdf"))
    for i,p in enumerate(files,1):
        code=p.stem.replace("RDS_","")
        with pdfplumber.open(p) as pdf:
            cache[code]="\n".join((pg.extract_text() or "") for pg in pdf.pages)
        if i%100==0: print(f"  extract {i}/{len(files)}",flush=True)
    CACHE.write_text(json.dumps(cache))
    return cache

def parse_one(code, text):
    ends=[]; pending=[]
    for line in text.split("\n"):
        s=line.strip()
        m=ROW.match(s)
        if m:
            rwy,cn,tora,toda,asda,lda=m.groups()
            d={"code":code,"rwy":rwy,"cn":int(cn) if cn.isdigit() else cn,
               "tora_m":int(tora),"toda_m":int(toda),
               "asda_m":int(asda),"lda_m":int(lda),
               "width_m":None,"slope":None}
            ends.append(d); pending.append(d)
            continue
        w=WID.search(s)
        if w:
            sl=SLOPE.search(s)
            for d in pending:
                d["width_m"]=int(w.group(1))
                if sl: d["slope"]=sl.group(1).strip()
            pending=[]
    return ends

def main():
    text=load_text()
    all_ends=[]
    for code in sorted(text):
        all_ends.extend(parse_one(code, text[code]))
    codes_with=len({e["code"] for e in all_ends})
    print(f"Parsed {len(all_ends)} runway ends across {codes_with} aerodromes")

    # JSON
    (CTX/"rds_database.json").write_text(json.dumps(all_ends,indent=1))
    # CSV
    cols=["code","rwy","cn","tora_m","toda_m","asda_m","lda_m","width_m","slope"]
    with open(CTX/"rds_database.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols); w.writeheader()
        for e in all_ends: w.writerow(e)
    # merge into existing sqlite DB
    db=CTX/"fac_database.sqlite"
    if db.exists():
        con=sqlite3.connect(db); cur=con.cursor()
        cur.execute("DROP TABLE IF EXISTS rds")
        cur.execute("""CREATE TABLE rds(code TEXT,rwy TEXT,cn TEXT,tora_m INT,
          toda_m INT,asda_m INT,lda_m INT,width_m INT,slope TEXT)""")
        cur.executemany("INSERT INTO rds VALUES(?,?,?,?,?,?,?,?,?)",
            [tuple(e[c] for c in cols) for e in all_ends])
        con.commit(); con.close()
        print(f"Merged 'rds' table into {db.name}")
    else:
        print("WARN: fac_database.sqlite not found; run parse_fac.py first")

if __name__=="__main__":
    if "--refresh" in sys.argv and CACHE.exists(): CACHE.unlink()
    main()
