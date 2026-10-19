"""Generate complete locale JSON files from en-keys.json using Google Translate."""
import json
import sys
import time
from pathlib import Path

try:
    from deep_translator import GoogleTranslator
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'deep-translator', '-q'])
    from deep_translator import GoogleTranslator

ROOT = Path(__file__).parent
keys = json.loads((ROOT / 'en-keys.json').read_text(encoding='utf-8'))

# Preserve brand / acronym strings
SKIP_TRANSLATE = {'SOS', 'Tour Ceylon', 'Safe Journey', 'WhatsApp', 'GPS', 'PDF', 'NIC'}

LANGS = {
    'ja': 'ja',
    'si': 'si',
    'ta': 'ta',
    'ru': 'ru',
    'de': 'de',
    'zh': 'zh-CN',
    'es': 'es',
    'fr': 'fr',
    'ko': 'ko',
}

locales_dir = ROOT / 'locales'
locales_dir.mkdir(exist_ok=True)

for lang_code, google_code in LANGS.items():
    translator = GoogleTranslator(source='en', target=google_code)
    out = {}
    total = len(keys)
    for i, (k, v) in enumerate(keys.items(), 1):
        if not v or v in SKIP_TRANSLATE or v.strip() == 'SOS':
            out[k] = v
            continue
        # Keep phone numbers, emails, hours as-is
        if v.startswith('+') or '@' in v or v.startswith('09:00'):
            out[k] = v
            continue
        try:
            out[k] = translator.translate(v)
            if i % 20 == 0:
                print(f'{lang_code}: {i}/{total}', flush=True)
            time.sleep(0.08)
        except Exception as exc:
            print(f'{lang_code} {k}: {exc}', file=sys.stderr)
            out[k] = v
    path = locales_dir / f'{lang_code}.json'
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Wrote {path} ({len(out)} keys)')
