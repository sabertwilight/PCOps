#!/usr/bin/env python3
"""OpenCode Go 套餐用量获取

数据来源:OpenCode Go 官方配额接口(非文档公开,社区发现的官方端点):
  GET https://opencode.ai/zen/go/v1/usage
鉴权:Authorization: Bearer <API_KEY>(OpenCode 的 API key,无需 workspace ID)。

返回结构:usage.{rolling,weekly,monthly} 各含 status/percent/resetsAt(ISO-8601 UTC),
rolling 即 5 小时滚动窗口;错误时整体返回 {"error": {type, code, message}}(HTTP 200)。

凭据读取顺序:环境变量 OPENCODE_API_KEY →
~/.local/share/opencode/auth.json 中 type 为 api 的 opencode key。
"""
import os, json, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

USAGE_URL = "https://opencode.ai/zen/go/v1/usage"
AUTH_JSON = os.path.expanduser("~/.local/share/opencode/auth.json")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"


def _get_token():
    token = os.environ.get("OPENCODE_API_KEY", "").strip()
    if token:
        return token
    if os.path.exists(AUTH_JSON):
        try:
            with open(AUTH_JSON) as f:
                data = json.load(f)
            cred = data.get("opencode") or {}
            if cred.get("type") == "api" and cred.get("key"):
                return str(cred["key"]).strip()
        except Exception:
            pass
    return None


def _fetch(token):
    req = urllib.request.Request(USAGE_URL, method="GET")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", UA)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"error": {"message": f"HTTP {e.code}"}}
    except Exception as e:
        return {"error": {"message": f"网络请求失败: {e}"}}


def _fmt_reset(iso_str):
    """ISO-8601(UTC)→ MM-DD HH:MM(东八区)。"""
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(str(iso_str).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone(timedelta(hours=8))).strftime("%m-%d %H:%M")


def _pct(win):
    """窗口字典的 percent → int 百分比;非数字返回 None。"""
    if not isinstance(win, dict):
        return None
    try:
        return round(float(win.get("percent")))
    except (TypeError, ValueError):
        return None


def _reset(win):
    return _fmt_reset(win.get("resetsAt")) if isinstance(win, dict) else None


def main():
    token = _get_token()
    if not token:
        print(json.dumps({"platform": "OpenCode-Go",
                          "error": "缺少 OpenCode API Key,请设置 OPENCODE_API_KEY 或运行 opencode 登录 Zen/Go"}))
        return

    data = _fetch(token)

    err = data.get("error")
    if isinstance(err, dict):
        msg = err.get("message") or err.get("code") or "未知错误"
        if err.get("code") == "api_key_expired":
            msg = "API Key 已过期,请在 https://opencode.ai/console/account#api-keys 新建并更新 auth.json"
        print(json.dumps({"platform": "OpenCode-Go", "error": msg}))
        return

    usage = data.get("usage") or {}
    rolling, weekly, monthly = usage.get("rolling"), usage.get("weekly"), usage.get("monthly")

    usage_5h, usage_weekly, usage_monthly = _pct(rolling), _pct(weekly), _pct(monthly)
    if usage_5h is None and usage_weekly is None and usage_monthly is None:
        print(json.dumps({"platform": "OpenCode-Go", "error": "未订阅 Go 套餐或无法解析用量"}))
        return

    print(json.dumps({
        "platform": "OpenCode-Go",
        "usage_5h": usage_5h,
        "reset_5h": _reset(rolling),
        "usage_weekly": usage_weekly,
        "reset_weekly": _reset(weekly),
        "usage_monthly": usage_monthly,
        "reset_monthly": _reset(monthly),
    }))


if __name__ == "__main__":
    main()
