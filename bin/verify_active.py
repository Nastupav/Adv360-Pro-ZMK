#!/usr/bin/env python3
"""Verify the installed macOS host state matches this repository.

The static side of the protocol is already covered: validate_keymap.py checks
the keymap, validate_protocol.py checks all three host configs against it, and
render_keymap.py --check checks the README. This script covers the part none of
them can see - what is actually installed and running on this machine.

Ported from the pre-V3.0 scripts/verify_workflow.py --require-active on
2026-08-22. Checks that no longer have a subject were dropped rather than
reinterpreted: V3.0 ships no Neovim module, no Hammerspoon adapter and no
VS Code keybinding source, so those files are now checked for *absence* of the
retired integration instead of presence of a current one.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

failures: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def bindings_of(text: str) -> dict[str, str]:
    """Parse the [mode.main.binding] table, tolerating ''' quoting."""
    import re

    body = text.split("[mode.main.binding]", 1)[1]
    body = re.split(r"(?m)^\[", body)[0]
    pattern = re.compile(r"(?m)^([a-z0-9-]+)\s*=\s*('''(.*?)'''|'(.*?)')", re.S)
    return {m.group(1): (m.group(3) if m.group(3) is not None else m.group(4))
            for m in pattern.finditer(body)}


def main() -> int:
    from manage_host import rendered_aerospace

    home = Path.home()
    installed = home / ".config/aerospace/aerospace.toml"
    action_link = home / ".local/bin/adv360-action"
    nvim = home / ".config/nvim/init.lua"
    hammerspoon = home / ".hammerspoon/init.lua"
    karabiner = home / ".config/karabiner/karabiner.json"

    require(not (home / ".aerospace.toml").exists(),
            "legacy ~/.aerospace.toml would create config ambiguity")
    require(installed.exists(), "active AeroSpace configuration missing")
    matches = installed.exists() and installed.read_text() == rendered_aerospace()
    require(matches, "active AeroSpace config differs from repository source")

    # Retired by V3.0: the bindings call `open -a` directly.
    require(not action_link.exists() and not action_link.is_symlink(),
            f"{action_link} still present; V3.0 launches apps directly")
    if nvim.exists():
        require("nvim-adv360" not in nvim.read_text() and "ADV360 NVIM ADAPTER" not in nvim.read_text(),
                "active Neovim still loads the retired Advantage360 module")
    if hammerspoon.exists():
        text = hammerspoon.read_text()
        require("ADV360 HOST ADAPTER" not in text and "hammerspoon-adv360" not in text,
                "Hammerspoon still loads the retired Advantage360 adapter")
    if karabiner.exists():
        raw = karabiner.read_text()
        require("ADV360 normalize F14/F15 for Hammerspoon" not in raw and "ADV360 WM F21-F24" not in raw,
                "Karabiner still contains a retired Advantage360 protocol rule")

    aerospace = shutil.which("aerospace")
    require(aerospace is not None, "AeroSpace CLI is unavailable")

    # Runtime checks are skipped unless the installed file is ours: reloading
    # and asserting against somebody else's config would be meaningless, and
    # `reload-config` is a live action on the running window manager.
    if aerospace is not None and matches:
        def run(*arguments: str) -> str:
            result = subprocess.run([aerospace, *arguments], capture_output=True, text=True)
            if result.returncode != 0:
                failures.append(f"AeroSpace check failed ({' '.join(arguments)}): "
                                f"{result.stderr.strip() or result.stdout.strip()}")
                return ""
            return result.stdout

        loaded_path = run("config", "--config-path").strip()
        if loaded_path:
            require(Path(loaded_path).resolve(strict=False) == installed.resolve(strict=False),
                    f"AeroSpace server loaded unexpected config path: {loaded_path}")
        run("reload-config", "--dry-run")
        run("reload-config")

        raw_bindings = run("config", "--get", "mode.main.binding", "--json")
        if raw_bindings:
            loaded = json.loads(raw_bindings)
            require(isinstance(loaded, dict), "AeroSpace loaded binding table is not an object")
            if isinstance(loaded, dict):
                expected = bindings_of(installed.read_text())
                norm = lambda table: {k: " ".join(str(v).split()) for k, v in table.items()}
                require(norm(loaded) == norm(expected),
                        "AeroSpace runtime bindings differ from the installed config")

        # The preamble declares ten persistent workspaces; AeroSpace also
        # creates workspaces on demand when a window lands outside that set,
        # so require the persistent ten and let extras be.
        workspaces = run("list-workspaces", "--all").split()
        if workspaces:
            missing = [str(n) for n in range(1, 11) if str(n) not in workspaces]
            require(not missing, f"persistent workspaces missing: {missing}")

        monitors: dict[str, str] = {}
        for line in run("list-monitors").splitlines():
            parts = [part.strip() for part in line.split("|", 1)]
            if len(parts) == 2:
                monitors[parts[1]] = parts[0]
        if monitors:
            require("PG32UCDM" in monitors and "P34WD-40" in monitors,
                    f"expected monitors not active: {sorted(monitors)}")
            if "PG32UCDM" in monitors and "P34WD-40" in monitors:
                primary = run("list-workspaces", "--monitor", monitors["PG32UCDM"]).split()
                secondary = run("list-workspaces", "--monitor", monitors["P34WD-40"]).split()
                require(primary == ["1", "2", "3", "4", "5"],
                        f"PG32UCDM workspace assignment mismatch: {primary}")
                require(secondary == ["6", "7", "8", "9", "10"],
                        f"P34WD-40 workspace assignment mismatch: {secondary}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    print("  ok  installed AeroSpace config matches the repository")
    print("  ok  retired adapters (adv360-action, Neovim, Hammerspoon, Karabiner) are gone")
    print("  ok  AeroSpace runtime bindings, workspaces and monitor assignment agree"
          if aerospace is not None else "  --  AeroSpace CLI absent; runtime checks skipped")
    print("\nactive host: installed state matches this checkout")
    return 0


if __name__ == "__main__":
    sys.exit(main())
