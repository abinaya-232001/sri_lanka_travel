"""Generate Tour Ceylon RUN_GUIDE.pdf (first-time setup + everyday run)."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT = Path(__file__).resolve().parents[2] / "RUN_GUIDE.pdf"  # tour-ceylon/

TEAL = colors.HexColor("#0A4A52")
INK = colors.HexColor("#1A2332")
MUTED = colors.HexColor("#5A6570")
CODE_BG = colors.HexColor("#F2F6F7")
LINE = colors.HexColor("#D0DCE0")
ROW_ALT = colors.HexColor("#F5FAFA")


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "T",
            parent=base["Title"],
            fontSize=22,
            textColor=TEAL,
            spaceAfter=4,
            alignment=TA_CENTER,
        ),
        "sub": ParagraphStyle(
            "S",
            parent=base["Normal"],
            fontSize=11,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=16,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontSize=14,
            textColor=TEAL,
            spaceBefore=14,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontSize=12,
            textColor=INK,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "B",
            parent=base["Normal"],
            fontSize=10,
            textColor=INK,
            leading=14,
            spaceAfter=6,
        ),
        "code": ParagraphStyle(
            "C",
            parent=base["Code"],
            fontName="Courier",
            fontSize=8.5,
            leading=11,
            textColor=INK,
            backColor=CODE_BG,
            leftIndent=4,
            rightIndent=4,
            spaceBefore=4,
            spaceAfter=8,
        ),
        "note": ParagraphStyle(
            "N",
            parent=base["Normal"],
            fontSize=9,
            textColor=MUTED,
            leading=12,
            spaceAfter=6,
        ),
        "li": ParagraphStyle(
            "LI",
            parent=base["Normal"],
            fontSize=10,
            textColor=INK,
            leading=13,
        ),
    }


def code_block(text: str, s):
    return Preformatted(text.strip("\n"), s["code"])


def build():
    s = styles()
    story = []

    story.append(Paragraph("Tour Ceylon", s["title"]))
    story.append(Paragraph("Setup &amp; Run Guide (Backend + Frontend)", s["sub"]))
    story.append(HRFlowable(width="100%", thickness=1, color=LINE, spaceAfter=10))

    story.append(
        Paragraph(
            "Project folder: <b>D:\\tourceylon\\tour-ceylon</b> "
            "(change the drive/path if yours is different).",
            s["body"],
        )
    )

    # ---------- FIRST TIME ----------
    story.append(Paragraph("Part A — First-time setup", s["h1"]))
    story.append(
        Paragraph(
            "Do this once on a new PC (or after a fresh clone). "
            "You need Python 3.10+, Node.js 18+, and PostgreSQL + pgAdmin.",
            s["body"],
        )
    )

    story.append(Paragraph("A1. Create the database in pgAdmin", s["h2"]))
    story.append(
        ListFlowable(
            [
                ListItem(Paragraph("Open <b>pgAdmin</b> and connect to your local PostgreSQL server.", s["li"])),
                ListItem(Paragraph("Host: <b>localhost</b> &nbsp; Port: <b>5432</b> &nbsp; User: <b>postgres</b>", s["li"])),
                ListItem(Paragraph("Password = the one you set when installing PostgreSQL.", s["li"])),
                ListItem(Paragraph("Right-click <b>Databases</b> → <b>Create → Database</b>.", s["li"])),
                ListItem(Paragraph("Name: <b>travel_app</b> → Save.", s["li"])),
            ],
            bulletType="1",
            start=1,
        )
    )
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("A2. Backend virtualenv + packages", s["h2"]))
    story.append(code_block(
        r"""cd D:\tourceylon\tour-ceylon\backend
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env""",
        s,
    ))
    story.append(
        Paragraph(
            "Open <b>backend\\.env</b> and set your Postgres password, for example:",
            s["body"],
        )
    )
    story.append(code_block(
        r"""DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/travel_app
SECRET_KEY=dev-secret-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-change-in-production
PORT=5002
NOTIFY_MODE=console""",
        s,
    ))

    story.append(Paragraph("A3. Apply schema + seed data", s["h2"]))
    story.append(
        Paragraph(
            "Still in <b>backend</b> with venv activated:",
            s["body"],
        )
    )
    story.append(code_block(
        r"""cd D:\tourceylon\tour-ceylon\backend
.\.venv\Scripts\activate
python scripts\travel\apply_schema.py
python scripts\travel\seed_data.py
python seed_sos_data.py""",
        s,
    ))
    story.append(
        Paragraph(
            "This creates travel tables, loads Excel data from "
            "<b>backend\\data\\travel</b>, then SOS tables from "
            "<b>backend\\data\\sos</b>.",
            s["note"],
        )
    )

    story.append(Paragraph("A4. Install frontend dependencies", s["h2"]))
    story.append(code_block(
        r"""cd D:\tourceylon\tour-ceylon\frontend
npm install
npm run install:all""",
        s,
    ))

    # ---------- EVERY TIME ----------
    story.append(Paragraph("Part B — Every time you run the app", s["h1"]))
    story.append(
        Paragraph(
            "You need <b>2 terminals</b>: one for the backend, one for all frontends.",
            s["body"],
        )
    )

    story.append(Paragraph("B1. Start backend (Terminal 1)", s["h2"]))
    story.append(code_block(
        r"""cd D:\tourceylon\tour-ceylon\backend
.\.venv\Scripts\activate
python run.py""",
        s,
    ))
    story.append(
        Paragraph(
            "Leave this window open. API health check: "
            "<b>http://127.0.0.1:5002/api/health</b>",
            s["body"],
        )
    )

    story.append(Paragraph("B2. Start all frontends (Terminal 2)", s["h2"]))
    story.append(code_block(
        r"""cd D:\tourceylon\tour-ceylon\frontend
npm run dev""",
        s,
    ))
    story.append(
        Paragraph(
            "Leave this window open. All three UIs start together.",
            s["body"],
        )
    )

    story.append(Paragraph("B3. Open in browser", s["h2"]))
    data = [
        [Paragraph("<b>App</b>", s["body"]), Paragraph("<b>URL</b>", s["body"])],
        [Paragraph("Travel planner", s["body"]), Paragraph("http://localhost:5180", s["body"])],
        [Paragraph("Tourist SOS", s["body"]), Paragraph("http://localhost:5175", s["body"])],
        [Paragraph("Police dashboard", s["body"]), Paragraph("http://localhost:5174", s["body"])],
        [Paragraph("Backend API", s["body"]), Paragraph("http://127.0.0.1:5002", s["body"])],
    ]
    t = Table(data, colWidths=[55 * mm, 100 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), TEAL),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, 1), ROW_ALT),
                ("BACKGROUND", (0, 3), (-1, 3), ROW_ALT),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 6 * mm))

    # ---------- TIPS ----------
    story.append(Paragraph("Part C — Tips &amp; troubleshooting", s["h1"]))
    story.append(
        ListFlowable(
            [
                ListItem(
                    Paragraph(
                        "Always start <b>backend first</b>, then frontends.",
                        s["li"],
                    )
                ),
                ListItem(
                    Paragraph(
                        "If login/SOS fails after a code change: "
                        "<b>Log out → Log in again</b> (refresh JWT).",
                        s["li"],
                    )
                ),
                ListItem(
                    Paragraph(
                        "Postgres not running → pgAdmin connection timeout. "
                        "Start the PostgreSQL Windows service.",
                        s["li"],
                    )
                ),
                ListItem(
                    Paragraph(
                        "Port busy → close old <b>python run.py</b> / "
                        "<b>npm run dev</b> windows.",
                        s["li"],
                    )
                ),
                ListItem(
                    Paragraph(
                        "Police demo logins are in "
                        "<b>backend\\data\\sos\\station_credentials.csv</b> "
                        "(username like <b>st014</b>).",
                        s["li"],
                    )
                ),
                ListItem(
                    Paragraph(
                        "Do not commit <b>.env</b>, <b>.venv</b>, or "
                        "<b>node_modules</b> to GitHub.",
                        s["li"],
                    )
                ),
            ],
            bulletType="bullet",
        )
    )

    story.append(Spacer(1, 10 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LINE, spaceAfter=6))
    story.append(
        Paragraph(
            "Tour Ceylon — modular monolith (MVC). One backend on port 5002, "
            "three frontends under frontend/.",
            s["note"],
        )
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Tour Ceylon — Setup & Run Guide",
        author="Tour Ceylon",
    )
    doc.build(story)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()
