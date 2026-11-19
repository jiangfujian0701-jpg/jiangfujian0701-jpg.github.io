#!/usr/bin/env python3
"""把 data/archive.json 里引用的头像/横幅从源 R2 转存到本仓库，实现全站自托管。"""
import concurrent.futures as cf, datetime, json, os, re, sys, urllib.parse, urllib.request
SRC = os.environ.get("SRC_R2", "https://img.boomboom.nyc.mn")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 (mirror-bot)"}

def keys():
    d = json.load(open(os.path.join(ROOT, "data/archive.json"), encoding="utf-8"))
    out = []
    for it in d:
        for f in ("avatar_url", "cover_url"):
            u = str(it.get(f) or "")
            m = re.search(r"[?&]key=([^&]+)", u)
            if m: out.append(urllib.parse.unquote(m.group(1)))
    return d, sorted(set(out))

def fetch(key):
    dst = os.path.join(ROOT, key)
    if os.path.exists(dst) and os.path.getsize(dst) > 1200: return key, "skip"
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    for a in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(SRC + "/" + key, headers=UA), timeout=40) as r:
                b = r.read()
            if len(b) > 1200:
                open(dst, "wb").write(b); return key, "new"
            return key, "tiny"
        except Exception as e:
            if a == 2: return key, "fail:%s" % type(e).__name__
    return key, "fail"

def logo():
    p = os.path.join(ROOT, "logo-icon.png")
    if not os.path.exists(p): return 0
    kb = os.path.getsize(p) // 1024
    try:
        from PIL import Image
    except ImportError:
        return kb
    if kb <= 300: return kb
    im = Image.open(p).convert("RGBA"); im.thumbnail((512, 512), Image.LANCZOS)
    im.save(p, "PNG", optimize=True)
    os.makedirs(os.path.join(ROOT, "icons"), exist_ok=True)
    for s in (192, 512):
        c = im.copy(); c.thumbnail((s, s), Image.LANCZOS); c.save(os.path.join(ROOT, "icons/icon-%d.png" % s), "PNG", optimize=True)
    return os.path.getsize(p) // 1024

def main():
    data, ks = keys()
    new = skip = fail = 0; fails = []
    with cf.ThreadPoolExecutor(max_workers=12) as ex:
        for k, st in ex.map(fetch, ks):
            if st == "new": new += 1
            elif st == "skip": skip += 1
            else: fail += 1; fails.append(k)
    lkb = logo()
    local = sum(1 for k in ks if os.path.exists(os.path.join(ROOT, k)) and os.path.getsize(os.path.join(ROOT, k)) > 1200)
    total_mb = 0
    for dp, _, fs in os.walk(ROOT):
        if "/.git" in dp: continue
        for f in fs: total_mb += os.path.getsize(os.path.join(dp, f))
    json.dump({"generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
               "snapshot_at": max((i.get("backed_up_at") or "") for i in data)[:10],
               "bloggers": len(data), "images_total": len(ks), "images_local": local,
               "images_new": new, "images_failed": fail, "failed_sample": fails[:10],
               "logo_kb": lkb, "repo_mb": round(total_mb / 1048576, 1),
               "self_hosted": local == len(ks), "source_r2": SRC},
              open(os.path.join(ROOT, "ops-status.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("images: new=%d skip=%d fail=%d local=%d/%d logo=%dKB repo=%.1fMB" % (new, skip, fail, local, len(ks), lkb, total_mb / 1048576))
    return 0

sys.exit(main())
