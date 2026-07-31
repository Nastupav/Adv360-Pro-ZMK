#!/usr/bin/env python3
"""Semantic verification for the Advantage360 firmware and host workflow."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
KEYMAP = ROOT / "config/adv360.keymap"
EXPECTED_SHAPE = [14, 14, 18, 14, 16]
HOME_INDEX = {"A": 1, "S": 2, "D": 3, "F": 4, "G": 5, "H": 12, "J": 13, "K": 14, "L": 15, ";": 16}
ACTIONS = ["launcher", "terminal", "browser", "files", "editor", "project", "git", "ai"]
PINNED_ZMK = "86114880a03d3e219a1fa534d7c98d4786b1dfac"
PINNED_IMAGE = "sha256:edb1c953438c6f720ddb79c3762f3972013b7fbbaf4fff3592fc869983e7afc5"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    require(isinstance(data, dict), f"{path}: root must be an object")
    return data


def uncomment(text: str, marker: str = "//") -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return "\n".join(line.split(marker, 1)[0] for line in text.splitlines())


def split_bindings(text: str) -> list[str]:
    return [match.strip() for match in re.findall(r"&[^&]+?(?=\s+&|$)", text)]


def layer_rows(text: str, node: str) -> list[list[str]]:
    clean = uncomment(text)
    start = clean.index(node + " {")
    block = clean[start:]
    begin = block.index("bindings = <") + len("bindings = <")
    body = block[begin:block.index(">;", begin)]
    rows = [split_bindings(line.strip()) for line in body.splitlines() if line.strip()]
    require([len(row) for row in rows] == EXPECTED_SHAPE, f"{node}: invalid row shape {[len(row) for row in rows]}")
    return rows


def node_body(text: str, label: str) -> str:
    clean = uncomment(text)
    match = re.search(rf"\b{re.escape(label)}:\s+[A-Za-z0-9_]+\s*\{{(.*?)\}};", clean, re.S)
    require(match is not None, f"missing node: {label}")
    assert match is not None
    return match.group(1)


def macro_bindings(text: str, name: str) -> list[str]:
    body = node_body(text, name)
    prop = re.search(r"bindings\s*=\s*(.*?);", body, re.S)
    require(prop is not None, f"missing bindings in macro: {name}")
    assert prop is not None
    return split_bindings(prop.group(1).replace(">, <", " ").replace("<", "").replace(">", ""))


def check_unique(name: str, rows: list[list[str]]) -> None:
    bindings = [binding for row in rows for binding in row if binding not in {"&none", "&trans"}]
    duplicates = {binding: count for binding, count in Counter(bindings).items() if count > 1}
    require(not duplicates, f"{name}: duplicate active bindings {duplicates}")


def check_keymap() -> None:
    text = KEYMAP.read_text()
    clean = uncomment(text)
    layers = {
        "BASE": layer_rows(text, "default_layer"),
        "NAV": layer_rows(text, "layer_nav"),
        "SYM": layer_rows(text, "layer_sym"),
        "NUM": layer_rows(text, "layer_num"),
        "GLOBAL": layer_rows(text, "layer_global"),
        "SYS": layer_rows(text, "layer_sys"),
    }
    require("#include <behaviors/studio_unlock.dtsi>" in text, "ZMK Studio unlock behavior is not included")
    require(layers["SYS"][1][9] == "&studio_unlock", "SYS+U must provide ZMK Studio unlock")

    for name in ("NAV", "SYM", "NUM", "GLOBAL", "SYS"):
        home = layers[name][2]
        require(home[HOME_INDEX["G"]] == "&none", f"{name}: G must be inactive")
        require(home[HOME_INDEX["H"]] == "&none", f"{name}: H must be inactive")

    expected_home = {
        "NAV": {"A": "&kp HOME", "S": "&kp PG_DN", "D": "&kp PG_UP", "F": "&kp END", "J": "&kp LEFT", "K": "&kp DOWN", "L": "&kp UP", ";": "&kp RIGHT"},
        "SYM": {"A": "&kp UNDER", "S": "&kp COLON", "D": "&kp EXCL", "F": "&kp QMARK", "J": "&kp PLUS", "K": "&kp ASTRK", "L": "&kp AMPS", ";": "&kp PIPE"},
        "GLOBAL": {"A": "&kp LC(LS(F19))", "S": "&kp LC(LS(F20))", "D": "&kp LC(F20)", "F": "&kp LC(F19)", "J": "&kp LC(F13)", "K": "&kp LC(F14)", "L": "&kp LC(F15)", ";": "&kp LC(F16)"},
    }
    for name, expected in expected_home.items():
        for key, binding in expected.items():
            actual = layers[name][2][HOME_INDEX[key]]
            require(actual == binding, f"{name} {key}: expected {binding}, got {actual}")

    for name in ("NAV", "SYM", "GLOBAL"):
        check_unique(name, layers[name])

    global_top = layers["GLOBAL"][0]
    require(global_top[1:6] + global_top[8:11] == [f"&kp F{number}" for number in range(13, 21)], "GLOBAL workspace carriers differ from F13-F20")
    require(not re.search(r"\bF2[1-4]\b", clean), "active firmware must not emit F21-F24")

    base = " ".join(binding for row in layers["BASE"] for binding in row)
    expected_thumbs = ("&tlt NAV ESC", "&tlt SYM TAB", "&num_caps NUM 0", "&tlt GLOBAL LA(F13)")
    for binding in expected_thumbs:
        require(base.count(binding) == 1, f"BASE: expected exactly one {binding}")
    require(len(re.findall(r"&(tlt|num_caps)\b", base)) == 4, "dual-role behavior must be limited to four thumb keys")
    require(base.count("&sk_lazy LGUI") == 1 and base.count("&sk_lazy LCTRL") == 1, "lazy sticky GUI/Ctrl missing")

    for behavior in ("tlt", "num_caps"):
        body = node_body(text, behavior)
        require('flavor = "hold-preferred"' in body and "tapping-term-ms = <170>" in body, f"{behavior}: expected hold-preferred 170 ms")
    sticky = node_body(text, "sk_lazy")
    for token in ("release-after-ms = <1000>", "quick-release", "lazy", "bindings = <&kp>"):
        require(token in sticky, f"lazy sticky behavior missing {token}")

    speed_macros = {
        "op_eqeq": ["&kp EQUAL", "&kp EQUAL"],
        "op_neq": ["&kp EXCL", "&kp EQUAL"],
        "op_lte": ["&kp LT", "&kp EQUAL"],
        "op_gte": ["&kp GT", "&kp EQUAL"],
        "op_arrow": ["&kp MINUS", "&kp GT"],
        "op_fatarrow": ["&kp EQUAL", "&kp GT"],
        "op_and": ["&kp AMPS", "&kp AMPS"],
        "op_or": ["&kp PIPE", "&kp PIPE"],
        "op_walrus": ["&kp COLON", "&kp EQUAL"],
        "op_pow": ["&kp ASTRK", "&kp ASTRK"],
        "op_floordiv": ["&kp FSLH", "&kp FSLH"],
        "ps_eq": ["&kp MINUS", "&kp E", "&kp Q"],
        "ps_ne": ["&kp MINUS", "&kp N", "&kp E"],
        "ps_lt": ["&kp MINUS", "&kp L", "&kp T"],
        "ps_le": ["&kp MINUS", "&kp L", "&kp E"],
        "ps_gt": ["&kp MINUS", "&kp G", "&kp T"],
        "ps_ge": ["&kp MINUS", "&kp G", "&kp E"],
        "op_sql_ne": ["&kp LT", "&kp GT"],
        "op_scope": ["&kp COLON", "&kp COLON"],
        "ps_current": ["&kp DLLR", "&kp UNDER"],
        "op_comment": ["&kp MINUS", "&kp MINUS"],
    }
    macro_definitions = set(re.findall(r"^\s*([A-Za-z0-9_]+):\s+[A-Za-z0-9_]+\s*\{\s*compatible\s*=\s*\"zmk,behavior-macro\"", clean, re.M))
    require(macro_definitions == set(speed_macros), f"macro inventory mismatch: expected {sorted(speed_macros)}, got {sorted(macro_definitions)}")
    for macro, expected in speed_macros.items():
        body = node_body(text, macro)
        require("wait-ms = <20>" in body and "tap-ms = <20>" in body, f"{macro}: expected 20/20 ms timing")
        require(macro_bindings(text, macro) == expected, f"{macro}: incorrect output sequence")
        require(len(re.findall(rf"&{macro}\b", clean)) == 1, f"{macro}: expected one active use")

    expected_sym_rows = {
        1: ["&trans", "&op_eqeq", "&op_neq", "&op_lte", "&op_gte", "&op_arrow", "&trans", "&trans", "&op_fatarrow", "&op_and", "&op_or", "&op_walrus", "&op_pow", "&op_floordiv"],
        3: ["&trans", "&ps_eq", "&ps_ne", "&ps_lt", "&ps_le", "&ps_gt", "&trans", "&trans", "&ps_ge", "&op_sql_ne", "&op_scope", "&ps_current", "&op_comment", "&trans"],
    }
    for row_index, expected in expected_sym_rows.items():
        require(layers["SYM"][row_index] == expected, f"SYM row {row_index + 1}: speed macro placement changed")

    nav = " ".join(binding for row in layers["NAV"] for binding in row)
    for binding in ("&msc SCRL_LEFT", "&msc SCRL_DOWN", "&msc SCRL_UP", "&msc SCRL_RIGHT", "&mkp MCLK", "&mkp LCLK", "&mkp RCLK"):
        require(nav.count(binding) == 1, f"NAV pointer binding missing or duplicated: {binding}")
    require("MOVE_" not in nav, "NAV must not include pointer cursor movement")

    conf = uncomment((ROOT / "config/adv360.conf").read_text(), marker="#")
    for token in ("CONFIG_ZMK_HID_KEYBOARD_NKRO_EXTENDED_REPORT=y", "CONFIG_ZMK_POINTING=y", "CONFIG_ZMK_STUDIO=n", "CONFIG_ZMK_BACKLIGHT_ON_START=n", "CONFIG_ZMK_RGB_UNDERGLOW_ON_START=n"):
        require(token in conf, f"adv360.conf missing {token}")
    print("PASS keymap geometry, thumb timing, macros, Studio unlock, pointer controls, and power defaults")


def check_protocol() -> dict[str, Any]:
    protocol = read_json(ROOT / "host/protocol.json")
    require(protocol.get("schema") == 1, "protocol schema must be 1")
    require(protocol.get("carrier") == {"first_key": "F13", "last_key": "F20", "slots": 8}, "invalid carrier range")
    actions = protocol.get("actions")
    require(isinstance(actions, list) and len(actions) == 8, "protocol requires eight developer actions")
    for slot, action in enumerate(actions, start=1):
        require(action == {
            "slot": slot,
            "signal": f"Alt+F{12 + slot}",
            "gesture": ["tap GLOBAL thumb", "GLOBAL+T", "GLOBAL+W", "GLOBAL+O", "GLOBAL+E", "GLOBAL+P", "GLOBAL+U", "GLOBAL+I"][slot - 1],
            "name": ACTIONS[slot - 1],
        }, f"protocol action slot {slot} mismatch")
    require(protocol.get("directions") == ["left", "down", "up", "right"], "direction order mismatch")
    return protocol


def active_lines(path: Path, marker: str) -> list[str]:
    return [line.split(marker, 1)[0].strip() for line in path.read_text().splitlines() if line.split(marker, 1)[0].strip()]


def check_hyprland() -> None:
    lua = (ROOT / "host/hyprland-adv360.lua").read_text()
    required_lua = [
        'workspace("F" .. (12 + number), number)', "workspace = number, follow = true",
        'hl.bind("CTRL + F13", hl.dsp.focus({ direction = "l" }))',
        'hl.bind("CTRL + SHIFT + F20", hl.dsp.layout("togglesplit"))',
        'local actions = { "launcher", "terminal", "browser", "files", "editor", "project", "git", "ai" }',
        'hl.bind("ALT + F" .. (12 + slot), hl.dsp.exec_cmd(action(name)))',
    ]
    for token in required_lua:
        require(token in lua, f"Hyprland Lua missing: {token}")

    legacy_path = ROOT / "host/hyprland-adv360.conf"
    lines = active_lines(legacy_path, "#")
    binds = [line for line in lines if line.startswith("bind =")]
    identities = [tuple(part.strip() for part in line.split(",", 3)[:3]) for line in binds]
    require(len(identities) == len(set(identities)), "legacy Hyprland has conflicting duplicate bindings")
    for number in range(1, 9):
        require(f"bind = , F{12 + number}, workspace, {number}" in lines, f"legacy workspace {number} missing")
        require(f"bind = SHIFT, F{12 + number}, movetoworkspace, {number}" in lines, f"legacy move workspace {number} missing")
        require(f"bind = ALT, F{12 + number}, exec, adv360-action {ACTIONS[number - 1]}" in lines, f"legacy action {ACTIONS[number - 1]} missing")
    require(not re.search(r"\bF2[1-4]\b", lua + "\n" + legacy_path.read_text()), "supported Hyprland adapters must not use F21-F24")


def parse_nvim_maps(path: Path) -> dict[tuple[str, str], str]:
    clean = "\n".join(line for line in path.read_text().splitlines() if not line.lstrip().startswith("--"))
    mappings: dict[tuple[str, str], str] = {}
    pattern = re.compile(r"vim\.keymap\.set\('([nt])',\s*'([^']+)',\s*'([^']+)'")
    for mode, lhs, rhs in pattern.findall(clean):
        key = (mode, lhs)
        require(key not in mappings, f"{path}: duplicate mapping for {mode} {lhs}")
        mappings[key] = rhs
    return mappings


def check_nvim(path: Path, label: str) -> None:
    mappings = parse_nvim_maps(path)
    expected = {
        ("n", "<C-j>"): "<C-w><C-h>", ("n", "<C-k>"): "<C-w><C-j>",
        ("n", "<C-l>"): "<C-w><C-k>", ("n", "<C-;>"): "<C-w><C-l>",
        ("n", "<leader>wJ"): "<C-w>H", ("n", "<leader>wK"): "<C-w>J",
        ("n", "<leader>wL"): "<C-w>K", ("n", "<leader>w;"): "<C-w>L",
        ("t", "<C-j>"): r"<C-\\><C-n><C-w><C-h>", ("t", "<C-k>"): r"<C-\\><C-n><C-w><C-j>",
        ("t", "<C-l>"): r"<C-\\><C-n><C-w><C-k>", ("t", "<C-;>"): r"<C-\\><C-n><C-w><C-l>",
    }
    require(mappings == expected, f"{label}: mappings differ from the J/K/L/; contract")
    require(not any("C-S-" in lhs for _, lhs in mappings), f"{label}: unreliable Ctrl+Shift letter mapping remains")


def karabiner_rule(data: dict[str, Any]) -> dict[str, Any]:
    rules = data.get("rules")
    if not isinstance(rules, list):
        profiles = data.get("profiles")
        require(isinstance(profiles, list), "Karabiner data has no rules or profiles")
        rules = []
        for profile in profiles:
            rules.extend(profile.get("complex_modifications", {}).get("rules", []))
    matches = [rule for rule in rules if rule.get("description") == "ADV360 normalize F14/F15 for Hammerspoon"]
    require(len(matches) == 1, "expected one active ADV360 F14/F15 normalization rule")
    return matches[0]


def check_karabiner(data: dict[str, Any], label: str) -> None:
    rule = karabiner_rule(data)
    manipulators = rule.get("manipulators")
    require(isinstance(manipulators, list) and len(manipulators) == 10, f"{label}: expected ten exact F14/F15 variants")
    sources = Counter(item.get("from", {}).get("key_code") for item in manipulators)
    require(sources == {"f14": 5, "f15": 5}, f"{label}: source variants mismatch")
    for item in manipulators:
        identifiers = item.get("conditions", [{}])[0].get("identifiers", [{}])[0]
        require(identifiers.get("vendor_id") == 7504 and identifiers.get("product_id") == 24926, f"{label}: rule is not device scoped")
        output = item.get("to", [{}])[0]
        require(output.get("key_code") == item.get("from", {}).get("key_code"), f"{label}: carrier key changed")
        require("left_command" in output.get("modifiers", []), f"{label}: normalization tag missing")


def check_hammerspoon(path: Path) -> None:
    text = path.read_text()
    for token in (
        "local function bindCarrier", "duplicate Advantage360 hotkey", "hs.spaces.moveWindowToSpace",
        "create 8 user Spaces", 'local actions = { "launcher", "terminal", "browser", "files", "editor", "project", "git", "ai" }',
        '_G.ADV360_STATUS = { ready = true, bindings = 38, protocol = "F13-F20/v1" }',
    ):
        require(token in text, f"Hammerspoon adapter missing: {token}")
    require(not re.search(r"\bf2[1-4]\b", text, re.I), "Hammerspoon adapter must not use F21-F24")


def check_apps() -> None:
    defaults = read_json(ROOT / "host/apps.defaults.json")
    require(defaults.get("schema") == 1, "app defaults schema must be 1")
    for host in ("macos", "linux"):
        entries = defaults.get(host)
        require(isinstance(entries, dict), f"missing {host} app defaults")
        required = ACTIONS if host == "linux" else ACTIONS[1:]
        for action in required:
            command = entries.get(action, {}).get("command")
            require(isinstance(command, list) and command and all(isinstance(arg, str) for arg in command), f"{host}.{action} command invalid")


def check_lua_syntax() -> None:
    nvim = shutil.which("nvim")
    luac = shutil.which("luac5.4") or shutil.which("luac")
    paths = (ROOT / "host/hammerspoon-adv360.lua", ROOT / "host/hyprland-adv360.lua", ROOT / "host/nvim-adv360.lua")
    if nvim:
        for path in paths:
            expression = f"assert(loadfile({json.dumps(str(path))}))"
            result = subprocess.run([nvim, "--headless", "-u", "NONE", "-c", "lua " + expression, "-c", "qa"], capture_output=True, text=True)
            require(result.returncode == 0, f"{path}: Lua syntax error: {result.stderr}")
        return
    if luac:
        for path in paths:
            result = subprocess.run([luac, "-p", str(path)], capture_output=True, text=True)
            require(result.returncode == 0, f"{path}: Lua syntax error: {result.stderr}")
        return
    require(not os.environ.get("CI"), "CI requires a Lua syntax parser (nvim or luac)")
    print("SKIP Lua syntax parser outside CI: nvim/luac absent")


def check_build_and_docs() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text()
    west = (ROOT / "config/west.yml").read_text()
    makefile = (ROOT / "Makefile").read_text()
    build = (ROOT / "bin/build.sh").read_text()
    workflow = (ROOT / ".github/workflows/build.yml").read_text()
    require(PINNED_IMAGE in dockerfile, "build image is not digest pinned")
    require(f"revision: {PINNED_ZMK}" in west, "ZMK revision is not commit pinned")
    for token in ("CONFIG_HASH", "DIRTY_SUFFIX", "adv360-zmk-build:local"):
        require(token in makefile, f"Makefile provenance missing {token}")
    require("build-manifest.json" in build and "timestamp" not in build.lower(), "build outputs are not deterministic")
    require(".DEFAULT_GOAL := all" in makefile, "make must default to both firmware halves")
    require("lua5.4" in workflow, "CI must install a Lua syntax parser")
    require(build.count("-S studio-rpc-usb-uart") == 1 and build.count("-DCONFIG_ZMK_STUDIO=y") == 1,
            "local build must enable ZMK Studio only on the left/central half")
    require(workflow.count("-S studio-rpc-usb-uart") == 1 and workflow.count("-DCONFIG_ZMK_STUDIO=y") == 1,
            "CI must enable ZMK Studio only on the left/central half")

    board = (ROOT / "config/boards/arm/adv360/adv360.dtsi").read_text()
    layouts = (ROOT / "config/boards/arm/adv360/adv360-layouts.dtsi").read_text()
    require("zmk,physical-layout = &physical_layout0" in board, "board lacks selected ZMK Studio physical layout")
    require('compatible = "zmk,physical-layout"' in layouts and "keys" in layouts,
            "ZMK Studio physical layout lacks key geometry")

    readme = (ROOT / "README.md").read_text()
    protocol = (ROOT / "host/PROTOCOL.md").read_text()
    agent_contract = (ROOT / "AGENTS.md").read_text()
    optimization_log = (ROOT / "docs/optimization-log.md").read_text()
    for token in ("Hammerspoon", "Alt+F13", "Alt+F20", "scroll", "Bluetooth", "seven"):
        require(token.lower() in (readme + protocol).lower(), f"documentation missing {token}")
    for token in ("ASDF", "JKL;", "G", "H", "hold-preferred", "170 ms", "20/20 ms", "make verify", "make"):
        require(token in agent_contract, f"agent contract missing {token}")
    for token in ("speed-profile candidate", "independent spec re-review passed", "macro output errors", "accept / revert / iterate"):
        require(token in optimization_log, f"optimization log missing {token}")
    require("All 21 literal macros use 20/20 ms timing" in readme, "README speed-macro inventory is stale")
    require("ZMK Studio" in readme and "SYS + U" in readme and "Restore Stock Settings" in readme,
            "README lacks ZMK Studio connection/unlock/persistence guidance")
    require("SYS + U" in agent_contract and "Studio edits" in agent_contract and "ZMK Studio remains disabled" not in agent_contract,
            "agent contract contradicts ZMK Studio support")
    require((ROOT / "docs/7-day-field-test.md").exists(), "field-test documentation missing")


def check_repository() -> None:
    require(sys.version_info >= (3, 9), "Python 3.9 or newer is required")
    check_protocol()
    check_keymap()
    check_hammerspoon(ROOT / "host/hammerspoon-adv360.lua")
    check_hyprland()
    check_nvim(ROOT / "host/nvim-adv360.lua", "repository Neovim")
    check_karabiner(read_json(ROOT / "host/karabiner-adv360.json"), "repository Karabiner")
    check_apps()
    check_lua_syntax()
    check_build_and_docs()
    print("PASS protocol, Hammerspoon, Hyprland, Neovim, Karabiner, apps, build, and docs")


def check_active_macos() -> None:
    hammerspoon = Path.home() / ".hammerspoon/init.lua"
    nvim = Path.home() / ".config/nvim/init.lua"
    karabiner = Path.home() / ".config/karabiner/karabiner.json"
    require(hammerspoon.exists() and "hammerspoon-adv360.lua" in hammerspoon.read_text(), "active Hammerspoon does not load the Advantage360 adapter")
    require(nvim.exists() and "nvim-adv360.lua" in nvim.read_text(), "active Neovim does not load the Advantage360 module")
    require(karabiner.exists(), "active Karabiner configuration missing")
    check_karabiner(read_json(karabiner), "active Karabiner")

    hs = shutil.which("hs")
    require(hs is not None, "Hammerspoon CLI 'hs' is unavailable")
    status = subprocess.run([hs, "-c", "return ADV360_STATUS and ADV360_STATUS.ready and ADV360_STATUS.protocol or 'missing'"], capture_output=True, text=True)
    require(status.returncode == 0 and "F13-F20/v1" in status.stdout, f"Hammerspoon runtime adapter inactive: {status.stderr or status.stdout}")
    aerospace = subprocess.run([hs, "-c", "return hs.application.get('AeroSpace') == nil"], capture_output=True, text=True)
    require(aerospace.returncode == 0 and "true" in aerospace.stdout.lower(), "AeroSpace is running alongside Hammerspoon")
    print("PASS active Hammerspoon, Karabiner, Neovim, and exclusive window-manager ownership")


def check_active_linux() -> None:
    hypr = Path.home() / ".config/hypr/hyprland.lua"
    nvim = Path.home() / ".config/nvim/init.lua"
    require(hypr.exists() and "hyprland-adv360.lua" in hypr.read_text(), "active Hyprland Lua does not load Advantage360")
    require(nvim.exists() and "nvim-adv360.lua" in nvim.read_text(), "active Neovim does not load Advantage360")
    print("PASS active Hyprland and Neovim includes")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--require-active", action="store_true", help="also verify installed host files and running services")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        check_repository()
        if args.require_active:
            if platform.system() == "Darwin":
                check_active_macos()
            elif platform.system() == "Linux":
                check_active_linux()
            else:
                raise AssertionError(f"unsupported active host: {platform.system()}")
    except (AssertionError, json.JSONDecodeError, OSError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("WORKFLOW VERIFY PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
