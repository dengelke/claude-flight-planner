import pdfplumber, pathlib, json
ctx = pathlib.Path(__file__).resolve().parent.parent / "data"
pdfs = sorted((ctx/"pdfs").glob("FAC_*.pdf"))
cache = {}
for i,p in enumerate(pdfs,1):
    code = p.stem.replace("FAC_","")
    try:
        with pdfplumber.open(p) as pdf:
            txt = "\n".join((pg.extract_text() or "") for pg in pdf.pages)
    except Exception as e:
        txt = f"__ERROR__ {e}"
    cache[code] = txt
    if i%100==0: print(f"  {i}/{len(pdfs)}", flush=True)
(ctx/"text_cache.json").write_text(json.dumps(cache))
print("Extracted", len(cache), "->", ctx/"text_cache.json")
