<div align="center">

# 💌 KooL's Ubuntu Hyprland Installer 💌

## For Ubuntu 24.04 Noble Numbat

<p align="center">
  <img src="https://raw.githubusercontent.com/JaKooLit/Hyprland-Dots/main/assets/latte.png" width="400" />
</p>

![GitHub Repo stars](https://img.shields.io/github/stars/JaKooLit/Ubuntu-Hyprland?style=for-the-badge&color=cba6f7) ![GitHub last commit](https://img.shields.io/github/last-commit/JaKooLit/Ubuntu-Hyprland?style=for-the-badge&color=b4befe) ![GitHub repo size](https://img.shields.io/github/repo-size/JaKooLit/Ubuntu-Hyprland?style=for-the-badge&color=cba6f7) <a href="https://discord.gg/kool-tech-world"> <img src="https://img.shields.io/discord/1151869464405606400?style=for-the-badge&logo=discord&color=cba6f7&link=https%3A%2F%2Fdiscord.gg%kool-tech-world"> </a>

<br/>
</div>

<div align="center">
<br>
  <a href="#-prerequisites"><kbd>&emsp;<br>&emsp;Prerequisites&emsp;<br>&emsp;</kbd></a>&ensp;&ensp;
  <a href="#-installation"><kbd>&emsp;<br>&emsp;Installation&emsp;<br>&emsp;</kbd></a>&ensp;&ensp;
  <a href="#-configuration"><kbd>&emsp;<br>&emsp;Configuration&emsp;<br>&emsp;</kbd></a>&ensp;&ensp;
  <a href="#gallery-and-videos"><kbd>&emsp;<br>&emsp;Gallery&emsp;<br>&emsp;</kbd></a>&ensp;&ensp;
 </div><br>

> [!NOTE]
> Ubuntu 24.04 LTS specific

### Update:

- We are now using a PPA to get current Hyprland Packages
- https://github.com/cppiber/hyprland-ppa
- Install times are much shorter
- Updates to Hyprland will come during normal updates
- The current Jak dotfiles are compatible with this release
- **NEW**: Ansible-based installation for better automation and idempotency

<p align="center">
  <img src="https://raw.githubusercontent.com/JaKooLit/Hyprland-Dots/main/assets/latte.png" width="200" />
</p>

<div align="center">
👇 KOOL's Hyprland-Dots related Links 👇
<br/>
</div>
<div align="center">
<br>
  <a href="https://github.com/JaKooLit/Hyprland-Dots/tree/Ubuntu-24.04-Dots"><kbd>&emsp;<br>&emsp;Hyprland-Dots Ubuntu 24.04 repo&emsp;<br>&emsp;</kbd></a>&ensp;&ensp;
  <a href="https://www.youtube.com/playlist?list=PLDtGd5Fw5_GjXCznR0BzCJJDIQSZJRbxx"><kbd>&emsp;<br>&emsp;Youtube&emsp;<br>&emsp;</kbd></a>&ensp;&ensp;
  <a href="https://github.com/JaKooLit/Hyprland-Dots/wiki"><kbd>&emsp;<br>&emsp;Wiki&emsp;<br>&emsp;</kbd></a>&ensp;&ensp;
  <a href="https://github.com/JaKooLit/Hyprland-Dots/wiki/Keybinds"><kbd>&emsp;<br>&emsp;Keybinds&emsp;<br>&emsp;</kbd></a>&ensp;&ensp;
  <a href="https://github.com/JaKooLit/Hyprland-Dots/wiki/FAQ"><kbd>&emsp;<br>&emsp;FAQ&emsp;<br>&emsp;</kbd></a>&ensp;&ensp;
  <a href="https://discord.gg/kool-tech-world"><kbd>&emsp;<br>&emsp;Discord&emsp;<br>&emsp;</kbd></a>
</div><br>

> [!IMPORTANT]
> Install a backup tool like `snapper` or `timeshift` and backup your system before installing Hyprland (HIGHLY RECOMMENDED).

> [!CAUTION]
> Clone this repository in a directory where you have write permissions (e.g., HOME). Else the installation will fail.

---

## ⚠️ Prerequisites

- Do not run this installer as sudo or as root
- This installer requires a user with sudo privilege to install packages
- This is only for Ubuntu 24.04 LTS Noble Numbat

### Install Ansible

```bash
sudo apt update
sudo apt install ansible
```

---

## 🚀 Installation

### Quick Start

```bash
# Clone the repository
git clone -b 24.04 --depth=1 https://github.com/JaKooLit/Ubuntu-Hyprland.git ~/Ubuntu-Hyprland-24.04
cd ~/Ubuntu-Hyprland-24.04

# Run the playbook
ansible-playbook playbook.yml -K
```

### Install Specific Components

```bash
# Install only core components
ansible-playbook playbook.yml -K --tags "core"

# Install NVIDIA configuration
ansible-playbook playbook.yml -K --tags "nvidia"

# Install Zsh and dotfiles
ansible-playbook playbook.yml -K --tags "zsh,dotfiles"

# List all available tags
ansible-playbook playbook.yml --list-tags
```

### Use Custom Configuration

```bash
# Create a custom config file
cat > my-config.yml << EOF
install_nvidia: true
install_gtk_themes: true
install_bluetooth: false
install_thunar: true
install_zsh: true
install_dotfiles: true
EOF

# Run with custom config
ansible-playbook playbook.yml -K -e "@my-config.yml"
```

### Dry Run (Check Mode)

```bash
ansible-playbook playbook.yml -K --check
```

---

## ⚙️ Configuration

Edit `inventory/group_vars/all.yml` to customize the installation:

| Variable | Default | Description |
|----------|---------|-------------|
| `install_nvidia` | `false` | Install NVIDIA drivers (auto-detected) |
| `install_gtk_themes` | `true` | Install GTK themes and icons |
| `install_bluetooth` | `true` | Install and configure Bluetooth |
| `install_thunar` | `true` | Install Thunar file manager |
| `install_sddm` | `true` | Install SDDM login manager |
| `install_zsh` | `true` | Install Zsh + Oh-My-Zsh |
| `install_ags` | `true` | Install AGS desktop overview |
| `install_dotfiles` | `true` | Deploy KooL Hyprland dotfiles |
| `offline_mode` | `false` | Use cached files only |
| `use_cache` | `true` | Cache downloads for offline use |

---

## 📦 Available Tags

| Tag | Description |
|-----|-------------|
| `core` | All core components |
| `prerequisites` | System checks and dependencies |
| `hyprland` | Hyprland PPA and installation |
| `packages` | Core packages |
| `fonts` | Font installation |
| `build-tools` | Tools built from source |
| `sddm` | SDDM login manager |
| `nvidia` | NVIDIA configuration |
| `gtk` | GTK themes |
| `bluetooth` | Bluetooth |
| `thunar` | File manager |
| `zsh` | Shell |
| `ags` | Desktop overview |
| `rog` | ASUS ROG tools |
| `dotfiles` | Configuration files |
| `optional` | All optional components |

---

## 💥 Uninstall

```bash
./scripts/uninstall.sh
```

> [!WARNING]
> USE with caution as it may render your system unstable. The best way to revert is via timeshift or snapper.

---

## Gallery and Videos

### 🎥 Video Tutorials

- [YOUTUBE-LINK](https://youtu.be/wQ70lo7P6vA?si=_QcbrNKh_Bg0L3wC)
- [YOUTUBE-Hyprland-Playlist](https://youtube.com/playlist?list=PLDtGd5Fw5_GjXCznR0BzCJJDIQSZJRbxx&si=iaNjLulFdsZ6AV-t)

---

## 🪧 ANNOUNCEMENT

- This Repo does not contain Hyprland Dots or configs! Dotfiles can be checked here [`Hyprland-Dots`](https://github.com/JaKooLit/Hyprland-Dots/tree/Ubuntu-24.04-Dots)
- Hyprland-Dots are constantly evolving. Check CHANGELOGS here [`Hyprland-Dots-Changelogs`](https://github.com/JaKooLit/Hyprland-Dots/wiki/Changelogs)
- The wallpaper offered is from this [`REPO`](https://github.com/JaKooLit/Wallpaper-Bank)

---

## ❇️ NVIDIA Drivers

- If you choose to configure NVIDIA, driver will be installed via `sudo ubuntu-drivers install`
- If `nouveau` is installed, uninstall it first or DO NOT choose to configure NVIDIA
- NVIDIA users, after installation, check [`THIS`](https://github.com/JaKooLit/Hyprland-Dots/wiki/Notes_to_remember#--for-nvidia-gpu-users)

> [!IMPORTANT]
> If you want to use nouveau driver, don't enable `install_nvidia`. The NVIDIA installer will blacklist nouveau.

---

## ✨ Post-Installation

- Press `SUPER H` for HINT or click the waybar HINT! button
- Head over to [FAQ](https://github.com/JaKooLit/Hyprland-Dots/wiki/FAQ) and [TIPS](https://github.com/JaKooLit/Hyprland-Dots/wiki/TIPS)
- If brightness doesn't work on laptop: `sudo chmod +s $(which brightnessctl)`

### ZSH Configuration

```bash
chsh -s $(which zsh)
zsh
source ~/.zshrc
```

- Default theme: `agnosterzak` - change with `SUPER SHIFT O`
- Or edit `~/.zshrc` and set `ZSH_THEME="desired theme"`

---

## 📦 Packages Built from Source

These packages will not be updated by apt and need manual updates:

- swww [`LINK`](https://github.com/Horus645/swww)
- rofi-wayland [`LINK`](https://github.com/lbonn/rofi)
- wallust [`LINK`](https://codeberg.org/explosion-mental/wallust)
- swappy [`LINK`](https://github.com/jtheoof/swappy)
- nwg-look [`LINK`](https://github.com/nwg-piotr/nwg-look)
- nwg-displays [`LINK`](https://github.com/nwg-piotr/nwg-displays)
- Asus ROG asusctl [`LINK`](https://gitlab.com/asus-linux/asusctl) and supergfxctl [`LINK`](https://gitlab.com/asus-linux/supergfxctl)

> [!TIP]
> To update, re-run the playbook: `ansible-playbook playbook.yml -K --tags "build-tools"`

---

## 🛎 Offline Installation

1. First run with caching (default):
   ```bash
   ansible-playbook playbook.yml -K
   ```

2. For offline installation:
   ```bash
   ansible-playbook playbook.yml -K -e "offline_mode=true"
   ```

Cache directory: `~/.cache/hyprland-ansible/`

---

> [!NOTE]
> This script does not setup audio. Install pipewire: `sudo apt install -y pipewire`

---

## 🛎 Debian and Ubuntu Hyprland Dots Updating Notes

> [!IMPORTANT]
> Some parts of KooL's Hyprland Dots are not compatible on Debian and Ubuntu. The dots are pulled from a specific branch.

---

## 🙋 Support

- For installation issues: open an issue on this repo
- For Hyprland dots/configs: submit issue [`here`](https://github.com/JaKooLit/Hyprland-Dots/issues)

---

## 👍 Credits

- [`Hyprland`](https://hyprland.org/) - The awesome dynamic tiling compositor

### 💖 Support

- A Star on my Github repos would be nice 🌟
- Subscribe to my [YouTube Channel](https://www.youtube.com/@Ja.KooLit)
- [Ko-fi](https://ko-fi.com/jakoolit) or [Buy Me A Coffee](https://www.buymeacoffee.com/JaKooLit)

---

[![Stargazers over time](https://starchart.cc/JaKooLit/Ubuntu-Hyprland.svg?variant=adaptive)](https://starchart.cc/JaKooLit/Ubuntu-Hyprland)
