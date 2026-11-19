/* 详情弹层的手势与点击关闭 + 与安卓返回键联动 */
(function () {
  var backdrop = null, drawer = null, closeBtn = null;
  var startY = 0, curY = 0, armed = false, dragging = false;
  var THRESH = 90;

  function els() {
    backdrop = backdrop || document.getElementById('inspector-backdrop');
    drawer = drawer || document.getElementById('inspector-drawer');
    closeBtn = closeBtn || document.getElementById('drawer-close-btn');
    return !!(backdrop && drawer);
  }

  function isOpen() {
    return els() && !backdrop.classList.contains('hidden');
  }

  function close() {
    if (closeBtn) closeBtn.click();
  }

  function scrollerOf(node) {
    while (node && node !== document.body) {
      var st = getComputedStyle(node);
      if (/(auto|scroll|overlay)/.test(st.overflowY) && node.scrollHeight > node.clientHeight + 4) return node;
      node = node.parentElement;
    }
    return null;
  }

  function reset(spring) {
    drawer.style.transition = 'transform .22s cubic-bezier(.2,.8,.2,1)';
    drawer.style.transform = '';
    if (backdrop) backdrop.style.opacity = '';
    setTimeout(function () { if (drawer) drawer.style.transition = ''; }, 240);
  }

  document.addEventListener('touchstart', function (e) {
    if (!isOpen()) return;
    if (!drawer.contains(e.target)) { armed = false; return; }
    var sc = scrollerOf(e.target);
    armed = !sc || sc.scrollTop <= 0;
    startY = e.touches[0].clientY;
    curY = startY;
    dragging = false;
  }, { passive: true });

  document.addEventListener('touchmove', function (e) {
    if (!isOpen() || !armed) return;
    curY = e.touches[0].clientY;
    var dy = curY - startY;
    if (dy <= 0) { if (dragging) { dragging = false; reset(); } return; }
    dragging = true;
    drawer.style.transition = 'none';
    drawer.style.transform = 'translateY(' + Math.min(dy * 0.62, 320) + 'px)';
    if (backdrop) backdrop.style.opacity = String(Math.max(0.25, 1 - dy / 420));
  }, { passive: true });

  document.addEventListener('touchend', function () {
    if (!isOpen() || !dragging) { armed = false; return; }
    var dy = curY - startY;
    armed = false; dragging = false;
    if (dy > THRESH) { close(); reset(); } else { reset(); }
  }, { passive: true });

  // 点遮罩空白处关闭
  document.addEventListener('click', function (e) {
    if (!isOpen()) return;
    if (e.target === backdrop) close();
  });

  // 安卓返回键：由宿主调用
  window.__nvDrawerOpen = function () { return isOpen() ? 1 : 0; };
  window.__nvCloseDrawer = function () { if (isOpen()) { close(); return 1; } return 0; };

  // 状态同步给原生（用于返回键判断）
  function sync() {
    try {
      if (window.AndroidHost && window.AndroidHost.setDrawer) window.AndroidHost.setDrawer(isOpen());
    } catch (err) {}
  }
  var obs = new MutationObserver(sync);
  var timer = setInterval(function () {
    if (els()) {
      obs.observe(backdrop, { attributes: true, attributeFilter: ['class'] });
      clearInterval(timer);
      sync();
    }
  }, 200);
})();
