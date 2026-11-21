# 数据盘方案（nvme1n1, 2TB Predator GM7000）

> 2026-10-04 实施。原始需求：旧机器（Europa）整盘迁移过来的 2TB NVMe，
> 清空后作为本机数据盘；docker 与未来 KVM 镜像落在数据盘，不占系统盘。

## 一、当前布局

| 项 | 值 |
|---|---|
| 磁盘 | `/dev/nvme1n1` Predator GM7000 2TB（S/N: PSBG54090301835） |
| 分区 | `nvme1n1p1` 整盘 GPT 单分区（PARTLABEL=data，类型 8300） |
| 文件系统 | XFS，`LABEL=data`，`UUID=c648c2b2-bfc0-4620-b7c1-69382344ade8` |
| 挂载点 | `/mnt/data`（属主 `xiao:xiao`） |
| 子目录 | `/mnt/data/docker` → bind 到 `/var/lib/docker`；`/mnt/data/kvm` → bind 到 `/var/lib/libvirt/images`（libvirt 未装，前瞻挂载） |

`/etc/fstab` 追加行：

```
/dev/disk/by-uuid/c648c2b2-bfc0-4620-b7c1-69382344ade8 /mnt/data xfs defaults,nofail,x-systemd.device-timeout=5s 0 2
/mnt/data/docker /var/lib/docker none bind,nofail 0 0
/mnt/data/kvm /var/lib/libvirt/images none bind,nofail 0 0
```

systemd drop-in（防止服务抢在数据盘挂载前启动、在根盘新建空目录）：

```ini
# /etc/systemd/system/docker.service.d/order.conf（libvirtd 同理）
[Unit]
RequiresMountsFor=/mnt/data
```

## 二、为什么整盘单文件系统，不用 LVM 分墙

旧盘（Europa）就是 LVM 方案的实证样本，VG `data`（pe 4MiB × 305003）：

| 项 | 数值 | 说明 |
|---|---|---|
| LV 分配 | docker 100G + libvirt 200G + swap 8G = 308G | 另有 800G `image` LV 建后即删 |
| 实际使用 | ~114G（overlay2 12G、VM 镜像 101G、docker volumes 0.9G） | 利用率 37% |
| 滞留空闲 extent | ~91G | 想给谁都要 vgextend/lvextend 折腾 |

分区墙的问题不是"LVM 不行"，而是**预分配必然错配**：docker 只用 12G 却占 100G；
VM 用 101G 差点顶到 200G；中间计划外需求（800G image）建了又删。
单文件系统下所有消费者共享 1.9T，唯一满的时刻是整盘真满——届时谁大谁小一目了然。

**bind mount 优于软链接**：docker/libvirt 语义透明，systemd 沙箱
（`ProtectSystem=strict`）、rescue/initramfs、rsync 等工具不会踩路径歧义。

## 三、操作命令速查

```bash
# 查看空间
df -h /mnt/data
xfs_info /mnt/data

# docker 瘦身（最常见回血手段）
docker system df                 # 看各类占用
docker system prune              # 清悬空层/停止容器/无 tag 镜像
docker system prune -a --volumes # 核弹级，慎用
docker builder prune             # build cache 单独清（本机曾 17G）

# KVM（装 libvirt 后）镜像放在 /var/lib/libvirt/images（实为数据盘）
qemu-img info /var/lib/libvirt/images/foo.qcow2
virt-sparsify foo.qcow2 foo-sparse.qcow2   # 压缩稀疏

# 新增一类大目录（例：/mnt/data/media 挂到别处）
sudo mkdir -p /mnt/data/media /srv/media
echo '/mnt/data/media /srv/media none bind,nofail 0 0' | sudo tee -a /etc/fstab
sudo mount /srv/media

# 手工挂载/卸载整盘
sudo mount /mnt/data
sudo umount /mnt/data            # 需先停 docker/libvirt 或先卸 bind 点

# 故障排查
findmnt --verify                 # fstab 语法校验
systemctl status mnt-data.mount
journalctl -u docker --since -10min
```

### 数据盘不在时（拔盘/故障）的行为

- `/mnt/data` 行 `nofail,x-systemd.device-timeout=5s`：开机不卡，5s 后跳过；
- bind 行同样 `nofail`：docker/libvirt 服务仍能启动，但 `RequiresMountsFor`
  会等数据盘——盘不在时 docker 启动于根盘空目录，**此时拉起的容器数据不可见**，
  拔盘场景属预期行为，恢复插盘重启 docker 即可。

## 四、用法规划

```
/mnt/data/
├── docker/    ← /var/lib/docker bind（daemon 全部数据：镜像/容器/卷/build cache）
├── kvm/       ← /var/lib/libvirt/images bind（VM qcow2）
└── <自由区>   ← 个人数据、下载、模型权重等，属主 xiao:xiao
```

约定：

1. **一律先写满自由区**，docker/kvm 不设配额，靠 `docker system df` + `df -h` 巡检；
2. 大文件（数据集、模型、ISO）放自由区，不放 docker 卷；
3. `docker cp`/`-v` 挂载进容器的持久数据用本地卷，别塞匿名卷（难清理）。

## 五、未来可选演进

### 5.1 XFS project quota（防单消费者吃光，替代 LVM 分墙）

 fstab `/mnt/data` 行 options 加 `pquota` 后重挂，然后：

```bash
sudo xfs_quota -x -c 'project -s -p /mnt/data/docker docker' /mnt/data
sudo xfs_quota -x -c 'limit -p bhard=500g docker' /mnt/data
sudo xfs_quota -x -c 'limit -p bsoft=800g bhard=900g kvm' /mnt/data
sudo xfs_quota -x -c 'report -h' /mnt/data
```

配额改数字即生效，无 LVM 挪 extent 之苦。当前未启用（决定：暂不需要）。

### 5.2 若日后需要 VM 磁盘级快照回滚

从数据盘缩出空间建 LVM thin pool 是**顺路**的（整盘→LVM 只需腾尾部空间）；
反向（LVM→整盘）要搬数据。原则：先单盘，出现真实快照纪律需求再切。

## 六、历史与废弃说明

- 旧盘原 4 分区（EFI 1G / 旧根 238G xfs / 旧 home 477G xfs / LVM 1191G）已于
  2026-10-04 `sgdisk --zap-all` 清除，数据未迁移（用户确认弃置）；
- 本机原 `/var/lib/docker`（2.9G 表观，21 镜像/6 容器/16 卷/build cache 17G）
  已 `rsync -aHAX` 迁至 `/mnt/data/docker`，旧副本删除，服务迁移前后
  镜像/容器计数一致。
