/* static-mirror API shim: 保持原站 /api/* 语义，数据走本地文件与 R2 直链 */
(function(){
  var R2 = (window.__ENV__ && window.__ENV__.R2_PUBLIC_DOMAIN) || 'https://img.boomboom.nyc.mn';
  var json = function(o, s){ return new Response(JSON.stringify(o), {status:s||200, headers:{'Content-Type':'application/json'}}); };
  var clicks = JSON.parse(localStorage.getItem('x_mirror_local_clicks')||'{}');
  var orig = window.fetch.bind(window);
  window.fetch = function(input, init){
    var url = (typeof input === 'string') ? input : (input && input.url) || '';
    var m = (init && init.method || 'GET').toUpperCase();
    var p = url.replace(/^https?:\/\/[^/]+/, '');
    if (p.indexOf('/api/media') === 0) {
      var k = /[?&]key=([^&]+)/.exec(p); var u = /[?&]url=([^&]+)/.exec(p);
      var t = k ? R2 + '/' + decodeURIComponent(k[1]) : (u ? decodeURIComponent(u[1]) : R2);
      return orig(t, init);
    }
    if (p.indexOf('/api/archive') === 0) return orig('/data/archive.json');
    if (p.indexOf('/api/config') === 0) return json({success:true, r2_public_domain:R2});
    if (p.indexOf('/api/history') === 0) return json({success:true, data:[]});
    if (p.indexOf('/api/sync-status') === 0) return json({running:false,current:0,total:0,newFetched:0,lastItem:null,error:null});
    if (p.indexOf('/api/track-click') === 0) {
      try { var id=(/[?&]id=([^&]+)/.exec(p)||[])[1]||'unknown'; clicks[id]=(clicks[id]||0)+1;
            localStorage.setItem('x_mirror_local_clicks', JSON.stringify(clicks)); } catch(e){}
      return json({success:true, mode:'static-mirror'});
    }
    if (p.indexOf('/api/admin/') === 0 || p.indexOf('/api/verify-cookie') === 0 || p.indexOf('/api/sync-following') === 0) {
      return json({success:false, static_mirror:true, message:'静态镜像模式：本站数据由 AI 运维通过 git 提交与 Actions 更新，无服务端后台。'}, 200);
    }
    return orig(input, init);
  };
  if (navigator.sendBeacon) { var sb = navigator.sendBeacon.bind(navigator);
    navigator.sendBeacon = function(u, d){ if (String(u).indexOf('/api/track-click') === 0) { try{ window.fetch(u,{method:'POST',body:d}); }catch(e){} return true; } return sb(u,d); }; }
})();
