import { readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const dir = dirname(fileURLToPath(import.meta.url));
const en = JSON.parse(readFileSync(join(dir, 'en-keys.json'), 'utf8'));
const SKIP = new Set(['SOS', 'Tour Ceylon', 'Safe Journey', 'WhatsApp', 'GPS', 'PDF', 'NIC']);
const LANGS = { si: 'si', ta: 'ta', ru: 'ru', de: 'de', zh: 'zh-CN', ja: 'ja', es: 'es', fr: 'fr', ko: 'ko' };

async function gtx(text, target) {
  if (!text || SKIP.has(text) || text.startsWith('+') || text.includes('@') || text.startsWith('09:00')) return text;
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

async function sleep(ms) {
  await new Promise((r) => setTimeout(r, ms));
}

for (const [code, target] of Object.entries(LANGS)) {
  const path = join(dir, 'locales', `${code}.json`);
  const locale = JSON.parse(readFileSync(path, 'utf8'));
  let updated = 0;

  for (const [key, enVal] of Object.entries(en)) {
    const cur = locale[key];
    const needs = cur == null || cur === enVal;
    if (!needs) continue;
    try {
      locale[key] = await gtx(enVal, target);
      updated += 1;
      await sleep(120);
    } catch (err) {
      console.error(`${code} ${key}:`, err.message);
      await sleep(2000);
    }
  }

  writeFileSync(path, JSON.stringify(locale, null, 2), 'utf8');
  console.log(`${code}: filled ${updated} keys (${Object.keys(locale).length} total)`);
}
