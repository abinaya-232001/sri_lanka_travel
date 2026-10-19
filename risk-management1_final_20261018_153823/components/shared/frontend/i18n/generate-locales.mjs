import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dir = dirname(fileURLToPath(import.meta.url));
const keys = JSON.parse(readFileSync(join(__dir, 'en-keys.json'), 'utf8'));

const SKIP = new Set(['SOS', 'Tour Ceylon', 'Safe Journey', 'WhatsApp', 'GPS', 'PDF', 'NIC']);
const LANGS = {
  ja: 'ja',
  si: 'si',
  ta: 'ta',
  ru: 'ru',
  de: 'de',
  zh: 'zh-CN',
  es: 'es',
  fr: 'fr',
  ko: 'ko',
};

async function gtxTranslate(text, target) {
  if (!text || SKIP.has(text) || text.startsWith('+') || text.includes('@') || text.startsWith('09:00')) {
    return text;
  }
  const url =
    'https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=' +
    encodeURIComponent(target) +
    '&dt=t&q=' +
    encodeURIComponent(text);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return data[0]?.map((row) => row[0]).join('') || text;
}

async function translateLang(code, target) {
  const out = {};
  const entries = Object.entries(keys);
  for (let i = 0; i < entries.length; i += 1) {
    const [k, v] = entries[i];
    try {
      out[k] = await gtxTranslate(v, target);
    } catch (err) {
      console.error(`${code} ${k}:`, err.message);
      out[k] = v;
    }
    if ((i + 1) % 25 === 0) console.log(`${code}: ${i + 1}/${entries.length}`);
    await new Promise((r) => setTimeout(r, 30));
  }
  return out;
}

const localesDir = join(__dir, 'locales');
mkdirSync(localesDir, { recursive: true });

for (const [code, target] of Object.entries(LANGS)) {
  console.log(`Translating ${code}…`);
  const locale = await translateLang(code, target);
  writeFileSync(join(localesDir, `${code}.json`), JSON.stringify(locale, null, 2), 'utf8');
  console.log(`Wrote locales/${code}.json`);
}
