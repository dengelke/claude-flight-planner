import concurrent.futures as cf, pathlib, requests, sys

BASE = "https://www.airservicesaustralia.com/aip/pending/ersa/FAC_{}_09JUL2026.pdf"
ctx = pathlib.Path(__file__).resolve().parent.parent / "data"
codes = [c.strip() for c in (ctx/"codes.txt").read_text().split() if c.strip()]
out = ctx/"pdfs"; out.mkdir(exist_ok=True)
sess = requests.Session()
sess.headers["User-Agent"] = "Mozilla/5.0 (research; FAC parser)"

def get(code):
    f = out/f"FAC_{code}.pdf"
    if f.exists() and f.stat().st_size > 0:
        return (code, "cached")
    try:
        r = sess.get(BASE.format(code), timeout=60)
        if r.status_code == 200 and r.content[:4] == b"%PDF":
            f.write_bytes(r.content); return (code, "ok")
        return (code, f"HTTP{r.status_code}")
    except Exception as e:
        return (code, f"ERR:{e}")

ok=cached=0; errs=[]
with cf.ThreadPoolExecutor(max_workers=10) as ex:
    for i,(code,st) in enumerate(ex.map(get, codes),1):
        if st=="ok": ok+=1
        elif st=="cached": cached+=1
        else: errs.append((code,st))
        if i%100==0: print(f"  {i}/{len(codes)}...", flush=True)
print(f"\nDownloaded {ok}, cached {cached}, errors {len(errs)} of {len(codes)}")
for c,s in errs: print("  ERR", c, s)
(ctx/"download_errors.log").write_text("\n".join(f"{c} {s}" for c,s in errs))
