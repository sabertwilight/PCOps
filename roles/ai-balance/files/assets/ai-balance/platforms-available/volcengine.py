#!/usr/bin/env python3
"""火山方舟 (Volcengine Ark) Coding Plan / Agent Plan 用量获取

数据来源:火山方舟**控制面** OpenAPI(与数据面推理域名不同):
  POST https://open.volcengineapi.com/?Action=<Action>&Region=cn-beijing&Version=2024-01-01
鉴权:火山引擎签名 V4(AK/SK HMAC-SHA256,AWS SigV4 变体:固定 header 顺序
host;x-date;x-content-sha256;content-type、算法 HMAC-SHA256、scope 结尾 ark/request)。
注意:推理用的 Bearer API Key 会被网关拒绝(InvalidAuthorization),必须用火山账号的
AccessKey ID + Secret,在 https://console.volcengine.com/iam/keymanage 创建。

凭据读取顺序:环境变量(VOLC_ACCESS_KEY/VOLC_SECRET_KEY 等)→
~/.config/llm-providers/volcengine/.envrc(export VOLC_ACCESS_KEY=...)。

自动探测:先 GetAFPUsage(Agent Plan,回 AFPFiveHour/AFPWeekly/AFPMonthly 绝对
额度 Quota/Used),未订阅(各窗口 Quota<=0)再回落 GetCodingPlanUsage(Coding
Plan,回 QuotaUsage[] 百分比,Level 为 session/weekly/monthly,ResetTimestamp
秒级,-1 表示无活跃窗口)。
"""
import os, sys, json, hmac, hashlib, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

OPENAPI_HOST = "open.volcengineapi.com"
API_VERSION = "2024-01-01"
DEFAULT_REGION = "cn-beijing"
SERVICE = "ark"
CONTENT_TYPE = "application/json; charset=utf-8"
SIGNED_HEADERS = "host;x-date;x-content-sha256;content-type"

ENVRC = os.path.expanduser("~/.config/llm-providers/volcengine/.envrc")

AK_ENV_KEYS = ("VOLC_ACCESS_KEY", "VOLCENGINE_ACCESS_KEY", "VOLCENGINE_ACCESS_KEY_ID")
SK_ENV_KEYS = ("VOLC_SECRET_KEY", "VOLCENGINE_SECRET_KEY", "VOLCENGINE_SECRET_ACCESS_KEY")

# 鉴权类错误码特征:命中即停(两个 plan 共用凭据),提示换 AK/SK
_AUTH_MARKERS = ("auth", "signature", "accessdenied", "denied", "unauthorized",
                 "forbidden", "credential", "token")


def _read_envrc():
    """解析 .envrc 的 export NAME=VALUE 行。"""
    kv = {}
    if os.path.exists(ENVRC):
        with open(ENVRC) as f:
            for line in f:
                line = line.strip()
                if line.startswith("export ") and "=" in line:
                    k, v = line[len("export "):].split("=", 1)
                    kv[k.strip()] = v.strip().strip('"').strip("'")
    return kv


def _get_aksk():
    """(AccessKeyId, SecretAccessKey) 或 None。"""
    envrc = _read_envrc()
    ak = next((os.environ.get(k, "").strip() for k in AK_ENV_KEYS
               if os.environ.get(k, "").strip()), "") or \
         next((envrc[k] for k in AK_ENV_KEYS if envrc.get(k)), "")
    sk = next((os.environ.get(k, "").strip() for k in SK_ENV_KEYS
               if os.environ.get(k, "").strip()), "") or \
         next((envrc[k] for k in SK_ENV_KEYS if envrc.get(k)), "")
    return (ak, sk) if ak and sk else None


def _get_region():
    """从 base URL(数据面域名里的 cn-*/ap-* 段)推导控制面 Region,默认 cn-beijing。"""
    base = (os.environ.get("VOLC_BASE_URL", "").strip()
            or _read_envrc().get("ANTHROPIC_BASE_URL", "")
            or os.environ.get("ANTHROPIC_BASE_URL", ""))
    host = base.split("://", 1)[-1].split("/", 1)[0]
    for part in host.split("."):
        if part.startswith("cn-") or part.startswith("ap-"):
            return part
    return DEFAULT_REGION


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hmac_sha256(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha256).digest()


def _uri_encode(s: str) -> str:
    """RFC3986:unreserved 之外全部 %XX 大写编码。"""
    safe = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.~"
    return "".join(chr(b) if b in safe else "%%%02X" % b for b in s.encode("utf-8"))


def _canonical_query(action: str, region: str) -> str:
    pairs = sorted([("Action", action), ("Region", region), ("Version", API_VERSION)])
    return "&".join(f"{_uri_encode(k)}={_uri_encode(v)}" for k, v in pairs)


def _sign(ak: str, sk: str, region: str, canonical_query: str, now: datetime):
    x_date = now.strftime("%Y%m%dT%H%M%SZ")
    short_date = now.strftime("%Y%m%d")
    payload_hash = _sha256_hex(b"")

    canonical_headers = (f"host:{OPENAPI_HOST}\n"
                         f"x-date:{x_date}\n"
                         f"x-content-sha256:{payload_hash}\n"
                         f"content-type:{CONTENT_TYPE}\n")
    canonical_request = (f"POST\n/\n{canonical_query}\n{canonical_headers}\n"
                         f"{SIGNED_HEADERS}\n{payload_hash}")

    scope = f"{short_date}/{region}/{SERVICE}/request"
    string_to_sign = (f"HMAC-SHA256\n{x_date}\n{scope}\n"
                      f"{_sha256_hex(canonical_request.encode())}")

    # 密钥派生:SK 不加 AWS4 前缀,终止串 request
    k_date = _hmac_sha256(sk.encode(), short_date.encode())
    k_region = _hmac_sha256(k_date, region.encode())
    k_service = _hmac_sha256(k_region, SERVICE.encode())
    k_signing = _hmac_sha256(k_service, b"request")
    signature = hmac.new(k_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()

    auth = (f"HMAC-SHA256 Credential={ak}/{scope}, "
            f"SignedHeaders={SIGNED_HEADERS}, Signature={signature}")
    return auth, x_date, payload_hash


def _call(ak: str, sk: str, region: str, action: str):
    """单次 OpenAPI 调用。返回 (kind, payload):
    body=拿到业务 JSON;auth=鉴权类硬错误(描述);soft=其它错误(描述)。"""
    query = _canonical_query(action, region)
    url = f"https://{OPENAPI_HOST}/?{query}"
    auth, x_date, payload_hash = _sign(ak, sk, region, query, datetime.now(timezone.utc))

    req = urllib.request.Request(url, data=b"", method="POST")
    req.add_header("X-Date", x_date)
    req.add_header("X-Content-Sha256", payload_hash)
    req.add_header("Content-Type", CONTENT_TYPE)
    req.add_header("Authorization", auth)

    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return _classify(e.code, json.loads(raw))
        except Exception:
            return ("soft", f"HTTP {e.code}: {raw[:120]}")
    except Exception as e:
        return ("soft", f"网络请求失败: {e}")

    try:
        body = json.loads(raw)
    except Exception:
        return ("soft", f"响应解析失败: {raw[:120]}")
    return _classify(200, body)


def _classify(status: int, body: dict):
    err = (body.get("ResponseMetadata", {}).get("Error")
           or body.get("Error") or {})
    code, msg = str(err.get("Code", "")), str(err.get("Message", ""))
    if code or msg:
        detail = f"HTTP {status} {code}: {msg}".strip()
        if any(m in code.lower() for m in _AUTH_MARKERS):
            return ("auth", detail)
        return ("soft", detail)
    if status != 200:
        return ("soft", f"HTTP {status}")
    return ("body", body)


def _fmt_ts(n):
    """秒/毫秒时间戳 → MM-DD HH:MM(东八区);<=0 视为无重置时间。"""
    if n is None or n <= 0:
        return None
    ms = n * 1000 if n < 1_000_000_000_000 else n
    dt = datetime.fromtimestamp(ms // 1000, tz=timezone(timedelta(hours=8)))
    return dt.strftime("%m-%d %H:%M")


def _to_f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_afp(result: dict):
    """GetAFPUsage(Agent Plan):AFPFiveHour/AFPWeekly/AFPMonthly 的 Quota/Used。
    各窗口 Quota<=0 = 未订阅/未启用 → 返回 {} 以回落 Coding Plan。"""
    tiers = {}
    for key, slot in (("AFPFiveHour", "5h"), ("AFPWeekly", "weekly"), ("AFPMonthly", "monthly")):
        win = result.get(key) or {}
        quota = _to_f(win.get("Quota")) or 0.0
        if quota <= 0:
            continue
        used = _to_f(win.get("Used")) or 0.0
        tiers[slot] = (round(used / quota * 100), _fmt_ts(_to_f(win.get("ResetTime"))))
    return tiers


def _parse_coding(result: dict):
    """GetCodingPlanUsage(Coding Plan):QuotaUsage[] 仅百分比,Level 为窗口标签。"""
    label_map = {"session": "5h", "5h": "5h", "fivehour": "5h", "five_hour": "5h",
                 "weekly": "weekly", "week": "weekly", "7d": "weekly",
                 "monthly": "monthly", "month": "monthly"}
    tiers = {}
    arr = result.get("QuotaUsage") or result.get("Usages") or result.get("Details") or []
    for item in arr:
        if not isinstance(item, dict):
            continue
        label = str(item.get("Level") or item.get("Type") or item.get("Period") or "")
        slot = label_map.get(label.lower())
        if not slot or slot in tiers:
            continue
        pct = round(_to_f(item.get("Percent")) or 0.0)
        tiers[slot] = (pct, _fmt_ts(_to_f(item.get("ResetTimestamp") or item.get("ResetTime"))))
    return tiers


def main():
    creds = _get_aksk()
    if not creds:
        print(json.dumps({"platform": "火山方舟",
                          "error": "缺少 AccessKey,请在 ~/.config/llm-providers/volcengine/.envrc "
                                   "配置 VOLC_ACCESS_KEY / VOLC_SECRET_KEY(console.volcengine.com/iam/keymanage)"}))
        return
    ak, sk = creds
    region = _get_region()

    soft_errors = []
    # 1) Agent Plan:GetAFPUsage
    kind, payload = _call(ak, sk, region, "GetAFPUsage")
    if kind == "auth":
        print(json.dumps({"platform": "火山方舟", "error": f"AK/SK 鉴权失败:{payload}"}))
        return
    if kind == "body":
        tiers = _parse_afp(payload.get("Result", {}) or {})
        if tiers:
            print(json.dumps({"platform": "火山方舟",
                              "usage_5h": tiers.get("5h", (None,))[0],
                              "reset_5h": tiers.get("5h", (None, None))[1],
                              "usage_weekly": tiers.get("weekly", (None,))[0],
                              "reset_weekly": tiers.get("weekly", (None, None))[1],
                              "usage_monthly": tiers.get("monthly", (None,))[0],
                              "reset_monthly": tiers.get("monthly", (None, None))[1]}))
            return
    else:
        soft_errors.append(f"GetAFPUsage: {payload}")

    # 2) Coding Plan:GetCodingPlanUsage
    kind, payload = _call(ak, sk, region, "GetCodingPlanUsage")
    if kind == "auth":
        print(json.dumps({"platform": "火山方舟", "error": f"AK/SK 鉴权失败:{payload}"}))
        return
    if kind == "body":
        tiers = _parse_coding(payload.get("Result", {}) or {})
        if tiers:
            print(json.dumps({"platform": "火山方舟",
                              "usage_5h": tiers.get("5h", (None,))[0],
                              "reset_5h": tiers.get("5h", (None, None))[1],
                              "usage_weekly": tiers.get("weekly", (None,))[0],
                              "reset_weekly": tiers.get("weekly", (None, None))[1],
                              "usage_monthly": tiers.get("monthly", (None,))[0],
                              "reset_monthly": tiers.get("monthly", (None, None))[1]}))
            return
    else:
        soft_errors.append(f"GetCodingPlanUsage: {payload}")

    if soft_errors:
        print(json.dumps({"platform": "火山方舟", "error": "; ".join(soft_errors)}))
    else:
        print(json.dumps({"platform": "火山方舟", "error": "未订阅 Agent Plan / Coding Plan"}))


if __name__ == "__main__":
    main()
