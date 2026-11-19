import { webcrypto as c } from 'node:crypto';
import fs from 'node:fs';
const pass = process.env.PASS;
if (!pass) { console.error('missing PASS'); process.exit(1); }
const raw = fs.readFileSync('/tmp/plain.json');
const salt = c.getRandomValues(new Uint8Array(16));
const iv = c.getRandomValues(new Uint8Array(12));
const km = await c.subtle.importKey('raw', new TextEncoder().encode(pass), 'PBKDF2', false, ['deriveKey']);
const key = await c.subtle.deriveKey({ name: 'PBKDF2', salt, iterations: 210000, hash: 'SHA-256' },
  km, { name: 'AES-GCM', length: 256 }, false, ['encrypt']);
const ct = await c.subtle.encrypt({ name: 'AES-GCM', iv }, key, raw);
fs.writeFileSync('data/archive.enc.json', JSON.stringify({
  v: 1, iter: 210000, salt: Buffer.from(salt).toString('base64'),
  iv: Buffer.from(iv).toString('base64'), ct: Buffer.from(ct).toString('base64')
}));
fs.unlinkSync('/tmp/plain.json');
console.log('encrypted ->', fs.statSync('data/archive.enc.json').size);
