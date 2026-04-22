# yq Installation Role Design

## Overview

Create a new `roles/yq/` role to install yq (YAML processor) from pre-built GitHub releases into `~/.local/bin/yq`.

## Variables

Add to `inventory/group_vars/all.yml`:

```yaml
yq_version: "v4.35.1"
yq_install_path: "{{ target_user_home }}/.local/bin/yq"
yq_repo: "https://github.com/mikefarah/yq"
```

## Architecture Mapping

| Ansible machine | Download arch |
|----------------|---------------|
| `x86_64`       | `amd64`       |
| `aarch64`      | `arm64`       |

## Installation Flow

1. Check if yq already installed at `~/.local/bin/yq`
2. Download checksum file for verification
3. Download yq binary: `https://github.com/mikefarah/yq/releases/download/{version}/yq_{version}_linux_{arch}.tar.gz`
4. Extract to install path
5. Set executable permissions

## Tags

- `yq` - standalone tag
- `optional` - included in optional tag group

## Proxy Support

Uses `environment: "{{ proxy_env }}"` for proxy passthrough.

## Files

- `roles/yq/tasks/main.yml` - main tasks
