# Ubuntu + Hyprland 桌面工具指南

本文档针对 Ubuntu 24.04 + Hyprland 场景，梳理各领域的必备工具。Hyprland 是"裸"窗口管理器，需要自己搭建桌面环境，本文档帮助你补齐所有能力。

---

## 本项目已安装的工具

| 领域 | 工具 | 说明 |
|------|------|------|
| 窗口管理 | hyprland | 核心合成器 |
| 状态栏 | waybar | 顶部状态栏 |
| 启动器 | rofi-wayland | 应用启动/窗口切换 |
| 终端 | kitty | GPU 加速终端 |
| 剪贴板 | cliphist + wl-clipboard | 剪贴板历史 |
| 截图 | grim + slurp + swappy | 截图+标注 |
| 壁纸 | swww | 动态壁纸 |
| 锁屏 | hyprlock | 锁屏界面 |
| 空闲管理 | hypridle | 自动锁屏/休眠 |
| 通知 | sway-notification-center | 通知中心 |
| 文件管理器 | thunar | 图形化文件管理 |
| 音量控制 | pavucontrol | 音频控制面板 |
| 亮度控制 | brightnessctl | 屏幕亮度 |
| 登录管理器 | SDDM | 图形登录界面 |
| GTK 主题 | nwg-look | 主题切换工具 |
| 显示器配置 | nwg-displays | 多显示器配置 |
| 蓝光过滤 | hyprsunset | 夜间模式 |
| 取色器 | hyprpicker | 屏幕取色 |
| 配色生成 | wallust | 壁纸配色方案 |
| Shell | zsh + oh-my-zsh | 增强终端 |

---

## 一、系统管理

### 已安装
- 无

### 需要补充

| 工具 | 用途 | 安装命令 |
|------|------|----------|
| **nala** | 更友好的包管理器 | `sudo apt install nala` |
| **btop** | 系统资源监控 | `sudo apt install btop` |
| **nvtop** | 显卡监控 | `sudo apt install nvtop` |
| **gparted** | 分区管理 | `sudo apt install gparted` |
| **baobab** | 磁盘占用分析 | `sudo apt install baobab` |
| **ncdu** | 终端磁盘分析 | `sudo apt install ncdu` |
| **bleachbit** | 系统清理 | `sudo apt install bleachbit` |

### 推荐安装

```bash
sudo apt install nala btop nvtop gparted baobab ncdu bleachbit
```

### nala 使用

```bash
# 替代 apt
sudo nala update
sudo nala install <package>
sudo nala upgrade

# 并行下载、进度条更友好
```

---

## 二、输入与快捷操作

### 已安装
- 无

### 需要补充

| 工具 | 用途 | 安装命令 |
|------|------|----------|
| **fcitx5** | 中文输入法 | `sudo apt install fcitx5 fcitx5-chinese-addons fcitx5-config-qt` |
| **copyq** | 图形化剪贴板管理 | `sudo apt install copyq` |
| **espanso** | 文本展开/自动替换 | 下载 .deb 安装 |

### fcitx5 输入法配置

```bash
# 安装
sudo apt install fcitx5 fcitx5-chinese-addons fcitx5-config-qt

# 设置默认输入法
im-config -n fcitx5

# 环境变量 (添加到 ~/.zshrc 或 ~/.bashrc)
export GTK_IM_MODULE=fcitx
export QT_IM_MODULE=fcitx
export XMODIFIERS=@im=fcitx
```

### copyq 剪贴板管理

```bash
sudo apt install copyq

# 启动
copyq start

# 设置开机自启 (hyprland.conf)
exec-once = copyq
```

> 注意：本项目已安装 cliphist，它是轻量的命令行剪贴板历史工具，配合 rofi 使用。copyq 是图形化方案，功能更丰富。

---

## 三、网络与远程

### 已安装
- 无

### 需要补充

| 工具 | 用途 | 安装命令 |
|------|------|----------|
| **nm-applet** | 网络托盘图标 | `sudo apt install network-manager-applet` |
| **remmina** | 远程桌面 (RDP/VNC) | `sudo apt install remmina remmina-plugin-rdp remmina-plugin-vnc` |
| **filezilla** | FTP/SFTP 客户端 | `sudo apt install filezilla` |
| **syncthing** | 文件同步 | `sudo apt install syncthing` |
| **nmap** | 网络扫描 | `sudo apt install nmap` |

### 推荐安装

```bash
sudo apt install network-manager-applet remmina remmina-plugin-rdp \
                 remmina-plugin-vnc filezilla syncthing nmap
```

### 网络托盘配置

```ini
# hyprland.conf
exec-once = nm-applet --indicator
```

### syncthing 文件同步

```bash
# 启用服务
sudo systemctl enable syncthing@$(whoami).service
sudo systemctl start syncthing@$(whoami).service

# Web UI: http://localhost:8384
```

---

## 四、文件与文档

### 已安装
- thunar (文件管理器)

### 需要补充

| 工具 | 用途 | 安装命令 |
|------|------|----------|
| **fd-find** | 快速文件搜索 | `sudo apt install fd-find` |
| **ripgrep** | 快速内容搜索 | `sudo apt install ripgrep` |
| **meld** | 文件对比 | `sudo apt install meld` |
| **pdfarranger** | PDF 合并/拆分 | `sudo apt install pdfarranger` |
| **pandoc** | 文档格式转换 | `sudo apt install pandoc` |
| **p7zip-full** | 7z 压缩支持 | `sudo apt install p7zip-full` |
| **peazip** | 图形化解压工具 | `sudo apt install peazip` |

### 推荐安装

```bash
sudo apt install fd-find ripgrep meld pdfarranger pandoc p7zip-full peazip
```

### 常用命令

```bash
# 快速搜索文件名
fd "pattern"

# 快速搜索文件内容
rg "pattern"

# PDF 合并/拆分 (GUI)
pdfarranger

# 文档转换
pandoc input.md -o output.pdf
```

---

## 五、多媒体

### 已安装
- 无

### 需要补充

| 工具 | 用途 | 安装命令 |
|------|------|----------|
| **mpv** | 视频播放 | `sudo apt install mpv` |
| **vlc** | 备用播放器 | `sudo apt install vlc` |
| **ffmpeg** | 音视频转换 | `sudo apt install ffmpeg` |
| **obs-studio** | 录屏/直播 | `sudo apt install obs-studio` |
| **gimp** | 图像编辑 | `sudo apt install gimp` |
| **loupe** | 图片查看 | `sudo apt install loupe` |

### 推荐安装

```bash
sudo apt install mpv vlc ffmpeg obs-studio gimp loupe
```

### ffmpeg 常用命令

```bash
# 格式转换
ffmpeg -i input.mp4 output.webm

# 压缩视频
ffmpeg -i input.mp4 -crf 28 output.mp4

# 提取音频
ffmpeg -i video.mp4 -vn -acodec copy audio.aac

# GIF 制作
ffmpeg -i video.mp4 -vf "fps=10,scale=320:-1" output.gif
```

### yt-dlp 视频下载

```bash
# 安装
pip install yt-dlp

# 下载视频
yt-dlp "URL"

# 下载最佳质量
yt-dlp -f "bestvideo+bestaudio" "URL"

# 下载音频
yt-dlp -x --audio-format mp3 "URL"
```

---

## 六、开发工具

### 已安装
- kitty (终端)
- zsh + oh-my-zsh (Shell)

### 需要补充

| 工具 | 用途 | 安装命令 |
|------|------|----------|
| **tmux** | 终端复用 | `sudo apt install tmux` |
| **starship** | 终端主题 | 下载安装脚本 |
| **git** | 版本控制 | `sudo apt install git` |
| **neovim** | 编辑器 | `sudo apt install neovim` |
| **docker.io** | 容器 | `sudo apt install docker.io` |
| **dbeaver** | 数据库客户端 | `sudo apt install dbeaver` |
| **meld** | 代码对比 | 已在文件工具中 |

### 推荐安装

```bash
sudo apt install tmux git neovim docker.io dbeaver
```

### tmux 配置

```bash
# ~/.tmux.conf
set -g mouse on
set -g history-limit 50000
set -g base-index 1

# 分屏快捷键
bind | split-window -h
bind - split-window -v
```

### starship 终端主题

```bash
# 安装
curl -sS https://starship.rs/install.sh | sh

# ~/.zshrc 末尾添加
eval "$(starship init zsh)"
```

---

## 七、办公与协作

### 已安装
- 无

### 需要补充

| 工具 | 用途 | 安装命令 |
|------|------|----------|
| **libreoffice** | 办公套件 | `sudo apt install libreoffice` |
| **obsidian** | 笔记软件 | Flatpak 安装 |
| **thunderbird** | 邮件/日历 | `sudo apt install thunderbird` |

### 推荐安装

```bash
# 办公套件
sudo apt install libreoffice thunderbird

# Obsidian (Flatpak)
flatpak install flathub md.obsidian.Obsidian
```

### WPS Office (可选)

从官网下载 .deb 包安装，对中文文档兼容性更好。

---

## 八、硬件与外设

### 已安装
- brightnessctl (亮度控制)
- nwg-displays (显示器配置)

### 需要补充

| 工具 | 用途 | 安装命令 |
|------|------|----------|
| **blueman** | 蓝牙管理 | `sudo apt install blueman` |
| **tlp** | 笔记本电源管理 | `sudo apt install tlp` |
| **gparted** | 分区管理 | 已在系统工具中 |

### 蓝牙配置

```bash
sudo apt install blueman

# hyprland.conf
exec-once = blueman-applet
```

### 笔记本电源管理

```bash
sudo apt install tlp tlp-rdw
sudo tlp start
```

---

## 九、安全与隐私

### 已安装
- hyprlock (锁屏)
- hypridle (空闲管理)

### 需要补充

| 工具 | 用途 | 安装命令 |
|------|------|----------|
| **keepassxc** | 密码管理 | `sudo apt install keepassxc` |
| **veracrypt** | 文件加密 | 下载 .deb 安装 |
| **timeshift** | 系统备份 | `sudo apt install timeshift` |
| **ufw** | 防火墙 | `sudo apt install ufw gufw` |

### 推荐安装

```bash
sudo apt install keepassxc timeshift ufw gufw
```

### Timeshift 系统备份

```bash
# 创建快照
sudo timeshift --create --comments "description"

# 恢复快照
sudo timeshift --restore

# 定时自动备份 (配置 GUI)
timeshift-launcher
```

### 防火墙配置

```bash
# 启用
sudo ufw enable

# 允许常用端口
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS

# 图形化管理
gufw
```

---

## 十、效率与自动化

### 已安装
- hyprland (窗口管理)
- rofi-wayland (启动器)
- wallust (配色)

### 需要补充

| 工具 | 用途 | 安装命令 |
|------|------|----------|
| **autokey** | 按键宏/文本展开 | `sudo apt install autokey-gtk` |

---

## 快速安装清单

### 必装工具 (高优先级)

```bash
# 系统管理
sudo apt install nala btop gparted

# 输入法
sudo apt install fcitx5 fcitx5-chinese-addons fcitx5-config-qt

# 文件工具
sudo apt install fd-find ripgrep meld p7zip-full

# 多媒体
sudo apt install mpv ffmpeg

# 安全
sudo apt install keepassxc timeshift

# 网络
sudo apt install network-manager-applet remmina
```

### 推荐工具 (中优先级)

```bash
# 开发
sudo apt install tmux git neovim docker.io

# 办公
sudo apt install libreoffice thunderbird

# 多媒体
sudo apt install obs-studio gimp

# 文档
sudo apt install pdfarranger pandoc

# 硬件
sudo apt install blueman
```

### 可选工具 (按需)

```bash
# 数据库
sudo apt install dbeaver

# 文件同步
sudo apt install syncthing

# 网络工具
sudo apt install filezilla nmap

# 终端主题
curl -sS https://starship.rs/install.sh | sh
```

---

## Flatpak 补充

部分软件在 Flatpak 中版本更新：

```bash
# 启用 Flatpak
sudo apt install flatpak
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# 推荐安装
flatpak install flathub md.obsidian.Obsidian        # 笔记
flatpak install flathub com.remmina.Remmina         # 远程桌面
flatpak install flathub org.telegram.desktop        # Telegram
```

---

## 配置检查清单

安装完成后，确认以下配置：

- [ ] fcitx5 输入法已配置并测试
- [ ] keepassxc 密码库已创建
- [ ] timeshift 备份计划已设置
- [ ] 网络托盘 (nm-applet) 正常显示
- [ ] 蓝牙托盘 (blueman-applet) 正常工作
- [ ] 常用软件快捷键已绑定
