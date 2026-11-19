#!/usr/bin/env python3
"""云端自动同步：拉关注/粉丝增量 → 补资料下图片 → 合并（只读，严格控制请求量）。"""
import hashlib, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
import concurrent.futures as cf

COOKIE = os.environ.get("NV_COOKIE", "").strip()
MAX_NEW = int(os.environ.get("NV_MAX_NEW", "40"))
MAX_PAGES = int(os.environ.get("NV_MAX_PAGES", "12"))
GAP = float(os.environ.get("NV_GAP", "3"))
OUT = "/tmp/plain.json"
if not COOKIE:
    print("missing NV_COOKIE"); sys.exit(1)

CT0 = (re.search(r"ct0=([^;]+)", COOKIE) or [None, ""])[1]
BEARER = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
H = {"User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
     "Cookie": COOKIE, "Authorization": "Bearer " + BEARER, "x-csrf-token": CT0,
     "x-twitter-auth-type": "OAuth2Session", "x-twitter-active-user": "yes",
     "x-twitter-client-language": "zh-cn", "Accept": "application/json", "Referer": "https://x.com/"}
FEATURES = {"rweb_video_screen_enabled": False, "rweb_cashtags_enabled": True,
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
OP_USER = ("AMIBMjtxEEATh4z8V9GtRg", "UserByScreenName")
OP_FOLLOWING = ("eDqlbOS46zda8jDT8dEQ_Q", "Following")
OP_FOLLOWERS = ("Xe3y9_ndZ9-RtWz8zd_wpg", "Followers")
CODES = []
STOP = False


def call(op, variables, tries=2):
    global STOP
    if STOP:
        return 0, {"error": "aborted"}
    oid, name = op
    url = "https://x.com/i/api/graphql/%s/%s?variables=%s&features=%s" % (
        oid, name, urllib.parse.quote(json.dumps(variables)), urllib.parse.quote(json.dumps(FEATURES)))
    for t in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=30) as r:
                CODES.append(r.status)
                return r.status, json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            CODES.append(e.code)
            if e.code in (429, 403, 401):
                STOP = True
            return e.code, {"error": e.read()[:160].decode("utf-8", "replace")}
        except Exception:
            CODES.append(0)
            if t + 1 < tries:
                time.sleep(5)
                continue
            return 0, {"error": "net"}
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


def pull(op, uid, cap):
    out, cursor, pages = [], None, 0
    while pages < cap and not STOP:
        kv = {"userId": str(uid), "count": 20, "includePromotedContent": False}
        if cursor:
            kv["cursor"] = cursor
        if op is OP_FOLLOWERS:
            kv["withGrokTranslatedBio"] = False
        st, j = call(op, kv)
        if st != 200:
            print("  停止：%s 返回 %s" % (op[1], st))
            break
        pages += 1
        ins = ((((j.get("data", {}) or {}).get("user") or {}).get("result") or {}).get("timeline") or {}).get("timeline", {}).get("instructions") or []
        got, nxt = 0, None
        for i in ins:
            for e in i.get("entries") or []:
                c = e.get("content") or {}
                eid = str(e.get("entryId") or "")
                if "cursor" in eid.lower() or c.get("entryType") == "TimelineTimelineCursor":
                    v = c.get("value") or (c.get("itemContent") or {}).get("value")
                    if v and ("bottom" in eid.lower() or c.get("cursorType") == "Bottom"):
                        nxt = v
                    continue
                u = norm(((c.get("itemContent") or {}).get("user_results") or {}).get("result") or {})
                if u:
                    out.append(u)
                    got += 1
        print("  %s 第%d页 +%d 累计 %d" % (op[1], pages, got, len(out)), flush=True)
        if not nxt or got == 0:
            break
        cursor = nxt
        time.sleep(GAP)
    return out


ADULT = ["onlyfans","fansly","fansone","fanbox","patreon","cosplay","コスプレ","写真","私房","福利","资源","约拍","模特","主播","图包","18+","nsfw","私密","女菩萨","电报","telegram","商务","接稿","拍摄","ドール","グラビア","모델","lingerie","写真集","写真部","性感","美女","情欲","成人"]
ORG = ["openai","grok","xai","anthropic","meta","google","microsoft","apple","github","nvidia","adobe","vercel","cloudflare","stripe","notion","figma","tesla","spacex","binance","coinbase","aws","azure","docker","unity","steam","discord","labs","inc.","llc","corp","foundation","university","institute","官方","公式","official","news","daily","times","bot","机器人","ai绘画","ai-generated"]


def load_blocklist():
    import json as _j, os as _o
    p = _o.path.join(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))), "scripts/blocklist.json")
    try:
        b = _j.load(open(p, encoding="utf-8"))
        return {h.lower() for h in b.get("handles", [])}, {x.lower() for x in b.get("patterns", [])}
    except Exception:
        return set(), set()


BL_HANDLES, BL_PATTERNS = load_blocklist()


def blocked(u):
    sn = (u.get("screen_name") or "").lower()
    t = ((u.get("description") or "") + " " + (u.get("name") or "") + " " + sn).lower()
    return sn in BL_HANDLES or any(p in t for p in BL_PATTERNS)


def classify(u):
    """adult=像创作者 / org=明显机构或工具号 / unknown=资料不足"""
    bio = (u.get("description") or "").lower()
    name = (u.get("name") or "").lower()
    sn = (u.get("screen_name") or "").lower()
    t = bio + " " + name + " " + sn
    a = [k for k in ADULT if k in t]
    o = [k for k in ORG if k in t]
    if o and not a:
        return "org", a, o
    if not bio.strip():
        return "empty", a, o   # 空简介直接跳过
    if a:
        return "adult", a, o
    return "unknown", a, o


def dl(url, tag, root):
    if not url:
        return ""
    if tag == "cover" and not re.search(r"/\d+x\d+$", url):
        url = url.rstrip("/") + "/1500x500"
    h = hashlib.sha256((url + tag).encode()).hexdigest()[:20]
    rel = "media/%s.jpg" % h
    dst = os.path.join(root, rel)
    if os.path.exists(dst) and os.path.getsize(dst) > 300:
        return "/" + rel
    for _ in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": H["User-Agent"]}), timeout=25) as r:
                b = r.read()
            if len(b) > 300:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                open(dst, "wb").write(b)
                return "/" + rel
        except Exception:
            time.sleep(1)
    return ""


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    arch = json.load(open(OUT, encoding="utf-8"))
    by_id = {str(x.get("id")): x for x in arch}
    st, j = call(OP_USER, {"screen_name": os.environ.get("NV_HANDLE", "riverFujian"), "withSafetyModeUserFields": True})
    me = norm(((j.get("data", {}) or {}).get("user") or {}).get("result") or {})
    if not me:
        print("账号解析失败", st, str(j)[:150]); return 1
    print("账号 @%s id=%s 库内 %d 条" % (me["screen_name"], me["id"], len(arch)), flush=True)

    candidates = pull(OP_FOLLOWING, me["id"], MAX_PAGES) + pull(OP_FOLLOWERS, me["id"], 3)
    seen, fresh = set(), []
    for u in candidates:
        if u["id"] in seen or u["id"] in by_id:
            continue
        seen.add(u["id"])
        fresh.append(u)
    print("候选 %d 个，其中新增 %d 个（本轮上限 %d）" % (len(candidates), len(fresh), MAX_NEW), flush=True)

    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    added, skipped = [], []
    for u in fresh[:MAX_NEW]:
        if blocked(u):
            skipped.append((u["screen_name"], "blocklist"))
            continue
        kind, aw, ow = classify(u)
        if kind in ("org", "empty"):
            skipped.append((u["screen_name"], kind + ":" + (",".join(ow[:2]) if ow else "")))
            continue
        av = dl(u["avatar_url"], "avatar", root)
        cv = dl(u["cover_url"], "cover", root)
        added.append({"id": u["id"], "screen_name": u["screen_name"], "name": u["name"],
                      "avatar_url": av, "cover_url": cv, "followers_count": u["followers_count"],
                      "description": u["description"], "verified": u["verified"], "backed_up_at": ts,
                      "is_blocked": 0, "is_suspended": 0, "clicks_card": 0, "clicks_timeline": 0,
                      "clicks_roulette": 0, "total_clicks": 0, "last_synced_at": ts})
    # 已有记录刷新粉丝数/认证/简介
    updated = 0
    for u in candidates:
        old = by_id.get(u["id"])
        if not old:
            continue
        changed = False
        for k in ("followers_count", "verified", "name"):
            if old.get(k) != u.get(k):
                old[k] = u.get(k); changed = True
        if u["description"] and old.get("description") != u["description"]:
            old["description"] = u["description"]; changed = True
        if changed:
            old["last_synced_at"] = ts; updated += 1
    if skipped:
        print("已跳过非创作者账号 %d 个：%s" % (len(skipped), skipped[:10]))
    arch.extend(added)
    json.dump(arch, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("本轮：新增 %d，刷新 %d，库内总数 %d，请求状态 %s，熔断 %s" % (
        len(added), updated, len(arch), CODES, "是" if STOP else "否"))
    wf = os.environ.get("GITHUB_OUTPUT")
    if wf:
        with open(wf, "a") as f:
            f.write("added=%d\nupdated=%d\ntotal=%d\nstop=%s\n" % (len(added), updated, len(arch), STOP))
    return 0


sys.exit(main())
