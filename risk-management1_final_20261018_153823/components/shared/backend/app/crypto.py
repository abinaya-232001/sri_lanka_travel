"""Field-level encryption helpers for sensitive tourist data at rest."""

from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken


def _derive_fernet_key(raw: str) -> bytes:
    """Derive a valid Fernet key from an arbitrary secret string."""
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def get_fernet(app_config_key: str | None = None) -> Fernet:
    raw = app_config_key or os.getenv("FERNET_KEY") or os.getenv("SECRET_KEY") or "dev-fernet"
    if len(raw) == 44 and raw.endswith("="):
        try:
            return Fernet(raw.encode("utf-8"))
        except Exception:
            pass
    return Fernet(_derive_fernet_key(raw))


def encrypt_text(value: str | None, fernet: Fernet | None = None) -> str | None:
    if value is None or value == "":
        return value
    f = fernet or get_fernet()
    return f.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_text(value: str | None, fernet: Fernet | None = None) -> str | None:
    if value is None or value == "":
        return value
    f = fernet or get_fernet()
    try:
        return f.decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        # Allow reading plaintext leftovers from early seeds / migrations
        return value
