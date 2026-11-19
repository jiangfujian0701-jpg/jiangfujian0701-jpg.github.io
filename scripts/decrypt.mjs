import { webcrypto as c } from 'node:crypto';
import fs from 'node:fs';
const pass = process.env.PASS;
if (!pass) { console.error('missing PASS'); process.exit(1); }
const env = JSON.parse(fs.readFileSync('data/archive.enc.json', 'utf8'));
const b = s => Uint8Array.from(Buffer.from(s, 'base64'));
const km = await c.subtle.importKey('raw', new TextEncoder().encode(pass), 'PBKDF2', false, ['deriveKey']);
const key = await c.subtle.deriveKey({ name: 'PBKDF2', salt: b(env.salt), iterations: env.iter, hash: 'SHA-256' },
  km, { name: 'AES-GCM', length: 256 }, false, ['decrypt']);
const pt = await c.subtle.decrypt({ name: 'AES-GCM', iv: b(env.iv) }, key, b(env.ct));
fs.writeFileSync('/tmp/plain.json', Buffer.from(pt));
console.log('decrypted', JSON.parse(new TextDecoder().decode(pt)).length, 'records');
