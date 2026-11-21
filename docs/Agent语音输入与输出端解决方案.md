# Agent 语音输入与输出端解决方案

> 整理时间：2026-11-16；输入端调研回补：2026-11-20  
> 适用栈：Ubuntu 24.04 / Hyprland(Wayland) / kitty / chezmoi / herdr + omp / Claude Code(cc) / kimi cli / zcode  
> 背景：zcode 已跑通语音输入；herdr 手机端借助输入法语音输入可用；输出端目前纯文字。当前 Linux 语音输入已确认是 Doubao Murmur 1.5.1（Flatpak，`com.doubao.Murmur`），中文识别准确率一般，且不接受商业版方案。  
> 核心结论：  
> 1. **输出端**：文字仍是 Agent 的可核验交付层，音频只是新的注意力界面；先做 turn-end 结论播报，不做双向语音 Agent。  
> 2. **输入端**：**已部署定型：fcitx5-vinput + 豆包语音官方 ASR API（云端）**。原"不接商业 ASR API"边界已修订为"官方 API 按量付费可接受"；本地 Qwen3-ASR-1.7B 降级为离线/隐私备选（未部署），SenseVoice 仅为资源受限备用。Doubao Murmur 已于 2026-11-20 按用户实测决定卸载。

---

# 第一部分：输出端（结论播报）

## 1. 输出端现状判断（2026）

输出端已经不是"仍局限于文字"，进展在三层：

1. **可打断实时对话**：ChatGPT Advanced Voice、Gemini Live 等延迟 200–500ms 级，支持 barge-in；工程关键是 turn-taking——打断处理 P95 约 142ms、轮次间隙 P95 约 310ms，被打断时只保留用户实际听到的内容。
2. **native S2S vs pipeline**：native（OpenAI Realtime / Gemini Live / Moshi）延迟 200–400ms 但模型不可换；pipeline（STT→LLM→TTS）延迟 500–800ms 但可路由、可插业务逻辑。本栈应走 pipeline。
3. **长内容收听化**：TTS 适合晨报摘要、PR/Issue 摘要、告警 triage、巡检结果；不适合替代代码 diff、栈追踪、测试失败细节。

## 2. 落地原则

| 组件 | 角色 | 不做 |
|---|---|---|
| omp / cc / kimi / zcode | 产生 transcript / hook 事件 | 不把 stdout 直接当播报源 |
| `agent-say` | 清洗文本并触发 TTS，one-shot 播放 | 不读屏幕、不解析 ANSI/spinner |
| herdr | pane 完成/空闲/焦点/通知音信号 | 不承载结论文本内容 |
| 屏幕 | 可核验真相层：diff、日志、命令 | 不被语音替代 |
| 麦克风 | 只在输入阶段武装 | TTS 播放期间 mute，避免回采 |

三条硬规则：结论必须能一键展开成文字；hook stdout 必须吞掉（exit 0 的 stdout 可能注入模型上下文）；只把需要立即占用耳朵的事件语音化。

## 3. 播报脚本

```bash
mkdir -p ~/.local/bin

cat > ~/.local/bin/say-turn.py <<'PY'
#!/usr/bin/env python3
import json, os, re, subprocess, sys

def clean(s: str) -> str:
    s = re.sub(r"```.*?```", "。这一段是代码，屏幕上看。", s, flags=re.S)
    s = re.sub(r"`([^`]+)`", lambda m: m.group(1) if len(m.group(1)) <= 24 else "这段命令或标识符", s)
    s = re.sub(r"https?://\S+", "这个链接", s)
    s = re.sub(r"(?:(?:~|\.|\.\.)/)?[\w./-]+\.(?:py|go|ts|tsx|js|jsx|json|ya?ml|toml|sh|md|log|sql|tf)", "这个文件", s)
    s = re.sub(r"^\s*[-*+>#\d.)\[]+\s*", "", s, flags=re.M)
    s = re.sub(r"\$\s+[^\n]+", "下面这条命令", s)
    s = re.sub(r"\b(?:[a-f0-9]{7,40}|sha256:[a-f0-9]{16,})\b", "这个哈希", s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > 220:
        parts = re.split(r"(?<=[。！？!?；;])\s*", s)
        out = ""
        for p in parts:
            if len(out) + len(p) > 220:
                break
            out += p
        s = out.strip() or s[:220]
        s += "。详细内容在终端里。"
    return s

def last_assistant_text_from_transcript(path: str) -> str:
    text = ""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except Exception:
                continue
            msg = obj.get("message") if isinstance(obj, dict) else None
            if not isinstance(msg, dict) or msg.get("role") != "assistant":
                continue
            content = msg.get("content")
            chunk = []
            if isinstance(content, str):
                chunk.append(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        chunk.append(part.get("text", ""))
            if chunk:
                text = "\n".join(chunk)
    return text

def main():
    if os.environ.get("TTS_MUTE") == "1":
        return 0
    raw = sys.stdin.read()
    data = {}
    try:
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        pass
    text = os.environ.get("TURN_TEXT", "").strip()
    path = data.get("transcript_path") or data.get("session_path") or ""
    if not text and path and os.path.exists(path):
        text = last_assistant_text_from_transcript(path)
    text = clean(text)
    if not text:
        return 0
    home = os.path.expanduser("~")
    wrapper = os.path.join(home, ".local", "bin", "agent-say-core")
    subprocess.run([wrapper, text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
PY

cat > ~/.local/bin/agent-say-core <<'SH'
#!/usr/bin/env bash
set -u
text="${*: -1}"
[ -n "${text:-}" ] || exit 0
if command -v edge-tts >/dev/null 2>&1; then
  tmp="$(mktemp /dev/shm/agent-say.XXXXXX.mp3)"
  edge-tts --voice "${TTS_VOICE:-zh-CN-XiaoxiaoNeural}" --text "$text" --write-media "$tmp" >/dev/null 2>&1
  if command -v ffplay >/dev/null 2>&1; then
    ffplay -nodisp -autoexit -loglevel error "$tmp" >/dev/null 2>&1
  elif command -v mpv >/dev/null 2>&1; then
    mpv --no-video --really-quiet "$tmp" >/dev/null 2>&1
  elif command -v paplay >/dev/null 2>&1; then
    paplay "$tmp" >/dev/null 2>&1 || true
  fi
  rm -f "$tmp"
elif command -v spd-say >/dev/null 2>&1; then
  spd-say "$text" >/dev/null 2>&1
elif command -v espeak-ng >/dev/null 2>&1; then
  espeak-ng -v zh "$text" >/dev/null 2>&1
fi
exit 0
SH

cat > ~/.local/bin/agent-say <<'SH'
#!/usr/bin/env bash
# hook 入口：stdin 收 JSON，stdout/stderr 全部吞掉，只向音频设备输出。
exec python3 "$HOME/.local/bin/say-turn.py" </dev/stdin >/dev/null 2>&1
SH

chmod +x ~/.local/bin/say-turn.py ~/.local/bin/agent-say-core ~/.local/bin/agent-say
python3 -m pip install --user edge-tts
sudo apt-get install -y ffmpeg speech-dispatcher
```

验证：

```bash
printf '{"transcript_path":"/nonexistent","cwd":"%s"}' "$PWD" \
  | TURN_TEXT='结论播报测试：已完成本轮修改，测试还没跑。' ~/.local/bin/say-turn.py
pgrep -af 'edge-tts|ffplay|mpv|spd-say' || true
```

## 4. 接入各 Agent

### omp：原生 extension

`~/.omp/agent/extensions/voice-turn.ts`：

```ts
import { spawn } from "node:child_process";
import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";

function lastAssistantText(messages: any[]): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i];
    if (!m || m.role !== "assistant" || !Array.isArray(m.content)) continue;
    const texts = m.content
      .filter((p: any) => p?.type === "text" && typeof p.text === "string")
      .map((p: any) => p.text);
    const t = texts.join("\n").trim();
    if (t) return t;
  }
  return "";
}

export default function voiceTurn(pi: ExtensionAPI) {
  pi.on("agent_end", async (event: any) => {
    const text = lastAssistantText(event.messages ?? []);
    if (!text) return;
    const bin = `${process.env.HOME}/.local/bin/agent-say`;
    const child = spawn(bin, [], {
      env: { ...process.env, TURN_TEXT: text },
      stdio: "ignore",
      detached: true,
    });
    child.unref();
  });
}
```

验证：`ls -l ~/.omp/agent/extensions/voice-turn.ts`，在 omp 里发小任务后 `pgrep -af 'agent-say|edge-tts|ffplay|mpv'`。

### Claude Code：Stop hook

`~/.claude/settings.json`：

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash -lc '$HOME/.local/bin/agent-say'",
            "async": true,
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### kimi cli / zcode：先探查事件，不猜 hook 名

```bash
kimi --help | sed -n '1,160p'
zcode --help | sed -n '1,200p'
ls -la ~/.kimi ~/.zcode ~/.config/kimi ~/.config/zcode 2>/dev/null || true
find ~/.kimi ~/.zcode ~/.config/kimi ~/.config/zcode -maxdepth 3 -type f \
  \( -name '*.json' -o -name '*.jsonl' -o -name '*hook*' -o -name '*event*' \) 2>/dev/null | sed -n '1,80p'
```

有 `Stop / turn_end / agent_end / session_stop` 类事件就接 `agent-say`；没有就 tail JSONL transcript，复用 `say-turn.py` 的 `last_assistant_text_from_transcript`。

## 5. herdr 职责边界与场景表

herdr 只做 pane 完成/空闲/焦点/通知音；文本结论不要从屏幕抓（spinner、ANSI、tool 输出会混进去）。

| 场景 | 播报策略 |
|---|---|
| 小任务完成 | 直接播清洗后的结论 |
| 跑测试 / CI / terraform plan | 只播"成功/失败 + 第一个失败名" |
| 大 diff / 迁移 / 重构 | 不播全文；让 Agent 第一句输出人话结论 |
| 长输出离开屏幕 | 播前固定口令"先说结论"，限制 220 字内 |

## 6. 输出端已知坑

1. hook stdout 回灌：播报脚本必须 stdout/stderr 全吞。
2. TTS 回采：连续语音输入 + TTS 外放同机同麦同音箱时会形成"播放→回采→STT→Agent→再播放"死循环；one-shot 播报风险小，播放期间 mute mic 或戴耳机。
3. 不要直接播 markdown/路径/哈希/代码块，清洗规则已内置。
4. 最有效的一招是在 agent rule 文件里加硬规则："每轮最终输出第一句必须是可播报结论，之后才是命令、路径、diff 引用。"

---

# 第二部分：输入端（开源语音输入）

> 2026-11-20 调研回补：已核实本机环境、当前工具、官方模型资料和可用接入接口；**同日已完成 vinput 部署并打通云端 ASR 全链路（见下文"0. 实施记录"），同音频 A/B 实测仍待做**。下文第 1–7 节为调研与决策依据，保留备查；其中"主路线=本地 Qwen3-ASR-1.7B"的表述已被实施记录取代。

## 0. 实施记录（2026-11-20 部署，同日实测通过）

实际落地方案与下文原"主路线"不同，输入端改为**云端官方 API 路线**。决策动因：识别质量与 Murmur 同源、打平即满足，同时消除非官方客户端风险；免除本地 GPU 显存博弈；官方 API 支持热词/替换词/上下文，为运维术语优化留出正路。

已完成的部署：

| 组件 | 状态 |
|---|---|
| fcitx5-vinput 2.4.2（PPA `xifan233/ppa`，完整版带 sherpa-onnx 运行时） | 已安装，fcitx5 插件加载正常，与 rime 并存无冲突 |
| `vinput-daemon.service`（用户级） | enabled + running |
| 录音设备 | PipeWire 正常；默认系统默认设备，可 `vinput device use` 切 WH-1000XM5 |
| provider `doubao-batch` | 已激活；按住右 Alt 说话、松开即出字，中文实测通过 |
| Ansible 固化 | 已固化为 PCOps `roles/voice-input`，API Key 经 `-e @my-config.yml` 传入（gitignored），排障要点见该 role tasks 注释 |

关键配置事实（重装/排障用）：

- 火山控制台开通"**豆包录音文件识别模型2.0**"，Resource ID 为 **`volc.seedasr.auc`**。注意：vinput 脚本旧默认的 `volc.bigasr.auc*` 系列在本账号报 `45000030 not granted`，不要混用。
- 新控制台只发**单个 API Key**（`X-Api-Key` 头），与旧版 AppId + AccessToken 对不同；本地 provider 脚本已改造：`X-Api-Key` 鉴权，凭证读取回退链 `VINPUT_ASR_API_KEY → VINPUT_ASR_ACCESS_TOKEN`（当前配在后者）。脚本路径 `~/.local/share/vinput/providers/doubao/batch`。
- 端点：flash 同步接口 `https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash`（脚本默认）；控制台示例给的是 submit/query 异步接口，当前未用。
- 费用：按量后付费（大模型录音文件识别价目约 2.3 元/小时标准版、4.5 元/小时极速版，以控制台为准），创建应用有免费试用额度；个人语音输入量级约 ¥20–70/月。火山 Coding Plan 订阅**不含** ASR（语音模型挂在 Agent Plan 下），未采用。
- 已知服务端行为：非语音音频返回 `20000003 Normal silence audio`，属正常；vinput 侧 VAD 默认开启。

待办：

1. ~~同音频 A/B~~（2026-11-20 已由用户主观对比替代：官方 API 准确率明显优于 Murmur，Murmur 随之卸载；如需更严格的数据可回装再测，覆盖术语、中英混说、数字/路径）。
2. 热词评估：豆包语音支持热词/替换词/上下文，收集 `terraform/kubernetes/ansible/herdr/omp` 错词样本后测试 provider 侧传参方式。
3. 本地离线备选（Qwen3-ASR-1.7B 或 SenseVoice）仅在出现离线/隐私需求时部署；断网时新链路不可用，回退为 herdr + 手机语音（Murmur 已卸载）。
4. 流式（边说边出字）暂不升级，理由见第 5 节。

## 1. 当前方案与本机约束（已确认）

| 项目 | 本机事实 | 对方案的影响 |
|---|---|---|
| 系统与会话 | Ubuntu 24.04.4 LTS；Hyprland；`XDG_SESSION_TYPE=wayland` | 不采用依赖 xdotool 的注入路线 |
| 主要输入场景 | kitty 中的 Agent CLI，以及普通 GUI 输入框 | 终端注入可靠性是硬门槛，不能只看 ASR 基准 |
| 输入法框架 | **Fcitx5 5.1.7 正在运行**，不是 IBus | 优先 Fcitx5 原生提交，不再以 IBus 工具为首选 |
| CPU / 内存 | i5-14600KF；32GB RAM | 可跑 CPU 备用模型，但主路线不必局限于 CPU |
| GPU | NVIDIA RTX 5060 8GB；驱动 580.173.02 | 主力模型选 Qwen3-ASR-1.7B；显存仍需实测 |
| Python / 磁盘 | Python 3.12.3；调研时 `/home` 可用约 164GB；未发现 uv/conda | 可按官方建议使用隔离 Python 3.12 环境 |
| 当前语音工具 | Doubao Murmur 1.5.1，Flatpak ID `com.doubao.Murmur` | 保留作对照与回退，实施初期不要卸载 |

Doubao Murmur 官方 README 已确认其工作方式：通过内嵌 WebView 登录豆包并保存网页凭证，之后通过 WebSocket 把麦克风音频发送到豆包服务端识别。它**不是本地 ASR，也不是官方 API/SDK 路线**，存在凭证过期、网页协议变动、依赖网络和音频离开本机的约束。[Doubao Murmur 官方说明](https://github.com/lilong7676/doubao-murmur)

## 2. 最终选型

**主路线：`fcitx5-vinput + 本地 Qwen3-ASR-1.7B（GPU）`。第一版使用批量转写，主链路稳定后再评估流式。**

```text
麦克风
  → fcitx5-vinput（录音、快捷键、文本提交）
  → oai-batch provider
  → http://127.0.0.1:8000/v1/audio/transcriptions
  → 本地 qwen-asr / vLLM + Qwen3-ASR-1.7B
  → vinput 通过 Fcitx5 提交到 kitty / GUI
```

后续如确需边说边出字，再把 provider 换成 `vllm-stream`，接本机 `/v1/realtime`；不要第一版就同时调试输入法、模型服务和新实时协议。

选择理由：

1. **注入层匹配现有环境**：vinput 是 Fcitx5 插件，支持按住说话和单击开始/停止，避免把主链路押在剪贴板粘贴或模拟键盘上。
2. **模型有升级潜力**：Qwen3-ASR-1.7B 的官方中文基准总体优于 Doubao-ASR，并支持中英混合、流式/离线和多种中文方言。
3. **数据与账号解耦**：模型下载完成后，识别可在本机完成，不依赖豆包 Cookie、网页协议或商业 API。
4. **保留回退能力**：vinput 支持本地/云端 provider 切换；Doubao Murmur 在新方案验收前保持原样。
5. **默认不加 LLM 改写**：先评估原始 ASR，避免纠错场景引入额外延迟、内容改写和新的故障点。

## 3. 模型证据与取舍

### Qwen3-ASR-1.7B 与 Doubao-ASR

以下为 Qwen 官方 README 的 WER 基准，数值越低越好：

| 数据集 | Doubao-ASR | Qwen3-ASR-0.6B | Qwen3-ASR-1.7B |
|---|---:|---:|---:|
| AISHELL-2-test | 2.85 | 3.15 | **2.71** |
| SpeechIO | 2.93 | 3.44 | **2.88** |
| Fleurs-zh | 2.69 | 2.88 | **2.41** |
| CV-zh | 5.95 | 6.89 | **5.35** |
| 内部 Dialog-Mandarin | 6.61 | 7.06 | **6.54** |

因此主力选择 **1.7B，不是 0.6B**。0.6B 更轻，但在这些中文集上并没有超过 Doubao，不能把它当作必然升级。官方基准中的 Doubao-ASR 也不一定等同于 Murmur 当前调用的网页模型；最终是否更好，必须用本人声音、麦克风和运维术语做同音频测试。[Qwen3-ASR 官方模型与基准](https://github.com/QwenLM/Qwen3-ASR/blob/main/README.md)

### 其他模型定位

| 模型 | 已核实情况 | 本栈定位 |
|---|---|---|
| SenseVoice Small int8 | vinput 当前资源包约 158MiB；多语言；`supports_hotwords: false` | 轻量 CPU 备用，不作默认准度升级 |
| Qwen3-ASR-0.6B int8 | vinput 资源包约 827MiB；`supports_hotwords: false` | 资源受限备用，不承诺优于当前豆包 |
| FireRedASR2-CTC int8 | `model.int8.onnx` 约 740MB，模型目录约 1.5GB；支持中英和 20+ 方言；官方示例单线程 RTF 0.173 | 纯 CPU、方言需求的备选，不是本机 GPU 主路线 |
| Fun-ASR-Nano | 有独立模型能力和不同运行时，但本次未验证其与 vinput 主链路的直接集成 | 暂不引入，避免同时比较过多运行时 |

### 热词结论修正

原文“SenseVoice/Paraformer/Qwen3-ASR 都可直接使用 `hotwords_file`”不准确。sherpa-onnx 官方明确说明：**通用 `hotwords_file` 只支持 transducer 模型，并要求 `modified_beam_search`**；vinput 资源库也把 SenseVoice 和 Qwen3-0.6B 标为不支持热词。某些模型或云 API 可能有独立的 prompt/biasing 机制，但不能与 sherpa 通用热词参数混为一谈。[sherpa-onnx 热词文档](https://k2-fsa.github.io/sherpa/onnx/hotwords/index.html)、[vinput 模型资源定义](https://raw.githubusercontent.com/xifan2333/vinput-registry/main/registry/models.json)

后续先收集 `terraform / kubernetes / ansible / herdr / omp` 等真实错词样本。确有需要时再增加固定替换或本地纠错场景，不要预设“热词已支持”，也不要默认开启可能改写命令和路径的 LLM 后处理。

## 4. 工具层调研结论

### 主选：fcitx5-vinput

调研时最新 release 为 2.4.2（2026-10-14），GPL-3.0，官方支持 Ubuntu 24.04 PPA、GUI/CLI、按住说话、云端与本地 ASR。[vinput 项目与安装说明](https://github.com/xifan2333/fcitx5-vinput)、[2.4.2 release](https://github.com/xifan2333/fcitx5-vinput/releases/latest)

与主路线直接相关的官方 provider：

- `oai-batch`：接 `/v1/audio/transcriptions`，支持自定义 URL、model、API key 等，适合作为第一版。
- `vllm-stream`：接 OpenAI Realtime 风格 WebSocket；官方说明已用本地 vLLM `Qwen3ASRRealtimeGeneration` 的 `/v1/realtime` 测试，适合作为后续流式升级。[provider 资源库](https://raw.githubusercontent.com/xifan2333/vinput-registry/main/registry/providers.json)、[vllm-stream 说明](https://github.com/xifan2333/vinput-registry/blob/main/resources/providers/vllm/streaming/README.md)

### 不作为主路线的工具

| 工具 | 结论 |
|---|---|
| LazyTyper | 可方便切换本地 Qwen3 等模型，但属于闭源免费软件；已有 Linux 部分终端注入问题报告。可作临时对照，不作为 kitty 主链路。[调研时稳定版 1.9.3](https://github.com/oldcai/LazyTyper-releases/releases)、[第三方实测与问题记录](https://techmoon.xyz/lazytyper-voice-input/) |
| vocalinux / voice-typing-linux | 分别以 IBus/远程识别或 IBus 注入为主；当前机器已经在用 Fcitx5，没有必要为此更换框架 |
| CapsWriter-Offline | 模型选择可参考，但 `keyboard` 注入不适合当前 Hyprland/Wayland 主链路 |
| 闪电说 | 本次没有取得足够的第一方资料验证模型与 Wayland 能力，不据此推进 |
| 自制 sherpa-onnx + ydotool 脚本 | 可作为实验，但 vinput 已提供 Fcitx5 原生集成，不再重复造输入法和守护进程 |

## 5. 后续 agent 实施顺序

### 第 0 步：边界与回退

1. 原边界"实施期间不卸载 Doubao Murmur"已于 2026-11-20 失效：用户实测官方 API 准确率明显更优，Murmur 已卸载（flatpak `--delete-data`，无残留）；卸载过程未读取或复制其 Cookie、凭证和配置。
2. 原边界"不接商业 ASR API"已于 2026-11-20 修订：采用豆包语音**官方** API（按量付费、音频上云可接受）；仍不采用非官方/灰色通道。
3. ASR 服务只监听 `127.0.0.1`，模型和 Python 依赖放在独立目录/虚拟环境。
4. 先记录 `nvidia-smi`：调研时显存总计 8151MiB、已用约 5542MiB、可用约 2138MiB。这个值会变化，实施时必须重新测量。

### 第 1 步：安装并验证 vinput

优先采用官方 Ubuntu 24.04 PPA；若仓库策略不允许新增 PPA，再使用官方 release 的 `.deb`：

```bash
sudo add-apt-repository ppa:xifan233/ppa
sudo apt update
sudo apt install fcitx5-vinput
systemctl --user enable --now vinput-daemon.service
fcitx5 -r
```

打开 Vinput GUI，确认插件、守护进程和 PipeWire 录音正常。快捷键优先设为右 Alt，与现有肌肉记忆保持一致。

### 第 2 步：部署本地 Qwen3-ASR-1.7B

官方推荐隔离 Python 3.12 环境。以下只是**官方部署起点，尚未在本机执行**；实施时先核对 `qwen-asr-serve --help` 和官方 README：

```bash
python3 -m venv ~/.venvs/qwen3-asr
~/.venvs/qwen3-asr/bin/pip install -U 'qwen-asr[vllm]'
~/.venvs/qwen3-asr/bin/qwen-asr-serve Qwen/Qwen3-ASR-1.7B \
  --host 127.0.0.1 --port 8000 --gpu-memory-utilization 0.7
```

先用 `/v1/models` 和一段本地测试音频验证 `/v1/audio/transcriptions`，通过后再接 vinput。记录模型加载时间、单次识别耗时和峰值显存。

**显存门槛**：8GB 只是具备尝试条件，不是已验证可运行。先释放不必要的 GPU 计算任务，并限制单请求、短上下文；若 1.7B 仍不稳定，继续评估 1.7B 的量化或更轻运行时，不要静默降级为可能不如豆包的 0.6B/SenseVoice。

### 第 3 步：接入 `oai-batch`

在 Vinput GUI → Resources → ASR Providers 安装并配置 `oai-batch`：

```text
VINPUT_ASR_API_KEY=EMPTY
VINPUT_ASR_URL=http://127.0.0.1:8000/v1/audio/transcriptions
VINPUT_ASR_MODEL=Qwen/Qwen3-ASR-1.7B
```

`EMPTY` 只是满足 provider 的必填字段；若服务端实际配置了其他 key 或 served model name，以服务端为准。语言先保持自动，不要未经验证增加 prompt、response format 或 LLM 场景。

### 第 4 步：验证输入链路

依次在 kitty、浏览器、代码编辑器中验证：

- 按住说话、松开提交，以及单击开始/停止两种模式。
- 中文、英文术语、中英混说、数字、路径和标点。
- 连续多次输入、取消录音、切换焦点、长句和服务重启后的恢复。
- 断网后仍能识别（模型与依赖已下载完成的前提下）。

### 第 5 步：按需升级流式

只有批量链路验收通过且确实需要实时预览时才做。`vllm-stream` 默认地址为 `ws://localhost:8000/v1/realtime`；Qwen3 realtime 需要服务端显式使用 `Qwen3ASRRealtimeGeneration`，vLLM 文档要求通过 `--hf-overrides` 指定，不能直接假设普通批量服务已开放该端点。[vLLM 支持模型说明](https://docs.vllm.ai/en/latest/models/supported_models.html)

实时路径已有独立 issue 和兼容性约束，应单独验证准确率、延迟和资源占用，不回写为“批量已验证所以流式也可用”。

## 6. A/B 实测与切换标准

准备约 20 段带标准答案的短录音，覆盖：普通中文、运维术语、中英混说、数字/路径、口音或噪声。尽量让两套系统接收**同一份音频**，不要分别口述后直接把差异归因于模型。

每段记录：

1. 字错率或至少人工修改次数，以及术语错误清单。
2. 松开到文字提交的延迟；模型加载时间与稳态识别时间分开统计。
3. kitty / GUI 注入是否成功，是否发生重复、丢字或焦点错误。
4. GPU/CPU/RAM 占用，以及断网可用性。

切换默认方案前至少满足：kitty 注入稳定、离线可用、整体识别质量不逊于 Doubao Murmur、运维术语错误有改善、延迟可接受。若 1.7B 实测没有更好，就保留当前豆包并记录失败样本，**不要为了“本地化”而宣称体验已经升级**。

## 7. 输入端已知坑

1. **Wayland 注入**：xdotool 在 Hyprland 下不作为主方案；当前优先 Fcitx5 原生提交。
2. **热词能力不能泛化**：sherpa 通用热词仅支持 transducer；Qwen/SenseVoice 不应直接照抄 `hotwords_file`。
3. **流式与批量是两条部署路径**：先用批量证明模型和注入，再增加 `/v1/realtime`。
4. **显存是动态约束**：本机还有其他桌面和计算进程使用 GPU，不能只看显卡总容量。
5. **基准不等于个人体验**：官方 Doubao-ASR 数据不等于 Murmur 网页模型实测，必须保留同音频 A/B。
6. **麦克风质量是下限**：先确认输入设备、增益和噪声；录音问题不能靠换模型解决。
7. **输入端稳定后再接输出端播报**：TTS 播放期间 mute 麦克风，避免回采。
