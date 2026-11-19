#!/usr/bin/env python3
"""交叉挖掘：从库内头部创作者的关注列表里找同类，严格过滤后入库。"""
import hashlib, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

COOKIE = os.environ.get("NV_COOKIE", "").strip()
if not COOKIE:
    print("missing NV_COOKIE"); sys.exit(1)
CT0 = (re.search(r"ct0=([^;]+)", COOKIE) or [None, ""])[1]
BEARER = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
H = {"User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
     "Cookie": COOKIE, "Authorization": "Bearer " + BEARER, "x-csrf-token": CT0,
     "x-twitter-auth-type": "OAuth2Session", "x-twitter-active-user": "yes",
     "x-twitter-client-language": "zh-cn", "Accept": "application/json", "Referer": "https://x.com/"}
F = {"rweb_video_screen_enabled": False, "rweb_cashtags_enabled": True,
     "profile_label_improvements_pcf_label_in_post_enabled": True, "rweb_tipjar_consumption_enabled": True,
     "verified_phone_label_enabled": False, "creator_subscriptions_tweet_preview_api_enabled": True,
     "responsive_web_graphql_timeline_navigation_enabled": True,
     "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
     "premium_content_api_read_enabled": False, "communities_web_enable_tweet_community_results_fetch": True,
     "c9s_tweet_anatomy_moderator_badge_enabled": True, "articles_preview_enabled": True,
     "responsive_web_edit_tweet_api_enabled": True, "view_counts_everywhere_api_enabled": True,
     "longform_notetweets_consumption_enabled": True, "tweet_awards_web_tipping_enabled": False,
     "freedom_of_speech_not_reach_fetch_enabled": True, "standardized_nudges_misinfo": True,
     "longform_notetweets_rich_text_read_enabled": True, "longform_notetweets_inline_media_enabled": True}
OP_FOLLOWING = ("eDqlbOS46zda8jDT8dEQ_Q", "Following")
SEEDS = int(os.environ.get("NV_SEEDS", "10"))
MAX_NEW = int(os.environ.get("NV_MINE_MAX", "15"))
GAP = float(os.environ.get("NV_GAP", "3"))
ADULT = ["onlyfans", "fansly", "fansone", "fanbox", "patreon", "cosplay", "コスプレ", "写真", "私房", "福利",
         "资源", "约拍", "模特", "主播", "图包", "18+", "nsfw", "私密", "女菩萨", "电报", "telegram", "商务",
         "接稿", "拍摄", "ドール", "グラビア", "모델", "lingerie", "写真集", "写真部", "性感", "美女", "情欲", "成人", "🔞"]
CODES = []


def call(op, variables, tries=2):
    oid, name = op
    url = "https://x.com/i/api/graphql/%s/%s?variables=%s&features=%s" % (
        oid, name, urllib.parse.quote(json.dumps(variables)), urllib.parse.quote(json.dumps(F)))
    for t in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=25) as r:
                CODES.append(r.status)
                return r.status, json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            CODES.append(e.code)
            if e.code in (429, 403, 401):
                return e.code, {"error": "abort"}
            return e.code, {}
        except Exception:
            CODES.append(0)
            if t + 1 < tries:
                time.sleep(5)
                continue
    return 0, {}


def norm(u):
    core, lg = u.get("core") or {}, u.get("legacy") or {}
    rel = u.get("relationship_counts") or {}
    sn = core.get("screen_name") or lg.get("screen_name")
    if not sn:
        return None
    return {"id": str(u.get("rest_id") or u.get("id")), "screen_name": sn,
            "name": core.get("name") or lg.get("name") or sn,
            "description": (u.get("profile_bio") or {}).get("description") or lg.get("description") or "",
            "followers_count": rel.get("followers", lg.get("followers_count", 0)) or 0,
            "verified": 1 if ((u.get("verification") or {}).get("verified") or u.get("is_blue_verified")) else 0,
            "avatar_url": ((u.get("avatar") or {}).get("image_url") or lg.get("profile_image_url_https") or "").replace("_normal.", "_400x400."),
            "cover_url": (u.get("banner") or {}).get("image_url") or lg.get("profile_banner_url") or ""}


def has_adult(text):
    t = (text or "").lower()
    return any(k in t for k in ADULT)


def blocked(u, bl_h, bl_p, bl_i):
    if str(u.get("id")) in bl_i:
        return True
    sn = (u.get("screen_name") or "").lower()
    t = ((u.get("description") or "") + " " + (u.get("name") or "") + " " + sn).lower()
    return sn in bl_h or any(p in t for p in bl_p)


def dl(url, tag, root):
    if not url:
        return ""
    if tag == "cover" and not re.search(r"/\d+x\d+$", url):
        url = url.rstrip("/") + "/1500x500"
    h = hashlib.sha256((url + tag).encode()).hexdigest()[:20]
    for ext in (".webp", ".jpg"):
        p = os.path.join(root, "media/" + h + ext)
        if os.path.exists(p) and os.path.getsize(p) > 300:
            return "/media/" + h + ext
    for _ in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": H["User-Agent"]}), timeout=25) as r:
                b = r.read()
            if len(b) <= 300:
                continue
            rel, data = "/media/%s.jpg" % h, b
            try:
                from PIL import Image
                import io
                im = Image.open(io.BytesIO(b)).convert("RGB")
                if max(im.size) > 1200:
                    im.thumbnail((1200, 1200), Image.LANCZOS)
                buf = io.BytesIO(); im.save(buf, "WEBP", quality=80, method=4)
                rel, data = "/media/%s.webp" % h, buf.getvalue()
            except Exception:
                pass
            dst = os.path.join(root, rel.lstrip("/"))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            open(dst, "wb").write(data)
            return rel
        except Exception:
            time.sleep(1)
    return ""


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    arch = json.load(open("/tmp/plain.json", encoding="utf-8"))
    have = {str(x["id"]) for x in arch}
    bl = json.load(open(os.path.join(root, "scripts/blocklist.json"), encoding="utf-8"))
    blh = {h.lower() for h in bl.get("handles", [])}
    blp = {p.lower() for p in bl.get("patterns", [])}
    bli = {str(i) for i in bl.get("ids", [])}
    seeds = [x for x in arch if not x.get("is_suspended") and has_adult(x.get("description"))
             and (x.get("followers_count") or 0) >= 200000]
    seeds.sort(key=lambda x: -(x.get("followers_count") or 0))
    seeds = seeds[:SEEDS]
    print("种子创作者 %d 个：%s" % (len(seeds), [s["screen_name"] for s in seeds]), flush=True)
    cand, seen = [], set()
    for s in seeds:
        st, j = call(OP_FOLLOWING, {"userId": s["id"], "count": 20, "includePromotedContent": False})
        if st != 200:
            print("  种子 @%s 返回 %s，跳过" % (s["screen_name"], st), flush=True)
            time.sleep(GAP)
            continue
        got = 0
        for ins in ((((j.get("data", {}) or {}).get("user") or {}).get("result") or {}).get("timeline") or {}).get("timeline", {}).get("instructions") or []:
            for e in ins.get("entries") or []:
                u = norm(((e.get("content") or {}).get("itemContent") or {}).get("user_results", {}).get("result") or {})
                if not u or u["id"] in have or u["id"] in seen:
                    continue
                if blocked(u, blh, blp, bli):
                    continue
                if not (u["description"] or "").strip():
                    continue
                if not has_adult(u["description"]):
                    continue
                if (u["followers_count"] or 0) < 1000:
                    continue
                seen.add(u["id"]); cand.append(u); got += 1
        print("  @%s → 合格候选 %d（累计 %d）" % (s["screen_name"], got, len(cand)), flush=True)
        time.sleep(GAP)
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    added = []
    for u in cand[:MAX_NEW]:
        added.append({"id": u["id"], "screen_name": u["screen_name"], "name": u["name"],
                      "avatar_url": dl(u["avatar_url"], "avatar", root),
                      "cover_url": dl(u["cover_url"], "cover", root),
                      "followers_count": u["followers_count"], "description": u["description"],
                      "verified": u["verified"], "backed_up_at": ts, "is_blocked": 0, "is_suspended": 0,
                      "clicks_card": 0, "clicks_timeline": 0, "clicks_roulette": 0, "total_clicks": 0,
                      "last_synced_at": ts})
    arch.extend(added)
    json.dump(arch, open("/tmp/plain.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("本轮入库 %d，库内总数 %d，请求状态 %s" % (len(added), len(arch), CODES))
    for a in added[:10]:
        print("   + @%s %s 粉丝 %s" % (a["screen_name"], a["name"][:10], a["followers_count"]))
    return 0


sys.exit(main())
