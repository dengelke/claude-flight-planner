# Plan 2 — Kalgoorlie → Busselton return via White Gum (1-day)

**Route (1-day, White Gum fuel · Northam YNTM the alternate):** **YPKG → YWGM → YBLN**
· **YPKG→YWGM 241 nm (~253°T)** then **YWGM→YBLN 134 nm (~216°T)**
**Aircraft:** [Tecnam P2002 Sierra](../../aircraft/P2002.md) · Rotax 912 ULS · **empty 355 kg (this airframe)** · MTOW **600 kg** · 99 L usable
**Planning basis:** No wind · Cruise 100 KTAS · Burn **20 L/hr** (conservative; POH ~15–18) · **final reserve 10 L (30 min, day VFR)**
**Loading:** occupants **170 kg** + cargo **5–10 kg** (staying light) · **fuel capped ~90 L, NOT full** — full fuel busts MTOW (see W&B)
**Data source:** ERSA FAC/RDS effective **09 JUL 2026** — verify against current ERSA + NOTAMs on the day.

> ✈️ **Bottom line:** The straight run home — **375 nm in two short legs**, split at **White Gum** for a Mogas top-up, with
> **Northam (YNTM, 19 nm) as the alternate** if the bowser's dry. **In this 355 kg-empty airframe you can't carry full
> fuel:** 355 kg empty + 170 kg pax + even 5 kg cargo already needs fuel held to ~97 L, and with 10 kg cargo to ~90 L, to
> stay under the 600 kg MTOW. That's no hardship — the legs only need ~60 L, so **cap the fill at ~90 L and both legs still
> land with big margins** (nil-wind ~38 L at White Gum, ~59 L at Busselton). CoG sits mid-envelope throughout. Only the
> Kalgoorlie leg runs on AVGAS; the leg home from White Gum is Mogas.

---

## Route Summary

| Leg | From → To | Distance | Track | Time @ 100 kt | Trip fuel (L) |
|-----|-----------|---------:|------:|--------------:|--------------:|
| 1 | YPKG → YWGM | 241 nm | ~253°T | 2 h 24 m | ~50 |
| 2 | YWGM → YBLN | 134 nm | ~216°T | 1 h 20 m | ~29 |
| **Total** | **YPKG → YBLN** | **375 nm** | | **~3 h 44 m** | |

- One WA day (AWST) — no timezone change. Longest leg 241 nm (~2.4 h); ~90 L covers it with room to spare (~60 L needed).

## Fuel plan — cap the fill at ~90 L, top up Mogas at White Gum (Northam the alternate)

| Departure | Fuel type | Depart | Leg | Land with (nil wind) | Over 30-min reserve (10 L) |
|-----------|-----------|-------:|-----|---------------------:|---------------------------:|
| YPKG | AVGAS 100LL | **~90 L** | → YWGM 241 nm | **~38 L** | **+28 L** |
| YWGM | **Mogas (bowser)** | **~90 L** | → YBLN 134 nm | ~59 L | +49 L |

- **Don't fill to full** — in the 355 kg airframe, ~90 L (10 kg cargo) / ~97 L (5 kg cargo) is the MTOW ceiling; ~90 L is
  plenty for these legs, so filling to it keeps a comfortable margin under 600 kg.
- **Wind is not a range issue** — even a 25 kt headwind on the 241 nm leg (~66 L) still lands White Gum with ~24 L from 90 L.
- **⛽ Alternate if White Gum is dry → Northam (YNTM), 19 nm WNW** — sealed 14/32 (1248 m), **AVGAS H24 credit-card
  bowser**, no PPR. You reach White Gum with ~38 L, so the diversion costs ~4 L. AVGAS not Mogas, but the 912 runs on it.
- **Fuel type:** only the Kalgoorlie→White Gum leg is AVGAS; the leg home is Mogas (the 912's preferred fuel).

## Weight & Balance — 355 kg-empty airframe, 170 kg pax, light cargo (fuel MTOW-limited)

Recommended loadout — **cargo 10 kg, fill to ~90 L** (not full):

| Item | Mass (kg) | Arm (in) | Moment (kg·in) |
|------|----------:|---------:|---------------:|
| Empty (this airframe) | 355 | ~67.8 | 24,069 |
| Occupants | 170 | 70.86 | 12,046 |
| Cargo | 10 | 86.61 | 866 |
| Fuel (~90 L) | 65 | 60.23 | 3,915 |
| **Takeoff** | **600** | **68.2** | **40,896** |

- **Full fuel does NOT fit.** With 355 kg empty + 170 kg pax the MTOW ceiling on fuel is **~97 L at 5 kg cargo / ~90 L at
  10 kg cargo** — full 99 L would put you 1–6 kg over 600 kg. Cap the fill accordingly.
- **~90 L is well above what the legs need** (~60 L for the 241 nm leg incl. reserve), so hold a little below the ceiling
  (say **85–88 L**) for a few kg of MTOW margin — you'll still land Busselton with ~55 L. Do the W&B on the real empty weight.
- **CoG stays mid-envelope** — ~68.1–68.4 in across the fuel range, comfortably inside 63.4–70.4 in ✓ (fuel arm is forward,
  so lighter fuel nudges CoG only slightly aft).

## Route Map

![Kalgoorlie → White Gum → Busselton](map.png)

- 🗺️ **[Interactive: `map.geojson`](map.geojson)** · 🌐 **[Great Circle Mapper](https://www.gcmap.com/mapui?P=YPKG-YWGM-YBLN)**
- Regenerate: `.venv/bin/python scripts/route_map.py map YPKG YWGM YBLN --out flightplans/P2002/YPKG-YBLN`

## Density altitude
- **Kalgoorlie 1203 ft, White Gum 1000 ft** — warm-day density altitude climbs well above these; the 98 hp Rotax loses
  climb and lengthens the roll. **Check TODR**, prefer early-morning departures near MTOW.

---

## Aerodromes

### [YPKG](../../aerodromes/YPKG.md) — Kalgoorlie-Boulder (WA) — DEPART
- -30.789, 121.462 · Elev 1203 ft · AVGAS + Jet A1 + F34 (**no Mogas**) · CTAF/UNICOM 126.6 · RWY 11/29 2000 m sealed; 18/36 1200 m · **H24 AVGAS card bowser** (Carnet/credit)

### [YWGM](../../aerodromes/YWGM.md) — White Gum (WA) — FUEL STOP (Mogas)
- -31.867, 116.939 · Elev 1000 ft · **UNCR, private — PPR** · CTAF 126.7 · **MOGAS bowser** (TWY east of RWY 14/32)
- **RWY 14/32 1400 m SAND; 09/27 750 m gravel** (ample) · confirm PPR + Mogas ahead.

### [YNTM](../../aerodromes/YNTM.md) — Northam (WA) — FUEL ALTERNATE (if White Gum dry)
- -31.626, 116.684 · Elev 500 ft · **UNCR** · CTAF 124.2 · **AVGAS H24 credit-card bowser** (no Jet A1) · RWY 14/32 1248 m sealed · **~19 nm WNW of White Gum**

### [YBLN](../../aerodromes/YBLN.md) — Busselton (WA) — HOME BASE
- -33.687, 115.400 · Elev 56 ft · AVGAS + Jet A1 (+ **aeroclub Mogas**) · CTAF 127.0 · RWY 03/21 grooved, 2460 m, 45 m wide

## Pre-Flight Checks
- [ ] **PPR + Mogas confirmed at White Gum**; if unavailable, divert to **Northam (YNTM, ~19 nm)**.
- [ ] **W&B** against real empty weight (355 kg) — **do NOT fill to full**; cap at ~90 L (10 kg cargo) / ~97 L (5 kg), hold ~85–88 L for MTOW margin.
- [ ] Kalgoorlie AVGAS to **~90 L** (not full) before departure; Carnet/credit carried. White Gum Mogas to the same ~90 L cap for the leg home.
- [ ] Density altitude / TODR for Kalgoorlie (1203 ft) & White Gum (1000 ft); cool-of-day departures near MTOW.
- [ ] ARFOR/TAFs + NOTAMs for YPKG, YWGM, YNTM, YBLN; crosswind ≤ 22 kt demonstrated; water + PLB on the inland legs.

---
*Planning only. Cross-check current ERSA, NOTAMs, weather, W&B and the P2002 Flight Manual before flight.*
