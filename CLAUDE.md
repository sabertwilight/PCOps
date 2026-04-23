# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is KooL's Hyprland installation project for Ubuntu 24.04 LTS (Noble Numbat). It uses Ansible to automate the installation of Hyprland (a dynamic tiling Wayland compositor) along with related packages, themes, and pre-configured dotfiles.

## Key Commands

### Running the Installer
```bash
ansible-playbook playbook.yml -K                    # Interactive installation (sudo password required)
ansible-playbook playbook.yml -K --tags "core"      # Install only core components
ansible-playbook playbook.yml -K -e "@my-config.yml" # Use custom configuration
```

### Uninstallation
```bash
./scripts/uninstall.sh                  # Guided removal of packages and configs
```

### Useful Ansible Commands
```bash
ansible-playbook playbook.yml --syntax-check       # Check syntax
ansible-playbook playbook.yml --list-tags          # List available tags
ansible-playbook playbook.yml -K --check           # Dry run
ansible-playbook playbook.yml -K -vvv              # Verbose output
```

### Molecule Testing
```bash
cd roles/<role_name> && molecule test              # Run all test stages
cd roles/<role_name> && molecule converge         # Create and provision
cd roles/<role_name> && molecule verify            # Run verification
```

All roles use `geerlingguy/docker-ubuntu2404-ansible:latest` with `network_mode: host`. For network access during testing, set proxy via `proxy_env` variable in role defaults.

## Architecture

### Main Entry Points
- `playbook.yml` - Main Ansible playbook orchestrating all roles
- `inventory/group_vars/all.yml` - Configuration variables (replaces preset.sh)
- `scripts/uninstall.sh` - Guided removal of Hyprland packages and user configs

### Ansible Roles (`roles/`)
Roles are executed in order:
1. `proxy` - Proxy configuration for users behind firewalls (China mainland)
2. `00-prerequisites` - System checks, dependencies, Rust installation
3. `01-hyprland-ppa` - Adds PPA and installs Hyprland from cppiber/hyprland PPA
4. `02-core-packages` - Core Hyprland packages (waybar, kitty, etc.)
5. `03-fonts` - JetBrainsMono, VictorMono, FantasqueSansMono
6. `04-build-tools` - Tools built from source (swww, rofi-wayland, wallust, etc.)
7. Optional roles: `sddm`, `nvidia`, `gtk-themes`, `bluetooth`, `thunar`, `zsh`, `ags`, `rog`, `dotfiles`
8. `final-check` - Verifies essential packages are installed

### Assets (`files/assets/`)
Configuration templates copied to user's home during installation:
- `.zshrc`, `.zprofile` - Shell configs
- `hyprland.desktop` - Wayland session entry
- `fastfetch/` - System info tool configs
- ZSH themes in `add_zsh_theme/`

## Installation Flow

1. **Proxy** - Optional proxy configuration for restricted networks
2. **Prerequisites** - Distro check, root check, dependencies, Rust
3. **Hyprland PPA** - Adds cppiber/hyprland PPA, installs Hyprland stack
4. **Core Packages** - Waybar, kitty, cliphist, etc.
5. **Fonts** - Nerd fonts installation
6. **Build Tools** - swww, rofi-wayland, wallust, swappy, nwg-*
7. **Optional Components** - Based on variables (SDDM, GTK themes, zsh, AGS, etc.)
8. **Dotfiles** - Clones and deploys configs from JaKooLit/Hyprland-Dots
9. **Final Check** - Verifies installation

## Configuration

Edit `inventory/group_vars/all.yml` to customize installation:

| Variable | Default | Description |
|----------|---------|-------------|
| `install_nvidia` | `false` | NVIDIA drivers (auto-detected) |
| `install_gtk_themes` | `true` | GTK themes and icons |
| `install_bluetooth` | `true` | Bluetooth support |
| `install_thunar` | `true` | Thunar file manager |
| `install_sddm` | `true` | SDDM login manager |
| `install_zsh` | `true` | Zsh + Oh-My-Zsh |
| `install_ags` | `true` | AGS desktop overview |
| `install_dotfiles` | `true` | KooL Hyprland dotfiles |
| `offline_mode` | `false` | Use cached files only |
| `use_cache` | `true` | Cache downloads |

## Available Tags

- `core` - All core components
- `prerequisites`, `hyprland`, `packages`, `fonts`, `build-tools`
- `sddm`, `nvidia`, `gtk`, `bluetooth`, `thunar`, `zsh`, `ags`, `rog`, `dotfiles`
- `optional` - All optional components

## Package Sources

- **PPA packages**: Hyprland, hypridle, hyprlock, hyprpaper, waybar, xdg-desktop-portal-hyprland
- **Built from source**: swww, rofi-wayland, wallust, swappy, nwg-look, nwg-displays
- **Cloned repos**: Hyprland-Dots, GTK-themes-icons, simple-sddm

## Important Notes

- Do not run as root - use `-K` flag for sudo
- NVIDIA configuration blacklists nouveau drivers
- The dotfiles repo is separate: `https://github.com/JaKooLit/Hyprland-Dots`
- Cache directory: `~/.cache/hyprland-ansible/`

## Commit Convention

Use conventional commits:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `chore:` for maintenance tasks
