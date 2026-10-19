"""
app.py - Flask backend for the travel web app.

    pip install -r requirements.txt
    python app.py            # then open http://127.0.0.1:5000

Home, itinerary, wellness and risk are open without an account. One TourCeylon
account is required for SOS. A signed-in user has one saved trip (SQLite: app.db).
Guests keep a trip in guest_trips until they register.
"""
import base64, hashlib, hmac, io, json, os, re, secrets, sqlite3, time, zipfile
from datetime import datetime
from urllib.parse import quote
from urllib.request import Request, urlopen
from functools import wraps
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, send_file, send_from_directory, session, g, redirect, Response
from werkzeug.security import generate_password_hash, check_password_hash
from common import Gazetteer, load_attractions, load_hotels, MEAL_PLANS, BASE, TRAIN, haversine
from models import RFPolicy
from planner import Planner, itinerary_rows, ITINERARY_COLUMNS
from directory import Directory

DB = os.path.join(BASE, "app.db")

# ---------------------------------------------------------------- settings
# Fixed starting split of the total budget. The user can change it on the Budget page.
DEFAULT_SPLIT = {"Accommodation": 40, "Food": 20, "Travel": 20, "Shopping": 10, "Other": 10}
# Comfort labels shown to users -> comfort level used by the accommodation model
COMFORT_OPTIONS = [("Budget", "Budget"), ("Standard", "Standard"), ("Mid-range", "Comfort"), ("Luxury", "Luxury")]
COMFORT_MAP = dict(COMFORT_OPTIONS)
SHOP_NEAR_KM = 30

app = Flask(__name__, static_folder=os.path.join(BASE, "static"))
_secret_file = os.path.join(BASE, "models", ".secret_key")
if not os.path.exists(_secret_file):
    open(_secret_file, "w").write(secrets.token_hex(32))
app.secret_key = os.environ.get("SECRET_KEY") or open(_secret_file).read().strip()
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
app.json.sort_keys = False   # keep budget categories in their natural order
HANDOFF_SECRET = os.environ.get("HANDOFF_SECRET", "tourceylon-account-handoff")


def _text_picture(value):
    """A picture stored as a link or a data URI. Anything else is not an image."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if value.startswith(("http://", "https://")):
        return ("url", value)
    if value.startswith("data:image"):
        return ("data", value)
    return None


def _mime_of(blob, fallback="image/jpeg"):
    if blob[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if blob[:2] == b"\xff\xd8":
        return "image/jpeg"
    if blob[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    return fallback


def _load_attraction_pictures():
    """Pictures for attraction cards, from data/attractions-images.xlsx only.

    Excel stores many of these as photos placed in the Image cell. Those are not
    cell text, so a normal spreadsheet read misses them. A link or data URI in
    the same column is used when a cell has no placed photo.
    """
    path = os.path.join(BASE, "data", "attractions-images.xlsx")
    pictures = {}
    with zipfile.ZipFile(path) as book:
        placed = {}
        try:
            rels = dict(re.findall(
                r'Id="(rId\d+)"[^>]*Target="([^"]+)"',
                book.read("xl/richData/_rels/richValueRel.xml.rels").decode("utf-8")))
            rel_ids = re.findall(r'r:id="(rId\d+)"', book.read("xl/richData/richValueRel.xml").decode("utf-8"))
            local_ids = [int(v) for v in re.findall(
                r"<rv[^>]*>\s*<v>(\d+)</v>", book.read("xl/richData/rdrichvalue.xml").decode("utf-8"))]
            meta = book.read("xl/metadata.xml").decode("utf-8").split("<valueMetadata", 1)[1]
            vm_targets = [int(v) for v in re.findall(r'<rc t="1" v="(\d+)"/>', meta)]
            sheet = book.read("xl/worksheets/sheet1.xml").decode("utf-8")
            for ref, vm in re.findall(r'<c r="F(\d+)"[^>]*vm="(\d+)"', sheet):
                idx = int(vm) - 1
                if not (0 <= idx < len(vm_targets)):
                    continue
                rv_i = vm_targets[idx]
                if not (0 <= rv_i < len(local_ids)):
                    continue
                rel_i = local_ids[rv_i]
                if not (0 <= rel_i < len(rel_ids)):
                    continue
                target = rels.get(rel_ids[rel_i], "").replace("\\", "/")
                if not target:
                    continue
                media = target if target.startswith("xl/") else "xl/" + target.lstrip("./").replace("../", "")
                placed[int(ref)] = media
        except KeyError:
            placed = {}
        table = pd.read_excel(path, sheet_name="Attractions")
        for i, row in table.iterrows():
            name = str(row["Attraction Name"]).strip()
            if not name or name in pictures:
                continue
            media = placed.get(i + 2)
            if media:
                blob = book.read(media)
                pictures[name] = ("bytes", _mime_of(blob), blob)
                continue
            text = _text_picture(row.get("Image"))
            if text:
                pictures[name] = text
    return pictures


def _load_hotel_pictures():
    """Stay photos from data/accomadation-images.xlsx. Not used by the models."""
    table = pd.read_excel(os.path.join(BASE, "data", "accomadation-images.xlsx"))
    pictures = {}
    for name, img in zip(table["Name"], table["Images"]):
        key = str(name).strip()
        if not key or key in pictures:
            continue
        text = _text_picture(img)
        if text:
            pictures[key] = text[1]
    return pictures


def _picture_src(name, row_id):
    pic = ATTR_PICTURES.get(str(name).strip())
    if not pic:
        return ""
    if pic[0] in ("url", "data"):
        return pic[1]
    return f"/api/attractions/{int(row_id)}/image"


print("Loading data and models ...")
_gz = Gazetteer()
A = load_attractions(_gz)
H = load_hotels(_gz)
# Pictures are display-only. The three models never read these columns.
ATTR_PICTURES = _load_attraction_pictures()
HOTEL_PICTURES = _load_hotel_pictures()
A["Image URL"] = ""
A["Image"] = [_picture_src(n, i) for n, i in zip(A["Attraction Name"], A["RowID"])]
H["Images"] = [("/api/hotels/image?name=" + quote(str(n).strip())) if HOTEL_PICTURES.get(str(n).strip()) else ""
              for n in H["Hotel"]]
PLANNER = Planner(A, H, RFPolicy(A, H))
DIRECTORY = Directory(_gz)
try:
    EXPORT_COLUMNS = list(pd.read_excel(os.path.join(TRAIN, "final_itinerary_samples.xlsx"), nrows=0).columns)
except Exception:
    EXPORT_COLUMNS = ITINERARY_COLUMNS

# one card per attraction for the home page
_first = A.sort_values("Rating", ascending=False).groupby("AttrID", sort=False).head(1)
ATTRACTIONS = []
for _, r in _first.sort_values(["Rating", "Attraction Name"], ascending=[False, True]).iterrows():
    rows = A[A["AttrID"] == r["AttrID"]]
    ATTRACTIONS.append({
        "id": int(r["RowID"]), "name": r["Attraction Name"], "destination": r["Destination"], "area": r["Area"],
        "category": r["Category"], "moods": sorted(rows["Mood"].unique().tolist()), "rating": float(r["Rating"]),
        "best_months": r["Best Months to Visit"],
        "activities": [p.partition(":")[0].strip() for p in str(r["Activities"]).split("|") if p.strip()],
        "details": r["Details"],
        "has_image": str(r["Attraction Name"]).strip() in ATTR_PICTURES,
    })
print("Ready.")


# ---------------------------------------------------------------- database
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def _close(_):
    c = g.pop("db", None)
    if c:
        c.close()


def init_db():
    c = sqlite3.connect(DB)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS trips (user_id INTEGER PRIMARY KEY REFERENCES users(id),
        state TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS guest_trips (token TEXT PRIMARY KEY, state TEXT NOT NULL, updated_at TEXT NOT NULL);
    """)
    cols = {r[1] for r in c.execute("PRAGMA table_info(users)")}
    for name in ("phone", "nationality", "language", "passport"):
        if name not in cols:
            c.execute(f"ALTER TABLE users ADD COLUMN {name} TEXT")
    c.commit(); c.close()


init_db()


def login_required(f):
    @wraps(f)
    def wrap(*a, **k):
        if not session.get("uid"):
            return jsonify({"errors": ["Please sign in to continue."]}), 401
        return f(*a, **k)
    return wrap


def _blank_state():
    return {"inputs": None, "split": dict(DEFAULT_SPLIT),
            "selections": {"guides": [], "agencies": [], "shops": []}, "itinerary": None}


def _guest_token():
    tok = session.get("guest")
    if not tok:
        tok = secrets.token_hex(16)
        session["guest"] = tok
    return tok


def load_state():
    uid = session.get("uid")
    if uid:
        row = db().execute("SELECT state FROM trips WHERE user_id=?", (uid,)).fetchone()
    else:
        row = db().execute("SELECT state FROM guest_trips WHERE token=?", (_guest_token(),)).fetchone()
    st = json.loads(row["state"]) if row else {}
    for k, v in _blank_state().items():
        st.setdefault(k, v)
    return st


def save_state(st):
    payload, now = json.dumps(st, default=float), datetime.utcnow().isoformat()
    uid = session.get("uid")
    if uid:
        db().execute("INSERT INTO trips(user_id, state, updated_at) VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET "
                     "state=excluded.state, updated_at=excluded.updated_at", (uid, payload, now))
    else:
        db().execute("INSERT INTO guest_trips(token, state, updated_at) VALUES(?,?,?) ON CONFLICT(token) DO UPDATE SET "
                     "state=excluded.state, updated_at=excluded.updated_at", (_guest_token(), payload, now))
    db().commit()


def _clean_passport(value):
    return re.sub(r"\s+", "", str(value or "")).upper()


def _user_public(u):
    if not u:
        return None
    return {"name": u["name"], "email": u["email"], "phone": u["phone"] or "",
            "nationality": u["nationality"] or "", "passport": u["passport"] or "",
            "language": u["language"] or "en"}


# ---------------------------------------------------------------- trip logic
def budget_breakdown(total, split):
    return [{"category": k, "percent": split[k], "amount": round(total * split[k] / 100)} for k in DEFAULT_SPLIT]


def parse_inputs(d):
    errors, out = [], {}
    msg = str(d.get("experience_message", "")).strip()
    if len(msg) < 3:
        errors.append("Tell us the experience you want, for example: peaceful nature and waterfalls.")
    try:
        arr = datetime.fromisoformat(f"{d['arrival_date']}T{d['arrival_time']}")
        dep = datetime.fromisoformat(f"{d['departure_date']}T{d['departure_time']}")
        if dep <= arr:
            errors.append("Departure needs to be after arrival.")
        elif (dep.date() - arr.date()).days > 21:
            errors.append("Trips can be up to 21 nights.")
    except Exception:
        errors.append("Add your arrival and departure dates and times.")
    try:
        budget = float(str(d.get("budget", "")).replace(",", ""))
        if budget < 1000:
            raise ValueError
    except Exception:
        errors.append("Add your total budget in LKR (at least 1,000).")
        budget = 0
    if d.get("comfort_level") not in COMFORT_MAP:
        errors.append("Choose a comfort level.")
    if d.get("meal_plan") not in MEAL_PLANS:
        errors.append("Choose a meal plan.")
    if not errors:
        out = {k: d[k] for k in ("arrival_date", "arrival_time", "departure_date", "departure_time",
                                 "comfort_level", "meal_plan")}
        out.update({"budget": budget, "experience_message": msg})
    return errors, out


def run_planner(inputs, split):
    acc_budget = inputs["budget"] * split["Accommodation"] / 100
    user = {"message": inputs["experience_message"],
            "arrival": datetime.fromisoformat(f"{inputs['arrival_date']}T{inputs['arrival_time']}"),
            "departure": datetime.fromisoformat(f"{inputs['departure_date']}T{inputs['departure_time']}"),
            "budget": max(acc_budget, 1.0), "comfort": COMFORT_MAP[inputs["comfort_level"]], "plan": inputs["meal_plan"]}
    it = PLANNER.plan(user)
    it.pop("_internal", None)
    # how much the cheapest stays near each overnight area would cost (for an honest budget message)
    plan = inputs["meal_plan"]
    price = ((H[f"{plan}_Min"] + H[f"{plan}_Max"]) / 2).values
    cheapest_total, cheapest_night = 0.0, None
    for st in it["stays"]:
        d = np.array([haversine(st["lat"], st["lon"], la, lo) for la, lo in zip(H["Lat"], H["Lon"])])
        c = float(price[d <= 25].min()) if (d <= 25).any() else (st["price_per_night_min"] + st["price_per_night_max"]) / 2
        cheapest_total += c * st["nights"]
        cheapest_night = c if cheapest_night is None else min(cheapest_night, c)
    s = it["summary"]
    s["accommodation_share"] = acc_budget
    s["cheapest_possible_total"] = cheapest_total
    s["cheapest_night_price"] = cheapest_night
    s["share_too_small"] = bool(cheapest_total > acc_budget)
    return it


def centers_of(it):
    if not it:
        return []
    cs = [{"lat": d["center"]["lat"], "lon": d["center"]["lon"], "label": f"Day {d['day']}, {d['center']['label']}"}
          for d in it["days"] if d.get("center")]
    for s in it.get("stays", []):
        cs.append({"lat": s["lat"], "lon": s["lon"], "label": f"your stay in {s['town']}"})
    return cs


def _no_nan(d):
    return {k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in d.items() if k not in ("lat", "lon")}


def public_state(st):
    """What the browser sees: saved state + budget breakdown + selected items placed on the itinerary."""
    out = {"inputs": st["inputs"], "split": st["split"], "selections": st["selections"]}
    total = st["inputs"]["budget"] if st["inputs"] else 0
    out["budget"] = {"total": total, "breakdown": budget_breakdown(total, st["split"]), "default_split": DEFAULT_SPLIT}
    it = st["itinerary"]
    team = {k: DIRECTORY.get_many(k, st["selections"].get(k, [])) for k in ("guides", "agencies", "shops")}
    if it:
        it = json.loads(json.dumps(it))
        out["budget"]["accommodation_estimate"] = it["summary"]["accommodation_cost_estimate"]
        for d in it["days"]:
            d["shops"] = []
            if d.get("center"):
                for s in team["shops"]:
                    km = haversine(d["center"]["lat"], d["center"]["lon"], s["lat"], s["lon"])
                    if not np.isnan(km) and km <= SHOP_NEAR_KM:
                        d["shops"].append({**_no_nan(s), "distance_km": round(km, 1)})
            if d["kind"] == "Departure":
                d["shops"] = [_no_nan(s) for s in team["shops"]]
    out["itinerary"] = it
    out["team"] = {k: [_no_nan(s) for s in v] for k, v in team.items()}
    return out


# ---------------------------------------------------------------- pages
@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


# ---------------------------------------------------------------- auth
@app.post("/api/auth/signup")
def signup():
    d = request.get_json(force=True) or {}
    name, email, pw = str(d.get("name", "")).strip(), str(d.get("email", "")).strip().lower(), str(d.get("password", ""))
    passport = _clean_passport(d.get("passport"))
    errors = []
    if len(name) < 2:
        errors.append("Add your name.")
    if not re.fullmatch(r"[A-Z0-9]{5,20}", passport):
        errors.append("Add your passport number. Use 5 to 20 letters or numbers.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        errors.append("Add a valid email address.")
    if len(pw) < 6:
        errors.append("Use a password with at least 6 characters.")
    if not errors and db().execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
        errors.append("An account with this email already exists. Sign in instead.")
    if errors:
        return jsonify({"errors": errors}), 400
    guest = session.get("guest")
    cur = db().execute("INSERT INTO users(name,email,password_hash,created_at,language,passport) VALUES(?,?,?,?,?,?)",
                       (name, email, generate_password_hash(pw), datetime.utcnow().isoformat(), "en", passport))
    db().commit()
    session.clear(); session["uid"] = cur.lastrowid
    if guest:
        row = db().execute("SELECT state FROM guest_trips WHERE token=?", (guest,)).fetchone()
        if row:
            save_state(json.loads(row["state"]))
            db().execute("DELETE FROM guest_trips WHERE token=?", (guest,))
            db().commit()
    u = db().execute("SELECT name,email,phone,nationality,language,passport FROM users WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify({"user": _user_public(u)})


@app.post("/api/auth/login")
def login():
    d = request.get_json(force=True) or {}
    email, pw = str(d.get("email", "")).strip().lower(), str(d.get("password", ""))
    u = db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if not u or not check_password_hash(u["password_hash"], pw):
        return jsonify({"errors": ["That email and password don't match. Check them and try again."]}), 401
    session.clear(); session["uid"] = u["id"]
    return jsonify({"user": _user_public(u)})


@app.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/auth/me")
def me():
    uid = session.get("uid")
    u = db().execute("SELECT name,email,phone,nationality,language,passport FROM users WHERE id=?", (uid,)).fetchone() if uid else None
    return jsonify({"user": _user_public(u)})


@app.patch("/api/auth/me")
def update_me():
    uid = session.get("uid")
    if not uid:
        return jsonify({"errors": ["Create an account to save a profile."]}), 401
    d = request.get_json(force=True) or {}
    name = str(d.get("name", "")).strip()
    if len(name) < 2:
        return jsonify({"errors": ["Add your name."]}), 400
    phone = str(d.get("phone", "")).strip()[:32]
    nationality = str(d.get("nationality", "")).strip()[:80]
    passport = _clean_passport(d.get("passport"))
    if not re.fullmatch(r"[A-Z0-9]{5,20}", passport):
        return jsonify({"errors": ["Add your passport number. Use 5 to 20 letters or numbers."]}), 400
    language = str(d.get("language", "en")).strip()[:8] or "en"
    db().execute("UPDATE users SET name=?, phone=?, nationality=?, language=?, passport=? WHERE id=?",
                 (name, phone, nationality, language, passport, uid))
    db().commit()
    u = db().execute("SELECT name,email,phone,nationality,language,passport FROM users WHERE id=?", (uid,)).fetchone()
    return jsonify({"user": _user_public(u)})


@app.post("/api/auth/sos-handoff")
def sos_handoff():
    uid = session.get("uid")
    if not uid:
        return jsonify({"errors": ["Create an account to use SOS."]}), 401
    u = db().execute("SELECT name,email,phone,nationality,language,passport FROM users WHERE id=?", (uid,)).fetchone()
    if not u["passport"]:
        return jsonify({"errors": ["Add your passport number before using SOS."]}), 400
    body = json.dumps({"name": u["name"], "email": u["email"], "phone": u["phone"] or "",
                       "nationality": u["nationality"] or "", "passport": u["passport"],
                       "language": u["language"] or "en",
                       "exp": int(time.time()) + 120}, separators=(",", ":")).encode()
    sig = hmac.new(HANDOFF_SECRET.encode(), body, hashlib.sha256).hexdigest()
    token = base64.urlsafe_b64encode(body).decode().rstrip("=") + "." + sig
    return jsonify({"token": token})


# ---------------------------------------------------------------- reference data
@app.get("/api/meta")
def meta():
    return jsonify({"comfort_levels": [k for k, _ in COMFORT_OPTIONS], "meal_plans": MEAL_PLANS,
                    "default_split": DEFAULT_SPLIT, "categories": sorted(A["Category"].unique().tolist()),
                    **DIRECTORY.facets()})


@app.get("/api/attractions")
def attractions():
    q = request.args.get("q", "").strip().lower()
    cat = request.args.get("category", "")
    page = max(1, int(request.args.get("page", 1)))
    per = min(48, int(request.args.get("per_page", 12)))
    items = [x for x in ATTRACTIONS if (not cat or x["category"] == cat) and
             (not q or q in (x["name"] + " " + x["destination"] + " " + x["area"] + " " + " ".join(x["activities"])).lower())]
    return jsonify({"total": len(items), "page": page, "items": items[(page - 1) * per: page * per]})


@app.get("/api/attractions/<int:rid>/image")
def attraction_image(rid):
    if rid < 0 or rid >= len(A):
        return "", 404
    pic = ATTR_PICTURES.get(str(A.iloc[rid]["Attraction Name"]).strip())
    if not pic:
        return "", 404
    if pic[0] == "url":
        return redirect(pic[1])
    if pic[0] == "data":
        head, _, data = pic[1].partition(",")
        mime = head[5:].split(";")[0] or "image/jpeg"
        body = base64.b64decode(data)
    else:
        mime, body = pic[1], pic[2]
    resp = Response(body, mimetype=mime)
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


@app.get("/api/hotels/image")
def hotel_image():
    pic = HOTEL_PICTURES.get(request.args.get("name", "").strip())
    if not pic:
        return "", 404
    if pic.startswith(("http://", "https://")):
        return redirect(pic)
    if pic.startswith("data:image"):
        head, _, data = pic.partition(",")
        mime = head[5:].split(";")[0] or "image/jpeg"
        resp = Response(base64.b64decode(data), mimetype=mime)
        resp.headers["Cache-Control"] = "public, max-age=86400"
        return resp
    return "", 404


@app.get("/api/directory/<kind>")
def directory(kind):
    if kind not in ("guides", "agencies", "shops"):
        return "", 404
    st = load_state()
    filters = {k: request.args.get(k, "") for k in ("category", "language", "kind")}
    res = DIRECTORY.search(kind, request.args.get("q", "").strip(), filters, centers_of(st["itinerary"]),
                           page=max(1, int(request.args.get("page", 1))), per_page=12,
                           selected=st["selections"].get(kind, []))
    sel = set(st["selections"].get(kind, []))
    for it in res["items"]:
        it["selected"] = it["id"] in sel
    res["near_route"] = bool(st["itinerary"])
    return jsonify(res)


# ---------------------------------------------------------------- trip
@app.get("/api/trip")
def get_trip():
    return jsonify(public_state(load_state()))


@app.post("/api/trip/plan")
def plan_trip():
    errors, inputs = parse_inputs(request.get_json(force=True) or {})
    if errors:
        return jsonify({"errors": errors}), 400
    st = load_state()
    st["inputs"] = inputs
    st["itinerary"] = run_planner(inputs, st["split"])
    save_state(st)
    return jsonify(public_state(st))


@app.put("/api/trip/budget")
def set_budget():
    d = request.get_json(force=True) or {}
    split = d.get("split") if not d.get("reset") else dict(DEFAULT_SPLIT)
    try:
        split = {k: float(split[k]) for k in DEFAULT_SPLIT}
    except Exception:
        return jsonify({"errors": ["Give a percentage for every category."]}), 400
    if any(v < 0 for v in split.values()) or abs(sum(split.values()) - 100) > 0.01:
        return jsonify({"errors": [f"The categories add up to {sum(split.values()):g}%. Make them add up to 100%."]}), 400
    if split["Accommodation"] <= 0:
        return jsonify({"errors": ["Accommodation needs more than 0% to find a place to stay."]}), 400
    st = load_state()
    changed = st["split"]["Accommodation"] != split["Accommodation"]
    st["split"] = split
    if changed and st["inputs"]:
        st["itinerary"] = run_planner(st["inputs"], split)
    save_state(st)
    return jsonify({**public_state(st), "replanned": bool(changed and st["inputs"])})


@app.post("/api/trip/select")
def select_item():
    d = request.get_json(force=True) or {}
    kind, iid, on = d.get("kind"), str(d.get("id", "")), bool(d.get("selected"))
    if kind not in ("guides", "agencies", "shops") or not iid:
        return jsonify({"errors": ["Unknown item."]}), 400
    st = load_state()
    cur = [x for x in st["selections"].get(kind, []) if x != iid]
    if on:
        cur.append(iid)
    st["selections"][kind] = cur
    save_state(st)
    return jsonify(public_state(st))


@app.get("/api/trip/export")
def export():
    st = public_state(load_state())
    if not st["itinerary"]:
        return jsonify({"errors": ["Create your itinerary first."]}), 400
    df = itinerary_rows(st["itinerary"], "MY-TRIP").reindex(columns=EXPORT_COLUMNS)
    df["Budget (LKR)"] = st["budget"]["total"]
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Itinerary")
        pd.DataFrame(st["budget"]["breakdown"]).rename(columns=str.title).to_excel(w, index=False, sheet_name="Budget")
        for k, title in (("guides", "Tour guides"), ("agencies", "Travel agencies"), ("shops", "Shopping")):
            if st["team"][k]:
                rows = [{kk: (", ".join(vv) if isinstance(vv, list) else vv) for kk, vv in x.items()} for x in st["team"][k]]
                pd.DataFrame(rows).drop(columns=["distance_km", "near"], errors="ignore").to_excel(w, index=False, sheet_name=title)
        for ws in w.sheets.values():
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = min(50, max(10, max(len(str(c.value or "")) for c in col) + 2))
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="my_sri_lanka_itinerary.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def _fetch_image_bytes(src, limit=1_500_000):
    """Bytes for a picture the app already knows: a local photo, a data URI, or a short web fetch."""
    if not src:
        return None
    try:
        if src.startswith("/api/attractions/") and "/image" in src:
            rid = int(src.split("/")[3])
            pic = ATTR_PICTURES.get(str(A.iloc[rid]["Attraction Name"]).strip())
            if not pic:
                return None
            if pic[0] == "bytes":
                return pic[2]
            if pic[0] == "data":
                return base64.b64decode(pic[1].partition(",")[2])
            src = pic[1]
        elif src.startswith("/api/hotels/image"):
            from urllib.parse import parse_qs, unquote, urlparse
            name = unquote(parse_qs(urlparse(src).query).get("name", [""])[0]).strip()
            pic = HOTEL_PICTURES.get(name, "")
            if pic.startswith("data:image"):
                return base64.b64decode(pic.partition(",")[2])
            if not pic.startswith(("http://", "https://")):
                return None
            src = pic
        if src.startswith("data:image"):
            return base64.b64decode(src.partition(",")[2])
        if src.startswith(("http://", "https://")):
            req = Request(src, headers={"User-Agent": "LankaJourney/1.0"})
            with urlopen(req, timeout=4) as resp:
                blob = resp.read(limit + 1)
            return blob if len(blob) <= limit else None
    except Exception:
        return None
    return None


def _build_itinerary_pdf(st):
    from fpdf import FPDF
    it = st["itinerary"]
    s = it["summary"]
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=16)
    regular, bold = r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"
    if os.path.exists(regular):
        pdf.add_font("Body", "", regular)
        pdf.add_font("Body", "B", bold if os.path.exists(bold) else regular)
        family = "Body"
    else:
        family = "Helvetica"
    pdf.add_page()
    pdf.set_font(family, "B", 22)
    pdf.set_text_color(22, 63, 48)
    def para(text, size=10, style="", h=5, x=None):
        pdf.set_x(pdf.l_margin if x is None else x)
        pdf.set_font(family, style, size)
        width = pdf.w - pdf.r_margin - pdf.get_x()
        pdf.multi_cell(max(width, 20), h, str(text or ""))

    para("Your Sri Lanka itinerary", 22, "B", 12)
    pdf.set_text_color(40, 50, 45)
    msg = (st.get("inputs") or {}).get("experience_message") or s.get("message") or ""
    para(msg, 11, "", 6)
    pdf.ln(2)
    facts = (
        f"Arrival: {s.get('arrival', '')}    Departure: {s.get('departure', '')}\n"
        f"Nights: {s.get('nights', '')}    Sightseeing days: {s.get('sightseeing_days', '')}    "
        f"Comfort: {s.get('comfort', '')}    Meals: {s.get('meal_plan', '')}\n"
        f"Budget: LKR {int(st['budget']['total']):,}"
    )
    para(facts)
    pdf.ln(2)
    photos = 0
    for day in it["days"]:
        title = {"Arrival": "Arrival day", "Departure": "Departure day"}.get(day["kind"], f"Day {day['day']}")
        pdf.set_text_color(22, 63, 48)
        pdf.ln(2)
        para(f"{title}  -  {day['date']}", 14, "B", 8)
        pdf.set_text_color(40, 50, 45)
        for ev in day.get("events") or []:
            para(f"{ev.get('time', '')}   {ev.get('text', '')}")
        for v in day.get("visits") or []:
            pdf.ln(1)
            y = pdf.get_y()
            if y > 250:
                pdf.add_page()
                y = pdf.get_y()
            blob = _fetch_image_bytes(v.get("image")) if photos < 12 else None
            text_x = pdf.l_margin
            if blob:
                try:
                    pdf.image(io.BytesIO(blob), x=pdf.l_margin, y=y, w=36, h=26)
                    text_x = pdf.l_margin + 40
                    photos += 1
                except Exception:
                    blob = None
            para(f"{v.get('start', '')} - {v.get('end', '')}  {v.get('attraction', '')}", 11, "B", 5, text_x)
            para(f"{v.get('area', '')}, {v.get('category', '')}", 10, "", 5, text_x)
            detail = (v.get("details") or "").strip()
            if len(detail) > 280:
                detail = detail[:277].rsplit(" ", 1)[0] + "..."
            if detail:
                para(detail, 10, "", 5, text_x)
            if blob:
                pdf.set_y(max(pdf.get_y(), y + 28))
        stay = day.get("stay_tonight")
        if stay:
            pdf.ln(1)
            para(f"Stay: {stay.get('name', '')}", 11, "B")
            para(f"{stay.get('category', '')}, {stay.get('town', '')}. {stay.get('address', '')}")
    if it.get("stays"):
        pdf.ln(3)
        pdf.set_text_color(22, 63, 48)
        para("Where you'll stay", 14, "B", 8)
        pdf.set_text_color(40, 50, 45)
        for stay in it["stays"]:
            para(f"{stay.get('name', '')}  -  {stay.get('check_in', '')} to {stay.get('check_out', '')}  -  {stay.get('nights', '')} nights", 11, "B")
            para(stay.get("address", ""))
            pdf.ln(1)
    team = st.get("team") or {}
    people = [("Tour guide", g) for g in team.get("guides") or []] + [("Travel agency", a) for a in team.get("agencies") or []]
    if people:
        pdf.ln(2)
        pdf.set_text_color(22, 63, 48)
        para("Your trip team", 14, "B", 8)
        pdf.set_text_color(40, 50, 45)
        for role, person in people:
            para(f"{role}: {person.get('name', '')}")
    out = io.BytesIO(pdf.output())
    return out


@app.get("/api/trip/export.pdf")
def export_pdf():
    st = public_state(load_state())
    if not st["itinerary"]:
        return jsonify({"errors": ["Create your itinerary first."]}), 400
    buf = _build_itinerary_pdf(st)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="my_sri_lanka_itinerary.pdf", mimetype="application/pdf")


# Risk analyst tab. Crowd/risk pipelines live in the risk-management folder.
# The itinerary models in models/ are not loaded or changed here.
try:
    from risk_bridge import mount_risk
    mount_risk(app)
except Exception as exc:
    print(f"WARNING: risk tab backend was not mounted: {exc}")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
