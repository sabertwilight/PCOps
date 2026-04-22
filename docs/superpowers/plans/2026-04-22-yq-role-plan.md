# yq Installation Role Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a new `roles/yq/` Ansible role that downloads and installs yq from GitHub releases into `~/.local/bin/yq`

**Architecture:** Simple single-role installation using `unarchive` module to extract pre-built binary, with architecture detection and proxy support following existing project patterns.

**Tech Stack:** Ansible, GitHub releases, `unarchive` module

---

## File Structure

- **Create:** `roles/yq/tasks/main.yml` - yq installation tasks
- **Modify:** `inventory/group_vars/all.yml` - add yq variables

---

## Tasks

### Task 1: Add yq variables to all.yml

**Files:**
- Modify: `inventory/group_vars/all.yml`

- [ ] **Step 1: Add yq_version variable**

Find the `# ===========================================` section for `# 版本标签 (可覆盖)` and add:

```yaml
yq_version: "v4.35.1"
```

- [ ] **Step 2: Verify additions**

Read the file to confirm variables are added in correct section.

---

### Task 2: Create yq role tasks

**Files:**
- Create: `roles/yq/tasks/main.yml`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p roles/yq/tasks
```

- [ ] **Step 2: Write main.yml**

```yaml
---
# yq tasks
# 从 GitHub releases 下载并安装 yq

- name: Detect system architecture for yq
  set_fact:
    yq_arch: "{{ 'arm64' if ansible_architecture == 'aarch64' else 'amd64' }}"
  tags: [yq, optional]

- name: Check if yq is already installed
  stat:
    path: "{{ target_user_home }}/.local/bin/yq"
  register: yq_installed
  become: false
  tags: [yq, optional]

- name: Download yq binary
  get_url:
    url: "https://github.com/mikefarah/yq/releases/download/{{ yq_version }}/yq_linux_{{ yq_arch }}.tar.gz"
    dest: "{{ cache_dir }}/archives/yq_linux_{{ yq_arch }}.tar.gz"
    mode: '0644'
  environment: "{{ proxy_env }}"
  when: not yq_installed.stat.exists
  tags: [yq, optional]

- name: Extract yq to installation directory
  unarchive:
    src: "{{ cache_dir }}/archives/yq_linux_{{ yq_arch }}.tar.gz"
    dest: "{{ target_user_home }}/.local/bin/"
    extra_opts:
      - --strip-components=1
      - yq_linux_{{ yq_arch }}
    remote_src: true
    creates: "{{ target_user_home }}/.local/bin/yq"
  become: false
  when: not yq_installed.stat.exists
  tags: [yq, optional]

- name: Set executable permissions on yq
  file:
    path: "{{ target_user_home }}/.local/bin/yq"
    mode: '0755'
  become: false
  when: not yq_installed.stat.exists
  tags: [yq, optional]

- name: Display yq installation info
  debug:
    msg: "yq {{ yq_version }} installed at {{ target_user_home }}/.local/bin/yq"
  when: yq_installed.stat.exists
  tags: [yq, optional]
```

- [ ] **Step 3: Verify file syntax**

Run: `ansible-playbook playbook.yml --syntax-check`

---

## Self-Review Checklist

- [ ] yq_version variable added to all.yml
- [ ] roles/yq/tasks/main.yml created
- [ ] Architecture detection uses `ansible_architecture` (x86_64 → amd64, aarch64 → arm64)
- [ ] Uses `proxy_env` for download
- [ ] Uses `cache_dir` for downloaded archive
- [ ] Installs to `~/.local/bin/yq`
- [ ] Tags: `yq` and `optional`
- [ ] Idempotent: checks if already installed
- [ ] No placeholder/TODO in code
