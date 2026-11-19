/* 入口门禁 + 数据解密：无口令只能看到空壳 */
(function () {
  var ENC = '/data/archive.enc.json';
  var LS_PW = 'nv_pw', LS_DATA = 'nv_data';
  var env = null, plain = null, pending = null;
  function b64(s) { var b = atob(s), u = new Uint8Array(b.length); for (var i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); return u; }
  function dec(buf) { return new TextDecoder().decode(buf); }
  async function derive(pw, salt, iter) {
    var km = await crypto.subtle.importKey('raw', new TextEncoder().encode(pw), 'PBKDF2', false, ['deriveKey']);
    return crypto.subtle.deriveKey({ name: 'PBKDF2', salt: salt, iterations: iter, hash: 'SHA-256' },
      km, { name: 'AES-GCM', length: 256 }, false, ['decrypt']);
  }
  var rawFetch = window.fetch.bind(window);

  async function unlock(pw) {
    if (!env) env = await (await rawFetch(ENC + '?t=' + Date.now(), { cache: 'no-store' })).json();
    var key = await derive(pw, b64(env.salt), env.iter);
    var buf = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: b64(env.iv) }, key, b64(env.ct));
    plain = JSON.parse(dec(buf));
    try { localStorage.setItem(LS_DATA, JSON.stringify(plain)); localStorage.setItem(LS_PW, pw); } catch (e) {}
    return plain;
  }

  function overlay() {
    var d = document.createElement('div');
    d.id = 'nv-gate';
    d.innerHTML = '<div class="nv-gate-card">' +
      '<div class="nv-gate-mark"></div>' +
      '<div class="nv-gate-title">私人归档库</div>' +
      '<div class="nv-gate-sub">请输入访问口令</div>' +
      '<input id="nv-gate-pw" type="password" autocomplete="current-password" placeholder="口令" inputmode="text">' +
      '<button id="nv-gate-go">进入</button>' +
      '<div id="nv-gate-msg" class="nv-gate-msg"></div>' +
      '<label class="nv-gate-remember"><input id="nv-gate-rm" type="checkbox" checked> 记住此设备</label>' +
      '</div>';
    document.body.appendChild(d);
    var pw = d.querySelector('#nv-gate-pw'), go = d.querySelector('#nv-gate-go'), msg = d.querySelector('#nv-gate-msg');
    function submit() {
      var v = (pw.value || '').trim();
      if (!v) { msg.textContent = '口令不能为空'; return; }
      go.disabled = true; msg.textContent = '校验中…';
      unlock(v).then(function () {
        if (!d.querySelector('#nv-gate-rm').checked) { try { localStorage.removeItem(LS_PW); } catch (e) {} }
        d.classList.add('nv-gate-out');
        setTimeout(function () { d.remove(); }, 220);
        location.reload();
      }).catch(function () {
        go.disabled = false; msg.textContent = '口令不正确'; pw.select();
      });
    }
    go.addEventListener('click', submit);
    pw.addEventListener('keydown', function (e) { if (e.key === 'Enter') submit(); });
    setTimeout(function () { pw.focus(); }, 60);
  }

  function ask() {
    if (pending) return pending;
    pending = new Promise(function (res, rej) {
      var wait = setInterval(function () {
        if (!document.body) return;
        clearInterval(wait);
        overlay();
        var tick = setInterval(function () {
          if (plain) { clearInterval(tick); pending = null; res(plain); }
        }, 150);
      }, 30);
    });
    return pending;
  }

  function refresh() {
    var pw = null; try { pw = localStorage.getItem(LS_PW); } catch (e) {}
    if (!pw) return;
    unlock(pw).catch(function () { try { localStorage.removeItem(LS_PW); } catch (e) {} });
  }

  function getData() {
    if (plain) return Promise.resolve(plain);
    var c = null; try { c = localStorage.getItem(LS_DATA); } catch (e) {}
    if (c) { try { plain = JSON.parse(c); refresh(); return Promise.resolve(plain); } catch (e) {} }
    var pw = null; try { pw = localStorage.getItem(LS_PW); } catch (e) {}
    if (pw) return unlock(pw).catch(function () {
      try { localStorage.removeItem(LS_PW); localStorage.removeItem(LS_DATA); } catch (e) {}
      return ask();
    });
    return ask();
  }

  var dataPromise = null;
  window.fetch = function (input, init) {
    var url = typeof input === 'string' ? input : (input && input.url) || '';
    var p = url.replace(/^https?:\/\/[^/]+/, '');
    if (p.indexOf('/data/archive.json') === 0 || p.indexOf('/api/archive') === 0) {
      if (!dataPromise) dataPromise = getData();
      return dataPromise.then(function (o) {
        return new Response(JSON.stringify(o), { status: 200, headers: { 'Content-Type': 'application/json' } });
      });
    }
    return rawFetch(input, init);
  };
})();
