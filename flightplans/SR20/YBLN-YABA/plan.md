# Flight Plan — YBLN ⇄ YABA return (Cirrus SR20 G1, AVGAS)

**Route:** Busselton (YBLN) ⇄ Albany (YABA) — **return, weekend away** · each leg **141 nm**, track out **~123°T / ~125°M**, back **~303°T / ~305°M**
**Aircraft:** [Cirrus SR20 G1 (s/n 1312)](../../aircraft/SR20.md) · Empty **973 kg** · MTOW **1361 kg** · Fuel **AVGAS**
**Planning basis:** No wind · Cruise 150 KTAS · Burn **12.5 USG/hr** (safe; ~11.6 book) · reserve 10.1 USG (45 min)
**Loading:** 2 occupants **150 kg** + baggage **10 kg** + equipment **5 kg** = **165 kg** · **departing Busselton with FULL fuel (56 USG)**
**Data source:** ERSA FAC/RDS effective **09 JUL 2026** — verify against current ERSA + NOTAMs on the day.

> ✈️ **Bottom line:** the SR20 does the **whole return on one Busselton fill — no uplift at Albany required.**
> Round trip burns ~26 of 56 USG; you land back at Busselton with **~30 USG** (~3× the 45-min reserve). Legs are
> ~2 days apart so wind won't cancel out-and-back — each leg is checked on its own below, and the SR20 clears
> reserve on both regardless of wind.

---

## Route Summary (return)

| Leg | Day | From → To | Distance | Time @ 150 kt | Trip fuel (USG) |
|-----|-----|-----------|---------:|--------------:|----------------:|
| 1 (out) | Sat | YBLN → YABA | 141 nm | 0 h 56 m | ~13 (incl. taxi) |
| 2 (back) | Sun/Mon | YABA → YBLN | 141 nm | 0 h 56 m | ~13 (incl. taxi) |
| **Round trip** | | | **282 nm** | **~1 h 53 m** | **~26 of 56** |

- Full tank ≈ **4 h 29 m / ~600 nm** endurance — the round trip uses under half of it.
- All in WA (AWST) — no timezone change; each leg ~1 h, easy inside any daylight window.

## Fuel plan — one fill does the weekend

- **Depart Busselton full (56 USG).** Arrive Albany with **~43 USG**.
- **Return needs no refuel:** depart Albany on that ~43 USG, land Busselton with **~30 USG** (reserve is 10.1).
- **Optional top-up at Albany** only if you want to come home full or the return-day forecast is nasty — Air BP
  Carnet, H24 bowser. Not required for fuel; see the return-leg margin table.

### Return leg (YABA → YBLN) — fuel on landing at Busselton, departing Albany with ~43 USG

| Wind on return | Groundspeed | Land YBLN with | Over 45-min reserve |
|----------------|------------:|---------------:|--------------------:|
| Still air | 150 kt | ~30 USG | **+20 USG (~1.6 h)** |
| 15 kt headwind | 135 kt | ~29 USG | +19 USG |
| 25 kt headwind | 125 kt | ~28 USG | +18 USG |

The SR20 is effectively wind-immune over 141 nm — no scenario needs Albany fuel.

## Route Map

![YBLN ⇄ YABA route over the SW WA coast](map.png)

- 🗺️ **[Interactive version: `map.geojson`](map.geojson)** — GitHub renders it as a pan/zoom map (drawn one direction; the return retraces it).
- 🌐 **[Great Circle Mapper](https://www.gcmap.com/mapui?P=YBLN-YABA)**
- Regenerate: `.venv/bin/python scripts/route_map.py map YBLN YABA --out flightplans/SR20/YBLN-YABA`

---

## Weight & Balance

**Outbound (full fuel + 165 kg) is the heavy case:**

| Item | Mass | Arm (FS in) | Moment |
|------|-----:|------------:|-------:|
| Empty (s/n 1312) | 973 kg (2145 lb) | ~140.5 *(from your W&B record)* | 301,373 |
| Front seats (2 occ) | 150 kg (331 lb) | 143.5 | 47,499 |
| Baggage + equipment | 15 kg (33 lb) | 208.0 | 6,864 |
| **Zero-fuel weight** | **1138 kg (2509 lb)** | | |
| Full usable fuel | 152 kg (336 lb / 56 USG) | 153.95 | 51,727 |
| **Ramp / takeoff** | **~1290 kg (2845 lb)** | **~143.2** | 407,463 |

- **Takeoff 2845 lb < 3000 MTOW ✓** (155 lb / 70 kg margin) · **baggage 33 lb < 130 ✓** · **landing < 2900 ✓**
- **CG ~143.2 in — in envelope but near the forward limit** (fwd limit ≈ FS 142.5 at this weight). Both occupants
  up front pushes CG forward; ⚠️ **confirm against the aircraft's actual empty arm** (est. 139.5–141.0), and stow
  the equipment in the baggage bay (arm 208) to help hold CG aft.
- **Return leg is lighter** (departs Albany with ~43 USG, not full) → further inside MTOW; if you top up to full at
  Albany the return W&B equals the outbound case above (still fine).

---

## Aerodromes

### [YBLN](../../aerodromes/YBLN.md) — Busselton (WA) — HOME BASE
- Position: -33.687, 115.400 · Elev 56 ft · AVGAS + Jet A1 · CTAF 127.0 · RWY 03/21 TORA 2460 m, grooved, 45 m wide

### [YABA](../../aerodromes/YABA.md) — Albany (WA) — WEEKEND DESTINATION
- Position: -34.943, 117.809 · Elev 233 ft · AVGAS + Jet A1 · CTAF 127.85
- RWY 14/32: TORA 1800 m · RWY 05/23: TORA 1096 m (both 30 m wide)

## Fuel & Payment

| Field | AVGAS provider | Card needed | Notes |
|-------|---------------|-------------|-------|
| YBLN Busselton | Air BP / City | ⚠️ **Air BP Carnet ONLY** | Phone AD OPR — fill full before departure |
| YABA Albany | Air BP | **Air BP Carnet** (H24 bowser) | Only needed for an optional top-up |

**Carry an Air BP Carnet** — covers both ends.

## Pre-Flight Checks
- [ ] W&B/CG confirmed against **actual empty CG** (CG near forward limit with both occupants up front) — outbound is the heavy case.
- [ ] **Full fuel at Busselton** covers the whole return; confirm ~43 USG on arrival Albany before deciding on an (optional) top-up.
- [ ] ARFOR + TAFs + NOTAMs for YBLN, YABA on **both** days — legs are ~2 days apart, so check the return-day wx separately.
- [ ] Air BP Carnet carried (both fields carnet-only).
- [ ] Current ERSA/AIP; charts + GPS current; SARTIME/flight notes as desired for each leg.

---
*Planning only. Cross-check current ERSA, NOTAMs, weather, W&B and the SR20 POH before flight.*
