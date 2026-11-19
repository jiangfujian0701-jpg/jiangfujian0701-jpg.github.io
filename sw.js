const VER = 'nv-v4';
const SHELL = ['/', '/index.html', '/app.js?v=3.0', '/style.css?v=3.0', '/boot.js', '/fx.js', '/ui.js', '/env-config.js',
               '/runtime-config.json', '/manifest.webmanifest', '/assets/mark-192.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(VER).then(c => c.addAll(SHELL).catch(()=>{})).then(()=>self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VER && !k.startsWith('nv-img')).map(k => caches.delete(k)))).then(()=>self.clients.claim())); });
self.addEventListener('fetch', e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin) return;
  if (url.pathname === '/data/archive.enc.json') { e.respondWith(fetch(req).catch(()=>caches.match(req))); return; }
  if (/\/(media|avatars|covers|assets)\//.test(url.pathname) || /\.(png|jpe?g|webp|svg|ico)$/i.test(url.pathname)) {
    e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
      if (res && res.status === 200) { const cl = res.clone(); caches.open(VER + '-img').then(c => c.put(req, cl)); }
      return res;
    }).catch(() => caches.match('/assets/mark-192.png'))));
    return;
  }
  e.respondWith(caches.match(req).then(hit => hit || fetch(req)));
});
