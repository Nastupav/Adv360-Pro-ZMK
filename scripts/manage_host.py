#!/usr/bin/env python3
"""Install or roll back Advantage360 host adapters with timestamped backups."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE_ROOT = Path.home() / ".local/state/adv360-host-backups"
ACTION_LINK = Path.home() / ".local/bin/adv360-action"

HAMMER_START = "-- BEGIN ADV360 HOST ADAPTER"
HAMMER_END = "-- END ADV360 HOST ADAPTER"
NVIM_START = "-- BEGIN ADV360 NVIM ADAPTER"
NVIM_END = "-- END ADV360 NVIM ADAPTER"
HYPR_START = "-- BEGIN ADV360 HYPRLAND ADAPTER"
HYPR_END = "-- END ADV360 HYPRLAND ADAPTER"


class InstallError(ValueError):
    """The host installation cannot be completed safely."""


def upsert_block(text: str, start: str, end: str, body: str) -> str:
    starts = text.count(start)
    ends = text.count(end)
    if starts != ends or starts > 1:
        raise InstallError(f"unbalanced or duplicate managed block: {start}")
    block = f"{start}\n{body.rstrip()}\n{end}"
    pattern = re.compile(rf"{re.escape(start)}.*?{re.escape(end)}", re.S)
    if starts == 1:
        return pattern.sub(block, text, count=1)
    suffix = "" if text.endswith("\n") else "\n"
    return text + suffix + "\n" + block + "\n"


def remove_block(text: str, start: str, end: str) -> str:
    starts = text.count(start)
    ends = text.count(end)
    if starts == 0 and ends == 0:
        return text
    if starts != 1 or ends != 1:
        raise InstallError(f"unbalanced or duplicate managed block: {start}")
    pattern = re.compile(rf"(?m)^\s*{re.escape(start)}.*?^\s*{re.escape(end)}\s*\n?", re.S)
    result, count = pattern.subn("", text, count=1)
    if count != 1:
        raise InstallError(f"cannot remove managed block: {start}")
    return result


def nvim_block() -> str:
    return f"dofile({json.dumps(str(ROOT / 'host/nvim-adv360.lua'))})"


def hypr_block() -> str:
    return f"dofile({json.dumps(str(ROOT / 'host/hyprland-adv360.lua'))})"


def rendered_aerospace() -> str:
    source = (ROOT / "host/macos/aerospace.toml").read_text()
    token = "__ADV360_ACTION__"
    if source.count(token) != 8:
        raise InstallError("AeroSpace source must contain eight action-link placeholders")
    return source.replace(token, str(ACTION_LINK))


def cleaned_karabiner(data: dict[str, Any]) -> dict[str, Any]:
    profiles = data.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise InstallError("Karabiner configuration has no profile")
    obsolete = ("ADV360 WM F21-F24", "ADV360 normalize F14/F15 for Hammerspoon")
    for profile in profiles:
        modifications = profile.setdefault("complex_modifications", {})
        rules = modifications.setdefault("rules", [])
        if not isinstance(rules, list):
            raise InstallError("Karabiner complex_modifications.rules is not an array")
        modifications["rules"] = [
            rule for rule in rules
            if not any(rule.get("description", "").startswith(prefix) for prefix in obsolete)
        ]
    return data


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.adv360.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except BaseException:
        if temporary.exists() and not temporary.is_symlink():
            temporary.unlink()
        raise


def managed_file_paths() -> set[Path]:
    home = Path.home()
    return {
        Path(os.path.abspath(home / ".config/nvim/init.lua")),
        Path(os.path.abspath(home / ".hammerspoon/init.lua")),
        Path(os.path.abspath(home / ".config/karabiner/karabiner.json")),
        Path(os.path.abspath(home / ".config/aerospace/aerospace.toml")),
        Path(os.path.abspath(home / ".config/hypr/hyprland.lua")),
    }


def managed_root() -> Path:
    return Path.home().resolve()


def require_managed_containment(path: Path) -> None:
    root = managed_root()
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise InstallError(f"managed path escapes home through a symlink: {path} -> {resolved}") from error


def proposed_files() -> dict[Path, str]:
    home = Path.home()
    result: dict[Path, str] = {}
    nvim = home / ".config/nvim/init.lua"
    nvim_text = nvim.read_text() if nvim.exists() else ""
    result[nvim] = upsert_block(nvim_text, NVIM_START, NVIM_END, nvim_block())

    system = platform.system()
    if system == "Darwin":
        legacy_aerospace = home / ".aerospace.toml"
        if legacy_aerospace.exists():
            raise InstallError("ambiguous AeroSpace configuration: archive ~/.aerospace.toml before installation")

        hammerspoon = home / ".hammerspoon/init.lua"
        if hammerspoon.exists():
            result[hammerspoon] = remove_block(hammerspoon.read_text(), HAMMER_START, HAMMER_END)

        karabiner = home / ".config/karabiner/karabiner.json"
        if karabiner.exists():
            data = cleaned_karabiner(json.loads(karabiner.read_text()))
            result[karabiner] = json.dumps(data, indent=2) + "\n"

        aerospace = home / ".config/aerospace/aerospace.toml"
        result[aerospace] = rendered_aerospace()
    elif system == "Linux":
        hyprland = home / ".config/hypr/hyprland.lua"
        hypr_text = hyprland.read_text() if hyprland.exists() else ""
        result[hyprland] = upsert_block(hypr_text, HYPR_START, HYPR_END, hypr_block())
    else:
        raise InstallError(f"unsupported operating system: {system}")
    return result


def install(dry_run: bool) -> int:
    files = proposed_files()
    allowed_files = managed_file_paths()
    for path in files:
        normalized = Path(os.path.abspath(path))
        if normalized not in allowed_files:
            raise InstallError(f"refusing to update unmanaged path: {normalized}")
        require_managed_containment(normalized)
        if normalized.is_symlink():
            raise InstallError(f"refusing to replace managed symlink: {normalized}")
    changed = {path: text for path, text in files.items() if not path.exists() or path.read_text() != text}

    link_source = ROOT / "scripts/adv360_action.py"
    require_managed_containment(ACTION_LINK)
    link_changed = not ACTION_LINK.is_symlink() or ACTION_LINK.resolve() != link_source.resolve()
    if ACTION_LINK.exists() and not ACTION_LINK.is_symlink():
        raise InstallError(f"refusing to replace non-symlink {ACTION_LINK}")

    for path in changed:
        print(f"UPDATE {path}")
    if link_changed:
        print(f"LINK   {ACTION_LINK} -> {link_source}")
    if not changed and not link_changed:
        print("host integration already current")
        return 0
    if dry_run:
        print("dry run; use 'install' to apply")
        return 0

    identifier = dt.datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    state = STATE_ROOT / identifier
    state.mkdir(parents=True, exist_ok=False)
    manifest: dict[str, Any] = {"schema": 1, "root": str(ROOT), "files": [], "links": []}

    # Finish every backup and persist the complete rollback plan before the
    # first live file changes. This makes a mid-install failure reversible.
    for index, path in enumerate(changed):
        existed = path.exists()
        backup = state / f"file-{index}.backup"
        if existed:
            shutil.copy2(path, backup)
        manifest["files"].append({"path": str(path), "existed": existed, "backup": str(backup) if existed else None})
    if link_changed:
        previous = os.readlink(ACTION_LINK) if ACTION_LINK.is_symlink() else None
        manifest["links"].append({"path": str(ACTION_LINK), "previous": previous})
    (state / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    try:
        for path, text in changed.items():
            atomic_write(path, text)
        if link_changed:
            ACTION_LINK.parent.mkdir(parents=True, exist_ok=True)
            if ACTION_LINK.is_symlink():
                ACTION_LINK.unlink()
            ACTION_LINK.symlink_to(link_source)
    except OSError as error:
        try:
            rollback(identifier)
        except (InstallError, OSError, json.JSONDecodeError) as rollback_error:
            raise InstallError(f"install failed ({error}); automatic rollback also failed ({rollback_error})") from error
        raise InstallError(f"install failed and was rolled back: {error}") from error

    print(f"installed; rollback state: {state}")
    return 0


def latest_state(identifier: str) -> Path:
    if identifier != "latest":
        if not re.fullmatch(r"\d{8}T\d{6}[+-]\d{4}", identifier):
            raise InstallError(f"invalid backup identifier: {identifier!r}")
        root = STATE_ROOT.resolve()
        state = (STATE_ROOT / identifier).resolve()
        if state.parent != root:
            raise InstallError(f"backup escapes state root: {state}")
        if not state.is_dir():
            raise InstallError(f"backup not found: {state}")
        return state
    root = STATE_ROOT.resolve()
    candidates = sorted(
        path.resolve()
        for path in STATE_ROOT.glob("*")
        if not path.is_symlink() and path.is_dir() and path.resolve().parent == root and (path / "manifest.json").is_file()
    )
    if not candidates:
        raise InstallError("no Advantage360 host backup found")
    return candidates[-1]


def rollback(identifier: str) -> int:
    state = latest_state(identifier)
    manifest = json.loads((state / "manifest.json").read_text())
    if not isinstance(manifest, dict) or manifest.get("schema") != 1:
        raise InstallError(f"invalid backup manifest: {state / 'manifest.json'}")

    allowed_files = managed_file_paths()
    state_resolved = state.resolve()

    prepared_files: list[tuple[Path, bool, Path | None]] = []
    files = manifest.get("files", [])
    if not isinstance(files, list):
        raise InstallError("backup manifest files must be an array")
    for entry in files:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or not isinstance(entry.get("existed"), bool):
            raise InstallError("invalid file entry in backup manifest")
        raw_path = Path(entry["path"])
        if not raw_path.is_absolute():
            raise InstallError(f"backup target must be absolute: {raw_path}")
        path = Path(os.path.abspath(raw_path))
        if path not in allowed_files:
            raise InstallError(f"refusing to restore unmanaged path: {path}")
        require_managed_containment(path)
        if path.is_symlink():
            raise InstallError(f"refusing to restore through symlink: {path}")
        if path.exists() and not path.is_file():
            raise InstallError(f"rollback target is not a regular file: {path}")
        backup: Path | None = None
        if entry["existed"]:
            if not isinstance(entry.get("backup"), str):
                raise InstallError(f"missing backup for {path}")
            backup = Path(entry["backup"]).resolve()
            if backup.parent != state_resolved or not backup.is_file():
                raise InstallError(f"backup file escapes state directory: {backup}")
        elif entry.get("backup") is not None:
            raise InstallError(f"unexpected backup for newly created path: {path}")
        prepared_files.append((path, entry["existed"], backup))

    prepared_links: list[tuple[Path, str | None]] = []
    links = manifest.get("links", [])
    if not isinstance(links, list):
        raise InstallError("backup manifest links must be an array")
    allowed_link = Path(os.path.abspath(ACTION_LINK))
    for entry in links:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise InstallError("invalid link entry in backup manifest")
        path = Path(os.path.abspath(Path(entry["path"])))
        previous = entry.get("previous")
        if path != allowed_link or previous is not None and not isinstance(previous, str):
            raise InstallError(f"refusing to restore unmanaged link: {path}")
        require_managed_containment(path)
        if path.exists() and not path.is_symlink():
            raise InstallError(f"refusing to replace non-symlink during rollback: {path}")
        prepared_links.append((path, previous))

    for path, existed, backup in prepared_files:
        if existed:
            assert backup is not None
            atomic_write(path, backup.read_text())
        elif path.exists():
            path.unlink()
        print(f"RESTORE {path}")
    for path, previous in prepared_links:
        if path.is_symlink():
            path.unlink()
        if previous is not None:
            path.symlink_to(previous)
        print(f"RESTORE {path}")
    print(f"rolled back from {state}")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("plan", help="show changes without writing")
    commands.add_parser("install", help="apply changes after creating backups")
    undo = commands.add_parser("rollback", help="restore a prior install backup")
    undo.add_argument("backup", nargs="?", default="latest", help="backup directory name or latest")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "plan":
            return install(dry_run=True)
        if args.command == "install":
            return install(dry_run=False)
        return rollback(args.backup)
    except (InstallError, OSError, json.JSONDecodeError) as error:
        print(f"manage-host: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
