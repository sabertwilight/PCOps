# voice-input

部署 **fcitx5-vinput + 豆包语音官方 ASR API** 的语音输入方案：按住右 Alt 说话，松开即出字到当前光标处（kitty / 浏览器 / 编辑器均可）。

```
麦克风 → vinput-daemon（录音/VAD）→ doubao-batch provider
      → 豆包语音官方 API（大模型录音文件识别）→ fcitx5 提交文本
```

背景、选型对比与输出端方案见仓库根目录 `docs/Agent语音输入与输出端解决方案.md`。

## 前置条件（需人工完成，无法自动化）

1. 火山引擎控制台完成实名认证；
2. 开通「**豆包语音 → 豆包录音文件识别模型2.0**」（创建应用后有免费试用额度，按量后付费约 2.3 元/小时，个人用量约 ¥20–70/月）；
3. 在应用的「快捷API接入」里创建 **API Key**。

火山方舟 Coding Plan 订阅**不含** ASR（语音模型挂在 Agent Plan 下），本方案按量付费即可，无需订阅。

## 使用

```bash
# 仓库根目录 my-config.yml（已被 .gitignore 忽略，不要提交）
voice_input_api_key: "<你的 API Key>"

# 运行
ansible-playbook playbooks/app.yml -K -e @my-config.yml --tags voice
```

未提供 `voice_input_api_key` 时 role 会 fail-fast，报错文案即上述前置步骤。

## 变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `voice_input_api_key` | `""` | 豆包语音 API Key（必填，经 `-e @my-config.yml` 传入） |
| `voice_input_resource_id` | `volc.seedasr.auc` | 识别资源 ID，对应控制台开通的"豆包录音文件识别模型2.0" |
| `voice_input_provider_script` | `~/.local/share/vinput/providers/doubao/batch` | provider 脚本路径（`vinput provider add` 物化落地） |
| `proxy_env` | 本机 7890 代理 | 兜底值；完整运行时由 `proxy` role 的 set_fact 覆盖 |

开关：`inventory/group_vars/all.yml` 的 `install_voice_input`（默认 `true`）。

## 实现要点

- **鉴权补丁**：vinput registry 的 `doubao-batch` 脚本按旧版控制台设计（`X-Api-App-Key` + `X-Api-Access-Key` 头）。新版控制台只发单个 API Key，role 用幂等的 `replace` 任务打四处补丁改为 `X-Api-Key` 鉴权，凭证读取回退链 `VINPUT_ASR_API_KEY → VINPUT_ASR_ACCESS_TOKEN`（当前配在后者）。已打补丁的脚本不再匹配，重复运行无副作用。
- **Resource ID 陷阱**：脚本旧默认 `volc.bigasr.auc*` 系列会返回 `45000030 not granted`；必须配 `volc.seedasr.auc`。
- **fcitx5 共存**：vinput 是 fcitx5 插件引擎，与 rime 并列，不替换现有输入法；右 Alt 为 vinput 默认触发键（单击=开关模式，按住=push-to-talk，`Shift_R` 命令面板）。
- **幂等**：provider 注册有 guard；配置写入前先读 config.json 比对，值相同跳过；daemon 仅在变更时经 handler 重启；fcitx5 仅在运行时 reload。
- **密钥不落库**：API Key 只写入本机 `~/.config/vinput/config.json`，仓库内仅留空默认值。

## 排障

| 现象 | 排查 |
|---|---|
| 按住右 Alt 无反应 | `journalctl --user -u vinput-daemon -n 50`；确认 fcitx5 已加载插件（`fcitx5 -r` 重载） |
| 识别报错 `45000030 not granted` | Resource ID 不对，或未在控制台开通模型2.0；确认 `voice_input_resource_id` |
| 识别报错 `20000003 Normal silence audio` | 正常现象：音频里没有语音（VAD 未检出说话） |
| 首次运行卡在 provider 注册几分钟 | registry 走 gh-proxy/ghfast 镜像回落，非卡死 |
| 想换录音设备（如 WH-1000XM5 话筒） | `vinput device list` / `vinput device use <id>` |

卸载：`sudo apt remove fcitx5-vinput && systemctl --user disable --now vinput-daemon.service`，配置在 `~/.config/vinput/` 与 `~/.local/share/vinput/`（如不再需要可一并删除）。
