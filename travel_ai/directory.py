"""
directory.py - tourist guides, travel agencies and shops, cleaned and located on the map,
so they can be searched and sorted by how close they are to the traveller's itinerary.
"""
import os, re
import numpy as np
import pandas as pd
from common import DATA, haversine


def _clean(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    s = str(v).strip()
    return "" if s.lower() in ("nan", "none") else s


def _phone(v):
    s = _clean(v)
    if re.fullmatch(r"\d+\.0", s):
        s = s[:-2]
    if re.fullmatch(r"\d{9}", s):
        s = "0" + s
    return s


def _guide_photo(v):
    """Turn the guides file's image path into a photo the page can show."""
    s = _clean(v)
    low = s.lower()
    if not s or "no_profile" in low or "covidimg" in low:
        return ""
    if low.startswith("image/"):
        return "https://www.srilanka.travel/" + s.lstrip("/")
    if s.startswith("//"):
        return "https:" + s
    if low.startswith("http://") or low.startswith("https://"):
        return s
    return ""


def _web(v):
    s = _clean(v)
    if s and not s.startswith("http"):
        s = "http://" + s
    return s


def _locate(gz, *texts):
    for t in texts:
        t = _clean(t)
        if not t:
            continue
        parts = [p.strip() for p in re.split(r"[,\n]", t) if p.strip()]
        for p in reversed(parts):
            hit = gz.lookup(p)
            if hit:
                return hit
        hits = gz.find_all(t)
        if hits:
            return hits[-1]
    return None


class Directory:
    def __init__(self, gz):
        self.gz = gz
        self.guides = self._load_guides()
        self.agencies = self._load_agencies()
        self.shops = self._load_shops()

    def _coords(self, df, towns):
        ll = [self.gz.ll(t) if t else (np.nan, np.nan) for t in towns]
        df["town"] = [t or "" for t in towns]
        df["lat"] = [x[0] for x in ll]
        df["lon"] = [x[1] for x in ll]
        return df

    def _load_guides(self):
        g = pd.read_csv(os.path.join(DATA, "tourist_guides.csv"), dtype=str)
        g = g.drop_duplicates("registration_no").reset_index(drop=True)
        # the site's own language list appears in the file as "All Languages Arabic Chinese ... Search"
        menu = next((s for s in g["languages"].dropna() if s.startswith("All Languages")), "")
        vocab = {w for w in re.findall(r"[A-Z][a-z]+", menu) if w not in ("All", "Languages", "Search")}
        vocab = {("Mandarin" if w == "Mandarian" else w) for w in vocab} or {"English"}
        langs = []
        for s in g["languages"].fillna(""):
            if s.startswith("All Languages"):
                langs.append([]); continue
            words = [("Mandarin" if w == "Mandarian" else w) for w in re.findall(r"[A-Z][a-z]+", s)]
            langs.append(sorted({w for w in words if w in vocab}))
        out = pd.DataFrame({
            "id": "G" + g["registration_no"].fillna(g.index.to_series().astype(str)).str.replace(r"\W", "", regex=True),
            "name": g["name"].map(_clean).str.replace(r"\s+", " ", regex=True).str.title(),
            "category": g["category"].map(_clean).replace("", "Not listed"),
            "languages": langs,
            "phone": g["tel"].map(_phone),
            "email": g["email"].map(_clean),
            "address": g["address"].map(_clean),
            "registration": g["registration_no"].map(_clean),
            "validity": g["validity"].map(_clean),
            "image": [_guide_photo(u) for u in g["image_url"]],
        })
        out = out.drop_duplicates("id").reset_index(drop=True)
        return self._coords(out, [_locate(self.gz, a) for a in out["address"]])

    def _load_agencies(self):
        t = pd.read_excel(os.path.join(DATA, "travel_agencies.xlsx"), dtype=str)
        out = pd.DataFrame({
            "id": "A" + t.index.astype(str),
            "name": t["Name"].map(_clean).str.rstrip("."),
            "address": t["Address"].map(_clean),
            "area": t["Local Authority"].map(_clean),
            "website": t["Website"].map(_web),
            "email": t["Email"].map(_clean),
            "phone": t["Telephone"].map(_phone),
            "mobile": t["Mobile"].map(_phone),
            "licence": t["Licence No."].map(_clean),
            "validity": t["Licence Validity"].map(_clean),
        })
        return self._coords(out, [_locate(self.gz, a, b) for a, b in zip(out["address"], out["area"])])

    def _load_shops(self):
        b = pd.read_excel(os.path.join(DATA, "business_directory.xlsx"), dtype=str)
        b = b.drop_duplicates(["Business Name", "Address"]).reset_index(drop=True)
        out = pd.DataFrame({
            "id": "S" + b.index.astype(str),
            "name": b["Business Name"].map(_clean),
            "address": b["Address"].map(_clean),
            "district": b["District"].map(_clean),
            "website": b["Website"].map(_web),
            "email": b["Email"].map(_clean),
            "phone": b["Telephone"].map(_phone),
        })
        kinds = []
        for n in out["name"].str.lower():
            if re.search(r"gem|jewel|sapph|silver|gold|stone", n):
                kinds.append("Gems and jewellery")
            elif re.search(r"batik|craft|silk|handloom|wood|lacquer|mask", n):
                kinds.append("Batik and handicrafts")
            elif re.search(r"fashion|garment|mall|fair|odel|clothing", n):
                kinds.append("Fashion")
            else:
                kinds.append("Gifts and other")
        out["kind"] = kinds
        return self._coords(out, [_locate(self.gz, a, d) for a, d in zip(out["address"], out["district"])])

    # ------------------------------------------------------------------ search
    @staticmethod
    def _near(df, centers):
        """Distance (km) from each row to the closest itinerary area, and that area's name."""
        if not centers:
            return np.full(len(df), np.nan), [""] * len(df)
        dist, label = [], []
        for la, lo in zip(df["lat"], df["lon"]):
            best, lab = np.nan, ""
            for c in centers:
                d = haversine(la, lo, c["lat"], c["lon"])
                if not np.isnan(d) and (np.isnan(best) or d < best):
                    best, lab = d, c["label"]
            dist.append(best); label.append(lab)
        return np.array(dist), label

    def search(self, kind, q="", filters=None, centers=None, page=1, per_page=24, selected=()):
        df = {"guides": self.guides, "agencies": self.agencies, "shops": self.shops}[kind].copy()
        filters = filters or {}
        if q:
            ql = q.lower()
            hay = df["name"].str.lower() + " " + df["address"].str.lower() + " " + df["town"].str.lower()
            if kind == "agencies":
                hay = hay + " " + df["area"].str.lower()
            if kind == "shops":
                hay = hay + " " + df["district"].str.lower() + " " + df["kind"].str.lower()
            df = df[hay.str.contains(re.escape(ql), na=False)]
        if kind == "guides":
            if filters.get("category"):
                df = df[df["category"] == filters["category"]]
            if filters.get("language"):
                df = df[df["languages"].map(lambda l: filters["language"] in l)]
        if kind == "shops" and filters.get("kind"):
            df = df[df["kind"] == filters["kind"]]
        d, lab = self._near(df, centers)
        df = df.assign(distance_km=d, near=lab)
        df["is_selected"] = df["id"].isin(set(selected))
        if centers:
            df = df.sort_values(["distance_km", "name"], na_position="last")
        else:
            df = df.sort_values("name")
        total = len(df)
        page_df = df.iloc[(page - 1) * per_page: page * per_page]
        return {"total": total, "page": page, "per_page": per_page, "items": [self.item(r) for _, r in page_df.iterrows()]}

    def item(self, r):
        out = {k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in r.items() if k not in ("lat", "lon", "is_selected")}
        if out.get("distance_km") is not None:
            out["distance_km"] = round(float(out["distance_km"]), 1)
        return out

    def get_many(self, kind, ids):
        df = {"guides": self.guides, "agencies": self.agencies, "shops": self.shops}[kind]
        sub = df[df["id"].isin(set(ids))]
        return [{**self.item(r), "lat": r["lat"], "lon": r["lon"]} for _, r in sub.iterrows()]

    def facets(self):
        langs = sorted({l for ls in self.guides["languages"] for l in ls})
        return {"guide_categories": sorted(self.guides["category"].unique().tolist()), "guide_languages": langs,
                "shop_kinds": sorted(self.shops["kind"].unique().tolist())}
