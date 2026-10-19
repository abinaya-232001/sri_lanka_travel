/** Fill missing locale keys using MyMemory (fallback when Google gtx is rate-limited). */
import { readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const dir = dirname(fileURLToPath(import.meta.url));
const en = JSON.parse(readFileSync(join(dir, 'en-keys.json'), 'utf8'));
const PRIORITY = ['si', 'ta', 'ja', 'ru', 'de', 'zh', 'es', 'fr', 'ko'];

const targets = {
  si: 'si',
  ta: 'ta',
  ru: 'ru',
  de: 'de',
  zh: 'zh-CN',
  ja: 'ja',
  es: 'es',
  fr: 'fr',
  ko: 'ko',
};

async function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function myMemory(text, target) {
  const url =
    'https://api.mymemory.translated.net/get?q=' +
    encodeURIComponent(text.slice(0, 450)) +
    '&langpair=en|' +
    encodeURIComponent(target);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  const translated = data?.responseData?.translatedText;
  if (!translated || data.responseStatus === 429) throw new Error('rate limited');
  return translated;
}

for (const code of PRIORITY) {
  const path = join(dir, 'locales', `${code}.json`);
  const locale = JSON.parse(readFileSync(path, 'utf8'));
  const missing = Object.keys(en).filter((k) => {
    const val = locale[k];
    return val == null || val === en[k];
  });
  console.log(`${code}: ${missing.length} keys`);
  let done = 0;
  for (const key of missing) {
    try {
      locale[key] = await myMemory(en[key], targets[code]);
      done++;
      if (done % 20 === 0) {
        writeFileSync(path, JSON.stringify(locale, null, 2), 'utf8');
        console.log(`${code}: ${done}/${missing.length}`);
      }
      await sleep(350);
    } catch (err) {
      console.warn(`${code} ${key}: ${err.message}`);
      await sleep(2000);
    }
  }
  writeFileSync(path, JSON.stringify(locale, null, 2), 'utf8');
  console.log(`${code}: finished`);
}

console.log('MyMemory locale fill complete.');
