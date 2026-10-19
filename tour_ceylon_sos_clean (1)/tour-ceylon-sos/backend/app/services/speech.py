"""Voice and text -> English.

* Voice + OPENAI_API_KEY: Whisper *translations* turns speech in any language
  directly into English text.
* Otherwise: the transcript made by the browser's speech recognition is used,
  then translated to English (Google Translate web endpoint, best effort).
If translation is impossible the original text is kept and flagged.
"""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request

from flask import current_app

log = logging.getLogger(__name__)


def translate_to_english(text: str | None, source_lang: str | None = "auto") -> tuple[str | None, str, bool]:
    """Return (english_text, detected_language, translated_ok)."""
    text = (text or "").strip()
    if not text:
        return None, source_lang or "en", True
    if (source_lang or "").lower().startswith("en"):
        return text, "en", True
    try:
        url = ("https://translate.googleapis.com/translate_a/single?client=gtx&dt=t&tl=en&sl="
               + urllib.parse.quote(source_lang or "auto") + "&q=" + urllib.parse.quote(text))
        with urllib.request.urlopen(url, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        english = "".join(part[0] for part in data[0] if part and part[0]).strip()
        detected = data[2] if len(data) > 2 and isinstance(data[2], str) else (source_lang or "auto")
        return english or text, detected, bool(english)
    except Exception as exc:  # offline / blocked
        log.warning("Translation unavailable: %s", exc)
        ascii_ratio = sum(c.isascii() for c in text) / max(len(text), 1)
        return text, source_lang or "auto", ascii_ratio > 0.95 and source_lang in (None, "auto", "en")


def voice_to_english(audio_path: str | None, client_transcript: str | None, language: str | None) -> dict:
    """Best English text for a voice note: Whisper translation, else browser transcript translated."""
    key = current_app.config.get("OPENAI_API_KEY")
    if audio_path and key:
        try:
            from openai import OpenAI

            with open(audio_path, "rb") as fh:
                result = OpenAI(api_key=key).audio.translations.create(model="whisper-1", file=fh)
            english = (getattr(result, "text", "") or "").strip()
            if english:
                return {"original": client_transcript or english, "english": english,
                        "language": language or "auto", "translated": True, "source": "whisper"}
        except Exception as exc:
            log.warning("Whisper unavailable, using browser transcript: %s", exc)
    english, detected, ok = translate_to_english(client_transcript, language or "auto")
    return {"original": client_transcript, "english": english, "language": detected,
            "translated": ok, "source": "browser_stt"}
