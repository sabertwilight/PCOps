#!/usr/bin/env python3
"""智谱 GLM 平台数据获取"""
import os, sys, json, subprocess

TOKEN_DIR = os.path.expanduser("~/.local/share/ai-balance")


def _get_token():
    token = os.environ.get("ZHIPU_AUTH_TOKEN", "").strip()
    if token:
        return token
    envrc = os.path.expanduser("~/.config/llm-providers/zhipu/.envrc")
    if os.path.exists(envrc):
        with open(envrc) as f:
            for line in f:
                if line.startswith("export ANTHROPIC_AUTH_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _get_base_url():
    url = os.environ.get("ZHIPU_BASE_URL", "").strip()
    if url:
        return url
    cfg_file = os.path.expanduser("~/.claude/settings.json")
    if os.path.exists(cfg_file):
        try:
            import json as j
            with open(cfg_file) as f:
                cfg = j.load(f)
            base = cfg.get("env", {}).get("ANTHROPIC_BASE_URL", "")
            if "z.ai" in base:
                return "https://api.z.ai"
        except Exception:
            pass
    return "https://open.bigmodel.cn"


def _fmt_timestamp(ts):
    """毫秒时间戳转 MM-DD HH:MM"""
    if ts is None or ts <= 0:
        return None
    import datetime
    tz = datetime.timezone(datetime.timedelta(hours=8))
    dt = datetime.datetime.fromtimestamp(ts/1000, tz=datetime.timezone.utc).astimezone(tz)
    return dt.strftime("%m-%d %H:%M")


def main():
    token = _get_token()
    if not token:
        print(json.dumps({"platform": "智谱", "error": "请设置 ZHIPU_AUTH_TOKEN 或检查配置文件"}))
        return

    base_url = _get_base_url()
    try:
        result = subprocess.run(
            ["curl", "-s", f"{base_url}/api/monitor/usage/quota/limit",
             "-H", f"Authorization: {token}",
             "-H", "Content-Type: application/json"],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
    except Exception as e:
        print(json.dumps({"platform": "智谱", "error": f"网络请求失败: {e}"}))
        return

    if data.get("success") != True:
        msg = data.get("msg", data.get("error", {}).get("message", "Token 无效"))
        print(json.dumps({"platform": "智谱", "error": msg}))
        return

    limits = data.get("data", {}).get("limits", [])
    tokens_limits = [l for l in limits if l.get("type") == "TOKENS_LIMIT"]
    time_limit = [l for l in limits if l.get("type") == "TIME_LIMIT"]

    # 5H 用量 (TOKENS_LIMIT[0])
    usage_5h = round(tokens_limits[0]["percentage"]) if len(tokens_limits) > 0 else None
    reset_5h = _fmt_timestamp(tokens_limits[0].get("nextResetTime")) if len(tokens_limits) > 0 else None

    # 周用量 (TOKENS_LIMIT[1])
    usage_weekly = round(tokens_limits[1]["percentage"]) if len(tokens_limits) > 1 else None
    reset_weekly = _fmt_timestamp(tokens_limits[1].get("nextResetTime")) if len(tokens_limits) > 1 else None

    # 月用量 (TIME_LIMIT)
    usage_monthly = round(time_limit[0]["percentage"]) if len(time_limit) > 0 else None
    reset_monthly = _fmt_timestamp(time_limit[0].get("nextResetTime")) if len(time_limit) > 0 else None

    # 智谱 + 智谱-MCP 两行
    print(json.dumps({
        "platform": "智谱",
        "usage_5h": usage_5h,
        "usage_weekly": usage_weekly,
        "reset_5h": reset_5h,
        "reset_weekly": reset_weekly,
        "usage_monthly": None,
        "reset_monthly": None,
    }))
    print(json.dumps({
        "platform": "智谱-MCP",
        "usage_5h": None,
        "usage_weekly": None,
        "reset_5h": None,
        "reset_weekly": None,
        "usage_monthly": usage_monthly,
        "reset_monthly": reset_monthly,
    }))


if __name__ == "__main__":
    main()