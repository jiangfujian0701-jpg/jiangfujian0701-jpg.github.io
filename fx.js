/* 动效开关：星空 / 抽卡动画 / 卡片倾斜 */
(function () {
  var KEY = 'nv_fx';
  var def = { bg: true, anim: true, tilt: true };
  var st;
  try { st = Object.assign({}, def, JSON.parse(localStorage.getItem(KEY) || '{}')); } catch (e) { st = Object.assign({}, def); }
  function apply() {
    var h = document.documentElement;
    h.classList.toggle('nv-no-bg', !st.bg);
    h.classList.toggle('nv-no-anim', !st.anim);
    h.classList.toggle('nv-no-tilt', !st.tilt);
  }
  apply();
  function save() { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) {} apply(); }
  function build() {
    var btn = document.createElement('button');
    btn.id = 'nv-fx-btn'; btn.type = 'button'; btn.title = '特效开关';
    btn.textContent = '✦';
    document.body.appendChild(btn);
    var panel = document.createElement('div');
    panel.id = 'nv-fx-panel';
    panel.innerHTML = '<div class="nv-fx-title">特效</div>' +
      '<label class="nv-fx-row"><input type="checkbox" data-k="bg"> 星空背景</label>' +
      '<label class="nv-fx-row"><input type="checkbox" data-k="anim"> 抽卡动画</label>' +
      '<label class="nv-fx-row"><input type="checkbox" data-k="tilt"> 卡片倾斜</label>' +
      '<div class="nv-fx-hint">低配手机可全关，滚动更顺</div>';
    document.body.appendChild(panel);
    Array.prototype.forEach.call(panel.querySelectorAll('input[data-k]'), function (i) {
      i.checked = !!st[i.getAttribute('data-k')];
      i.addEventListener('change', function () { st[i.getAttribute('data-k')] = i.checked; save(); });
    });
    function toggle(force) {
      var open = force !== undefined ? force : !panel.classList.contains('open');
      panel.classList.toggle('open', open);
    }
    btn.addEventListener('click', function (e) { e.stopPropagation(); toggle(); });
    document.addEventListener('click', function (e) {
      if (panel.classList.contains('open') && !panel.contains(e.target) && e.target !== btn) toggle(false);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', build); else build();
})();
