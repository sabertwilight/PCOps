#!/usr/bin/env python3
"""Kimi Code 平台用量获取

数据来源:Kimi Code 官方用量接口 GET https://api.kimi.com/coding/v1/usages
鉴权:OAuth Bearer Token。Token 取自 Kimi Code CLI 登录后写入的凭据文件
(~/.kimi-code/credentials/kimi-code.json);access_token 过期(~15min)时,用
refresh_token(~30 天)自动向 https://auth.kimi.com/api/oauth/token 换发新 token。

注意:这与 Kimi 开放平台(platform.kimi.com)的 /v1/users/me/balance 是两套完全
独立的系统,后者只返回现金余额,与本接口的订阅额度不互通。
"""
import os, json, time, base64, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone, timedelta

CRED_PATH = os.path.expanduser("~/.kimi-code/credentials/kimi-code.json")
CLIENT_ID = "17e5f671-d194-4dfb-9706-5516cb48c098"
OAUTH_TOKEN_URL = "https://auth.kimi.com/api/oauth/token"
USAGE_URL = "https://api.kimi.com/coding/v1/usages"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"


def _jwt_payload(token):
    """解码 JWT 的 payload;非 JWT 或解析失败返回 None。"""
    if not token or token.count(".") != 2:
        return None
    try:
        seg = token.split(".")[1]
        seg += "=" * (-len(seg) % 4)
        return json.loads(base64.urlsafe_b64decode(seg).decode("utf-8", "replace"))
    except Exception:
        return None


def _token_alive(token):
    """token 是否仍在有效期内;无法判断时保守返回 True。"""
    p = _jwt_payload(token)
    if p is None:
        return True
    exp = p.get("exp")
    return bool(exp) and time.time() < exp


def _read_credentials():
    try:
        with open(CRED_PATH) as f:
            return json.load(f)
    except Exception:
        return None


def _write_credentials(cred):
    """原子写回凭据文件。Kimi Code 的 refresh_token 每次刷新都会轮换,必须持久化新的。"""
    try:
        os.makedirs(os.path.dirname(CRED_PATH), exist_ok=True)
        tmp = CRED_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(cred, f, indent=2)
        os.replace(tmp, CRED_PATH)
    except Exception:
        pass


def _refresh(refresh_token):
    """用 refresh_token 换新 access_token;成功返回响应 dict,失败返回 None。"""
    body = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }).encode()
    req = urllib.request.Request(OAUTH_TOKEN_URL, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", UA)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def _token_from_localstorage():
    """兜底:从 Chrome localStorage 扫一个未过期的 Kimi access token(短命,排除 refresh token)。"""
    import glob, re
    jwt_re = re.compile(rb'eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{6,}')
    roots = (glob.glob(os.path.expanduser("~/.config/google-chrome/*/Local Storage/leveldb"))
             + glob.glob(os.path.expanduser("~/.config/chromium/*/Local Storage/leveldb")))
    now = time.time()
    best = None  # (exp, token):挑寿命最短且未过期的(即 access token)
    for d in roots:
        for f in glob.glob(os.path.join(d, "*")):
            try:
                raw = open(f, "rb").read()
            except Exception:
                continue
            # localStorage 可能以 UTF-16LE 或 Latin1 存储,两种都扫
            for data in (raw, raw.decode("utf-16-le", "ignore").encode("latin-1", "ignore")):
                for m in jwt_re.finditer(data):
                    tok = m.group().decode("ascii", "replace")
                    p = _jwt_payload(tok)
                    if not isinstance(p, dict):
                        continue
                    if not any(k in p for k in ("membership", "space_id", "abstract_user_id")):
                        continue
                    exp = p.get("exp")
                    if not exp or exp <= now or exp - now > 3600:
                        continue  # 已过期,或寿命太长(= refresh token)
                    if best is None or exp < best[0]:
                        best = (exp, tok)
    return best[1] if best else None


def _get_token(force_refresh=False):
    token = os.environ.get("KIMI_AUTH_TOKEN", "").strip()
    if token:
        return token

    # 首选:Kimi Code CLI 凭据文件(access 过期则用 refresh 自动换新)
    cred = _read_credentials()
    if cred:
        at = cred.get("access_token")
        if not force_refresh and _token_alive(at):
            return at
        rt = cred.get("refresh_token")
        if _token_alive(rt):
            new = _refresh(rt)
            if new and new.get("access_token"):
                cred["access_token"] = new["access_token"]
                cred["refresh_token"] = new.get("refresh_token", rt)  # 轮换后的新 refresh_token
                cred["expires_in"] = new.get("expires_in", cred.get("expires_in", 900))
                cred["expires_at"] = int(time.time()) + int(cred["expires_in"])
                if new.get("token_type"):
                    cred["token_type"] = new["token_type"]
                if new.get("scope"):
                    cred["scope"] = new["scope"]
                _write_credentials(cred)
                return new["access_token"]

    # 兜底:浏览器 localStorage 里的实时 access token
    return _token_from_localstorage()


def _fetch(token):
    req = urllib.request.Request(USAGE_URL, method="GET")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", UA)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_error": True, "_status": e.code, "_body": e.read().decode("utf-8", "replace")}
    except Exception as e:
        return {"_error": True, "_msg": str(e)}


def _fmt_reset(iso_str):
    if not iso_str or iso_str == "?":
        return None
    s = iso_str.rstrip("Z")
    if "." in s:
        s = s.split(".")[0]
    dt_utc = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    dt_cn = dt_utc + timedelta(hours=8)
    return dt_cn.strftime("%m-%d %H:%M")


_AUTH_MARKERS = (
    "unauthenticated", "invalid_auth_token", "invalid user token", "reason_invalid_auth_token",
)


def _humanize_error(data):
    """认证类错误给出“重新登录”提示;其它错误返回截断后的可读信息,避免整段 JSON 刷屏。"""
    status = data.get("_status")
    body = data.get("_body") or ""
    msg = data.get("_msg") or ""
    code, message = "", ""
    try:
        j = json.loads(body)
        if isinstance(j, dict):
            code = str(j.get("code", ""))
            message = str(j.get("message", ""))
    except Exception:
        pass
    blob = " ".join(s.lower() for s in (code, message, body, msg))
    if status == 401 or any(m in blob for m in _AUTH_MARKERS):
        return "登录已过期,请运行 `kimi` 重新 /login(Kimi Code OAuth)"
    detail = message or body or msg or "未知错误"
    if len(detail) > 120:
        detail = detail[:117] + "..."
    return detail


def _pct(detail):
    """detail 字典里的 used/limit -> 百分比(int 或 None)。"""
    if not detail:
        return None
    used = int(detail.get("used", 0) or 0)
    limit = int(detail.get("limit", 0) or 0)
    return round(used / limit * 100) if limit else None


def main():
    token = _get_token()
    if not token:
        print(json.dumps({"platform": "Kimi", "error": "无可用 Token,请运行 `kimi` 完成 /login(Kimi Code OAuth)"}))
        return

    data = _fetch(token)
    # 401 时强制刷新一次再重试
    if data.get("_error") and data.get("_status") == 401:
        token = _get_token(force_refresh=True)
        if token:
            data = _fetch(token)

    if data.get("_error"):
        print(json.dumps({"platform": "Kimi", "error": _humanize_error(data)}))
        return

    # 顶层 usage = 周用量(7 天滚动);limits[0].detail = 5H 滚动窗口
    usage = data.get("usage", {}) or {}
    limits = data.get("limits", []) or []
    detail_5h = limits[0].get("detail", {}) if limits else {}

    print(json.dumps({
        "platform": "Kimi",
        "usage_5h": _pct(detail_5h),
        "reset_5h": _fmt_reset(detail_5h.get("resetTime")),
        "usage_weekly": _pct(usage),
        "reset_weekly": _fmt_reset(usage.get("resetTime")),
        "usage_monthly": None,
        "reset_monthly": None,
    }))


if __name__ == "__main__":
    main()
