from datetime import datetime
import secrets

from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    google_id = db.Column(db.String(255), unique=True)
    auth_provider = db.Column(db.String(32), nullable=False, default="password")
    name = db.Column(db.String(255))
    picture = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    trips = db.relationship("UserTripInput", back_populates="user", lazy="dynamic")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def set_unusable_password(self) -> None:
        """Google-only accounts have no usable local password."""
        self.password_hash = generate_password_hash(secrets.token_urlsafe(32))

    def check_password(self, password: str) -> bool:
        if not self.password_hash or not password:
            return False
        # Google-provisioned random hashes still verify technically; we block
        # password login for google-only users in the auth route instead.
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "picture": self.picture,
            "auth_provider": self.auth_provider,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
