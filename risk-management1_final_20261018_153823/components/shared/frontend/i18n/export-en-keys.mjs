import { readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const dir = dirname(fileURLToPath(import.meta.url));
const extra = readFileSync(join(dir, 'extraKeys.js'), 'utf8');
const itinerary = readFileSync(join(dir, 'itineraryPageKeys.js'), 'utf8');
const msgs = readFileSync(join(dir, 'messages.js'), 'utf8');
const enBlock = msgs.match(/export const EN = \{[\s\S]*?\n\}/)[0];
const en = {};
const re = /^\s+(\w+):\s+'((?:\\'|[^'])*)'/gm;
let m;
while ((m = re.exec(enBlock)) !== null) {
  en[m[1]] = m[2].replace(/\\'/g, "'");
}
for (const src of [extra, itinerary]) {
  re.lastIndex = 0;
  while ((m = re.exec(src)) !== null) {
    en[m[1]] = m[2].replace(/\\'/g, "'");
  }
}
writeFileSync(join(dir, 'en-keys.json'), JSON.stringify(en, null, 2));
console.log('keys', Object.keys(en).length);
