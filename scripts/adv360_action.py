#!/usr/bin/env python3
"""Launch a validated Advantage360 semantic host action without a shell."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = ROOT / "host/apps.defaults.json"
OVERRIDE = Path.home() / ".config/adv360/apps.json"
ACTIONS = ("launcher", "terminal", "browser", "files", "editor", "project", "git", "ai")


class ActionError(ValueError):
    """An action configuration cannot be executed safely."""


def host_name() -> str:
    system = platform.system()
    if system == "Darwin":
        return "macos"
    if system == "Linux":
        return "linux"
    raise ActionError(f"unsupported operating system: {system}")


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ActionError(f"cannot read {path}: {error}") from error
    if not isinstance(data, dict):
        raise ActionError(f"{path}: root must be an object")
    return data


def merged_config(host: str) -> dict[str, Any]:
    defaults = read_json(DEFAULTS).get(host)
    if not isinstance(defaults, dict):
        raise ActionError(f"{DEFAULTS}: missing {host} defaults")
    result = dict(defaults)
    if OVERRIDE.exists():
        override = read_json(OVERRIDE).get(host, {})
        if not isinstance(override, dict):
            raise ActionError(f"{OVERRIDE}: {host} must be an object")
        result.update(override)
    return result


def resolve_action(action: str, host: str) -> Tuple[list[str], Optional[str]]:
    entry = merged_config(host).get(action)
    if not isinstance(entry, dict):
        raise ActionError(f"missing action configuration: {host}.{action}")
    command = entry.get("command")
    if not isinstance(command, list) or not command or not all(isinstance(value, str) and value for value in command):
        raise ActionError(f"{host}.{action}.command must be a non-empty string array")
    expanded = [
        os.path.expandvars(os.path.expanduser(value.replace("{repo}", str(ROOT))))
        for value in command
    ]
    fallback = entry.get("fallback_url")
    if fallback is not None and not isinstance(fallback, str):
        raise ActionError(f"{host}.{action}.fallback_url must be a string")
    return expanded, fallback


def executable_exists(command: str) -> bool:
    if os.path.sep in command:
        return Path(command).is_file() and os.access(command, os.X_OK)
    return shutil.which(command) is not None


def launch(action: str, *, dry_run: bool = False) -> int:
    host = host_name()
    command, fallback = resolve_action(action, host)
    if not executable_exists(command[0]):
        if fallback:
            opener = "/usr/bin/open" if host == "macos" else "xdg-open"
            command = [opener, fallback]
        else:
            raise ActionError(f"executable not found: {command[0]}")
    if dry_run:
        print(json.dumps({"action": action, "host": host, "argv": command}))
        return 0
    subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("action", choices=ACTIONS)
    result.add_argument("--dry-run", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        return launch(args.action, dry_run=args.dry_run)
    except ActionError as error:
        print(f"adv360-action: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
