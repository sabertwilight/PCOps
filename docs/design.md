# Hyprland 生态工具全景分析

本文档详细分析 Ubuntu 24.04 下 Hyprland 桌面环境中各个组件的角色、同类竞品及优缺点。

---

## 一、核心组件 (Hyprland 官方出品)

| 工具 | 角色 | 同类竞品 | 优点 | 缺点 |
|------|------|----------|------|------|
| **hyprland** | Wayland 合成器/窗口管理器 | Sway, river, niri, GNOME/KDE | 动画华丽、配置灵活、活跃开发中 | 配置复杂、文档分散 |
| **hypridle** | 空闲检测 (自动锁屏/休眠) | swayidle | 官方集成、配置简单 | 功能单一 |
| **hyprlock** | 锁屏界面 | swaylock, gtklock | 原生支持、可自定义 | 相对较新 |
| **hyprpicker** | 屏幕取色器 | grim + imagemagick | 精准、支持格式输出 | 功能单一 |
| **hyprsunset** | 蓝光过滤 | redshift, wlsunset | 原生 Wayland 支持 | 无地理位置自动调节 |

### 详细说明

- **hyprland**: 整个桌面环境的核心，负责窗口管理、动画、工作区等。采用 wlroots 构建在 Wayland 协议之上。
- **hypridle**: 监测用户空闲时间，触发锁屏或休眠。可与 hyprlock 配合实现完整的电源管理。
- **hyprpicker**: 按需使用的取色工具，运行后点击屏幕即可获取颜色值。
- **hyprsunset**: 夜间模式工具，默认 4500K 色温，可通过 waybar 或快捷键切换。

---

## 二、状态栏与通知

| 工具 | 角色 | 同类竞品 | 优点 | 缺点 |
|------|------|----------|------|------|
| **waybar** | 状态栏 | yambar, polybar (X11) | 模块丰富、高度可定制、社区活跃 | JSON 配置繁琐 |
| **sway-notification-center** | 通知守护进程 | mako, dunst (X11), fnott | 功能完整、有通知中心 GUI | 相对较重 |

### 为什么需要

Wayland 下没有桌面环境自动提供状态栏和通知，必须自己配置。waybar 显示系统信息（时间、音量、网络等），sway-notification-center 管理应用通知。

### 竞品对比

- **mako**: 最轻量的通知守护进程，无 GUI 通知中心
- **fnott**: 轻量且美观，但功能较少
- **yambar**: waybar 的替代品，使用 YAML 配置

---

## 三、应用启动与菜单

| 工具 | 角色 | 同类竞品 | 优点 | 缺点 |
|------|------|----------|------|------|
| **rofi-wayland** | 应用启动器/窗口切换 | wofi, fuzzel, tofi | 功能强大、插件丰富、Wayland 移植完善 | 需要从源码编译 |
| **wlogout** | 登出/关机菜单 | rofi 脚本、nwg-bar | 开箱即用、美观 | 样式定制有限 |

### 竞品对比

| 工具 | 特点 | 适用场景 |
|------|------|----------|
| **wofi** | 轻量、简单配置 | 极简主义者 |
| **fuzzel** | 简洁高效、启动快 | 追求性能的用户 |
| **tofi** | 最快的启动器 | 低配置机器 |
| **rofi-wayland** | 功能最全、插件生态 | 需要高级功能的用户 |

---

## 四、截图与剪贴板

| 工具 | 角色 | 同类竞品 | 优点 | 缺点 |
|------|------|----------|------|------|
| **grim** | 截图核心工具 | grimshot, hyprshot | 底层工具、灵活 | 需配合 slurp |
| **slurp** | 区域选择工具 | - | 与 grim 完美配合 | 功能单一 |
| **swappy** | 截图编辑/标注 | spectacle, flameshot | 轻量、支持标注 | 功能不如 flameshot 全面 |
| **wl-clipboard** | Wayland 剪贴板工具 | - | Wayland 标准 | - |
| **cliphist** | 剪贴板历史管理 | clipman, copyq | 轻量、与 rofi 配合好 | 无 GUI |

### 截图工作流

```
grim + slurp 截图 → swappy 编辑 → wl-clipboard 复制 → cliphist 管理历史
```

### 常用快捷键配置示例

```ini
# hyprland.conf
bind = SUPER, Print, exec, grim -g "$(slurp)" - | swappy -f -
bind = SUPER SHIFT, Print, exec, grim - | swappy -f -
```

---

## 五、壁纸与配色

| 工具 | 角色 | 同类竞品 | 优点 | 缺点 |
|------|------|----------|------|------|
| **swww** | 动态壁纸/幻灯片 | hyprpaper, wpaperd | 支持动画、过渡效果、GIF | 相对较重 |
| **wallust** | 从壁纸生成配色方案 | pywal, wpgtk | 生成完整主题、支持多种格式 | 需要学习模板 |

### wallust 工作原理

1. 分析壁纸主色调
2. 生成 16 色配色方案
3. 应用到终端、状态栏、GTK 主题等

### 配置文件位置

- 壁纸: `~/.config/hypr/hyprpaper.conf` 或 `swww` 命令
- wallust: `~/.config/wallust/`

---

## 六、系统工具

| 工具 | 角色 | 同类竞品 | 优点 | 缺点 |
|------|------|----------|------|------|
| **pavucontrol** | 音量控制/音频路由 | pamixer, wpctl | GUI 直观、功能完整 | 需要 GTK |
| **pamixer** | 命令行音量控制 | wpctl | 轻量、适合绑定快捷键 | 无 GUI |
| **playerctl** | 媒体播放控制 | - | 支持多播放器、统一接口 | - |
| **brightnessctl** | 屏幕亮度控制 | light, ddcutil | 简单、支持背光 | - |
| **nwg-look** | GTK 主题切换 | lxappearance | Wayland 原生、支持 cursor | 仅 GTK |
| **nwg-displays** | 显示器配置 GUI | wdisplays, kanshi | 图形化配置显示器 | - |
| **polkit-kde-agent-1** | 权限认证代理 | polkit-gnome, lxpolkit | 美观、KDE 风格 | 需要 KDE 依赖 |

### polkit 代理的重要性

没有 polkit 代理，GUI 应用请求 root 权限时会静默失败。常见问题：

- Thunar 无法挂载分区
- GParted 无法启动
- 系统设置无法修改

### 音量控制快捷键示例

```ini
# hyprland.conf
bind = , XF86AudioRaiseVolume, exec, pamixer -i 5
bind = , XF86AudioLowerVolume, exec, pamixer -d 5
bind = , XF86AudioMute, exec, pamixer -t
bind = , XF86MonBrightnessUp, exec, brightnessctl set +5%
bind = , XF86MonBrightnessDown, exec, brightnessctl set 5%-
```

---

## 七、终端与 Shell

| 工具 | 角色 | 同类竞品 | 优点 | 缺点 |
|------|------|----------|------|------|
| **kitty** | GPU 加速终端 | alacritty, foot, wezterm | 功能丰富、支持图片显示、Python 配置 | 相对较重 |
| **zsh + oh-my-zsh** | Shell | fish, bash | 插件丰富、社区活跃 | 启动稍慢 |

### 终端竞品对比

| 终端 | 特点 | 适用场景 |
|------|------|----------|
| **alacritty** | 最快、GPU 加速 | 追求极致性能 |
| **foot** | 轻量、无 GPU 依赖 | 低配置机器、服务器 |
| **wezterm** | 功能强大、Lua 配置 | 需要高级功能（分屏、标签等） |
| **kitty** | 功能最全、支持图片 | 需要图片显示、GPU 加速 |

---

## 八、文件管理器

| 工具 | 角色 | 同类竞品 | 优点 | 缺点 |
|------|------|----------|------|------|
| **thunar** | 文件管理器 | nautilus, dolphin, nemo | 轻量、可自定义动作、插件支持 | 功能不如 nautilus 全面 |

### Thunar 自定义动作示例

- 一键压缩选中文件
- 在终端打开当前目录
- 批量重命名

---

## 九、登录管理器

| 工具 | 角色 | 同类竞品 | 优点 | 缺点 |
|------|------|----------|------|------|
| **SDDM** | 显示管理器/登录界面 | GDM, LightDM, ly | Wayland 原生、主题丰富 | 相对较重 |

### 替代方案

可以不用登录管理器，直接从 TTY 启动 Hyprland：

```bash
# ~/.bash_profile 或 ~/.zprofile
if [ -z "$WAYLAND_DISPLAY" ] && [ "$XDG_VTNR" -eq 1 ]; then
    exec Hyprland
fi
```

---

## 十、桌面组件 (AGS)

| 工具 | 角色 | 同类竞品 | 优点 | 缺点 |
|------|------|----------|------|------|
| **AGS (Aylur's GTK Shell)** | 桌面组件框架 | eww, ironbar | 功能强大、支持 TypeScript | 学习曲线陡峭 |

### AGS 用途

- 自定义状态栏
- 通知中心
- 控制面板（音量、亮度、网络）
- 音乐播放器小部件
- 系统监控仪表盘

### 竞品对比

- **eww**: 使用 YAML/SCSS 配置，更简单但功能较少
- **ironbar**: Rust 编写，专为 Wayland 设计，配置简单

---

## 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    SDDM (登录)                          │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│                    Hyprland (合成器)                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │                 waybar (状态栏)                  │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │  kitty   │  │  thunar  │  │    rofi-wayland     │  │
│  │ (终端)   │  │ (文件)   │  │    (启动器)         │  │
│  └──────────┘  └──────────┘  └──────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  后台服务:                                        │  │
│  │  • hypridle (空闲管理)                           │  │
│  │  • hyprpaper/swww (壁纸)                         │  │
│  │  • sway-nc (通知)                                │  │
│  │  • polkit-agent (权限)                           │  │
│  │  • cliphist (剪贴板历史)                         │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 关键依赖关系

### 1. 截图工作流

```
grim + slurp + swappy + wl-clipboard + cliphist
```

这是一套完整的截图解决方案，缺一不可。

### 2. 权限系统

```
polkit-kde-agent-1 (必需)
```

没有 polkit 代理，很多 GUI 操作会静默失败。

### 3. XDG Portal

```
xdg-desktop-portal-hyprland
```

让屏幕共享、文件选择器正常工作。对于 OBS 录屏、浏览器屏幕共享至关重要。

### 4. 配色一致性

```
wallust
```

让终端、状态栏、GTK 主题都跟随壁纸配色，实现视觉统一。

---

## 可选组件

### GTK 主题

- **gtk-themes-icons**: 提供多款 GTK 主题和图标包
- **nwg-look**: GUI 工具切换主题

### 蓝牙

- **bluez** + **blueman**: 蓝牙支持和图形化管理

### ROG 笔记本

- **asusctl**: ASUS 笔记本控制工具
- **supergfxctl**: 显卡切换工具

### 字体

- **JetBrainsMono**: 编程字体
- **VictorMono**: 连字字体
- **FantasqueSansMono**: 等宽字体

---

## 快速参考

### 最小化安装

如果只想要最基础的 Hyprland 体验：

```
hyprland + waybar + kitty + rofi-wayland + grim + slurp
```

### 完整安装

本项目默认安装的完整套件提供了开箱即用的桌面体验。

### 轻量替代方案

| 组件 | 完整版 | 轻量版 |
|------|--------|--------|
| 终端 | kitty | foot |
| 启动器 | rofi-wayland | fuzzel |
| 壁纸 | swww | hyprpaper |
| 通知 | sway-nc | mako |
| 状态栏 | waybar | yambar |
