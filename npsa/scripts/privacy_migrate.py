#!/usr/bin/env python3
"""图片哈希改名 + 数据直链化：把 /avatars/x.jpg → /media/<sha1>  ; 然后由 encrypt.mjs 加密。"""
import hashlib, json, os, re, shutil, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data/archive.json")
if not os.path.exists(DATA):
    print("no plaintext data (already migrated)"); sys.exit(0)
items = json.load(open(DATA, encoding="utf-8"))
os.makedirs(os.path.join(ROOT, "media"), exist_ok=True)
moved = missing = 0
def migrate(u):
    global moved, missing
    if not isinstance(u, str) or not u.startswith("/"): return u
    src = os.path.join(ROOT, u.lstrip("/"))
    if not os.path.exists(src): missing += 1; return u
    ext = os.path.splitext(u)[1].lower() or ".jpg"
    h = hashlib.sha256(u.encode()).hexdigest()[:20]
    dst_rel = "media/" + h + ext
    dst = os.path.join(ROOT, dst_rel)
    if not os.path.exists(dst): shutil.move(src, dst); moved += 1
    return "/" + dst_rel
for it in items:
    it["avatar_url"] = migrate(it.get("avatar_url"))
    it["cover_url"] = migrate(it.get("cover_url"))
json.dump(items, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
# 清掉空目录
for d in ("avatars", "covers"):
    p = os.path.join(ROOT, d)
    if os.path.isdir(p) and not os.listdir(p): os.rmdir(p)
print("moved=%d missing=%d" % (moved, missing))
