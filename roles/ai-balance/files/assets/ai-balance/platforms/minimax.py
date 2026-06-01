#!/usr/bin/env python3
"""MiniMax 平台数据获取"""
import os, sys, json, subprocess

TOKEN_DIR = os.path.expanduser("~/.local/share/ai-balance")


def _get_token():
    token = os.environ.get("MINIMAX_API_KEY", "").strip()
    if token:
        return token
    envrc = os.path.expanduser("~/.config/llm-providers/minimax/.envrc")
    if os.path.exists(envrc):
        with open(envrc) as f:
            for line in f:
                if line.startswith("export ANTHROPIC_AUTH_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _fmt_ts(ms):
    """毫秒时间戳转 MM-DD HH:MM"""
    if ms is None or ms <= 0:
        return None
    import datetime
    tz = datetime.timezone(datetime.timedelta(hours=8))
    dt = datetime.datetime.fromtimestamp(ms/1000, tz=datetime.timezone.utc).astimezone(tz)
    return dt.strftime("%m-%d %H:%M")


def main():
    token = _get_token()
    if not token:
        print(json.dumps({"platform": "MiniMax", "error": "请设置 MINIMAX_API_KEY"}))
        return

    try:
        result = subprocess.run(
            ["curl", "-s", "https://www.minimaxi.com/v1/token_plan/remains",
             "-H", f"Authorization: Bearer {token}",
             "-H", "Content-Type: application/json"],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
    except Exception as e:
        print(json.dumps({"platform": "MiniMax", "error": f"网络请求失败: {e}"}))
        return

    if data.get("base_resp", {}).get("status_code") != 0:
        msg = data.get("base_resp", {}).get("status_msg", "未知错误")
        print(json.dumps({"platform": "MiniMax", "error": msg}))
        return

    mm_item = None
    search_item = None
    video_item = None
    for item in data.get("model_remains", []):
        model = item.get("model_name", "")
        if "general" in model or "MiniMax" in model:
            mm_item = item
        elif "search" in model:
            search_item = item
        elif "video" in model:
            video_item = item

    lines = []

    # MiniMax 文本生成
    if mm_item:
        usage_5h = 100 - (mm_item.get("current_interval_remaining_percent") or 0)
        usage_weekly = 100 - (mm_item.get("current_weekly_remaining_percent") or 0)
        lines.append(json.dumps({
            "platform": "MiniMax",
            "usage_5h": usage_5h,
            "usage_weekly": usage_weekly,
            "reset_5h": _fmt_ts(mm_item.get("end_time")),
            "reset_weekly": _fmt_ts(mm_item.get("weekly_end_time")),
            "usage_monthly": None,
            "reset_monthly": None,
        }))

    # MiniMax-MCP
    if search_item:
        usage_5h = 100 - (search_item.get("current_interval_remaining_percent") or 0)
        usage_weekly = 100 - (search_item.get("current_weekly_remaining_percent") or 0)
        lines.append(json.dumps({
            "platform": "MiniMax-MCP",
            "usage_5h": usage_5h,
            "usage_weekly": usage_weekly,
            "reset_5h": _fmt_ts(search_item.get("end_time")),
            "reset_weekly": _fmt_ts(search_item.get("weekly_end_time")),
            "usage_monthly": None,
            "reset_monthly": None,
        }))

    if not lines:
        print(json.dumps({"platform": "MiniMax", "error": "无可用额度配额"}))
        return

    print("\n".join(lines))


if __name__ == "__main__":
    main()