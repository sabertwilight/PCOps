#!/usr/bin/env python3
"""Idempotent editor for WirePlumber restore-stream state file.

Called by the volume-control Ansible role. Reads volume limits from the
AW_VOLUME_LIMITS env var (JSON), edits the state file to set per-app volumes,
and prints CHANGED or NO_CHANGE for Ansible changed_when detection.

Usage:
    AW_VOLUME_LIMITS='{"WeChat": 20, "Blanket": 100}' apply-volume-limits.py
"""

import json
import os
import sys
import tempfile

HEADER = "[restore-stream]"


def parse_limits():
    raw = os.environ.get("AW_VOLUME_LIMITS")
    if not raw:
        print("AW_VOLUME_LIMITS env var not set", file=sys.stderr)
        sys.exit(1)
    return json.loads(raw)


def read_state(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return [line.rstrip("\n") for line in f if line.strip()]


def filter_lines(lines, app_names):
    """Remove existing entries for managed apps."""
    prefixes = [f"Output/Audio:application.name:{name}:" for name in app_names]
    return [line for line in lines if not any(line.startswith(p) for p in prefixes)]


def build_entries(limits):
    """Build state file entries for each app."""
    entries = []
    for name in sorted(limits):
        linear = limits[name] / 100.0
        entries.append(f"Output/Audio:application.name:{name}:channelMap=FL;FR;")
        entries.append(f"Output/Audio:application.name:{name}:channelVolumes={linear};{linear};")
        entries.append(f"Output/Audio:application.name:{name}:mute=false")
        entries.append(f"Output/Audio:application.name:{name}:volume={linear}")
    return entries


def write_atomic(path, content):
    state_dir = os.path.dirname(path)
    os.makedirs(state_dir, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=state_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.rename(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def main():
    limits = parse_limits()

    home = os.path.expanduser("~")
    state_path = os.path.join(
        home, ".local", "state", "wireplumber", "restore-stream"
    )

    original = read_state(state_path)

    # Ensure header exists
    if original and original[0] == HEADER:
        base = list(original)
    elif HEADER in original:
        base = list(original)
    else:
        base = [HEADER] + list(original)

    # Remove our entries, add fresh ones
    filtered = filter_lines(base, limits.keys())
    new_lines = filtered + build_entries(limits)
    new_content = "\n".join(new_lines) + "\n"

    # Compare with current file content
    old_content = ""
    if os.path.exists(state_path):
        with open(state_path, "r") as f:
            old_content = f.read()

    if new_content == old_content:
        for name in sorted(limits):
            print(f"  {name}: {limits[name]}% (linear {limits[name] / 100.0:.4f}) [no change]")
        print("NO_CHANGE")
        return

    write_atomic(state_path, new_content)
    for name in sorted(limits):
        print(f"  {name}: {limits[name]}% (linear {limits[name] / 100.0:.4f})")
    print("CHANGED")


if __name__ == "__main__":
    main()
