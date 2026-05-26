#!/usr/bin/env python3
"""Kimi 平台数据获取"""
import os, sys, json, time, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

TOKEN_DIR = os.path.expanduser("~/.local/share/ai-balance")
CACHE = os.path.join(TOKEN_DIR, "kimi-auth.token")


def _get_token():
    token = os.environ.get("KIMI_AUTH_TOKEN", "").strip()
    if token:
        return token

    # 缓存 TTL: 1 小时
    CACHE_TTL = 3600
    if os.path.exists(CACHE):
        mtime = os.path.getmtime(CACHE)
        if time.time() - mtime < CACHE_TTL:
            with open(CACHE) as f:
                token = f.read().strip()
            if token:
                return token
        # 缓存过期，继续尝试重新抓取

    try:
        import browser_cookie3
        for loader in (browser_cookie3.chrome, browser_cookie3.chromium, browser_cookie3.firefox):
            try:
                for c in loader(domain_name="kimi.com"):
                    if c.name == "kimi-auth":
                        os.makedirs(TOKEN_DIR, exist_ok=True)
                        with open(CACHE, "w") as f:
                            f.write(c.value)
                        return c.value
            except Exception:
                continue
    except ImportError:
        pass
    return None


def _fetch(token):
    url = "https://www.kimi.com/apiv2/kimi.gateway.billing.v1.BillingService/GetUsages"
    payload = b'{"scope":["FEATURE_CODING"]}'
    req = urllib.request.Request(url, data=payload, method='POST')
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Accept', 'application/json, text/plain, */*')
    req.add_header('Referer', 'https://www.kimi.com/code/console?from=kfc_overview_topbar')
    req.add_header('Origin', 'https://www.kimi.com')
    req.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {"_error": True, "_status": e.code, "_body": e.read().decode('utf-8')}
    except Exception as e:
        return {"_error": True, "_msg": str(e)}


def _fmt_reset(iso_str):
    if not iso_str or iso_str == '?':
        return None
    s = iso_str.rstrip('Z')
    if '.' in s:
        s = s.split('.')[0]
    dt_utc = datetime.strptime(s, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
    dt_cn = dt_utc + timedelta(hours=8)
    return dt_cn.strftime('%m-%d %H:%M')


def _try_refresh_and_refetch():
    """删除缓存后重新从浏览器抓取 token 并请求"""
    if os.path.exists(CACHE):
        os.remove(CACHE)
    token = _get_token()
    if not token:
        return None
    return _fetch(token)


def main():
    token = _get_token()
    if not token:
        print(json.dumps({"platform": "Kimi", "error": "无法获取 Token，请登录 Kimi 或设置 KIMI_AUTH_TOKEN"}))
        return

    data = _fetch(token)

    # 401 时自动刷新缓存并重试一次
    if data.get("_error") and data.get("_status") == 401:
        data = _try_refresh_and_refetch()
        if data is None:
            print(json.dumps({"platform": "Kimi", "error": "无法获取 Token，请登录 Kimi 或设置 KIMI_AUTH_TOKEN"}))
            return

    if data.get("_error"):
        msg = data.get('_body', data.get('_msg', '未知错误'))
        print(json.dumps({"platform": "Kimi", "error": msg}))
        return

    usages = data.get("usages", [])
    coding = [u for u in usages if u.get("scope") == "FEATURE_CODING"]
    if not coding:
        print(json.dumps({"platform": "Kimi", "error": "无 FEATURE_CODING 额度"}))
        return

    u = coding[0]
    d = u["detail"]
    l = u.get("limits", [{}])[0].get("detail", {})

    # 周用量 (detail 层级)
    weekly_used = int(d.get('used', 0) or 0)
    weekly_limit = int(d.get('limit', 0) or 0)
    usage_weekly = round(weekly_used / weekly_limit * 100) if weekly_limit else None

    # 5H用量 (limits[0].detail 层级)
    used_5h = int(l.get('used', 0) or 0)
    limit_5h = int(l.get('limit', 0) or 0)
    usage_5h = round(used_5h / limit_5h * 100) if limit_5h else None

    print(json.dumps({
        "platform": "Kimi",
        "usage_5h": usage_5h,
        "usage_weekly": usage_weekly,
        "reset_5h": _fmt_reset(l.get("resetTime")),
        "reset_weekly": _fmt_reset(d.get("resetTime")),
        "usage_monthly": None,
        "reset_monthly": None,
    }))


if __name__ == "__main__":
    main()