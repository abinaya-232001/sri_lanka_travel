"""Database models: only what the SOS flow needs."""

from datetime import date, datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


def _iso(dt):
    return dt.isoformat() + "Z" if dt else None


class PasswordMixin:
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password or "")


class Tourist(PasswordMixin, db.Model):
    __tablename__ = "tourists"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(32))
    nationality = db.Column(db.String(80))
    passport = db.Column(db.String(20))
    language = db.Column(db.String(8), default="en")
    visa_type = db.Column(db.String(80))
    arrival_date = db.Column(db.Date)
    visa_expiry = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    family_contacts = db.relationship("FamilyContact", backref="tourist", cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "phone": self.phone,
                "nationality": self.nationality, "passport": self.passport, "language": self.language,
                "visa_type": self.visa_type,
                "arrival_date": self.arrival_date.isoformat() if isinstance(self.arrival_date, date) else self.arrival_date,
                "visa_expiry": self.visa_expiry.isoformat() if isinstance(self.visa_expiry, date) else self.visa_expiry}


class FamilyContact(db.Model):
    """Home / family WhatsApp numbers from the Safety Card."""
    __tablename__ = "family_contacts"
    MAX_PER_TOURIST = 5
    id = db.Column(db.Integer, primary_key=True)
    tourist_id = db.Column(db.Integer, db.ForeignKey("tourists.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)  # E.164, e.g. +4915112345678
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "phone": self.phone}


class Station(db.Model):
    __tablename__ = "stations"
    KIND_POLICE = "police"
    KIND_TOURISM = "tourism_police"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    kind = db.Column(db.String(20), default=KIND_POLICE, nullable=False)
    telephone = db.Column(db.String(40))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "kind": self.kind, "telephone": self.telephone,
                "latitude": self.latitude, "longitude": self.longitude}


class Officer(PasswordMixin, db.Model):
    __tablename__ = "officers"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    station_id = db.Column(db.Integer, db.ForeignKey("stations.id"), nullable=False)
    must_change_password = db.Column(db.Boolean, default=True, nullable=False)
    station = db.relationship("Station")


class Hospital(db.Model):
    __tablename__ = "hospitals"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    district = db.Column(db.String(80))
    phone = db.Column(db.String(40))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)


class Incident(db.Model):
    __tablename__ = "incidents"
    STATUSES = ("open", "acknowledged", "responding", "resolved", "closed")
    OPEN_STATUSES = ("open", "acknowledged", "responding")

    id = db.Column(db.Integer, primary_key=True)
    tourist_id = db.Column(db.Integer, db.ForeignKey("tourists.id"), nullable=False, index=True)
    station_id = db.Column(db.Integer, db.ForeignKey("stations.id"), nullable=False, index=True)
    incident_type = db.Column(db.String(32), nullable=False, default="other")
    status = db.Column(db.String(20), nullable=False, default="open", index=True)
    message_original = db.Column(db.Text)
    message_english = db.Column(db.Text)
    original_language = db.Column(db.String(8))
    classification = db.Column(db.JSON)
    guidance = db.Column(db.JSON)
    family_alerts = db.Column(db.JSON)
    start_lat = db.Column(db.Float, nullable=False)
    start_lng = db.Column(db.Float, nullable=False)
    distance_km = db.Column(db.Float)
    tracking_active = db.Column(db.Boolean, default=True, nullable=False)
    tracking_events = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tourist = db.relationship("Tourist")
    station = db.relationship("Station")

    @property
    def is_open(self):
        return self.status in self.OPEN_STATUSES

    def latest_ping(self):
        return LocationPing.query.filter_by(incident_id=self.id).order_by(LocationPing.id.desc()).first()

    def to_dict(self, for_police=False):
        ping = self.latest_ping()
        data = {
            "id": self.id,
            "incident_type": self.incident_type,
            "label": (self.guidance or {}).get("label", self.incident_type),
            "status": self.status,
            "message_original": self.message_original,
            "message_english": self.message_english,
            "original_language": self.original_language,
            "classification": self.classification,
            "guidance": self.guidance,
            "start": {"latitude": self.start_lat, "longitude": self.start_lng},
            "latest_location": ping.to_dict() if ping else None,
            "distance_km": self.distance_km,
            "tracking_active": self.tracking_active,
            "tracking_events": self.tracking_events or [],
            "station": self.station.to_dict() if self.station else None,
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
        }
        if for_police:
            t = self.tourist
            data["tourist"] = {"name": t.name, "phone": t.phone, "nationality": t.nationality,
                               "passport": t.passport, "language": t.language} if t else None
        else:
            data["family_alerts"] = self.family_alerts
        return data


class LocationPing(db.Model):
    __tablename__ = "location_pings"
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {"id": self.id, "incident_id": self.incident_id, "latitude": self.latitude,
                "longitude": self.longitude, "accuracy": self.accuracy, "recorded_at": _iso(self.recorded_at)}


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"
    KINDS = ("text", "image", "voice")
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=False, index=True)
    sender_role = db.Column(db.String(10), nullable=False)  # tourist | police | system
    kind = db.Column(db.String(10), nullable=False, default="text")
    body = db.Column(db.Text)
    body_english = db.Column(db.Text)
    media_path = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {"id": self.id, "incident_id": self.incident_id, "sender_role": self.sender_role,
                "kind": self.kind, "body": self.body, "body_english": self.body_english,
                "media_url": f"/api/media/{self.media_path}" if self.media_path else None,
                "created_at": _iso(self.created_at)}
