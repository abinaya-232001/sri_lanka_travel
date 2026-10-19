"""Generate TRAVEL_API_DOCS.pdf — Tour Ceylon travel component API reference."""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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

OUT = Path(__file__).resolve().parents[2] / "TRAVEL_API_DOCS.pdf"  # tour-ceylon/

TEAL = colors.HexColor("#0A4A52")
INK = colors.HexColor("#1A2332")
MUTED = colors.HexColor("#5A6570")
CODE_BG = colors.HexColor("#F2F6F7")
LINE = colors.HexColor("#D0DCE0")
ROW_ALT = colors.HexColor("#F5FAFA")
GREEN = colors.HexColor("#166534")
AMBER = colors.HexColor("#92400E")


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "T", parent=base["Title"], fontSize=20, textColor=TEAL,
            alignment=TA_CENTER, spaceAfter=4,
        ),
        "sub": ParagraphStyle(
            "S", parent=base["Normal"], fontSize=10, textColor=MUTED,
            alignment=TA_CENTER, spaceAfter=12,
        ),
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontSize=13, textColor=TEAL,
            spaceBefore=12, spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontSize=11, textColor=INK,
            spaceBefore=8, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "B", parent=base["Normal"], fontSize=9.5, textColor=INK,
            leading=13, spaceAfter=4,
        ),
        "meta": ParagraphStyle(
            "M", parent=base["Normal"], fontSize=9, textColor=MUTED,
            leading=12, spaceAfter=3,
        ),
        "code": ParagraphStyle(
            "C", parent=base["Code"], fontName="Courier", fontSize=7.5,
            leading=10, textColor=INK, backColor=CODE_BG,
            leftIndent=2, rightIndent=2, spaceBefore=2, spaceAfter=6,
        ),
        "method": ParagraphStyle(
            "Meth", parent=base["Normal"], fontSize=9, textColor=TEAL,
            fontName="Helvetica-Bold", spaceAfter=2,
        ),
    }


def code(text: str, s):
    return Preformatted(text.strip("\n"), s["code"])


def jdump(obj) -> str:
    return json.dumps(obj, indent=2)


def endpoint(story, s, method, path, auth, desc, req=None, resp=None, params=None):
    block = []
    block.append(Paragraph(f"{method}  {path}", s["method"]))
    block.append(Paragraph(desc, s["body"]))
    block.append(Paragraph(f"<b>Auth:</b> {auth}", s["meta"]))
    if params:
        block.append(Paragraph(f"<b>Query/params:</b> {params}", s["meta"]))
    if req is not None:
        block.append(Paragraph("<b>Sample request</b>", s["meta"]))
        block.append(code(jdump(req) if not isinstance(req, str) else req, s))
    if resp is not None:
        block.append(Paragraph("<b>Sample response</b>", s["meta"]))
        block.append(code(jdump(resp) if not isinstance(resp, str) else resp, s))
    block.append(Spacer(1, 3 * mm))
    story.append(KeepTogether(block))


def build(backend_live: bool, health_body: str | None):
    s = styles()
    story = []

    story.append(Paragraph("Tour Ceylon — Travel Component", s["title"]))
    story.append(Paragraph("Backend API Documentation", s["sub"]))
    story.append(HRFlowable(width="100%", thickness=1, color=LINE, spaceAfter=8))

    # 1. Base URL
    story.append(Paragraph("1. Base URL / Port", s["h1"]))
    story.append(Paragraph(
        "Unified Flask backend (Travel + SOS in one process).",
        s["body"],
    ))
    data = [
        [Paragraph("<b>Item</b>", s["body"]), Paragraph("<b>Value</b>", s["body"])],
        [Paragraph("Base URL", s["body"]), Paragraph("http://127.0.0.1:5002", s["body"])],
        [Paragraph("API prefix", s["body"]), Paragraph("/api", s["body"])],
        [Paragraph("Full API root", s["body"]), Paragraph("http://127.0.0.1:5002/api", s["body"])],
        [Paragraph("Health check", s["body"]), Paragraph("GET /api/health", s["body"])],
        [Paragraph("Frontend (Travel UI)", s["body"]), Paragraph("http://localhost:5180", s["body"])],
        [Paragraph("Dev proxy", s["body"]), Paragraph("Vite proxies /api → :5002", s["body"])],
    ]
    t = Table(data, colWidths=[45 * mm, 115 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("BACKGROUND", (0, 2), (-1, 2), ROW_ALT),
        ("BACKGROUND", (0, 4), (-1, 4), ROW_ALT),
        ("BACKGROUND", (0, 6), (-1, 6), ROW_ALT),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 4 * mm))

    # 4 first? User asked 5 items - I'll put status near top as section 5 at end, auth as section
    story.append(Paragraph("2. Authentication &amp; headers", s["h1"]))
    story.append(Paragraph(
        "Most travel endpoints require a JWT from register/login.",
        s["body"],
    ))
    story.append(code(
        "Authorization: Bearer <access_token>\n"
        "Content-Type: application/json",
        s,
    ))
    story.append(Paragraph(
        "Store <b>access_token</b> from login/register in localStorage "
        "(Travel UI key: <b>access_token</b>). "
        "Public (no JWT): health, attractions list, Google config, media images.",
        s["body"],
    ))

    # Endpoint list summary table
    story.append(Paragraph("3. Live travel endpoints (summary)", s["h1"]))
    rows = [
        [Paragraph("<b>Method</b>", s["body"]), Paragraph("<b>Path</b>", s["body"]), Paragraph("<b>Auth</b>", s["body"])],
        ["GET", "/api/health", "No"],
        ["POST", "/api/auth/register", "No"],
        ["POST", "/api/auth/login", "No"],
        ["POST", "/api/auth/google", "No"],
        ["GET", "/api/auth/google/config", "No"],
        ["POST", "/api/auth/link-account", "No"],
        ["GET", "/api/auth/me", "JWT"],
        ["GET", "/api/attractions", "No"],
        ["GET", "/api/media/attractions/&lt;file&gt;", "No"],
        ["GET", "/api/images/resolve", "No*"],
        ["GET", "/api/trip-input", "JWT"],
        ["POST", "/api/trip-input", "JWT"],
        ["GET", "/api/trip-input/&lt;trip_id&gt;", "JWT"],
        ["PATCH", "/api/trip-input/&lt;trip_id&gt;", "JWT"],
        ["POST", "/api/budget/split", "JWT"],
        ["GET", "/api/budget/split/&lt;trip_id&gt;", "JWT"],
        ["GET", "/api/accommodation", "JWT*"],
        ["POST", "/api/itinerary/generate", "JWT"],
        ["GET", "/api/itinerary/&lt;trip_id&gt;", "JWT"],
        ["GET", "/api/itinerary/history", "JWT"],
        ["GET", "/api/itinerary/&lt;trip_id&gt;/pdf", "JWT"],
        ["GET", "/api/business-directory", "No*"],
        ["GET", "/api/travel-agencies", "No*"],
        ["GET", "/api/tourist-guides", "No"],
        ["POST", "/api/saved-references", "JWT"],
        ["GET", "/api/saved-references", "JWT"],
    ]
    table_data = [rows[0]] + [
        [Paragraph(str(c), s["body"]) for c in r] for r in rows[1:]
    ]
    st = Table(table_data, colWidths=[22 * mm, 95 * mm, 40 * mm])
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.3, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    st.setStyle(TableStyle(style_cmds))
    story.append(st)
    story.append(Paragraph(
        "* Some list endpoints accept optional trip_id; accommodation typically needs trip_id.",
        s["meta"],
    ))

    story.append(PageBreak())
    story.append(Paragraph("4. Sample request / response (each endpoint)", s["h1"]))

    endpoint(
        story, s, "GET", "/api/health", "None",
        "Liveness check for the unified backend.",
        resp={"status": "ok", "app": "tour-ceylon-unified"},
    )

    endpoint(
        story, s, "POST", "/api/auth/register", "None",
        "Create a travel user account (email + password, min 6 chars).",
        req={"email": "visitor@example.com", "password": "secret123"},
        resp={
            "access_token": "<jwt>",
            "user": {
                "id": 1,
                "email": "visitor@example.com",
                "name": None,
                "auth_provider": "password",
            },
        },
    )

    endpoint(
        story, s, "POST", "/api/auth/login", "None",
        "Travel login with email. (Police uses username on the same path.)",
        req={"email": "visitor@example.com", "password": "secret123"},
        resp={
            "access_token": "<jwt>",
            "user": {"id": 1, "email": "visitor@example.com", "auth_provider": "password"},
        },
    )

    endpoint(
        story, s, "GET", "/api/auth/me", "Bearer JWT",
        "Return the logged-in travel user (or officer if role=officer).",
        resp={"user": {"id": 1, "email": "visitor@example.com", "name": "Alex"}},
    )

    endpoint(
        story, s, "POST", "/api/auth/google", "None",
        "Exchange Google GIS credential for app JWT. Requires GOOGLE_CLIENT_ID in .env.",
        req={"credential": "<google-id-token>"},
        resp={"access_token": "<jwt>", "user": {"email": "you@gmail.com", "auth_provider": "google"}},
    )

    endpoint(
        story, s, "GET", "/api/auth/google/config", "None",
        "Whether Google Sign-In button should show.",
        resp={"enabled": True, "client_id": "<GOOGLE_CLIENT_ID or null>"},
    )

    endpoint(
        story, s, "POST", "/api/auth/link-account", "None",
        "Bridge helper: create/verify travel user for shared SOS account linking.",
        req={"email": "visitor@example.com", "password": "secret123", "name": "Alex"},
        resp={"access_token": "<jwt>", "user": {"email": "visitor@example.com"}, "created": False},
    )

    endpoint(
        story, s, "GET", "/api/attractions", "None",
        "List attractions; optional mood filter.",
        params="moods=Culture,Nature (comma-separated)",
        resp={
            "attractions": [
                {
                    "id": 1,
                    "attraction_name": "Sigiriya",
                    "mood_tag": "Culture",
                    "normalized_destination": "Sigiriya",
                    "image": "/api/media/attractions/001-sigiriya.jpeg",
                }
            ],
            "count": 1,
            "available_moods": ["Adventure", "Culture", "Nature"],
            "filtered_moods": ["Culture"],
        },
    )

    endpoint(
        story, s, "GET", "/api/media/attractions/<filename>", "None",
        "Serve extracted attraction image files from backend/static/attractions.",
        resp="(binary image)",
    )

    endpoint(
        story, s, "POST", "/api/trip-input", "Bearer JWT",
        "Create a trip plan (days, moods, selected attractions).",
        req={
            "days": 5,
            "selected_moods": ["Culture", "Nature"],
            "finalized_attractions": [
                {"id": 12, "attraction_name": "Sigiriya", "normalized_destination": "Sigiriya"}
            ],
            "budget": 150000,
        },
        resp={
            "trip": {
                "trip_id": "a1b2c3d4-....",
                "days": 5,
                "selected_moods": ["Culture", "Nature"],
                "status": "draft",
            }
        },
    )

    endpoint(
        story, s, "GET", "/api/trip-input", "Bearer JWT",
        "List trips for the current user (history).",
        resp={"trips": [{"trip_id": "...", "days": 5, "status": "draft"}]},
    )

    endpoint(
        story, s, "GET", "/api/trip-input/<trip_id>", "Bearer JWT",
        "Get one trip owned by the current user.",
        resp={"trip": {"trip_id": "...", "days": 5, "finalized_attractions": []}},
    )

    endpoint(
        story, s, "PATCH", "/api/trip-input/<trip_id>", "Bearer JWT",
        "Update trip fields (e.g. hotel picks per destination).",
        req={
            "accommodations_by_destination": {
                "Sigiriya": {"id": 44, "name": "Hotel Example"}
            }
        },
        resp={"trip": {"trip_id": "...", "accommodations_by_destination": {"Sigiriya": 44}}},
    )

    endpoint(
        story, s, "POST", "/api/budget/split", "Bearer JWT",
        "Create/update budget split for a trip (default % or custom).",
        req={
            "trip_id": "a1b2c3d4-....",
            "budget": 150000,
            "customize": False,
        },
        resp={
            "trip_id": "a1b2c3d4-....",
            "budget": 150000,
            "split": {
                "food": 37500,
                "accommodation": 52500,
                "shopping": 22500,
                "transport": 37500,
                "food_pct": 25,
                "accommodation_pct": 35,
                "shopping_pct": 15,
                "transport_pct": 25,
            },
            "daily_estimate": 30000,
        },
    )

    endpoint(
        story, s, "GET", "/api/budget/split/<trip_id>", "Bearer JWT",
        "Fetch saved budget split for a trip.",
        resp={"trip_id": "...", "split": {"food": 37500, "accommodation": 52500}},
    )

    endpoint(
        story, s, "GET", "/api/accommodation", "Bearer JWT (typical)",
        "List hotels filtered for the trip destinations.",
        params="trip_id=<uuid>",
        resp={"accommodations": [{"id": 44, "name": "Hotel Example", "location": "Sigiriya"}]},
    )

    endpoint(
        story, s, "POST", "/api/itinerary/generate", "Bearer JWT",
        "Generate day-by-day itinerary (needs attractions + hotels + budget).",
        req={"trip_id": "a1b2c3d4-....", "day_start": "09:00"},
        resp={
            "itinerary": {
                "id": 1,
                "trip_id": "a1b2c3d4-....",
                "itinerary": {"days": [{"day": 1, "items": []}]},
            }
        },
    )

    endpoint(
        story, s, "GET", "/api/itinerary/<trip_id>", "Bearer JWT",
        "Get latest generated itinerary for a trip.",
        resp={"itinerary": {"itinerary": {"days": []}}},
    )

    endpoint(
        story, s, "GET", "/api/itinerary/history", "Bearer JWT",
        "All saved itineraries for the logged-in user.",
        resp={"items": [{"trip_id": "...", "created_at": "2026-07-30T..."}]},
    )

    endpoint(
        story, s, "GET", "/api/itinerary/<trip_id>/pdf", "Bearer JWT",
        "Download itinerary PDF (binary application/pdf).",
        resp="(PDF file bytes)",
    )

    endpoint(
        story, s, "GET", "/api/business-directory", "Optional trip context",
        "List businesses; may filter by trip destination when trip_id given.",
        params="trip_id=<uuid> (optional)",
        resp={"businesses": [{"id": 1, "name": "Example Cafe", "location": "Kandy"}]},
    )

    endpoint(
        story, s, "GET", "/api/travel-agencies", "Optional trip context",
        "List travel agencies.",
        params="trip_id=<uuid> (optional)",
        resp={"agencies": [{"id": 1, "name": "Ceylon Tours"}]},
    )

    endpoint(
        story, s, "GET", "/api/tourist-guides", "None",
        "Search tourist guides.",
        params="name, registration_no, guide_type, language, limit, offset",
        resp={"guides": [{"id": 1, "name": "Guide Name", "languages": "English, Sinhala"}], "count": 1},
    )

    endpoint(
        story, s, "POST", "/api/saved-references", "Bearer JWT",
        "Save a business/agency/guide reference onto a trip.",
        req={"trip_id": "...", "ref_type": "guide", "ref_id": 12},
        resp={"saved": {"id": 1, "trip_id": "...", "ref_type": "guide", "ref_id": 12}},
    )

    endpoint(
        story, s, "GET", "/api/saved-references", "Bearer JWT",
        "List saved references for the user / trip.",
        params="trip_id=<uuid> (optional)",
        resp={"saved_references": []},
    )

    # Status
    story.append(PageBreak())
    story.append(Paragraph("5. Current backend status", s["h1"]))
    if backend_live:
        story.append(Paragraph(
            "<font color='#166534'><b>RUNNING &amp; TESTABLE</b></font> — "
            "GET /api/health succeeded while this PDF was generated.",
            s["body"],
        ))
        if health_body:
            story.append(code(health_body, s))
    else:
        story.append(Paragraph(
            "<font color='#92400E'><b>IMPLEMENTED — NOT RUNNING RIGHT NOW</b></font>",
            s["body"],
        ))
        story.append(Paragraph(
            "The Travel API code is complete in the unified "
            "<b>tour-ceylon/backend</b> (port <b>5002</b>). "
            "At PDF generation time, nothing answered on "
            "http://127.0.0.1:5002/api/health.",
            s["body"],
        ))
        story.append(Paragraph("To make it testable:", s["body"]))
        story.append(code(
            r"""cd D:\tourceylon\tour-ceylon\backend
.\.venv\Scripts\activate
python run.py

# then open:
# http://127.0.0.1:5002/api/health""",
            s,
        ))

    story.append(Paragraph("How to smoke-test quickly", s["h2"]))
    story.append(code(
        r"""# 1) Health
curl http://127.0.0.1:5002/api/health

# 2) Register
curl -X POST http://127.0.0.1:5002/api/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"demo@example.com\",\"password\":\"secret123\"}"

# 3) Attractions (public)
curl http://127.0.0.1:5002/api/attractions

# 4) Authenticated call (paste token)
curl http://127.0.0.1:5002/api/trip-input ^
  -H "Authorization: Bearer YOUR_TOKEN""",
        s,
    ))

    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LINE, spaceAfter=4))
    story.append(Paragraph(
        "Scope: Travel component only. SOS/Police endpoints live on the same server "
        "under /api/tourists, /api/incidents, etc., but are documented separately.",
        s["meta"],
    ))

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Tour Ceylon Travel API Docs",
        author="Tour Ceylon",
    )
    doc.build(story)
    print(f"Wrote {OUT}")


def probe_health():
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen("http://127.0.0.1:5002/api/health", timeout=2) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return True, body
    except Exception:
        return False, None


if __name__ == "__main__":
    live, body = probe_health()
    build(live, body)
