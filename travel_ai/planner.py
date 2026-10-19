"""
planner.py - assembles a full itinerary from three decision-makers ("policies"):
  * attraction scorer   -> which attractions match the user's message
  * slot chooser        -> which start time (slot) to pick for each attraction, non-overlapping
  * hotel scorer        -> which accommodation to stay at for each day's area

The same assembly code is used with the ExpertPolicy (to produce the training samples)
and the RFPolicy (the trained Random-Forest models) so the models learn exactly the task
they are later asked to do.
"""
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from common import (CONFIG, haversine, transfer_minutes, fmt_min, to_minutes, slot_candidates,
                    fmt_phone, MEAL_PLANS)


def _name_key(n):
    import re
    return frozenset(w for w in re.findall(r"[a-z]+", n.lower()) if w not in {"the", "and", "of", "national", "park", "or", "sri", "lanka"})


def _attr_table(a):
    g = a.groupby("AttrID").agg(Name=("Attraction Name", "first"), Lat=("Lat", "first"), Lon=("Lon", "first"),
                                Destination=("Destination", "first"), Area=("Area", "first"),
                                Rating=("Rating", "max"))
    return g


class Planner:
    def __init__(self, a, h, policy):
        self.a, self.h, self.p = a, h, policy
        self.at = _attr_table(a)
        self.coh = CONFIG.get("route_coherence_km", 150)
        # attractions listed twice under slightly different names (e.g. "Horton Plains" / "Horton plains national park")
        keys = {i: _name_key(n) for i, n in self.at["Name"].items()}
        self.dupes = {i: set() for i in keys}
        ids = list(keys)
        for x in range(len(ids)):
            for y in range(x + 1, len(ids)):
                i, j = ids[x], ids[y]
                ki, kj = keys[i], keys[j]
                if ki and kj and (ki <= kj or kj <= ki) and haversine(self.at.at[i, "Lat"], self.at.at[i, "Lon"],
                                                                     self.at.at[j, "Lat"], self.at.at[j, "Lon"]) <= 40:
                    self.dupes[i].add(j); self.dupes[j].add(i)

    # ------------------------------------------------------------------ days
    def _pick_day_pool(self, attr_score, used, prev_ll):
        cand = self.at[~self.at.index.isin(used)].copy()
        if cand.empty:
            return None, []
        cand["score"] = cand.index.map(lambda i: attr_score.get(i, 0.0))
        # relevance first: among the strongest remaining matches, go to the one nearest the previous day
        top = cand[cand["score"] >= CONFIG.get("anchor_score_ratio", 0.8) * cand["score"].max()]
        if prev_ll is not None and len(top) > 1:
            d = top.apply(lambda r: haversine(prev_ll[0], prev_ll[1], r.Lat, r.Lon), axis=1)
            anchor = (top["score"] * np.exp(-d / self.coh)).idxmax()
        else:
            anchor = top["score"].idxmax()
        al = (cand.at[anchor, "Lat"], cand.at[anchor, "Lon"])
        cand["dist"] = cand.apply(lambda r: haversine(al[0], al[1], r.Lat, r.Lon), axis=1)
        pool = cand[cand["dist"] <= CONFIG["day_pool_radius_km"]].sort_values("score", ascending=False).head(8)
        return al, pool.index.tolist()

    def _schedule_day(self, pool_ids, ctx):
        rows = self.a[self.a["AttrID"].isin(pool_ids)]
        chosen, cursor, last_ll = [], None, None
        while True:
            cands = slot_candidates(rows, chosen, cursor, last_ll)
            if not cands:
                break
            k = self.p.choose_slot(cands, chosen, cursor, ctx, force=(len(chosen) == 0))
            if k is None:
                break
            r, km = cands[k]
            chosen.append(r)
            rows = rows[~rows["AttrID"].isin(self.dupes.get(r["AttrID"], set()))]
            cursor, last_ll = r["EndMin"], (r["Lat"], r["Lon"])
        return chosen

    # ------------------------------------------------------------------ main
    def plan(self, user):
        arr = user["arrival"]; dep = user["departure"]
        if dep <= arr:
            raise ValueError("Departure must be after arrival.")
        nights = (dep.date() - arr.date()).days
        visit_dates = [arr.date() + timedelta(days=i) for i in range(1, nights)]
        ctx = self.p.attraction_context(user["message"], arr.month)
        attr_score = ctx["attr_score"]

        # 1) choose + schedule attractions for each visit day
        used, days, prev, tries = set(), [], None, 0
        while len(days) < len(visit_dates) and tries < 3 * len(visit_dates) + 3:
            tries += 1
            al, pool = self._pick_day_pool(attr_score, used, prev)
            if not pool:
                break
            chosen = self._schedule_day(pool, ctx)
            if not chosen:
                used.update(pool[:1]); continue
            for c in chosen:
                used.add(c["AttrID"]); used.update(self.dupes.get(c["AttrID"], ()))
            lat = float(np.mean([c["Lat"] for c in chosen])); lon = float(np.mean([c["Lon"] for c in chosen]))
            days.append({"visits": chosen, "ll": (lat, lon), "pool": pool})
            prev = (lat, lon)
        # order days geographically starting from the airport (nearest-neighbour route)
        ap = self._airport_ll()
        ordered, cur = [], ap
        while days:
            j = int(np.argmin([haversine(cur[0], cur[1], d["ll"][0], d["ll"][1]) for d in days]))
            ordered.append(days.pop(j)); cur = ordered[-1]["ll"]
        days = ordered
        for d, dt in zip(days, visit_dates):
            d["date"] = dt

        # 2) accommodation for each day's area
        budget_pn = user["budget"] / max(nights, 1)
        hotel_for_day, prev_h = [], None
        for d in days:
            if prev_h is not None and haversine(prev_h["Lat"], prev_h["Lon"], *d["ll"]) <= CONFIG.get("hotel_reuse_km", 25):
                hotel_for_day.append(prev_h); continue
            hs = self.p.hotel_scores(d["ll"][0], d["ll"][1], user["comfort"], user["plan"], budget_pn)
            prev_h = self.h.iloc[int(np.nanargmax(hs))]
            hotel_for_day.append(prev_h)
        if not days and nights > 0:   # short stay: hotel near best-matching attraction
            best = max(attr_score, key=attr_score.get)
            ll = (self.at.at[best, "Lat"], self.at.at[best, "Lon"])
            hs = self.p.hotel_scores(ll[0], ll[1], user["comfort"], user["plan"], budget_pn)
            hotel_for_day = [self.h.iloc[int(np.nanargmax(hs))]]

        # nights: night of arrival -> hotel of day1; night of day k -> hotel of day k+1; last day -> its own hotel
        night_hotels = []
        for i in range(nights):
            idx = min(i, len(hotel_for_day) - 1)
            night_hotels.append(hotel_for_day[idx] if hotel_for_day else None)
        stays = []
        for i, hh in enumerate(night_hotels):
            if hh is None:
                continue
            if stays and stays[-1]["hotel"]["HotelID"] == hh["HotelID"]:
                stays[-1]["nights"] += 1
            else:
                stays.append({"hotel": hh, "check_in": arr.date() + timedelta(days=i), "nights": 1})
        return self._assemble(user, nights, days, stays, budget_pn, ctx)

    def _airport_ll(self):
        from common import Gazetteer
        if not hasattr(self, "_ap"):
            self._ap = Gazetteer().ll(CONFIG["airport"])
        return self._ap

    # ------------------------------------------------------------------ output
    def _hotel_info(self, hh, plan, nights, budget_pn, ll=None):
        lo, hi = float(hh[f"{plan}_Min"]), float(hh[f"{plan}_Max"])
        return {
            "name": hh["Hotel"], "category": hh["Category"], "town": hh["Town"],
            "rating": float(hh["Rating"]), "rating_count": int(hh["RatingCount"]),
            "meal_plan": plan, "price_per_night_min": lo, "price_per_night_max": hi,
            "nights": nights, "cost_min": lo * nights, "cost_max": hi * nights,
            "cost_estimate": (lo + hi) / 2 * nights, "within_budget": bool((lo + hi) / 2 <= budget_pn),
            "address": str(hh["Address"]), "tel": fmt_phone(hh["Tel"]), "mobile": fmt_phone(hh["Mobile"]),
            "email": "" if pd.isna(hh["Email"]) else str(hh["Email"]),
            "web": "" if pd.isna(hh["Web"]) else str(hh["Web"]),
            "image": "" if pd.isna(hh.get("Images")) else str(hh.get("Images")),
            "lat": float(hh["Lat"]), "lon": float(hh["Lon"]),
            "distance_km": None if ll is None else round(haversine(ll[0], ll[1], hh["Lat"], hh["Lon"]), 1),
        }

    def _visit_info(self, r):
        acts = []
        for p in str(r["Activities"]).split("|"):
            if p.strip():
                t, _, dsc = p.partition(":")
                acts.append({"title": t.strip(), "description": dsc.strip()})
        img = r.get("Image URL") if isinstance(r.get("Image URL"), str) and r.get("Image URL").startswith("http") else (
            r.get("Image") if isinstance(r.get("Image"), str) else "")
        return {"attraction": r["Attraction Name"], "destination": r["Destination"], "area": r["Area"],
                "category": r["Category"], "mood": r["Mood"], "rating": float(r["Rating"]),
                "start": fmt_min(r["StartMin"]), "end": fmt_min(r["EndMin"]),
                "duration_min": int(r["DurMin"]), "activities": acts, "details": r["Details"], "image": img or ""}

    def _assemble(self, user, nights, days, stays, budget_pn, ctx):
        arr, dep, plan = user["arrival"], user["departure"], user["plan"]
        ap = self._airport_ll()
        stay_by_date = {}
        stay_infos = []
        for s in stays:
            info = self._hotel_info(s["hotel"], plan, s["nights"], budget_pn)
            info["check_in"] = s["check_in"].isoformat()
            info["check_out"] = (s["check_in"] + timedelta(days=s["nights"])).isoformat()
            stay_infos.append(info)
            for k in range(s["nights"]):
                stay_by_date[(s["check_in"] + timedelta(days=k)).isoformat()] = info
        # distances from hotel to that day's attractions
        for d in days:
            st = stay_by_date.get((d["date"] - timedelta(days=1)).isoformat())
            if st is not None and st.get("distance_km") is None:
                hh = self.h[self.h["Hotel"] == st["name"]].iloc[0]
                st["distance_km"] = round(haversine(d["ll"][0], d["ll"][1], hh["Lat"], hh["Lon"]), 1)

        out_days = []
        first = stay_infos[0] if stay_infos else None
        ev = [{"time": arr.strftime("%H:%M"), "type": "arrival", "text": "Arrive at Bandaranaike International Airport (Katunayake)"}]
        if first:
            hh = self.h[self.h["Hotel"] == first["name"]].iloc[0]
            tmin = transfer_minutes(haversine(ap[0], ap[1], hh["Lat"], hh["Lon"]) * 1.3)
            ev.append({"time": fmt_min(arr.hour * 60 + arr.minute + 45), "type": "transfer",
                       "text": f"Transfer to {first['name']}, {first['town']} (≈{int(tmin // 60)}h {int(tmin % 60)}m drive)"})
            ev.append({"time": fmt_min(arr.hour * 60 + arr.minute + 45 + tmin), "type": "check-in",
                       "text": f"Check in at {first['name']} ({plan}) - rest of the day free"})
        out_days.append({"day": 0, "date": arr.date().isoformat(), "kind": "Arrival", "events": ev,
                         "visits": [], "stay_tonight": stay_by_date.get(arr.date().isoformat())})
        for i, d in enumerate(days, 1):
            out_days.append({"day": i, "date": d["date"].isoformat(), "kind": "Sightseeing", "events": [],
                             "center": {"lat": d["ll"][0], "lon": d["ll"][1], "label": d["visits"][0]["Area"]},
                             "visits": [self._visit_info(r) for r in d["visits"]],
                             "stay_tonight": stay_by_date.get(d["date"].isoformat())})
        last = stay_infos[-1] if stay_infos else None
        ev = []
        if last:
            hh = self.h[self.h["Hotel"] == last["name"]].iloc[0]
            tmin = transfer_minutes(haversine(ap[0], ap[1], hh["Lat"], hh["Lon"]) * 1.3)
            leave = dep.hour * 60 + dep.minute - 180 - tmin
            ev.append({"time": "Morning", "type": "check-out", "text": f"Breakfast and check-out from {last['name']}"})
            if leave > 9 * 60:
                ev.append({"time": f"until {fmt_min(leave)}", "type": "free", "text": "Free time: shopping, souvenirs and local food"})
            else:
                ev.append({"time": "-", "type": "free", "text": "Early departure: no time for shopping, head straight to the airport"})
            ev.append({"time": fmt_min(max(leave, 0)), "type": "transfer", "text": f"Leave for the airport (≈{int(tmin // 60)}h {int(tmin % 60)}m drive, 3h before flight)"})
        ev.append({"time": dep.strftime("%H:%M"), "type": "departure", "text": "Departure from Bandaranaike International Airport"})
        out_days.append({"day": len(days) + 1, "date": dep.date().isoformat(), "kind": "Departure", "events": ev,
                         "visits": [], "stay_tonight": None})
        total_est = sum(s["cost_estimate"] for s in stay_infos)
        return {
            "summary": {"arrival": arr.strftime("%Y-%m-%d %H:%M"), "departure": dep.strftime("%Y-%m-%d %H:%M"),
                        "nights": nights, "sightseeing_days": len(days), "comfort": user["comfort"],
                        "meal_plan": plan, "budget": user["budget"], "budget_per_night": round(budget_pn),
                        "accommodation_cost_estimate": total_est,
                        "accommodation_cost_min": sum(s["cost_min"] for s in stay_infos),
                        "accommodation_cost_max": sum(s["cost_max"] for s in stay_infos),
                        "message": user["message"],
                        "understood_moods": ctx.get("top_moods", []), "understood_categories": ctx.get("top_categories", [])},
            "days": out_days, "stays": stay_infos,
            "_internal": [{"pool": d["pool"], "chosen": [int(r["RowID"]) for r in d["visits"]]} for d in days],
        }


ITINERARY_COLUMNS = ["Sample ID", "User Message", "Arrival", "Departure", "Budget (LKR)", "Comfort Level", "Meal Plan",
                     "Day", "Date", "Day Type", "Item", "Start", "End", "Attraction / Accommodation", "Destination",
                     "Category", "Mood", "Rating", "Activities", "Details", "Nights", "Price per Night (LKR)",
                     "Accommodation Cost (LKR)", "Address", "Tel", "Mobile", "Email", "Web"]


def itinerary_rows(it, sample_id=""):
    """Flattens an itinerary into rows (same schema as final_itinerary_samples.xlsx)."""
    s = it["summary"]
    base = {"Sample ID": sample_id, "User Message": s["message"], "Arrival": s["arrival"], "Departure": s["departure"],
            "Budget (LKR)": s["budget"], "Comfort Level": s["comfort"], "Meal Plan": s["meal_plan"]}
    rows = []
    started = set()
    for d in it["days"]:
        for e in d["events"]:
            rows.append({**base, "Day": d["day"], "Date": d["date"], "Day Type": d["kind"], "Item": e["type"].title(),
                         "Start": e["time"], "Attraction / Accommodation": e["text"]})
        for v in d["visits"]:
            rows.append({**base, "Day": d["day"], "Date": d["date"], "Day Type": d["kind"], "Item": "Attraction",
                         "Start": v["start"], "End": v["end"], "Attraction / Accommodation": v["attraction"],
                         "Destination": v["destination"], "Category": v["category"], "Mood": v["mood"], "Rating": v["rating"],
                         "Activities": " | ".join(f"{x['title']}: {x['description']}" for x in v["activities"]),
                         "Details": v["details"]})
        st = d.get("stay_tonight")
        if st and st["check_in"] not in started:
            started.add(st["check_in"])
            rows.append({**base, "Day": d["day"], "Date": d["date"], "Day Type": d["kind"], "Item": "Accommodation",
                         "Start": "Check-in " + st["check_in"], "End": "Check-out " + st["check_out"],
                         "Attraction / Accommodation": st["name"], "Destination": st["town"], "Category": st["category"],
                         "Rating": st["rating"], "Nights": st["nights"],
                         "Price per Night (LKR)": f"{st['price_per_night_min']:,.0f} - {st['price_per_night_max']:,.0f} ({st['meal_plan']})",
                         "Accommodation Cost (LKR)": round(st["cost_estimate"]), "Address": st["address"], "Tel": st["tel"],
                         "Mobile": st["mobile"], "Email": st["email"], "Web": st["web"]})
    return pd.DataFrame(rows, columns=ITINERARY_COLUMNS)
