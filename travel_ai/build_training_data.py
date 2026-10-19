"""
build_training_data.py - creates the training workbooks in training_data/ from the ORIGINAL
attractions.xlsx and accommodation.xlsx.

  1. attraction_training.xlsx      user message  <->  attraction row  (relevance 0/1/2)
  2. accommodation_training.xlsx   user comfort / budget / meal plan / visiting attraction <-> hotel (suitability 0/1/2)
  3. visit_time_training.xlsx      sample day itineraries: which slot (start time) was chosen, in order
  4. final_itinerary_samples.xlsx  complete sample itineraries (arrival -> hotels -> attractions -> departure)

User messages are generated from the attractions' own activities, details, moods and categories,
phrased with the vocabulary in the "Message Vocabulary" sheet (edit it to teach new words).
You can also add your own rows to any of these sheets and re-run train_models.py.
"""
import random, re
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from common import (Gazetteer, load_attractions, load_hotels, tokens, haversine, COMFORT_LEVELS, MEAL_PLANS,
                    TRAIN, CONFIG, os)
from planner import Planner, itinerary_rows

R = random.Random(42)
NP = np.random.default_rng(42)

MOOD_WORDS = {
    "Peaceful": ["peaceful", "calm", "quiet", "serene", "tranquil"],
    "Relaxed": ["relaxed", "chill", "laid-back", "easy going", "relaxing"],
    "Curious": ["curious", "educational", "interesting", "eye-opening", "learning"],
    "Explore": ["exploring", "explorer", "sightseeing", "discovery", "wandering"],
    "Spiritual": ["spiritual", "religious", "sacred", "devotional", "meditative"],
    "Adventure": ["adventure", "adventurous", "thrilling", "adrenaline", "challenging"],
    "Healing": ["healing", "refreshing", "rejuvenating", "wellness", "recharging"],
    "Excited": ["exciting", "fun-filled", "energetic", "lively"],
    "Happy": ["happy", "joyful", "cheerful", "fun"],
    "Authentic": ["authentic", "local", "traditional", "genuine"],
}
CATEGORY_WORDS = {
    "Heritage": ["heritage", "history", "historical sites", "ancient ruins", "temples", "archaeology", "colonial history"],
    "Scenic": ["scenic views", "beautiful landscapes", "waterfalls", "viewpoints", "mountains", "nature"],
    "Essence": ["local life", "shopping", "markets", "city vibe", "parks", "food and culture"],
    "Wild": ["wildlife", "safari", "animals", "birds", "elephants", "national parks"],
    "Pristine": ["beaches", "the sea", "sunsets by the ocean", "sand and waves", "lagoons", "untouched coast"],
    "Thrills": ["thrills", "water parks", "rides", "snorkeling", "whale watching", "adventure sports"],
}
TEMPLATES = [
    "I want a {mood} trip where I can {act1} and {act2}",
    "Looking for {cat}, something {mood}",
    "We love {act1}. Prefer {mood} places with {kw}",
    "{mood} holiday with {cat} and {act1}",
    "Show me places for {act1}, {act2} and {kw}",
    "I'm interested in {cat}, especially {kw}",
    "family trip, {mood}, {act1}",
    "need a {mood} experience, {act1} and {cat}",
    "{act1} {act2} {kw}",
    "I like {cat}. Want to feel {mood}",
    "something {mood} - maybe {act1} or {kw}",
    "can you find {cat} where we can do {act1}",
    "honeymoon, {mood}, {cat}",
    "{kw} and {act1}, {mood} vibe please",
]


def write_book(path, sheets):
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        for name, df in sheets.items():
            df.to_excel(w, sheet_name=name[:31], index=False)
            ws = w.sheets[name[:31]]
            for col in ws.columns:
                width = min(60, max(10, max(len(str(c.value or ""))  for c in list(col)[:200]) + 2))
                ws.column_dimensions[col[0].column_letter].width = width
            ws.freeze_panes = "A2"


# =========================== message generator ====================================
class MessageGen:
    def __init__(self, a):
        self.a = a
        self.desc = a["Activities"].map(lambda s: " ".join(p.partition(":")[2] for p in str(s).split("|")))
        tf = TfidfVectorizer(stop_words="english", token_pattern=r"[a-zA-Z]{5,}")
        tf.fit(self.desc)
        idf = dict(zip(tf.get_feature_names_out(), tf.idf_))
        lo, hi = np.percentile(list(idf.values()), [20, 80])
        generic = set("""enjoy admire learn watch visit explore around through along various among while about
        their there these those where which other inside nearby offers offer often great small large
        early during people within beautiful amazing famous popular local scenic local""".split())
        self.kw_ok = {w for w, v in idf.items() if lo <= v <= hi and w not in generic}
        self.attr_ids = a["AttrID"].unique().tolist()

    def make(self):
        aid = R.choice(self.attr_ids)
        seed = self.a[self.a["AttrID"] == aid].sample(1, random_state=R.randint(0, 10**6)).iloc[0]
        use_mood = R.random() < 0.75
        use_cat = R.random() < 0.6
        acts = [t for t in seed["ActTitles"] if t]
        R.shuffle(acts)
        n_act = 0 if (not acts or R.random() < 0.12) else min(len(acts), R.choice([1, 1, 2]))
        acts = acts[:n_act]
        kws = [w for w in re.findall(r"[a-zA-Z]{5,}", self.desc[seed.name].lower()) if w in self.kw_ok]
        kw = R.choice(kws) if kws and R.random() < 0.5 else None
        if not (use_mood or use_cat or acts or kw):
            use_mood = True
        mood_w = R.choice(MOOD_WORDS.get(seed["Mood"], [seed["Mood"].lower()]))
        cat_w = R.choice(CATEGORY_WORDS.get(seed["Category"], [seed["Category"].lower()]))
        fill = {"mood": mood_w if use_mood else "", "cat": cat_w if use_cat else "",
                "act1": acts[0].lower() if acts else "", "act2": acts[1].lower() if len(acts) > 1 else "", "kw": kw or ""}
        good = [t for t in TEMPLATES if all(fill[k] for k in re.findall(r"{(\w+)}", t))]
        if good:
            msg = R.choice(good).format(**fill)
        else:
            parts = [p for p in [fill["mood"], fill["cat"], fill["act1"], fill["act2"], fill["kw"]] if p]
            msg = R.choice(["I want ", "looking for ", "", "we like "]) + ", ".join(parts)
        msg = re.sub(r"\s+", " ", msg).strip()
        return {"message": msg, "seed": aid, "mood": seed["Mood"] if use_mood else None,
                "category": seed["Category"] if use_cat else None, "seed_category": seed["Category"],
                "seed_mood": seed["Mood"], "acts": acts, "kw": kw}


def relevance_grades(a, spec, month):
    """Ground-truth relevance of every attraction row for a generated message.
    0 = not relevant, 1 = partly matches, 2 = fully matches, 3 = fully matches + well rated + in season."""
    act_tok = [tokens(t) for t in spec["acts"]]
    kw = tokens(spec["kw"]) if spec["kw"] else set()
    groups = []
    if spec["mood"]:
        groups.append((a["Mood"] == spec["mood"]).values)
    if spec["category"]:
        groups.append((a["Category"] == spec["category"]).values)
    if act_tok or kw:
        ok = []
        for titles, det, act in zip(a["ActTitles"], a["Details"], a["Activities"]):
            hit = False
            tt = [tokens(t) for t in titles]
            for at in act_tok:
                if any(t and len(at & t) / max(len(at | t), 1) >= 0.5 for t in tt):
                    hit = True; break
            if not hit and kw and kw <= tokens(det + " " + act):
                hit = True
            ok.append(hit)
        groups.append(np.array(ok))
    m = np.sum(groups, axis=0)
    n = len(groups)
    g = np.zeros(len(a), int)
    g[(m >= max(1, int(np.ceil(n / 2))))] = 1
    full = m == n
    g[full] = 2
    if full.any():
        med = np.median(a["Rating"].values[full])
        season = np.array([month in bm for bm in a["BestMonths"]])
        g[full & (a["Rating"].values >= med) & season] = 3
    return g


# =========================== accommodation ground truth ===========================
COMFORT_MAP = {
    "Hotels 5 Stars": "Luxury", "Hotels 4 Stars": "Luxury", "Boutique villas": "Luxury", "Boutique hotels": "Luxury",
    "Bungalow DELUXE": "Luxury", "Rented homes DELUXE": "Luxury", "Home stay DELUXE": "Luxury",
    "Hotels 3 Stars": "Comfort", "Hotels": "Comfort", "Bungalow SUPERIOR": "Comfort", "Rented homes SUPERIOR": "Comfort",
    "Home stay SUPERIOR": "Comfort", "Guest house A": "Comfort",
    "Hotels 2 Stars": "Standard", "Bungalow STANDARD": "Standard", "Home stay STANDARD": "Standard", "Guest house B": "Standard",
    "Guest house B&B": "Standard", "Hotels 1 Star": "Budget", "Guest house C": "Budget",
}


def hotel_grades(h, lat, lon, comfort, plan, budget_pn):
    d = np.array([haversine(lat, lon, a, b) for a, b in zip(h["Lat"], h["Lon"])])
    near_lim = max(20.0, np.sort(d)[min(9, len(d) - 1)])
    near = d <= near_lim
    price = ((h[f"{plan}_Min"] + h[f"{plan}_Max"]) / 2).values
    within = price <= budget_pn
    lvl = h["Category"].map(lambda c: COMFORT_MAP.get(c, "Standard")).map(COMFORT_LEVELS.index).values
    want = COMFORT_LEVELS.index(comfort)
    exact, adj = lvl == want, np.abs(lvl - want) == 1
    quality = (h["Rating"].values * h["RatingCount"].values + 8.5 * 20) / (h["RatingCount"].values + 20)
    g = np.zeros(len(h), int)
    fit = near & within
    if (fit & exact).any():                      # in budget, right comfort level
        g[fit & adj] = 1; g[fit & exact] = 1
        idx = np.where(fit & exact)[0]
        g[idx[np.argsort(-quality[idx])][:3]] = 2
    elif (fit & adj).any():                      # in budget, comfort one level off
        g[fit & adj] = 1
        idx = np.where(fit & adj)[0]
        g[idx[np.argsort(-quality[idx])][:2]] = 2
    elif fit.any():                              # in budget, any comfort level
        g[fit] = 1
        idx = np.where(fit)[0]
        g[idx[np.argsort(-quality[idx])][:2]] = 2
    elif near.any():                             # NOTHING nearby fits the budget:
        cheapest = price[near].min()             # the budget wins - pick the cheapest good stays
        tier = near & (price <= cheapest * 1.15)
        g[near & (price <= cheapest * 1.3)] = 1
        idx = np.where(tier)[0]
        g[idx[np.argsort(-quality[idx])][:3]] = 2
    score = g * 10 + quality - d / 50
    return g, score, d, price


# =========================== expert policy (for sample itineraries) ===============
class ExpertPolicy:
    def __init__(self, a, h):
        self.a, self.h = a, h

    def set_user(self, spec, month):
        self.spec, self.grades = spec, relevance_grades(self.a, spec, month)

    def attraction_context(self, msg, month):
        df = pd.DataFrame({"AttrID": self.a["AttrID"], "g": self.grades, "r": self.a["Rating"]})
        s = df.groupby("AttrID").agg(g=("g", "max"), r=("r", "max"))
        score = (s["g"] + s["r"] / 10 + NP.random(len(s)) * 0.05).to_dict()
        return {"attr_score": score, "grades": self.grades}

    def _util(self, r, km):
        g = self.grades[r["RowID"]]
        if g == 0:   # not requested, but a well-rated nearby filler is better than an empty afternoon
            return 0.2 + (r["Rating"] - 4.3) - 0.03 * (km or 0)
        mood_ok = 1.0 if (self.spec["mood"] and r["Mood"] == self.spec["mood"]) else 0.0
        return 0.6 + 1.0 * g + mood_ok + (r["Rating"] - 4.0) - 0.03 * (km or 0)

    def _best_day(self, rows):
        """Search the best non-overlapping sequence of relevant slots for the day."""
        from common import transfer_minutes, haversine
        rows = sorted(rows, key=lambda r: r["StartMin"])
        best = ([], 0.0)

        def dfs(i, seq, util, cursor, last):
            nonlocal best
            if util > best[1]:
                best = (list(seq), util)
            if len(seq) >= self.target or sum(x["DurMin"] for x in seq) > 600:
                return
            for j in range(i, len(rows)):
                r = rows[j]
                if any(r["AttrID"] == x["AttrID"] for x in seq):
                    continue
                km = 0.0 if last is None else haversine(last[0], last[1], r["Lat"], r["Lon"])
                if cursor is not None and r["StartMin"] < cursor + transfer_minutes(km):
                    continue
                u = self._util(r, km)
                if u <= 0:
                    continue
                seq.append(r)
                dfs(j + 1, seq, util + u, r["EndMin"], (r["Lat"], r["Lon"]))
                seq.pop()

        dfs(0, [], 0.0, None, None)
        return [r["RowID"] for r in best[0]]

    def choose_slot(self, cands, chosen, cursor, ctx, force=False):
        if not chosen:
            self.target = R.choice([2, 3, 3, 3, 4])
            self.day_plan = self._best_day([r for r, _ in cands])
            if not self.day_plan:   # nothing relevant nearby: take the best-rated slot
                return int(np.argmax([r["Rating"] - 0.1 * (r["StartMin"] / 60) for r, _ in cands]))
        nxt = len(chosen)
        if nxt >= len(self.day_plan):
            return None
        for i, (r, _) in enumerate(cands):
            if r["RowID"] == self.day_plan[nxt]:
                return i
        return None

    def hotel_scores(self, lat, lon, comfort, plan, budget_pn):
        return hotel_grades(self.h, lat, lon, comfort, plan, budget_pn)[1]


def random_user(gen, a, h):
    spec = gen.make()
    start = datetime(2026, 1, 1) + timedelta(days=R.randint(0, 364))
    arr = start.replace(hour=R.choice([1, 6, 9, 11, 14, 17, 20, 23]), minute=R.choice([0, 30]))
    nights = R.choice([2, 3, 3, 4, 4, 5, 6, 7])
    dep = (arr + timedelta(days=nights)).replace(hour=R.choice([2, 8, 12, 16, 19, 22]), minute=R.choice([0, 15, 45]))
    comfort = R.choice(COMFORT_LEVELS)
    cats = [c for c, l in COMFORT_MAP.items() if l == comfort]
    ref = h[h["Category"].isin(cats)]
    plan = R.choice(MEAL_PLANS)
    ref_price = float(((ref[f"{plan}_Min"] + ref[f"{plan}_Max"]) / 2).median()) if len(ref) else 20000
    budget = round(ref_price * nights * R.uniform(0.7, 1.8), -3)
    return spec, {"message": spec["message"], "arrival": arr, "departure": dep, "budget": budget,
                  "comfort": comfort, "plan": plan}


def main(n_msgs=1400, n_hotel_scen=700, n_trips=450, n_final=40, only=None):
    os.makedirs(TRAIN, exist_ok=True)
    gz = Gazetteer(); a = load_attractions(gz); h = load_hotels(gz)
    gen = MessageGen(a)

    # ---------- 1. attraction relevance -------------------------------------------
    rows, intents = [], []
    for i in range(0 if only == "hotels" else n_msgs):
        spec = gen.make(); month = R.randint(1, 12)
        g = relevance_grades(a, spec, month)
        pos = np.concatenate([NP.choice(np.where(g == k)[0], min(12, int((g == k).sum())), replace=False)
                              for k in (1, 2, 3) if (g == k).any()] or [np.array([], int)]).astype(int)
        same_cat = np.where((a["Category"] == spec["seed_category"]).values & (g == 0))[0]
        neg = np.concatenate([NP.choice(np.where(g == 0)[0], 30, replace=False),
                              NP.choice(same_cat, min(10, len(same_cat)), replace=False) if len(same_cat) else []]).astype(int)
        sid = f"M{i:05d}"
        intents.append({"Sample ID": sid, "User Message": spec["message"], "Travel Month": month,
                        "Intended Category": spec["seed_category"], "Intended Mood": spec["mood"] or "",
                        "Seed Attraction": spec["seed"]})
        for ridx in np.unique(np.concatenate([pos, neg])):
            r = a.iloc[ridx]
            rows.append({"Sample ID": sid, "User Message": spec["message"], "Travel Month": month, "RowID": int(ridx),
                         "Attraction Name": r["Attraction Name"], "Destination": r["Destination"],
                         "Category": r["Category"], "Mood": r["Mood"], "Visit Start": r["Visit Start"],
                         "Rating": r["Rating"], "Activities": "; ".join(r["ActTitles"]),
                         "Details": r["Details"][:160], "Relevance (0=no,1=partly,2=match,3=best)": int(g[ridx])})
    vocab = pd.DataFrame([{"Type": "Mood", "Value": k, "Words": "; ".join(v)} for k, v in MOOD_WORDS.items()] +
                         [{"Type": "Category", "Value": k, "Words": "; ".join(v)} for k, v in CATEGORY_WORDS.items()] +
                         [{"Type": "Template", "Value": "", "Words": t} for t in TEMPLATES])
    at_df = pd.DataFrame(rows)
    if only != "hotels":
      write_book(os.path.join(TRAIN, "attraction_training.xlsx"),
               {"Attraction Training": at_df, "Message Intents": pd.DataFrame(intents), "Message Vocabulary": vocab})
      print("attraction_training:", at_df.shape, at_df.iloc[:, -1].value_counts().to_dict())

    # ---------- 2. accommodation ------------------------------------------------------
    hrows = []
    for i in range(n_hotel_scen):
        r = a.sample(1, random_state=R.randint(0, 10**6)).iloc[0]
        comfort, plan = R.choice(COMFORT_LEVELS), R.choice(MEAL_PLANS)
        cats = [c for c, l in COMFORT_MAP.items() if l == comfort]
        ref = h[h["Category"].isin(cats)]
        bpn = float(((ref[f"{plan}_Min"] + ref[f"{plan}_Max"]) / 2).quantile(R.uniform(0.0, 0.95)))
        if R.random() < 0.3:                      # budgets too small for any stay nearby
            bpn *= R.uniform(0.35, 0.9)
        bpn = round(bpn, -2)
        g, score, d, price = hotel_grades(h, r["Lat"], r["Lon"], comfort, plan, bpn)
        cand = np.unique(np.concatenate([np.argsort(d)[:30], NP.choice(len(h), 15, replace=False), np.where(g > 0)[0]]))
        for k in cand:
            hh = h.iloc[k]
            hrows.append({"Scenario ID": f"H{i:05d}", "User Comfort Level": comfort, "Meal Plan": plan,
                          "Budget per Night (LKR)": bpn, "Visiting Attraction": r["Attraction Name"],
                          "Attraction Destination": r["Destination"], "Attraction Lat": r["Lat"], "Attraction Lon": r["Lon"],
                          "HotelID": int(hh["HotelID"]), "Hotel": hh["Hotel"], "Hotel Town": hh["Town"],
                          "Category": hh["Category"], "Rating": hh["Rating"], "Rating Count": int(hh["RatingCount"]),
                          "Price per Night (LKR)": round(price[k]), "Distance (km)": round(d[k], 1),
                          "Suitability (0=no,1=ok,2=best)": int(g[k])})
    hd = pd.DataFrame(hrows)
    cmap = pd.DataFrame([{"Category": k, "Comfort Level": v} for k, v in COMFORT_MAP.items()])
    write_book(os.path.join(TRAIN, "accommodation_training.xlsx"), {"Accommodation Training": hd, "Comfort Mapping": cmap})
    print("accommodation_training:", hd.shape, hd.iloc[:, -1].value_counts().to_dict())
    if only == "hotels":
        return

    # ---------- 3 + 4. sample itineraries -------------------------------------------
    exp = ExpertPolicy(a, h); planner = Planner(a, h, exp)
    vt, finals = [], []
    for t in range(n_trips):
        spec, user = random_user(gen, a, h)
        exp.set_user(spec, user["arrival"].month)
        it = planner.plan(user)
        sid = f"T{t:05d}"
        for di, dd in enumerate(it["_internal"], 1):
            for order, rid in enumerate(dd["chosen"], 1):
                r = a.iloc[rid]
                vt.append({"Sample ID": sid, "User Message": user["message"], "Travel Month": user["arrival"].month,
                           "Day": di, "Day Pool (AttrIDs)": " || ".join(dd["pool"]), "Order": order, "RowID": rid,
                           "Attraction Name": r["Attraction Name"], "Destination": r["Destination"], "Mood": r["Mood"],
                           "Rating": r["Rating"], "Start": r["Visit Start"], "End": r["Visit End"]})
        if t < n_final:
            finals.append(itinerary_rows(it, sid))
    vtd = pd.DataFrame(vt)
    write_book(os.path.join(TRAIN, "visit_time_training.xlsx"), {"Sample Itineraries": vtd})
    print("visit_time_training:", vtd.shape)
    fin = pd.concat(finals, ignore_index=True)
    write_book(os.path.join(TRAIN, "final_itinerary_samples.xlsx"), {"Final Itineraries": fin})
    print("final_itinerary_samples:", fin.shape)


if __name__ == "__main__":
    import sys
    main(only="hotels" if "--hotels-only" in sys.argv else None)
