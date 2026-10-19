from __future__ import annotations

from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.crypto import encrypt_text, decrypt_text


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Tourist(db.Model, TimestampMixin):
    __tablename__ = "tourists"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True, index=True)  # login email
    password_hash = db.Column(db.String(255))  # null if Google-only account
    google_sub = db.Column(db.String(128), unique=True, index=True)  # Google subject id
    auth_provider = db.Column(db.String(32), default="local", nullable=False)  # local | google | both
    phone = db.Column(db.String(512), nullable=False)  # encrypted
    nationality = db.Column(db.String(100), nullable=False)
    passport_or_nic = db.Column(db.String(512), nullable=False)  # encrypted
    photo_path = db.Column(db.String(500))
    document_photo_path = db.Column(db.String(500))
    trip_start = db.Column(db.Date)
    trip_end = db.Column(db.Date)
    hotel_name = db.Column(db.String(255))
    hotel_contact = db.Column(db.String(100))
    last_known_lat = db.Column(db.Float)
    last_known_lng = db.Column(db.Float)
    secure_tourist_id = db.Column(db.String(32), unique=True, index=True)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(32))
    visa_type = db.Column(db.String(80))
    visa_expiry = db.Column(db.Date)
    travel_purpose = db.Column(db.String(120))
    preferred_language = db.Column(db.String(16), default="en")
    medical_info = db.Column(db.Text)
    allergies = db.Column(db.String(500))
    blood_group = db.Column(db.String(10))
    special_requirements = db.Column(db.Text)
    privacy_consent = db.Column(db.Boolean, default=False, nullable=False)
    location_consent = db.Column(db.Boolean, default=False, nullable=False)
    # Official visa data from the Department of Immigration API (see services/immigration_api_client.py)
    immigration_verified = db.Column(db.Boolean, default=False, nullable=False)
    immigration_source = db.Column(db.String(32), default="self_declared", nullable=False)  # immigration_api | self_declared
    immigration_reference = db.Column(db.String(64))
    immigration_visa_status = db.Column(db.String(32))
    immigration_entry_date = db.Column(db.Date)
    immigration_exit_date = db.Column(db.Date)
    immigration_synced_at = db.Column(db.DateTime)
    immigration_sync_error = db.Column(db.String(255))

    emergency_contact = db.relationship(
        "EmergencyContact", back_populates="tourist", uselist=False, cascade="all, delete-orphan"
    )
    incidents = db.relationship("Incident", back_populates="tourist", lazy="dynamic")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def set_sensitive(self, phone: str, passport_or_nic: str):
        self.phone = encrypt_text(phone)
        self.passport_or_nic = encrypt_text(passport_or_nic)

    def get_phone(self) -> str | None:
        return decrypt_text(self.phone)

    def get_passport_or_nic(self) -> str | None:
        return decrypt_text(self.passport_or_nic)

    def to_dict(self, reveal_sensitive: bool = False):
        data = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "auth_provider": self.auth_provider,
            "nationality": self.nationality,
            "secure_tourist_id": self.secure_tourist_id,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "gender": self.gender,
            "visa_type": self.visa_type,
            "visa_expiry": self.visa_expiry.isoformat() if self.visa_expiry else None,
            "immigration_verified": bool(self.immigration_verified),
            "immigration_source": self.immigration_source or "self_declared",
            "travel_purpose": self.travel_purpose,
            "preferred_language": self.preferred_language or "en",
            "trip_start": self.trip_start.isoformat() if self.trip_start else None,
            "trip_end": self.trip_end.isoformat() if self.trip_end else None,
            "hotel_name": self.hotel_name,
            "hotel_contact": self.hotel_contact,
            "photo_path": self.photo_path,
            "document_photo_path": self.document_photo_path,
            "last_known_lat": self.last_known_lat,
            "last_known_lng": self.last_known_lng,
            "privacy_consent": self.privacy_consent,
            "location_consent": self.location_consent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "has_password": bool(self.password_hash),
        }
        if reveal_sensitive:
            data["phone"] = self.get_phone()
            data["passport_or_nic"] = self.get_passport_or_nic()
            data["medical_info"] = self.medical_info
            data["allergies"] = self.allergies
            data["blood_group"] = self.blood_group
            data["special_requirements"] = self.special_requirements
        if self.emergency_contact:
            data["emergency_contact"] = self.emergency_contact.to_dict(reveal_sensitive=reveal_sensitive)
        return data


class EmergencyContact(db.Model, TimestampMixin):
    __tablename__ = "emergency_contacts"

    id = db.Column(db.Integer, primary_key=True)
    tourist_id = db.Column(db.Integer, db.ForeignKey("tourists.id"), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(512), nullable=False)  # encrypted
    email = db.Column(db.String(512))  # encrypted
    relationship = db.Column(db.String(100))

    tourist = db.relationship("Tourist", back_populates="emergency_contact")

    def set_sensitive(self, phone: str, email: str | None = None):
        self.phone = encrypt_text(phone)
        self.email = encrypt_text(email) if email else None

    def get_phone(self) -> str | None:
        return decrypt_text(self.phone)

    def get_email(self) -> str | None:
        return decrypt_text(self.email)

    def to_dict(self, reveal_sensitive: bool = False):
        data = {
            "id": self.id,
            "name": self.name,
            "relationship": self.relationship,
        }
        if reveal_sensitive:
            data["phone"] = self.get_phone()
            data["email"] = self.get_email()
        return data


class Hotel(db.Model, TimestampMixin):
    """Registered accommodation from SLTDA-style listing (accomadation.xlsx)."""

    __tablename__ = "hotels"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(120))
    rooms = db.Column(db.Integer)
    address = db.Column(db.Text)
    contact = db.Column(db.String(100))
    mobile = db.Column(db.String(100))
    email = db.Column(db.String(200))
    website = db.Column(db.String(500))
    registration_no = db.Column(db.String(80))
    price_range = db.Column(db.String(80))
    district = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "rooms": self.rooms,
            "address": self.address,
            "contact": self.contact,
            "mobile": self.mobile,
            "email": self.email,
            "website": self.website,
            "registration_no": self.registration_no,
            "price_range": self.price_range,
            "district": self.district,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }


class Embassy(db.Model, TimestampMixin):
    __tablename__ = "embassies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    mission_type = db.Column(db.String(80))
    city = db.Column(db.String(100))
    address = db.Column(db.Text)
    emails = db.Column(db.Text)
    phones = db.Column(db.Text)
    fax = db.Column(db.String(80))
    website = db.Column(db.String(500))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "mission_type": self.mission_type,
            "city": self.city,
            "address": self.address,
            "emails": self.emails,
            "phones": self.phones,
            "fax": self.fax,
            "website": self.website,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }


class SosAttraction(db.Model, TimestampMixin):
    __tablename__ = "sos_attractions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(120))
    destination = db.Column(db.String(120))
    details = db.Column(db.Text)
    mood_tag = db.Column(db.String(80))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "destination": self.destination,
            "details": self.details,
            "mood_tag": self.mood_tag,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }


class PoliceStationDirectory(db.Model, TimestampMixin):
    """Division-level police contact directory (no coordinates)."""

    __tablename__ = "police_station_directory"

    id = db.Column(db.Integer, primary_key=True)
    division = db.Column(db.String(255), nullable=False, index=True)
    telephone = db.Column(db.String(50))

    def to_dict(self):
        return {
            "id": self.id,
            "division": self.division,
            "telephone": self.telephone,
        }


class Hospital(db.Model, TimestampMixin):
    __tablename__ = "hospitals"

    id = db.Column(db.Integer, primary_key=True)
    district = db.Column(db.String(100))
    name = db.Column(db.String(255), nullable=False)
    local_number = db.Column(db.String(50))
    international_number = db.Column(db.String(50))
    latitude = db.Column(db.Float)  # nullable for hotline-only entries
    longitude = db.Column(db.Float)
    is_private = db.Column(db.Boolean, default=False, nullable=False)
    is_hotline_only = db.Column(db.Boolean, default=False, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "district": self.district,
            "name": self.name,
            "local_number": self.local_number,
            "international_number": self.international_number,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "is_private": self.is_private,
            "is_hotline_only": self.is_hotline_only,
        }


class Station(db.Model, TimestampMixin):
    __tablename__ = "stations"

    id = db.Column(db.Integer, primary_key=True)
    range_name = db.Column(db.String(255), nullable=False)
    division = db.Column(db.String(255))  # often null in source data
    desk = db.Column(db.String(255))
    telephone = db.Column(db.String(50))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    # True for one representative desk per unique coordinate cluster
    is_dispatchable = db.Column(db.Boolean, default=True, nullable=False)

    officers = db.relationship("Officer", back_populates="station", lazy="dynamic")
    incidents = db.relationship("Incident", back_populates="station", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "range_name": self.range_name,
            "division": self.division,
            "desk": self.desk,
            "telephone": self.telephone,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "is_dispatchable": self.is_dispatchable,
            "display_name": self.display_name,
        }

    @property
    def display_name(self) -> str:
        parts = [p for p in [self.range_name, self.division, self.desk] if p]
        return " / ".join(parts) if parts else f"Station {self.id}"


class Officer(db.Model, TimestampMixin):
    __tablename__ = "officers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    badge_number = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    station_id = db.Column(db.Integer, db.ForeignKey("stations.id"), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    status = db.Column(db.String(32), default="available")  # available | busy | offline
    last_lat = db.Column(db.Float)
    last_lng = db.Column(db.Float)
    last_seen_at = db.Column(db.DateTime)

    station = db.relationship("Station", back_populates="officers")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "badge_number": self.badge_number,
            "username": self.username,
            "email": self.email,
            "station_id": self.station_id,
            "station": self.station.to_dict() if self.station else None,
            "is_active": self.is_active,
            "status": self.status or "available",
            "last_lat": self.last_lat,
            "last_lng": self.last_lng,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
        }


class Incident(db.Model, TimestampMixin):
    __tablename__ = "incidents"

    STATUS_OPEN = "open"
    STATUS_FLAGGED_FOR_REVIEW = "flagged_for_review"
    STATUS_ACKNOWLEDGED = "acknowledged"
    STATUS_OFFICER_ASSIGNED = "officer_assigned"
    STATUS_RESPONDING = "responding"
    STATUS_TOURIST_CONTACTED = "tourist_contacted"
    STATUS_ASSISTANCE_PROVIDED = "assistance_provided"
    STATUS_RESOLVED = "resolved"
    STATUS_CLOSED = "closed"
    # Legacy alias
    STATUS_DISPATCHED = STATUS_RESPONDING

    STATUS_ORDER = [
        STATUS_OPEN,
        STATUS_FLAGGED_FOR_REVIEW,
        STATUS_ACKNOWLEDGED,
        STATUS_OFFICER_ASSIGNED,
        STATUS_RESPONDING,
        STATUS_TOURIST_CONTACTED,
        STATUS_ASSISTANCE_PROVIDED,
        STATUS_RESOLVED,
        STATUS_CLOSED,
    ]

    STATUS_LABELS = {
        STATUS_OPEN: "NEW",
        STATUS_FLAGGED_FOR_REVIEW: "ESCALATED",
        STATUS_ACKNOWLEDGED: "ACKNOWLEDGED",
        STATUS_OFFICER_ASSIGNED: "OFFICER ASSIGNED",
        STATUS_RESPONDING: "RESPONDING",
        STATUS_TOURIST_CONTACTED: "TOURIST CONTACTED",
        STATUS_ASSISTANCE_PROVIDED: "ASSISTANCE PROVIDED",
        STATUS_RESOLVED: "RESOLVED",
        STATUS_CLOSED: "CLOSED",
    }

    TYPE_GENERAL = "general"
    TYPE_MEDICAL = "medical"
    TYPE_RAPE = "rape"
    TYPE_THEFT = "theft"
    TYPE_ACCIDENT = "accident"
    TYPE_HARASSMENT = "harassment"
    TYPE_HOSPITAL = "hospital_assistance"
    TYPE_POLICE = "police_assistance"
    TYPE_LOST_PASSPORT = "lost_passport"
    TYPE_MISSING = "missing_person"
    TYPE_FIRE = "fire"
    TYPE_NATURAL = "natural_disaster"
    TYPE_CYBER = "cybercrime"
    TYPE_FRAUD = "financial_fraud"
    TYPE_UNSAFE = "unsafe_location"
    TYPE_OTHER = "other"

    VALID_TYPES = {
        TYPE_GENERAL, TYPE_MEDICAL, TYPE_RAPE, TYPE_THEFT, TYPE_ACCIDENT,
        TYPE_HARASSMENT, TYPE_HOSPITAL, TYPE_POLICE, TYPE_LOST_PASSPORT,
        TYPE_MISSING, TYPE_FIRE, TYPE_NATURAL, TYPE_CYBER, TYPE_FRAUD,
        TYPE_UNSAFE, TYPE_OTHER,
    }

    TYPE_LABELS = {
        TYPE_GENERAL: "General Emergency",
        TYPE_MEDICAL: "Medical Emergency",
        TYPE_RAPE: "Assault",
        TYPE_THEFT: "Theft",
        TYPE_ACCIDENT: "Road Accident",
        TYPE_HARASSMENT: "Harassment",
        TYPE_HOSPITAL: "Hospital Assistance",
        TYPE_POLICE: "Police Assistance",
        TYPE_LOST_PASSPORT: "Lost Passport / Documents",
        TYPE_MISSING: "Missing Person",
        TYPE_FIRE: "Fire",
        TYPE_NATURAL: "Natural Disaster",
        TYPE_CYBER: "Cybercrime / Online Harassment",
        TYPE_FRAUD: "Financial Fraud",
        TYPE_UNSAFE: "Unsafe Location",
        TYPE_OTHER: "Other Emergency",
    }

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.String(128), unique=True, index=True)
    tourist_id = db.Column(db.Integer, db.ForeignKey("tourists.id"), nullable=False)
    station_id = db.Column(db.Integer, db.ForeignKey("stations.id"), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"))
    assigned_officer_id = db.Column(db.Integer, db.ForeignKey("officers.id"))

    incident_type = db.Column(db.String(32), default=TYPE_GENERAL, nullable=False, index=True)
    status = db.Column(db.String(32), default=STATUS_OPEN, nullable=False, index=True)
    initial_lat = db.Column(db.Float, nullable=False)
    initial_lng = db.Column(db.Float, nullable=False)
    distance_to_station_km = db.Column(db.Float)

    triggered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    acknowledged_at = db.Column(db.DateTime)
    officer_assigned_at = db.Column(db.DateTime)
    dispatched_at = db.Column(db.DateTime)
    tourist_contacted_at = db.Column(db.DateTime)
    assistance_provided_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    closed_at = db.Column(db.DateTime)

    hospital_notified_at = db.Column(db.DateTime)
    contact_notified_at = db.Column(db.DateTime)
    hotel_notified_at = db.Column(db.DateTime)
    station_notified_at = db.Column(db.DateTime)

    notes_summary = db.Column(db.Text)
    ai_summary = db.Column(db.Text)
    known_facts = db.Column(db.JSON)
    ai_inference = db.Column(db.JSON)
    tourist_statement = db.Column(db.Text)
    translated_statement = db.Column(db.Text)
    original_language = db.Column(db.String(16))
    voice_recording_path = db.Column(db.String(500))
    risk_score = db.Column(db.Integer)
    risk_level = db.Column(db.String(20))
    recommended_action = db.Column(db.Text)
    resolution_details = db.Column(db.Text)
    duplicate_check_result = db.Column(db.JSON)
    duplicate_matched_incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"))
    duplicate_requires_review = db.Column(db.Boolean, default=False, nullable=False)
    tracking_active = db.Column(db.Boolean, default=True, nullable=False)
    cyber_evidence_url = db.Column(db.Text)

    tourist = db.relationship("Tourist", back_populates="incidents")
    station = db.relationship("Station", back_populates="incidents")
    hospital = db.relationship("Hospital")
    assigned_officer = db.relationship("Officer", foreign_keys=[assigned_officer_id])
    location_pings = db.relationship(
        "LocationPing",
        back_populates="incident",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="LocationPing.recorded_at",
    )
    chat_messages = db.relationship(
        "ChatMessage",
        back_populates="incident",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )

    def to_dict(self, include_pings: bool = False, reveal_tourist: bool = False):
        latest = self.location_pings.order_by(LocationPing.recorded_at.desc()).first()
        data = {
            "id": self.id,
            "client_id": self.client_id,
            "tourist_id": self.tourist_id,
            "station_id": self.station_id,
            "hospital_id": self.hospital_id,
            "incident_type": self.incident_type or self.TYPE_GENERAL,
            "incident_type_label": self.TYPE_LABELS.get(
                self.incident_type or self.TYPE_GENERAL, "General"
            ),
            "type": self.incident_type or self.TYPE_GENERAL,
            "status": self.status,
            "status_label": self.STATUS_LABELS.get(self.status, self.status),
            "initial_lat": self.initial_lat,
            "initial_lng": self.initial_lng,
            "distance_to_station_km": self.distance_to_station_km,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "officer_assigned_at": self.officer_assigned_at.isoformat() if self.officer_assigned_at else None,
            "dispatched_at": self.dispatched_at.isoformat() if self.dispatched_at else None,
            "tourist_contacted_at": self.tourist_contacted_at.isoformat() if self.tourist_contacted_at else None,
            "assistance_provided_at": self.assistance_provided_at.isoformat() if self.assistance_provided_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "hospital_notified_at": self.hospital_notified_at.isoformat()
            if self.hospital_notified_at
            else None,
            "contact_notified_at": self.contact_notified_at.isoformat()
            if self.contact_notified_at
            else None,
            "hotel_notified_at": self.hotel_notified_at.isoformat()
            if self.hotel_notified_at
            else None,
            "station_notified_at": self.station_notified_at.isoformat()
            if self.station_notified_at
            else None,
            "notes_summary": self.notes_summary or self.ai_summary,
            "ai_summary": self.ai_summary,
            "known_facts": self.known_facts,
            "ai_inference": self.ai_inference,
            "tourist_statement": self.tourist_statement,
            "translated_statement": self.translated_statement,
            "original_language": self.original_language,
            "voice_recording_path": self.voice_recording_path,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "recommended_action": self.recommended_action,
            "resolution_details": self.resolution_details,
            "duplicate_check_result": self.duplicate_check_result,
            "duplicate_matched_incident_id": self.duplicate_matched_incident_id,
            "duplicate_requires_review": self.duplicate_requires_review,
            "assigned_officer_id": self.assigned_officer_id,
            "cyber_evidence_url": self.cyber_evidence_url,
            "tracking_active": self.tracking_active,
            "station": self.station.to_dict() if self.station else None,
            "hospital": self.hospital.to_dict() if self.hospital else None,
            "tourist": self.tourist.to_dict(reveal_sensitive=reveal_tourist) if self.tourist else None,
            "latest_ping": latest.to_dict() if latest else None,
        }
        if include_pings:
            data["pings"] = [p.to_dict() for p in self.location_pings.all()]
        return data


class LocationPing(db.Model):
    __tablename__ = "location_pings"

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float)
    bearing_deg = db.Column(db.Float)
    speed_kmh = db.Column(db.Float)
    direction = db.Column(db.String(8))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    incident = db.relationship("Incident", back_populates="location_pings")

    def to_dict(self):
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "accuracy": self.accuracy,
            "bearing_deg": self.bearing_deg,
            "speed_kmh": self.speed_kmh,
            "direction": self.direction,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }


class ChatMessage(db.Model):
    """Incident chat between tourist and the assigned (nearest) police station."""

    __tablename__ = "chat_messages"

    ROLE_TOURIST = "tourist"
    ROLE_OFFICER = "officer"
    TYPE_TEXT = "text"
    TYPE_IMAGE = "image"
    TYPE_VOICE = "voice"
    TYPE_VIDEO = "video"
    TYPE_LOCATION = "location"
    VALID_TYPES = {TYPE_TEXT, TYPE_IMAGE, TYPE_VOICE, TYPE_VIDEO, TYPE_LOCATION}

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=False, index=True)
    sender_role = db.Column(db.String(20), nullable=False)
    sender_id = db.Column(db.Integer)
    message_type = db.Column(db.String(20), default=TYPE_TEXT, nullable=False)
    body = db.Column(db.Text)
    media_path = db.Column(db.String(500))
    original_language = db.Column(db.String(16))
    translated_body = db.Column(db.Text)
    voice_transcription = db.Column(db.Text)  # For TYPE_VOICE messages
    voice_transcription_language = db.Column(db.String(16))  # Language of transcription
    voice_stt_provider = db.Column(db.String(64))  # Which STT provider was used
    voice_transcription_confidence = db.Column(db.Float)  # STT confidence
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    delivered_at = db.Column(db.DateTime)
    read_at = db.Column(db.DateTime)
    status = db.Column(db.String(16), default="sent")  # sent | delivered | read
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    incident = db.relationship("Incident", back_populates="chat_messages")

    def to_dict(self):
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "sender_role": self.sender_role,
            "sender_id": self.sender_id,
            "message_type": self.message_type,
            "body": self.body,
            "translated_body": self.translated_body,
            "original_language": self.original_language,
            "voice_transcription": self.voice_transcription,
            "voice_transcription_language": self.voice_transcription_language,
            "voice_stt_provider": self.voice_stt_provider,
            "voice_transcription_confidence": self.voice_transcription_confidence,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "media_path": self.media_path,
            "media_url": f"/uploads/{self.media_path}" if self.media_path else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "status": self.status,
            "created_at": (
                f"{self.created_at.isoformat()}Z"
                if self.created_at and self.created_at.tzinfo is None
                else (self.created_at.isoformat() if self.created_at else None)
            ),
        }


class CheckIn(db.Model, TimestampMixin):
    __tablename__ = "check_ins"

    PLACE_HOTEL = "hotel"
    PLACE_ATTRACTION = "attraction"
    PLACE_BEACH = "beach"
    PLACE_PARK = "park"
    PLACE_OTHER = "other"

    id = db.Column(db.Integer, primary_key=True)
    tourist_id = db.Column(db.Integer, db.ForeignKey("tourists.id"), nullable=False, index=True)
    place_type = db.Column(db.String(32), nullable=False)
    place_id = db.Column(db.Integer)
    place_name = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    safe_arrival_confirmed = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "tourist_id": self.tourist_id,
            "place_type": self.place_type,
            "place_id": self.place_id,
            "place_name": self.place_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "safe_arrival_confirmed": self.safe_arrival_confirmed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SafeJourney(db.Model, TimestampMixin):
    """Consent-aware journey monitoring record for a tourist."""

    __tablename__ = "safe_journeys"

    STATUS_NOT_STARTED = "not_started"
    STATUS_ACTIVE = "active"
    STATUS_DELAYED = "delayed"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_ESCALATED = "escalated"
    ACTIVE_STATUSES = {STATUS_NOT_STARTED, STATUS_ACTIVE, STATUS_DELAYED}
    STATUS_LABELS = {
        STATUS_NOT_STARTED: "Not started",
        STATUS_ACTIVE: "Active",
        STATUS_DELAYED: "Delayed",
        STATUS_COMPLETED: "Completed",
        STATUS_CANCELLED: "Cancelled",
        STATUS_ESCALATED: "Escalated",
    }

    id = db.Column(db.Integer, primary_key=True)
    tourist_id = db.Column(db.Integer, db.ForeignKey("tourists.id"), nullable=False, index=True)
    origin_name = db.Column(db.String(255), nullable=False)
    origin_lat = db.Column(db.Float, nullable=False)
    origin_lng = db.Column(db.Float, nullable=False)
    destination_name = db.Column(db.String(255), nullable=False)
    destination_lat = db.Column(db.Float, nullable=False)
    destination_lng = db.Column(db.Float, nullable=False)
    expected_duration_minutes = db.Column(db.Integer, nullable=False)
    started_at = db.Column(db.DateTime)
    expected_arrival_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    escalated_at = db.Column(db.DateTime)
    current_lat = db.Column(db.Float)
    current_lng = db.Column(db.Float)
    final_lat = db.Column(db.Float)
    final_lng = db.Column(db.Float)
    cancellation_reason = db.Column(db.Text)
    status = db.Column(db.String(32), nullable=False, default=STATUS_NOT_STARTED, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "tourist_id": self.tourist_id,
            "origin": {"name": self.origin_name, "latitude": self.origin_lat, "longitude": self.origin_lng},
            "destination": {"name": self.destination_name, "latitude": self.destination_lat, "longitude": self.destination_lng},
            "expected_duration_minutes": self.expected_duration_minutes,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "expected_arrival_at": self.expected_arrival_at.isoformat() if self.expected_arrival_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "escalated_at": self.escalated_at.isoformat() if self.escalated_at else None,
            "current_location": {"latitude": self.current_lat, "longitude": self.current_lng}
            if self.current_lat is not None and self.current_lng is not None else None,
            "final_location": {"latitude": self.final_lat, "longitude": self.final_lng}
            if self.final_lat is not None and self.final_lng is not None else None,
            "cancellation_reason": self.cancellation_reason,
            "status": self.status,
            "status_label": self.STATUS_LABELS.get(self.status, self.status),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SafeJourneyEvent(db.Model):
    """Immutable lifecycle and extension history for a Safe Journey."""

    __tablename__ = "safe_journey_events"

    id = db.Column(db.Integer, primary_key=True)
    journey_id = db.Column(db.Integer, db.ForeignKey("safe_journeys.id"), nullable=False, index=True)
    event_type = db.Column(db.String(32), nullable=False)
    from_status = db.Column(db.String(32))
    to_status = db.Column(db.String(32))
    details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


class MissingTouristCase(db.Model, TimestampMixin):
    """Police-reviewed missing-tourist case; delayed journeys never create one automatically."""

    __tablename__ = "missing_tourist_cases"

    STATUS_OPEN = "open"
    STATUS_INVESTIGATING = "investigating"
    STATUS_FOUND = "found"
    STATUS_CLOSED = "closed"
    VALID_STATUSES = {STATUS_OPEN, STATUS_INVESTIGATING, STATUS_FOUND, STATUS_CLOSED}

    id = db.Column(db.Integer, primary_key=True)
    tourist_id = db.Column(db.Integer, db.ForeignKey("tourists.id"), nullable=False, index=True)
    reported_by_officer_id = db.Column(db.Integer, db.ForeignKey("officers.id"), nullable=False)
    station_id = db.Column(db.Integer, db.ForeignKey("stations.id"), nullable=False)
    safe_journey_id = db.Column(db.Integer, db.ForeignKey("safe_journeys.id"))
    status = db.Column(db.String(32), nullable=False, default=STATUS_OPEN, index=True)
    last_known_lat = db.Column(db.Float)
    last_known_lng = db.Column(db.Float)
    last_interaction_at = db.Column(db.DateTime)
    facts = db.Column(db.JSON, nullable=False, default=dict)
    ai_inference = db.Column(db.JSON)
    resolved_at = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "tourist_id": self.tourist_id,
            "station_id": self.station_id,
            "safe_journey_id": self.safe_journey_id,
            "status": self.status,
            "last_known_location": {"latitude": self.last_known_lat, "longitude": self.last_known_lng}
            if self.last_known_lat is not None and self.last_known_lng is not None else None,
            "last_interaction_at": self.last_interaction_at.isoformat() if self.last_interaction_at else None,
            "known_facts": self.facts or {},
            "ai_inference": self.ai_inference,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(120), nullable=False)
    actor_role = db.Column(db.String(32))
    actor_id = db.Column(db.Integer)
    resource_type = db.Column(db.String(64))
    resource_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "action": self.action,
            "actor_role": self.actor_role,
            "actor_id": self.actor_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
