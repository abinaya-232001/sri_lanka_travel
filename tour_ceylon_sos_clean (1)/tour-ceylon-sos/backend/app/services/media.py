import uuid
from pathlib import Path

from flask import current_app

IMAGE_EXT = {"jpg", "jpeg", "png", "webp", "gif", "heic"}
VOICE_EXT = {"webm", "ogg", "mp3", "m4a", "wav", "mp4", "aac"}


def save_upload(file_storage, incident_id: int, kind: str) -> tuple[str | None, str | None]:
    """Save an uploaded photo/voice note. Returns (relative_path, error)."""
    if not file_storage or not file_storage.filename:
        return None, "No file"
    name = file_storage.filename.lower()
    ext = name.rsplit(".", 1)[-1] if "." in name else ""
    if not ext:
        ext = "webm" if kind == "voice" else "jpg"
    allowed = IMAGE_EXT if kind == "image" else VOICE_EXT
    if ext not in allowed:
        return None, f"Unsupported {kind} file type .{ext}"
    rel = f"{incident_id}/{uuid.uuid4().hex}.{ext}"
    dest = Path(current_app.config["UPLOAD_FOLDER"]) / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    file_storage.save(dest)
    return rel, None


def absolute(rel: str) -> str:
    return str(Path(current_app.config["UPLOAD_FOLDER"]) / rel)
