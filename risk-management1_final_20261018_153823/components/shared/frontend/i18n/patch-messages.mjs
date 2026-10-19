import { readFileSync, writeFileSync } from 'fs';

const path = 'messages.js';
let src = readFileSync(path, 'utf8');

const start = src.indexOf('const SI = bundle({');
const end = src.indexOf('export const messages = {');
if (start === -1 || end === -1) throw new Error('markers not found');

const replacement = `const SI = bundle(siLocale)
const TA = bundle(taLocale)
const RU = bundle(ruLocale)
const DE = bundle(deLocale)
const ZH = bundle(zhLocale)
const JA = bundle(jaLocale)
const ES = bundle(esLocale)
const FR = bundle(frLocale)
const KO = bundle(koLocale)

`;

src = src.slice(0, start) + replacement + src.slice(end);
writeFileSync(path, src);
console.log('patched messages.js');
