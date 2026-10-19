"""Generate TRAVEL_ARCHITECTURE.pdf — beginner-friendly deep guide."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT = Path(__file__).resolve().parents[2] / "TRAVEL_ARCHITECTURE.pdf"

TEAL = colors.HexColor("#0A4A52")
INK = colors.HexColor("#1A2332")
MUTED = colors.HexColor("#5A6570")
CODE_BG = colors.HexColor("#F2F6F7")
LINE = colors.HexColor("#D0DCE0")
ROW_ALT = colors.HexColor("#F5FAFA")
SOFT = colors.HexColor("#E8F4F5")


def S():
    b = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=b["Title"], fontSize=17, textColor=TEAL, alignment=TA_CENTER, spaceAfter=3),
        "sub": ParagraphStyle("s", parent=b["Normal"], fontSize=9.5, textColor=MUTED, alignment=TA_CENTER, spaceAfter=8),
        "h1": ParagraphStyle("h1", parent=b["Heading1"], fontSize=12.5, textColor=TEAL, spaceBefore=9, spaceAfter=5),
        "h2": ParagraphStyle("h2", parent=b["Heading2"], fontSize=10.5, textColor=INK, spaceBefore=7, spaceAfter=3),
        "h3": ParagraphStyle("h3", parent=b["Heading3"], fontSize=9.5, textColor=TEAL, spaceBefore=5, spaceAfter=2),
        "body": ParagraphStyle("body", parent=b["Normal"], fontSize=8.8, textColor=INK, leading=12, spaceAfter=3.5, alignment=TA_JUSTIFY),
        "tip": ParagraphStyle("tip", parent=b["Normal"], fontSize=8.5, textColor=TEAL, leading=11.5, spaceAfter=4, backColor=SOFT, borderPadding=4),
        "small": ParagraphStyle("sm", parent=b["Normal"], fontSize=7.8, textColor=MUTED, leading=10.5, spaceAfter=2),
        "code": ParagraphStyle("c", parent=b["Code"], fontName="Courier", fontSize=6.8, leading=9, textColor=INK, backColor=CODE_BG, spaceBefore=2, spaceAfter=4),
        "file": ParagraphStyle("f", parent=b["Normal"], fontSize=8.5, textColor=TEAL, fontName="Helvetica-Bold", spaceBefore=3, spaceAfter=1.5),
    }


def code(text, s):
    return Preformatted(text.strip("\n"), s["code"])


def tip(story, s, text):
    story.append(Paragraph(f"<b>Simple idea:</b> {text}", s["tip"]))
    story.append(Spacer(1, 1.5 * mm))


def file_block(story, s, path, in_simple, does, magic, connects):
    bits = [
        Paragraph(path, s["file"]),
        Paragraph(f"<b>In simple English:</b> {in_simple}", s["body"]),
        Paragraph(f"<b>What it does:</b> {does}", s["body"]),
        Paragraph(f"<b>The “magic”:</b> {magic}", s["body"]),
        Paragraph(f"<b>Talks to:</b> {connects}", s["small"]),
        Spacer(1, 1.8 * mm),
    ]
    story.append(KeepTogether(bits))


def build():
    s = S()
    story = []

    story.append(Paragraph("Tour Ceylon — Travel Component", s["title"]))
    story.append(Paragraph(
        "Beginner architecture guide: how it works, every file, and how they connect",
        s["sub"],
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=LINE, spaceAfter=6))

    # ========== CH0 ==========
    story.append(Paragraph("0. Read this first (for beginners)", s["h1"]))
    story.append(Paragraph(
        "Imagine Tour Ceylon Travel like an <b>online travel agent</b> for Sri Lanka. "
        "You open a website, pick moods (Adventure, Culture…), choose places, set a budget, "
        "pick hotels, then the app builds a day-by-day plan and can export a PDF.",
        s["body"],
    ))
    story.append(Paragraph(
        "The system has <b>two big halves</b> that work together:",
        s["body"],
    ))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "<b>Frontend (the shop window)</b> — React pages you see in the browser "
            "(folder <b>frontend/travel</b>, address http://localhost:5180).",
            s["body"],
        )),
        ListItem(Paragraph(
            "<b>Backend (the warehouse + brain)</b> — Flask API that stores data and does the hard work "
            "(folder <b>backend</b>, address http://127.0.0.1:5002).",
            s["body"],
        )),
        ListItem(Paragraph(
            "<b>Database (the filing cabinet)</b> — PostgreSQL database named <b>travel_app</b>. "
            "Excel seed files fill the cabinet the first time.",
            s["body"],
        )),
    ], bulletType="bullet"))
    tip(
        story, s,
        "The browser never talks to the database directly. "
        "It always asks the backend. The backend asks the database. That is safer and cleaner.",
    )

    # ========== CH1 TECH ==========
    story.append(Paragraph("1. Technologies used (and what each one is for)", s["h1"]))
    tech = [
        ["Technology", "Where", "What it does in plain English"],
        ["React 18", "Frontend", "Builds the interactive pages (buttons, forms, lists)."],
        ["Vite", "Frontend", "Dev server + fast rebuild. Proxies /api to the backend."],
        ["React Router", "Frontend", "Changes the URL page (/login, /budget…) without full reload."],
        ["Axios", "Frontend", "Sends HTTP requests (GET/POST) to the backend API."],
        ["Flask", "Backend", "Python web framework. Receives URLs like /api/login."],
        ["SQLAlchemy", "Backend", "Talks to PostgreSQL using Python classes (ORM)."],
        ["Flask-JWT-Extended", "Backend", "Login tokens (JWT). Proves “this request is from user 5”."],
        ["PostgreSQL", "Database", "Stores users, trips, attractions, hotels permanently."],
        ["Pandas / Excel", "Seed scripts", "Reads .xlsx files and inserts rows into the DB once."],
        ["ReportLab", "Backend", "Builds the itinerary PDF file for download."],
    ]
    cells = [[Paragraph(f"<b>{c}</b>" if i == 0 else c, s["body"]) for c in row] for i, row in enumerate(tech)]
    # first row already bold via loop - fix header
    cells[0] = [Paragraph(f"<b>{c}</b>", s["body"]) for c in tech[0]]
    tbl = Table(cells, colWidths=[32 * mm, 28 * mm, 98 * mm])
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), TEAL), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.3, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for i in range(2, len(cells), 2):
        cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    tbl.setStyle(TableStyle(cmds))
    story.append(tbl)
    story.append(Spacer(1, 2 * mm))
    tip(
        story, s,
        "MVC = Model (data), View (screens), Controller (API routes). "
        "Services = helper “workers” that do math/planning so routes stay short.",
    )

    # ========== CH2 HOW IT WORKS ==========
    story.append(Paragraph("2. How the Travel component works (big picture)", s["h1"]))
    story.append(Paragraph(
        "When you use the app, you walk through a <b>wizard</b> (step by step). "
        "Each step saves something important.",
        s["body"],
    ))
    story.append(code(
        """STEP 1  Login / Register
        → Backend checks email+password (or Google)
        → Gives you a JWT token (like a temporary ID card)
        → Browser stores it as access_token

STEP 2  Attractions page
        → Loads places from DB (public list)
        → You pick moods + attractions
        → Backend creates a “trip” row (user_trip_input)

STEP 3  Budget page
        → You enter total money
        → Backend splits into food / hotel / shopping / transport %

STEP 4  Accommodation page
        → Backend finds hotels near your destinations
        → You pick one hotel per place → saved on the trip

STEP 5  Itinerary page
        → Backend builds a day-by-day schedule FROM the DB places only
        → Saves generated_itinerary JSON

STEP 6  Recommendations + Export
        → Shows guides/agencies/businesses
        → Can download PDF of the plan

SOS button (header)
        → Uses your travel login token
        → Opens Tourist SOS app with a bridged session""",
        s,
    ))

    story.append(Paragraph("What happens on ONE button click (deep)", s["h2"]))
    story.append(Paragraph(
        "Example: you click <b>“Generate itinerary”</b>.",
        s["body"],
    ))
    story.append(code(
        """1. ItineraryPage.jsx runs JavaScript → itineraryApi.generate(tripId)
2. api/client.js Axios adds header: Authorization: Bearer <token>
3. Browser calls POST http://localhost:5180/api/itinerary/generate
4. Vite (vite.config.js) silently forwards that to http://127.0.0.1:5002/...
5. Flask finds the function in routes/itinerary.py (Controller)
6. @jwt_required() checks the token is real (JWT_SECRET_KEY)
7. get_user_trip() loads YOUR trip only (not someone else’s)
8. services/ai_service.py + trip_plan_service.py build the plan
9. SQLAlchemy saves GeneratedItinerary into PostgreSQL
10. Flask returns JSON → React shows the days on screen

That whole chain is the “magic”. No single file does everything —
each file does one small job, then passes the baton.""",
        s,
    ))

    # ========== CH3 FOLDER MAP ==========
    story.append(PageBreak())
    story.append(Paragraph("3. Folder map (where to look)", s["h1"]))
    story.append(code(
        """tour-ceylon/
  frontend/travel/          ← what you SEE (View)
    src/pages/              ← each wizard screen
    src/context/            ← memory while you click around
    src/api/                ← phone calls to backend
  backend/                  ← BRAIN + API (Controller + Model)
    app/models/             ← table shapes
    app/routes/             ← URL handlers
    app/services/           ← planning / budget / PDF logic
    data/travel/            ← Excel seed files
    database/               ← schema.sql
    scripts/travel/         ← first-time DB load tools
    run.py                  ← start the server""",
        s,
    ))

    # ========== CH4 BACKEND FILES ==========
    story.append(Paragraph("4. Backend files — simple English + how they connect", s["h1"]))

    story.append(Paragraph("4.1 Starting the server", s["h2"]))
    file_block(
        story, s, "backend/run.py",
        "The power button for the API.",
        "Runs create_app() and listens on port 5002.",
        "Without this process running, the website cannot save trips or generate plans.",
        "app/__init__.py",
    )
    file_block(
        story, s, "backend/app/__init__.py",
        "The factory that builds the whole web app.",
        "Loads config, turns on database + JWT + CORS, plugs in every route blueprint "
        "(auth, attractions, trip-input, budget, itinerary…).",
        "This is the switchboard. A URL arrives → this file already registered which "
        "Python function should answer.",
        "config.py, all routes/, models/",
    )
    file_block(
        story, s, "backend/app/config.py + backend/.env",
        "Settings and secrets.",
        "Database password, JWT secret, Google client id, money rate, CORS allowed sites.",
        "Changing .env changes behaviour without rewriting Python (e.g. different Postgres password).",
        "create_app reads Config from here",
    )

    story.append(Paragraph("4.2 Models (the filing cabinet drawers)", s["h2"]))
    tip(
        story, s,
        "A Model is a Python class that matches one database table. "
        "When you do User.query.filter_by(email=…), SQLAlchemy writes SQL for you.",
    )
    file_block(
        story, s, "models/__init__.py",
        "Import list so Flask knows all Travel tables exist.",
        "Imports User, Attraction, Accommodation, UserTripInput, BudgetSplit, etc.",
        "If a model is not imported, create_all / metadata may miss that table.",
        "Every model file below",
    )
    file_block(
        story, s, "models/user.py",
        "A tourist login account.",
        "Stores email, password hash (not plain password!), Google id, name.",
        "check_password() compares typed password to the hash. Login success → JWT with this user’s id.",
        "routes/auth.py, AuthContext",
    )
    file_block(
        story, s, "models/attraction.py",
        "A place to visit (Sigiriya, beach, temple…).",
        "Name, mood_tag, destination, image path. Filled from Excel seed.",
        "Attractions page filters by mood_tag. Trip stores selected attraction ids/names as JSON.",
        "routes/attractions.py, seed_data.py",
    )
    file_block(
        story, s, "models/accommodation.py",
        "A hotel / stay option.",
        "Seeded hotel rows. User picks hotels for each destination on the trip.",
        "Itinerary builder uses chosen hotels as overnight base for each day.",
        "routes/accommodation.py, trip_plan_service.py",
    )
    file_block(
        story, s, "models/user_trip_input.py",
        "THE main trip document (heart of Travel).",
        "One row per trip: days, moods, finalized_attractions (JSON), hotels (JSON), budget, status.",
        "Almost every wizard step updates this row. trip_id is a UUID primary key.",
        "trip_input routes, budget, itinerary, TripContext.tripId",
    )
    file_block(
        story, s, "models/budget_split.py",
        "Money split for one trip.",
        "Food / accommodation / shopping / transport amounts and percentages.",
        "Linked 1-to-1 with user_trip_input. Itinerary generate refuses to run without it.",
        "routes/budget.py",
    )
    file_block(
        story, s, "models/generated_itinerary.py",
        "Saved day-plan result.",
        "Stores the generated itinerary JSON + timestamps.",
        "History page reads these. PDF export reads these.",
        "routes/itinerary.py",
    )
    file_block(
        story, s, "models/business_directory.py, travel_agency.py, tourist_guide.py",
        "Recommendation catalogs.",
        "Extra lists for the recommendations step (cafes, agencies, licensed guides).",
        "Mostly read-only after seeding. Search filters on guides.",
        "routes/recommendations.py",
    )
    file_block(
        story, s, "models/saved_reference.py",
        "Bookmarks onto a trip.",
        "Saves “I liked this guide/agency” linked to trip_id.",
        "Lets recommendations stick to the trip for export/history.",
        "routes/saved_references.py",
    )

    story.append(PageBreak())
    story.append(Paragraph("4.3 Controllers / routes (the waiters taking orders)", s["h2"]))
    tip(
        story, s,
        "A route = one URL + HTTP method. Example: POST /api/auth/login. "
        "Decorator @jwt_required() means “show your ID card (token) first”.",
    )
    file_block(
        story, s, "routes/auth.py",
        "Door security for Travel users.",
        "register, login (email), google, me, link-account. Builds JWT with role=travel_user.",
        "Password is never stored raw — only a hash. JWT is signed with JWT_SECRET_KEY so "
        "nobody can forge “I am user 99” without the secret.",
        "LoginPage + AuthContext; also police username login on same /login path",
    )
    file_block(
        story, s, "routes/attractions.py",
        "Menu of places (public).",
        "GET /api/attractions?moods=Culture,Nature",
        "No login needed so the list can load fast. Filtering happens in SQLAlchemy query.",
        "AttractionsPage",
    )
    file_block(
        story, s, "routes/trip_input.py",
        "Create and edit the trip.",
        "POST creates trip; PATCH updates hotels/fields; GET lists history.",
        "Always checks the trip belongs to the logged-in user (get_user_trip). "
        "That stops User A from editing User B’s holiday.",
        "TripContext + Attractions/Accommodation pages",
    )
    file_block(
        story, s, "routes/budget.py",
        "Money calculator endpoint.",
        "POST /api/budget/split with trip_id + budget (+ optional custom %).",
        "Calls budget_service to make sure percentages add to 100, then saves BudgetSplit.",
        "BudgetPage",
    )
    file_block(
        story, s, "routes/accommodation.py",
        "Hotel picker data.",
        "GET /api/accommodation?trip_id=…",
        "Looks at destinations inside the trip’s attractions, returns matching hotels.",
        "AccommodationPage",
    )
    file_block(
        story, s, "routes/itinerary.py",
        "Plan generator + PDF.",
        "POST generate, GET plan, history, pdf download.",
        "Refuses if attractions/hotels/budget missing — forces the wizard order. "
        "Generation uses services, then commits GeneratedItinerary.",
        "ItineraryPage, ExportPage, HistoryPage",
    )
    file_block(
        story, s, "routes/recommendations.py + saved_references.py",
        "Extra suggestions + save buttons.",
        "List guides/agencies/businesses; save chosen ones on the trip.",
        "Guides support search query params (name, language, limit…).",
        "RecommendationsPage",
    )
    file_block(
        story, s, "routes/media.py + images.py",
        "Pictures.",
        "Serves attraction image files; optional URL resolve helper.",
        "Attraction cards show photos from /api/media/attractions/…",
        "AttractionPhoto.jsx, static/attractions/",
    )

    story.append(Paragraph("4.4 Services &amp; helpers (the kitchen staff)", s["h2"]))
    file_block(
        story, s, "services/trip_plan_service.py",
        "Understands destinations and days.",
        "Groups attractions by day, finds hotel for a day, validates hotel picks.",
        "Shared brain used by trip_input, accommodation listing, and itinerary generation.",
        "routes/trip_input, accommodation, ai_service",
    )
    file_block(
        story, s, "services/budget_service.py",
        "Percentage maths only.",
        "Default 25/35/15/25 split; validate; calculate LKR amounts.",
        "Keeps ugly maths out of the route file so routes stay readable.",
        "routes/budget.py",
    )
    file_block(
        story, s, "services/ai_service.py",
        "Builds the timetable (name is old — it uses DB rules).",
        "Creates timed activities from seeded attractions + hotels. Mood changes start hour "
        "(e.g. Spiritual earlier, Relaxed later).",
        "Important: it does not invent fake places. Only DB rows. That keeps the plan trustworthy.",
        "routes/itinerary.py",
    )
    file_block(
        story, s, "services/pdf_service.py",
        "Turns the plan into a PDF file.",
        "Used by GET /api/itinerary/&lt;id&gt;/pdf.",
        "Browser downloads bytes; Export page links here with your JWT.",
        "ExportPage",
    )
    file_block(
        story, s, "utils/trip_helpers.py",
        "Tiny security helpers.",
        "get_current_user_id() from JWT; get_user_trip(id) ownership check.",
        "Used everywhere a trip is loaded so we never skip the “is this yours?” check.",
        "All protected trip routes",
    )

    story.append(Paragraph("4.5 Seed / database scripts (first-time only)", s["h2"]))
    file_block(
        story, s, "data/travel/*.xlsx + tourist_guides.csv",
        "Raw Sri Lanka reference data.",
        "Human-editable Excel/CSV sources.",
        "Not used at runtime every request — copied into Postgres by seed_data.py once.",
        "seed_data.py",
    )
    file_block(
        story, s, "database/schema.sql + migrations/",
        "Blueprint of tables.",
        "SQL that creates columns/keys/enums.",
        "apply_schema.py runs this against travel_app.",
        "PostgreSQL",
    )
    file_block(
        story, s, "scripts/travel/apply_schema.py",
        "Builds empty tables.",
        "Connects with DATABASE_URL and executes schema.sql.",
        "Do this before seed, or seed will fail with “table does not exist”.",
        "database/schema.sql",
    )
    file_block(
        story, s, "scripts/travel/seed_data.py",
        "Fills catalogs from Excel.",
        "Reads data/travel files with pandas, inserts thousands of rows.",
        "Also normalizes messy place names so “Kandy Municipal…” becomes “Kandy”.",
        "Excel files + models",
    )
    file_block(
        story, s, "scripts/travel/excel_attraction_images.py",
        "Pulls pictures out of the Excel workbook.",
        "Excel can embed images; this extracts them to static/attractions.",
        "Then attraction.image points to /api/media/… so the UI can show them.",
        "media route + AttractionsPage",
    )

    # ========== CH5 FRONTEND ==========
    story.append(PageBreak())
    story.append(Paragraph("5. Frontend files — simple English + how they connect", s["h1"]))
    tip(
        story, s,
        "React components are LEGO blocks. A Page is a full screen. "
        "Context is shared memory so AttractionsPage and BudgetPage share the same tripId.",
    )

    file_block(
        story, s, "src/main.jsx",
        "App ignition.",
        "Wraps everything in Router + AuthProvider + TripProvider, then renders App.",
        "Providers must wrap App so every page can call useAuth() / useTrip().",
        "App.jsx, contexts",
    )
    file_block(
        story, s, "src/App.jsx",
        "Map of pages + lock on private pages.",
        "Defines routes. ProtectedRoute sends you to /login if no token.",
        "Progress bar % is just a prop on Layout (25, 45, 65…) — visual wizard cue.",
        "All pages",
    )
    file_block(
        story, s, "src/context/AuthContext.jsx",
        "“Am I logged in?” memory.",
        "login/register/logout; saves access_token + user in localStorage.",
        "On refresh, token is still there so you stay logged in until it expires or 401.",
        "client.js authApi, LoginPage",
    )
    file_block(
        story, s, "src/context/TripContext.jsx",
        "Wizard scratchpad.",
        "Holds tripId, moods, days, budget, hotels, itinerary in React state.",
        "Fast UI updates without waiting for DB on every keypress. "
        "Important saves still call the API so data is not lost on refresh.",
        "Wizard pages",
    )
    file_block(
        story, s, "src/api/client.js",
        "The telephone to the Travel API.",
        "Axios instance with /api base URL; auto-attaches Bearer token; "
        "on bad JWT redirects to login.",
        "One place for networking — pages stay cleaner.",
        "Backend /api/* travel routes",
    )
    file_block(
        story, s, "src/api/sosClient.js",
        "Side door to SOS.",
        "bridge-travel exchanges travel JWT for SOS tourist session; opens :5175.",
        "Lets one login feel connected across Travel + SOS without typing twice.",
        "Layout SOS button, tourists bridge route",
    )
    file_block(
        story, s, "src/components/Layout.jsx",
        "Frame around pages.",
        "Header links, progress, SOS, logout.",
        "Children = the current page content.",
        "App.jsx",
    )
    file_block(
        story, s, "src/components/AttractionPhoto.jsx",
        "Shows one photo safely.",
        "Handles missing images / media URLs.",
        "Used in attraction cards.",
        "AttractionsPage",
    )
    file_block(
        story, s, "pages/LoginPage.jsx",
        "Sign-in screen.",
        "Email/password or Google → AuthContext.",
        "First token appears here — without it ProtectedRoute blocks the wizard.",
        "auth routes",
    )
    file_block(
        story, s, "pages/AttractionsPage.jsx",
        "Step 1 screen.",
        "Fetch attractions, select moods/places, create trip via API.",
        "Writes tripId into TripContext so later steps know which trip to update.",
        "attractions + trip-input APIs",
    )
    file_block(
        story, s, "pages/BudgetPage.jsx",
        "Step 2 screen.",
        "Total budget + split → budget API.",
        "Must succeed before itinerary generate is allowed.",
        "budget API",
    )
    file_block(
        story, s, "pages/AccommodationPage.jsx",
        "Step 3 screen.",
        "Load hotels for destinations; save picks on trip.",
        "PATCH trip-input stores accommodations JSON.",
        "accommodation + trip-input APIs",
    )
    file_block(
        story, s, "pages/ItineraryPage.jsx",
        "Step 4 screen.",
        "Calls generate; draws the day plan.",
        "This is where ai_service “magic” becomes visible to the user.",
        "itinerary API",
    )
    file_block(
        story, s, "pages/RecommendationsPage.jsx",
        "Step 5 screen.",
        "Browse guides/agencies/businesses; optional save.",
        "Uses recommendation + saved-references endpoints.",
        "recommendations APIs",
    )
    file_block(
        story, s, "pages/ExportPage.jsx",
        "Step 6 screen.",
        "Download PDF / final summary.",
        "PDF URL needs JWT — same token as other calls.",
        "itinerary pdf route",
    )
    file_block(
        story, s, "pages/HistoryPage.jsx + ProfilePage.jsx",
        "Past trips + account/SOS profile.",
        "History reloads trips/itineraries. Profile may show linked SOS visitor info.",
        "Useful after you close the browser — data came back from DB, not only TripContext.",
        "trip-input, itinerary history, sosClient",
    )
    file_block(
        story, s, "styles/global.css + theme/sosProfile.js",
        "Look and feel.",
        "CSS + small style tokens.",
        "Does not change business logic — only appearance.",
        "Layout / pages",
    )
    file_block(
        story, s, "vite.config.js (frontend/travel)",
        "Dev helper.",
        "Port 5180; proxy /api and /sos-api → backend 5002.",
        "So the browser can call /api/... without CORS pain in development.",
        "Flask backend",
    )

    # ========== CH6 DIAGRAM ==========
    story.append(PageBreak())
    story.append(Paragraph("6. Connection diagram (how files “hold hands”)", s["h1"]))
    story.append(code(
        """[LoginPage] --authApi--> [client.js] --HTTP--> [routes/auth.py] --> [models/user.py] --> DB
                                      |
                                      +-- JWT stored by [AuthContext]

[AttractionsPage] --attractionsApi--> [routes/attractions.py] --> [models/attraction.py]
                 --tripApi----------> [routes/trip_input.py] --> [models/user_trip_input.py]
                 updates [TripContext.tripId]

[BudgetPage] ----budgetApi---------> [routes/budget.py] --> [budget_service.py]
                                                         --> [models/budget_split.py]

[AccommodationPage] --accommodationApi--> [routes/accommodation.py] --> [trip_plan_service.py]
                    --tripApi PATCH-----> [routes/trip_input.py]

[ItineraryPage] --itineraryApi.generate--> [routes/itinerary.py]
                                          --> [ai_service.py] + [trip_plan_service.py]
                                          --> [models/generated_itinerary.py]

[ExportPage] ---- PDF URL --------------> [routes/itinerary.py] --> [pdf_service.py]

[Layout SOS] ----sosClient--------------> [routes/tourists.py bridge-travel]
                                          --> opens frontend/tourist""",
        s,
    ))

    story.append(Paragraph("7. Database story (beginner)", s["h1"]))
    story.append(Paragraph(
        "Think of two kinds of data:",
        s["body"],
    ))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "<b>Reference data</b> — attractions, hotels, guides… loaded from Excel. "
            "Shared by all users. Rarely changes while the app runs.",
            s["body"],
        )),
        ListItem(Paragraph(
            "<b>User data</b> — your account, your trips, your budget split, your generated plan. "
            "Private. Protected by JWT + ownership checks.",
            s["body"],
        )),
    ], bulletType="bullet"))
    tip(
        story, s,
        "First-time setup = create empty drawers (schema) then fill catalogs (seed). "
        "Everyday use = only run.py + npm run dev. You do not re-seed every day.",
    )

    story.append(Paragraph("8. Security in simple words", s["h1"]))
    story.append(ListFlowable([
        ListItem(Paragraph("Passwords are hashed — even the database admin should not see your real password.", s["body"])),
        ListItem(Paragraph("JWT is a signed ticket. Changing a bit of it makes the signature fail.", s["body"])),
        ListItem(Paragraph("get_user_trip ensures trip_id in the URL belongs to the ticket’s user id.", s["body"])),
        ListItem(Paragraph(".env secrets stay on the server — never put JWT_SECRET_KEY in the React code.", s["body"])),
    ], bulletType="bullet"))

    story.append(Paragraph("9. How to study this as a beginner (suggested order)", s["h1"]))
    story.append(code(
        """1. Run backend + frontend (see RUN_GUIDE.pdf)
2. Click through the wizard once as a user
3. Read frontend: LoginPage → AttractionsPage → client.js
4. Read backend: auth.py → trip_input.py → user_trip_input.py
5. Read budget_service.py + ai_service.py (the “thinking”)
6. Watch Network tab in browser DevTools — see real JSON requests""",
        s,
    ))

    story.append(Spacer(1, 5 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LINE, spaceAfter=3))
    story.append(Paragraph(
        "You do not need to memorize every line. Learn the path: "
        "Page → api/client → route → service/model → database → JSON back to Page. "
        "That path is the whole Travel component.",
        s["body"],
    ))
    story.append(Paragraph(
        "File: TRAVEL_ARCHITECTURE.pdf  ·  Regenerate: "
        "python backend/scripts/generate_travel_architecture_pdf.py",
        s["small"],
    ))

    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=14 * mm, rightMargin=14 * mm,
        topMargin=11 * mm, bottomMargin=11 * mm,
        title="Tour Ceylon Travel Architecture (Beginner)",
        author="Tour Ceylon",
    )
    doc.build(story)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()
