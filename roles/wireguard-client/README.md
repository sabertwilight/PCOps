# wireguard-client

以**声明式配置把本机接入 WireGuard 网络**，由 NetworkManager 托管连接生命周期：登录自动连、桌面 applet 可开关、DNS 由 NM 统一处理，无需手写 wg-quick 或 systemd unit。

```
本机密钥（自动生成或指定）→ 渲染 wg 配置 → nmcli 导入 NetworkManager
→ 设置 DNS / autoconnect → 输出本机公钥（登记到服务端 Peer）
```

支持多连接：在 `wireguard_client_connections` 列表里追加 `wg1`、`wg2`…即可。

## 前置条件（服务端侧）

1. 已有一台 WireGuard **服务端**，拿到：服务端公钥（`peer_public_key`）、Endpoint（`peer_endpoint`）、客户端网段地址（`interface_address`）；
2. 运行本 role 后，把输出里打印的**客户端公钥**登记到服务端对应 Peer 的 `PublicKey` 下；
3. 本机使用 NetworkManager 管理网络（桌面版 Ubuntu 默认满足）。

## 使用

配置 `inventory/group_vars/all.yml`（或 `-e @my-config.yml`）：

```yaml
wireguard_client_connections:
  - id: wg0
    interface_address: 10.8.0.12/32
    mtu: 1280
    private_key: ""                    # 留空自动生成并保存到本机
    peer_public_key: "<服务端公钥>"
    peer_endpoint: "vpn.example.com:51820"
    peer_allowed_ips: "10.8.0.1/32, 172.16.32.0/24"   # 只放内网网段=分流；0.0.0.0/0=全流量
    peer_persistent_keepalive: 25
    dns: "172.16.32.11"
    dns_search: "example.internal"
    autoconnect: true
    force_reimport: false              # 改配置后设 true 强制删除旧连接重新导入
```

> **注意：本 role 尚未接入任何 playbook**（`hyprland.yml` / `app.yml` 中均无）。当前可用 ad-hoc 方式运行，或自行加进 playbook（建议加 `when: install_wireguard_client`）：
>
> ```bash
> ansible -i inventory localhost -m include_role -a 'name=wireguard-client' --become -K
> ```

## 变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `wireguard_client_connections` | `[]` | 连接列表，见上方示例；**为空则 role 什么都不做** |
| `wireguard_client_key_dir` | `~/.local/share/wireguard` | 密钥存放目录（0700，私钥 0600，只在本机） |
| `wireguard_client_enabled` | `true` | ⚠️ 当前是**死变量**，tasks 未引用；实际开关由连接列表非空 + playbook `when` 决定 |

连接条目字段：`id`（NM 连接名）、`interface_address`（本机 WG 地址）、`mtu`、`private_key`（留空自动生成）、`peer_public_key`、`peer_endpoint`、`peer_allowed_ips`、`peer_persistent_keepalive`（NAT 穿透必设 25）、`dns` + `dns_search`（可选）、`autoconnect`（默认 true）、`force_reimport`（默认 false）。

## 实现要点

- **NM 导入式设计**：配置渲染到 `/tmp/<id>.conf` 后 `nmcli connection import type wireguard` 导入，连接归 NM 管（用户级连接，无需 root 操作 nmcli）；`force_reimport: true` 先删旧连接再重新导入。
- **密钥管理**：未提供 `private_key` 时 `wg genkey` 自动生成并落盘（`creates:` 保证幂等），公钥由私钥推导；私钥相关的读取/渲染任务全部 `no_log: true`。
- **DNS**：`ipv4.ignore-auto-dns yes` + 显式 DNS/搜索域，避免内网域名解析被默认 DNS 抢占。
- **密钥不落库**：仓库里只放服务端公钥和 endpoint（非机密）；私钥只存在于本机 `wireguard_client_key_dir`。

## 排障

| 现象 | 排查 |
|---|---|
| 连接起不来 | `nmcli connection show wg0`；`sudo nmcli connection up wg0` 看报错 |
| 已 up 但无握手 | `sudo wg show` 看 latest handshake；多为服务端未登记客户端公钥，或 endpoint/UDP 端口不通 |
| 内网域名解析失败 | `nmcli connection show wg0 | grep -i dns`；确认配了 `dns` + `dns_search` |
| 改了配置不生效 | 同一 `id` 的 NM 连接已存在时导入会被跳过，设 `force_reimport: true` 再跑 |
| 自动连接未生效 | `nmcli connection show wg0 | grep autoconnect`；NM 在用户登录后按 autoconnect 拉起 |

## 卸载 / 回退

```bash
nmcli connection delete wg0            # 删连接（NM 侧）
rm -rf ~/.local/share/wireguard        # 删密钥（如需彻底清理）
```

服务端侧记得同步移除对应 Peer，避免残留公钥。
