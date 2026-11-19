const VER = 'npsa-v2';
const SHELL = ['/', '/index.html', '/app.js?v=3.0', '/style.css?v=3.0', '/api-shim.js', '/env-config.js',
               '/runtime-config.json', '/data/archive.json', '/manifest.webmanifest', '/logo-icon.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(VER).then(c => c.addAll(SHELL).catch(()=>{})).then(()=>self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VER).map(k => caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin) return;
  if (url.pathname.startsWith('/api/track-click')) return;
  // 图片：缓存优先，长期复用
  if (/\/(avatars|covers|icons)\//.test(url.pathname) || /\.(png|jpe?g|webp|svg|ico)$/i.test(url.pathname)) {
    e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
      if (res && res.status === 200) { const cl = res.clone(); caches.open(VER+'-img').then(c => c.put(req, cl)); }
      return res;
    }).catch(()=> caches.match('/logo-icon.png'))));
    return;
  }
  // 数据：网络优先，失败回缓存（离线可看）
  if (url.pathname === '/data/archive.json' || url.pathname === '/runtime-config.json' || url.pathname === '/ops-status.json') {
    e.respondWith(fetch(req).then(res => { const cl = res.clone(); caches.open(VER).then(c => c.put(req, cl)); return res; })
      .catch(()=> caches.match(req)));
    return;
  }
  e.respondWith(caches.match(req).then(hit => hit || fetch(req)));
});
