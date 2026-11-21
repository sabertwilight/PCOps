# AGENTS.md

This file provides guidance to coding agents (Claude Code, Kimi Code, etc.) working in this repository.

## Project Overview

PCOps — 个人桌面与工具链的 Ansible 自动化项目，目标系统 **Ubuntu 24.04 LTS (Noble Numbat)**，在 localhost 上运行。两条主线：

- **Hyprland 桌面**（fork 自 [JaKooLit/Ubuntu-Hyprland](https://github.com/JaKooLit/Ubuntu-Hyprland)）：Wayland 合成器及主题、dotfiles 的自动化安装
- **应用与工具**：输入法、浏览器、开发工具、语音输入、AI 工具等桌面应用

## Key Commands

### 运行 Playbook（不要以 root 运行，一律用 `-K` 提权）

```bash
ansible-playbook playbooks/hyprland.yml -K                       # Hyprland 桌面完整安装
ansible-playbook playbooks/hyprland.yml -K --tags "core"         # 只装核心组件
ansible-playbook playbooks/hyprland.yml -K --tags "nvidia"       # 只装 NVIDIA 配置
ansible-playbook playbooks/app.yml -K                            # 安装全部应用
ansible-playbook playbooks/app.yml -K --tags "dev"               # 只装开发工具
ansible-playbook playbooks/app.yml -K -e "@my-config.yml" --tags voice
                                                                 # 语音输入（需 my-config.yml 提供 API Key）
```

### 自定义配置与密钥约定

- 通用覆盖：`-e "@my-config.yml"`（放仓库根目录）
- **密钥只走 `my-config.yml`**：它与 `*-config.yml` 已被 `.gitignore` 忽略；不要把 API Key 写进 `inventory/` 或 role，也不要引入 ansible-vault
- `inventory/group_vars/all.yml` 只放非敏感开关与版本号

### 其他命令

```bash
./scripts/uninstall.sh                              # 引导式卸载
ansible-playbook playbooks/app.yml --syntax-check   # 语法检查
ansible-playbook playbooks/app.yml --list-tags      # 列出可用 tags
ansible-playbook playbooks/app.yml -K --check       # 干跑
```

### Molecule Testing

```bash
cd roles/<role_name> && molecule test
```

部分 role 带 Molecule 测试（如 `fcitx5-rime-ice`），镜像用 `geerlingguy/docker-ubuntu2404-ansible:latest`，`network_mode: host`；网络访问通过 role defaults 里的 `proxy_env` 变量配代理。

## Architecture

### Playbooks（入口在 `playbooks/`，根目录没有 playbook.yml）

- `playbooks/hyprland.yml` — 桌面环境：`proxy` → `00-prerequisites` → `01-hyprland-ppa` → `02-core-packages` → `03-fonts` → `04-build-tools` → 可选组件（`sddm`/`nvidia`/`gtk-themes`/`bluetooth`/`thunar`/`zsh`/`ags`/`dotfiles`/`fcitx5-rime-ice`/`volume-control`）→ `final-check`；pre_tasks 做 Ubuntu 24.04 / NVIDIA / 登录管理器检测
- `playbooks/app.yml` — 桌面应用：`fcitx5-rime-ice`、`google-chrome`、`microsoft-edge`、`vscode`、`dbeaver`、`scc`、`jq`、`yq`、`fastfetch`、`docker`、`ai-balance`、`cherrystudio`、`obsidian`、`drawio`、`dida`、`wechat`、`feeluown`、`voice-input` 等

### 配置（`inventory/group_vars/all.yml`）

- 可选组件开关：`install_nvidia`、`install_sddm`、`install_ags`、`install_dotfiles`、`install_fcitx5_rime_ice`、`install_voice_input`（需 API Key，缺失时 role 会 fail-fast 并提示控制台开通步骤）、`install_volume_control` 等
- 版本标签：`ags_version`、`swww_version`、`wallust_version` 等（可用 `-e` 覆盖）
- 构建与缓存：`build_dir`、`cache_dir`、`offline_mode`、`use_cache`
- 代理（中国大陆用户）：`configure_proxy` + `proxy_http/proxy_https/proxy_all`；`proxy` role 总是最先运行并构建全局 `proxy_env`，**role 里所有外网任务都应挂 `environment: "{{ proxy_env }}"`**

### Role 编写约定

- 标准布局 `tasks/` + `defaults/`（按需 `handlers/`、`vars/`、`meta/`）；playbook 级 `become: false`，需要 root 的任务（apt 等）在任务级写 `become: true`
- role 自带的脚本/配置放 `assets/` 子目录（参考 `ai-balance`）
- 操作用户目录用 `ansible_user_dir` / `ansible_user_id`（playbook 另有 `target_user` / `target_user_home` facts）
- 任务统一打 tag；只支持 Ubuntu 的 role 在开头断言发行版（参考 `ai-balance`、`voice-input`）
- 用户级 systemd 服务用 `systemd:` 模块的 `scope: user`（参考 `voice-input` 的 vinput-daemon）
- 幂等优先：命令类任务用 `creates:` / 预检 guard / `replace` 精确匹配，避免每次跑都报 changed

### Assets（`files/assets/`）

部署到用户 home 的静态资源：zsh 主题、`fastfetch/`、`gtk-3.0/`、`hyprland.desktop`、SDDM 背景、Thunar/xfce4 配置。

### Docs（`docs/`）

- `Agent语音输入与输出端解决方案.md` — **语音输入已部署定型**（fcitx5-vinput + 豆包语音官方 ASR），含 Resource ID、鉴权改造、费用与排障；改语音相关 role 前必读
- `design.md` / `data-disk.md` / `linux-desktop-essentials.md` — 其他设计笔记

## Important Notes

- NVIDIA role 会 blacklist nouveau 驱动
- dotfiles 来自独立仓库 [JaKooLit/Hyprland-Dots](https://github.com/JaKooLit/Hyprland-Dots)
- 缓存目录：`~/.cache/hyprland-ansible/`
- `vinput provider` 等从 GitHub raw 拉资源的命令会自动回落 `gh-proxy.com` / `ghfast.top` 镜像，首次可能需要几分钟，不是卡死

## Commit Convention

Use conventional commits:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `chore:` for maintenance tasks
