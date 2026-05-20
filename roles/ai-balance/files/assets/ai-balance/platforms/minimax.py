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
    for item in data.get("model_remains", []):
        if item.get("model_name") == "MiniMax-M*":
            mm_item = item
        elif item.get("model_name") == "coding-plan-search":
            search_item = item

    lines = []

    # MiniMax 文本生成
    if mm_item:
        used_i = mm_item["current_interval_usage_count"]
        total_i = mm_item["current_interval_total_count"]
        used_w = mm_item["current_weekly_usage_count"]
        total_w = mm_item["current_weekly_total_count"]
        usage_5h = round(used_i / total_i * 100) if total_i else None
        usage_weekly = round(used_w / total_w * 100) if total_w else None
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
        used_i = search_item["current_interval_usage_count"]
        total_i = search_item["current_interval_total_count"]
        used_w = search_item["current_weekly_usage_count"]
        total_w = search_item["current_weekly_total_count"]
        usage_5h = round(used_i / total_i * 100) if total_i else None
        usage_weekly = round(used_w / total_w * 100) if total_w else None
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