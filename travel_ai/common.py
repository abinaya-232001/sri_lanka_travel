"""
common.py - shared data loading, cleaning, location matching and feature engineering
for the three Random-Forest models (attractions, accommodation, visit-time).

Nothing in here decides WHICH attraction/hotel/time a user gets. It only turns raw data
into numeric features. The decisions are learned by the RF models in train_models.py.
"""
import re, math, os
from datetime import datetime, time, timedelta
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
TRAIN = os.path.join(BASE, "training_data")
MODELS = os.path.join(BASE, "models")

# ---- planning parameters (physical constraints, not recommendations) -------------
CONFIG = {
    "travel_speed_kmh": 35,        # average Sri Lankan road speed for transfer estimates
    "min_transfer_min": 20,        # minimum gap between two attractions on the same day
    "day_pool_radius_km": 45,      # attractions considered "same area" for one day
    "day_start": "05:30",          # earliest start time allowed for a visit
    "day_end": "21:30",            # latest end time allowed for a visit
    "airport": "Katunayake",       # arrival / departure point
    "route_coherence_km": 150,     # prefer the next day's area close to the previous one
    "hotel_reuse_km": 25,
    "anchor_score_ratio": 0.8,     # next day's area is chosen among attractions scoring >= 80% of the best left          # keep the same hotel if the next day's area is this close
}

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ============================ small helpers ======================================
def stem(w):
    w = w.lower()
    for suf in ("ings", "ing", "ers", "er", "ies", "ied", "es", "ed", "s"):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[: -len(suf)]
    return w


STOP = set("""a an the and or of to in on at for with by from is are be this that it its
i we me my our you your want like love some something place places trip visit see go
looking interested prefer would can do show please also very really especially where
which spots spot day holiday tour things thing get have has will just more most""".split())


def tokens(text):
    return {stem(t) for t in re.findall(r"[a-zA-Z]+", str(text)) if t.lower() not in STOP and len(t) > 2}


def to_minutes(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    if isinstance(v, time):
        return v.hour * 60 + v.minute
    if isinstance(v, datetime):
        return v.hour * 60 + v.minute
    m = re.match(r"\s*(\d{1,2}):(\d{2})", str(v))
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


def fmt_min(m):
    m = int(round(m)) % (24 * 60)
    return f"{m // 60:02d}:{m % 60:02d}"


def parse_duration(s):
    s = str(s).lower()
    m = re.match(r"([\d.]+)\s*h", s)
    if m:
        return float(m.group(1)) * 60
    m = re.match(r"([\d.]+)\s*min", s)
    if m:
        return float(m.group(1))
    return None


def parse_best_months(s):
    s = str(s)
    if "not" in s.lower():
        return set(range(1, 13))
    out = set()
    for part in s.split(","):
        p = re.split(r"[–\-]", part.strip())
        try:
            a = MONTHS.index(p[0].strip()[:3]) + 1
            b = MONTHS.index(p[-1].strip()[:3]) + 1
        except ValueError:
            continue
        m = a
        while True:
            out.add(m)
            if m == b:
                break
            m = m % 12 + 1
    return out or set(range(1, 13))


def haversine(lat1, lon1, lat2, lon2):
    if any(pd.isna(x) for x in (lat1, lon1, lat2, lon2)):
        return np.nan
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def transfer_minutes(km):
    km = 0 if pd.isna(km) else km
    return CONFIG["min_transfer_min"] + km / CONFIG["travel_speed_kmh"] * 60


# ============================ gazetteer ==========================================
class Gazetteer:
    def __init__(self):
        g = pd.read_excel(os.path.join(DATA, "places_gazetteer.xlsx"))
        self.coords = {}
        self.names = []  # (regex, canonical)
        for _, r in g.iterrows():
            canon = r["Place"]
            self.coords[canon.lower()] = (r["Latitude"], r["Longitude"])
            al = [canon] + [a.strip() for a in str(r.get("Aliases (;-separated)", "") or "").split(";") if a.strip() and a.strip() != "nan"]
            for a in al:
                self.names.append((re.compile(r"\b" + re.escape(a.lower()).replace(r"\ ", r"[\s\-]*") + r"\b"), canon, a))
        # longer names first so "Nuwara Eliya" wins over "Ella"
        self.names.sort(key=lambda x: -len(x[2]))

    def lookup(self, name):
        if not isinstance(name, str):
            return None
        hits = self.find_all(name)
        return hits[0] if hits else None

    def find_all(self, text):
        t = str(text).lower()
        found = []
        for rx, canon, _ in self.names:
            m = rx.search(t)
            if m:
                found.append((m.start(), canon))
        found.sort()
        seen, out = set(), []
        for _, c in found:
            if c not in seen:
                seen.add(c); out.append(c)
        return out

    def ll(self, canon):
        return self.coords.get(str(canon).lower(), (np.nan, np.nan))


# ============================ data loading =======================================
def load_attractions(gz=None):
    gz = gz or Gazetteer()
    path = os.path.join(DATA, "attractions.xlsx")
    a = pd.read_excel(path, sheet_name="All Data")
    try:
        alias = pd.read_excel(path, sheet_name="Destination Alias")
        amap = dict(zip(alias.iloc[:, 0].astype(str).str.strip(), alias.iloc[:, 1].astype(str).str.strip()))
    except Exception:
        amap = {}
    a = a[[c for c in a.columns if not str(c).startswith("Unnamed")] + (["Unnamed: 18"] if "Unnamed: 18" in a.columns else [])]
    a = a.rename(columns={"Unnamed: 18": "Image URL", "Rating (1-5)": "Rating"})
    a["Destination"] = a["Destination"].astype(str).str.replace(r"\+.*$", "", regex=True).str.strip()
    a.loc[a["Destination"].isin(["nan", "None", ""]), "Destination"] = np.nan
    a["Destination"] = a["Destination"].map(lambda d: amap.get(d, d) if isinstance(d, str) else d)
    # missing destinations: read the place out of the attraction's own description
    for i in a.index[a["Destination"].isna()]:
        hits = gz.find_all(str(a.at[i, "Attraction Name"]) + " " + str(a.at[i, "Details"]))
        a.at[i, "Destination"] = hits[0] if hits else "Colombo"
    # coordinates: destination centre, refined by a nearby town mentioned in Details
    lats, lons, towns = [], [], []
    for _, r in a.iterrows():
        canon = gz.lookup(r["Destination"]) or r["Destination"]
        dlat, dlon = gz.ll(canon)
        best = (dlat, dlon, canon)
        for t in gz.find_all(r["Details"]):
            tl = gz.ll(t)
            if not np.isnan(dlat) and haversine(dlat, dlon, *tl) <= 60 and t != canon:
                best = (tl[0], tl[1], t)
                break
        lats.append(best[0]); lons.append(best[1]); towns.append(best[2])
    a["Lat"], a["Lon"], a["Area"] = lats, lons, towns
    a["StartMin"] = a["Visit Start"].map(to_minutes)
    a["EndMin"] = a["Visit End"].map(to_minutes)
    dur = a["Visit_Duration"].map(parse_duration)
    calc = (a["EndMin"] - a["StartMin"]) % (24 * 60)
    a["DurMin"] = np.where(a["EndMin"].notna(), calc, dur)
    a["DurMin"] = a["DurMin"].fillna(dur).fillna(60).replace(0, 60)
    a["EndMin"] = a["StartMin"] + a["DurMin"]
    a["Rating"] = pd.to_numeric(a["Rating"], errors="coerce").fillna(a["Rating"].median() if "Rating" in a else 4.0)
    a["BestMonths"] = a["Best Months to Visit"].map(parse_best_months)
    a["ActTitles"] = a["Activities"].map(lambda s: [p.split(":")[0].strip() for p in str(s).split("|") if p.strip()])
    a["AttrID"] = (a["Attraction Name"].str.strip() + " @ " + a["Destination"].astype(str)).values
    for c in ["Category", "Mood", "Activities", "Details", "Attraction Name"]:
        a[c] = a[c].fillna("").astype(str).str.strip()
    a = a.reset_index(drop=True)
    a["RowID"] = a.index
    return a


COMFORT_LEVELS = ["Budget", "Standard", "Comfort", "Luxury"]
MEAL_PLANS = ["BB", "HB", "FB"]


def clean_category(c):
    c = str(c).strip()
    c = re.sub(r"\s+Grade.*$", "", c)
    c = re.sub(r"\s*-\s*Rooms.*$", "", c)
    c = re.sub(r"Hotels 1 stars", "Hotels 1 Star", c, flags=re.I)
    return c.strip()


def load_hotels(gz=None):
    gz = gz or Gazetteer()
    h = pd.read_excel(os.path.join(DATA, "accommodation.xlsx"))
    h = h.rename(columns={"Accomadation": "Hotel"})
    h["Rating"] = pd.to_numeric(h["Ratings"].astype(str).str.replace(r"^\.", "", regex=True), errors="coerce")
    h["RatingCount"] = pd.to_numeric(h["Rating count"], errors="coerce").fillna(0)
    h["Category"] = h["Category"].map(clean_category)
    for p in MEAL_PLANS:
        for k in ("Min", "Max"):
            h[f"{p}_{k}"] = pd.to_numeric(h[f"{p} {k} (LKR)"], errors="coerce")
    lat, lon, town = [], [], []
    for _, r in h.iterrows():
        addr = str(r["Address"])
        parts = [p.strip() for p in addr.split(",") if p.strip()]
        hit = None
        for p in reversed(parts):          # town is normally at the end of the address
            hit = gz.lookup(p)
            if hit:
                break
        hit = hit or gz.lookup(str(r.get("Local Authority", "")))
        ll = gz.ll(hit) if hit else (np.nan, np.nan)
        lat.append(ll[0]); lon.append(ll[1]); town.append(hit)
    h["Lat"], h["Lon"], h["Town"] = lat, lon, town
    h = h[h["Lat"].notna() & h["Rating"].notna() & h["BB_Min"].notna()].reset_index(drop=True)
    h["HotelID"] = h.index
    return h


def fmt_phone(v):
    if pd.isna(v):
        return ""
    s = str(int(v)) if isinstance(v, (int, float)) else str(v)
    return "0" + s if len(s) == 9 else s


# ============================ text engine ========================================
def stem_preprocess(s):
    """Module-level (picklable) text normaliser used by the TF-IDF vectoriser."""
    return " ".join(stem(w) for w in re.findall(r"[a-zA-Z]+", str(s).lower()))


class TextEngine:
    """Learns the vocabulary of the attraction data so a free-text user message can be
    compared with each attraction's name / category / mood / activities / details."""

    def fit(self, a):
        self.full = (a["Attraction Name"] + " . " + a["Category"] + " . " + a["Mood"] + " . " +
                     a["Activities"] + " . " + a["Details"]).tolist()
        self.word = TfidfVectorizer(stop_words=sorted({stem(w) for w in ENGLISH_STOP_WORDS}), sublinear_tf=True, ngram_range=(1, 2), min_df=1,
                                    token_pattern=r"[a-zA-Z]{3,}", preprocessor=stem_preprocess)
        self.char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, lowercase=True)
        W = self.word.fit_transform(self.full)
        self.char.fit(self.full)
        self.svd = TruncatedSVD(n_components=min(120, W.shape[1] - 1), random_state=0).fit(W)
        self._index(a)
        return self

    def _index(self, a):
        self.M_name_c = self.char.transform(a["Attraction Name"])
        self.M_act_w = self.word.transform(a["Activities"])
        self.M_act_c = self.char.transform(a["Activities"])
        self.M_det_w = self.word.transform(a["Details"])
        self.M_full_lsa = normalize(self.svd.transform(self.word.transform(self.full)))
        self.M_mood_c = self.char.transform(a["Mood"])
        self.M_cat_c = self.char.transform(a["Category"])
        # data-driven profiles: what words typically describe each category / mood
        fullW = self.word.transform(self.full)
        self.cat_prof, self.mood_prof = {}, {}
        for col, store in (("Category", self.cat_prof), ("Mood", self.mood_prof)):
            for val, idx in a.groupby(col).groups.items():
                store[val] = normalize(np.asarray(fullW[list(idx)].mean(axis=0)))
        self.row_cat = a["Category"].tolist()
        self.row_mood = a["Mood"].tolist()
        self.row_titles = [[tokens(t) for t in ts] for ts in a["ActTitles"]]
        self.row_text_tokens = [tokens(t) for t in self.full]

    def message_vectors(self, msg):
        w = self.word.transform([msg]); c = self.char.transform([msg])
        return w, c, normalize(self.svd.transform(w))

    def sims(self, msg):
        """Returns dict of arrays (one value per attraction row)."""
        w, c, l = self.message_vectors(msg)
        out = {
            "sim_name": (self.M_name_c @ c.T).toarray().ravel(),
            "sim_activities_word": (self.M_act_w @ w.T).toarray().ravel(),
            "sim_activities_char": (self.M_act_c @ c.T).toarray().ravel(),
            "sim_details_word": (self.M_det_w @ w.T).toarray().ravel(),
            "sim_semantic": (self.M_full_lsa @ l.T).ravel(),
            "sim_mood_word": (self.M_mood_c @ c.T).toarray().ravel(),
            "sim_category_word": (self.M_cat_c @ c.T).toarray().ravel(),
        }
        wd = w.toarray().ravel()
        cp = {k: float(v.ravel() @ wd) for k, v in self.cat_prof.items()}
        mp = {k: float(v.ravel() @ wd) for k, v in self.mood_prof.items()}
        out["sim_category_profile"] = np.array([cp[x] for x in self.row_cat])
        out["sim_mood_profile"] = np.array([mp[x] for x in self.row_mood])
        mt = tokens(msg)
        ov, hit = [], []
        for titles, txt in zip(self.row_titles, self.row_text_tokens):
            best = 0.0
            for t in titles:
                if t:
                    best = max(best, len(t & mt) / len(t))
            ov.append(best)
            hit.append(len(txt & mt) / (len(mt) or 1))
        out["activity_title_overlap"] = np.array(ov)
        out["message_word_coverage"] = np.array(hit)
        return out


ATTR_FEATURES = ["sim_name", "sim_activities_word", "sim_activities_char", "sim_details_word", "sim_semantic",
                 "sim_mood_word", "sim_category_word", "sim_category_profile", "sim_mood_profile",
                 "activity_title_overlap", "message_word_coverage", "p_intent_category", "p_intent_mood",
                 "rating", "in_season", "duration_h"]


def attraction_feature_frame(a, te, msg, month, p_cat=None, p_mood=None):
    s = te.sims(msg)
    df = pd.DataFrame(s)
    df["p_intent_category"] = [p_cat.get(c, 0.0) for c in a["Category"]] if p_cat else 0.0
    df["p_intent_mood"] = [p_mood.get(m, 0.0) for m in a["Mood"]] if p_mood else 0.0
    df["rating"] = a["Rating"].values
    df["in_season"] = [int(month in bm) for bm in a["BestMonths"]]
    df["duration_h"] = a["DurMin"].values / 60
    return df[ATTR_FEATURES]


# ---- accommodation features ------------------------------------------------------
def hotel_feature_frame(h, lat, lon, comfort, plan, budget_per_night, categories):
    d = np.array([haversine(lat, lon, la, lo) for la, lo in zip(h["Lat"], h["Lon"])])
    price = ((h[f"{plan}_Min"] + h[f"{plan}_Max"]) / 2).values
    df = pd.DataFrame({
        "distance_km": d,
        "distance_rank": pd.Series(d).rank(method="min").values,
        "price_per_night": price,
        "budget_per_night": budget_per_night,
        "price_to_budget": price / max(budget_per_night, 1),
        "hotel_rating": h["Rating"].values,
        "log_rating_count": np.log1p(h["RatingCount"].values),
        "rooms": h["Rooms"].values,
    })
    for c in COMFORT_LEVELS:
        df[f"user_comfort_{c}"] = int(comfort == c)
    for p in MEAL_PLANS:
        df[f"plan_{p}"] = int(plan == p)
    for c in categories:
        df[f"cat_{c}"] = (h["Category"] == c).astype(int).values
    return df


# ---- visit-time (slot) features ----------------------------------------------------
SLOT_FEATURES = ["attraction_score", "score_vs_best", "score_rank", "slot_mood_intent", "slot_mood_word_sim",
                 "slot_mood_profile_sim", "is_best_mood_slot", "rating", "start_hour", "start_rank", "duration_h",
                 "gap_from_cursor_h", "steps_done", "minutes_used_h", "transfer_km", "end_hour",
                 "n_feasible_after", "best_score_after", "sum_top2_after", "skipped_score", "n_skipped"]


def slot_candidates(day_rows, chosen, cursor_min, last_ll):
    """Feasible (non-overlapping) slots for the attractions not yet scheduled today."""
    ds, de = to_minutes(CONFIG["day_start"]), to_minutes(CONFIG["day_end"])
    done = {c["AttrID"] for c in chosen}
    out = []
    for _, r in day_rows.iterrows():
        if r["AttrID"] in done or r["StartMin"] is None:
            continue
        km = 0.0 if last_ll is None else haversine(last_ll[0], last_ll[1], r["Lat"], r["Lon"])
        earliest = ds if cursor_min is None else cursor_min + transfer_minutes(km)
        if r["StartMin"] >= earliest and r["EndMin"] <= de:
            out.append((r, km))
    return out


def slot_feature_rows(cands, chosen, cursor, attr_score, mood_intent, mood_word_sim, mood_prof_sim, best_mood_slot):
    """One row per feasible slot, including look-ahead: what is still possible after taking it,
    and what good options would be skipped by taking it."""
    used = sum(c["DurMin"] for c in chosen)
    sc = np.array([attr_score.get(r["AttrID"], 0.0) for r, _ in cands])
    st = np.array([r["StartMin"] for r, _ in cands])
    best = sc.max() if len(sc) else 0.0
    sc_rank = (-sc).argsort().argsort()
    st_rank = st.argsort().argsort()
    base = cursor if cursor is not None else to_minutes(CONFIG["day_start"])
    rows = []
    for i, (r, km) in enumerate(cands):
        after = []
        skipped = []
        for j, (r2, _) in enumerate(cands):
            if r2["AttrID"] == r["AttrID"]:
                continue
            if r2["StartMin"] >= r["EndMin"] + transfer_minutes(haversine(r["Lat"], r["Lon"], r2["Lat"], r2["Lon"])):
                after.append(sc[j])
            elif r2["StartMin"] < r["StartMin"]:
                skipped.append(sc[j])
        after = sorted(after, reverse=True)
        rows.append({
            "attraction_score": sc[i], "score_vs_best": sc[i] - best, "score_rank": sc_rank[i],
            "slot_mood_intent": mood_intent.get(r["Mood"], 0.0),
            "slot_mood_word_sim": mood_word_sim[r["RowID"]],
            "slot_mood_profile_sim": mood_prof_sim[r["RowID"]],
            "is_best_mood_slot": int(best_mood_slot.get(r["AttrID"]) == r["RowID"]),
            "rating": r["Rating"], "start_hour": r["StartMin"] / 60, "start_rank": st_rank[i],
            "duration_h": r["DurMin"] / 60, "gap_from_cursor_h": (r["StartMin"] - base) / 60,
            "steps_done": len(chosen), "minutes_used_h": used / 60,
            "transfer_km": km if not pd.isna(km) else 0.0, "end_hour": r["EndMin"] / 60,
            "n_feasible_after": len(after), "best_score_after": after[0] if after else 0.0,
            "sum_top2_after": sum(after[:2]), "skipped_score": max(skipped) if skipped else 0.0,
            "n_skipped": len(skipped),
        })
    return pd.DataFrame(rows, columns=SLOT_FEATURES)
