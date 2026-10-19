import { readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const dir = dirname(fileURLToPath(import.meta.url));
const en = JSON.parse(readFileSync(join(dir, 'en-keys.json'), 'utf8'));
const LANGS = ['si', 'ta', 'ru', 'de', 'zh', 'ja', 'es', 'fr', 'ko'];

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

async function gtx(text, target, retries = 4) {
  const url =
    'https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=' +
    encodeURIComponent(target) +
    '&dt=t&q=' +
    encodeURIComponent(text);
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(url);
      if (res.status === 429) {
        const wait = 3000 * (attempt + 1);
        console.warn(`429 for ${target}, waiting ${wait}ms…`);
        await sleep(wait);
        continue;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      return data[0]?.map((row) => row[0]).join('') || text;
    } catch (err) {
      if (attempt === retries) throw err;
      await sleep(2000 * (attempt + 1));
    }
  }
  return text;
}

for (const code of LANGS) {
  const path = join(dir, 'locales', `${code}.json`);
  const locale = JSON.parse(readFileSync(path, 'utf8'));
  const missing = Object.keys(en).filter((k) => {
    const val = locale[k];
    return val == null || val === en[k];
  });
  console.log(`${code}: ${missing.length} keys to translate`);
  let done = 0;
  for (const key of missing) {
    try {
      locale[key] = await gtx(en[key], targets[code]);
      done++;
      if (done % 25 === 0) {
        writeFileSync(path, JSON.stringify(locale, null, 2), 'utf8');
        console.log(`${code}: saved progress ${done}/${missing.length}`);
      }
      await sleep(400);
    } catch (err) {
      console.error(`${code} ${key}:`, err.message);
      locale[key] = en[key];
      await sleep(5000);
    }
  }
  writeFileSync(path, JSON.stringify(locale, null, 2), 'utf8');
  console.log(`${code}: done`);
}

console.log('Done syncing missing locale keys.');
