#!/usr/bin/env python3
"""AI Balance UI - 表格渲染层"""
import json
import sys
import unicodedata

# ANSI 颜色
C_RESET = "\033[0m"
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[96m"
C_MAGENTA = "\033[95m"

PLATFORM_COLORS = {
    "Kimi": C_BLUE,
    "MiniMax": C_MAGENTA,
    "MiniMax-MCP": C_MAGENTA,
    "智谱": C_GREEN,
    "智谱-MCP": C_GREEN,
}


def str_width(s):
    """计算字符串显示宽度（中文2格，英文1格）。"""
    width = 0
    for c in s:
        if unicodedata.east_asian_width(c) in ('F', 'W'):
            width += 2
        else:
            width += 1
    return width


def lpad(s, width):
    """左填充到指定显示宽度。"""
    w = str_width(s)
    return s + ' ' * (width - w) if w < width else s


def render_row(platform, usage_5h, usage_weekly, reset_5h, reset_weekly, usage_monthly=None, reset_monthly=None):
    """渲染一行数据。"""
    color = PLATFORM_COLORS.get(platform, C_RESET)

    # 百分比
    col_5h = lpad(f"{usage_5h}%" if usage_5h is not None else "-", 6)
    col_w = lpad(f"{usage_weekly}%" if usage_weekly is not None else "-", 6)
    col_m = lpad(f"{usage_monthly}%" if usage_monthly is not None else "-", 6)

    # 重置时间
    col_r5h = lpad(reset_5h if reset_5h else "-", 12)
    col_rw = lpad(reset_weekly if reset_weekly else "-", 12)
    col_rm = lpad(reset_monthly if reset_monthly else "-", 12)

    # 平台名称（带颜色）
    name_padded = lpad(platform, 12)
    return f"{color}{name_padded}{C_RESET}  {col_5h}  {col_r5h}  {col_w}  {col_rw}  {col_m}  {col_rm}"


def render_error(platform, msg):
    """渲染错误行。"""
    color = C_RED
    name_padded = lpad(platform, 12)
    return f"{color}{name_padded}{C_RESET}  {color}[ERROR] {msg}{C_RESET}"


def render_table(rows):
    """渲染完整表格。"""
    # 表头: 平台, 5H用量, 5H重置, 周用量, 周重置, 月用量, 月重置
    header = (
        f"{lpad('平台', 12)}  {lpad('5H用量', 6)}  {lpad('5H重置', 12)}  {lpad('周用量', 6)}  {lpad('周重置', 12)}  {lpad('月用量', 6)}  {lpad('月重置', 12)}\n"
        f"{'-' * 12}  {'-' * 6}  {'-' * 12}  {'-' * 6}  {'-' * 12}  {'-' * 6}  {'-' * 12}"
    )
    lines = [header]
    lines.extend(rows)
    return "\n".join(lines)


def main():
    """从 stdin 读取 JSON 数组，渲染表格。"""
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(f"{C_RED}输入不是有效 JSON{C_RESET}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, list):
        data = [data]

    rows = []
    for item in data:
        if "error" in item:
            rows.append(render_error(item["platform"], item["error"]))
        else:
            rows.append(render_row(
                item["platform"],
                item.get("usage_5h"),
                item.get("usage_weekly"),
                item.get("reset_5h"),
                item.get("reset_weekly"),
                item.get("usage_monthly"),
                item.get("reset_monthly"),
            ))

    print(render_table(rows))


if __name__ == "__main__":
    main()