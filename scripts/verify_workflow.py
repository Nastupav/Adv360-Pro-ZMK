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
HAMMERSPOON_CARRIER_QUERY = "local c={}; for _,h in ipairs(hs.hotkey.getHotkeys()) do local m=string.lower(tostring(h.idx or '')..' '..tostring(h.msg or '')); if string.match(m,'f1[3-9]') or string.match(m,'f20') then table.insert(c,m) end end; return hs.json.encode(c)"
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
    layer_nodes = {
        "BASE": "default_layer",
        "NAV": "layer_nav",
        "SYM": "layer_sym",
        "NUM": "layer_num",
        "GLOBAL": "layer_global",
        "SYS": "layer_sys",
    }
    layers = {name: layer_rows(text, node) for name, node in layer_nodes.items()}
    expected_defines = [(name, str(index)) for index, name in enumerate(layer_nodes)]
    actual_defines = re.findall(r"^#define\s+([A-Z][A-Z0-9_]*)\s+(\d+)\s*$", text, re.M)
    require(actual_defines == expected_defines,
            f"layer define inventory mismatch: expected {expected_defines}, got {actual_defines}")
    display_names = re.findall(r'display-name\s*=\s*"([A-Z][A-Z0-9_]*)"\s*;', clean)
    require(display_names == list(layer_nodes),
            f"keymap layer-node inventory mismatch: expected {list(layer_nodes)}, got {display_names}")

    for index, name in enumerate(layer_nodes):
        require(re.search(rf"^#define\s+{name}\s+{index}\s*$", text, re.M) is not None,
                f"{name}: expected layer index {index}")
        bindings = [binding for row in layers[name] for binding in row]
        require(len(bindings) == 76, f"{name}: expected 76 bindings")
        require("&none" not in bindings, f"{name}: dead &none binding remains")

    require("#include <behaviors/studio_unlock.dtsi>" in text, "ZMK Studio unlock behavior is not included")
    require(layers["SYS"][1][9] == "&studio_unlock", "SYS+U must provide ZMK Studio unlock")

    expected_base_home = [
        "&kp ESC", "&hml LGUI A", "&hml LALT S", "&hml LCTRL D", "&hml LSHFT F", "&kp G",
        "&kp LALT", "&kp LCTRL", "&kp LGUI", "&kp RGUI", "&kp RCTRL", "&kp RALT",
        "&kp H", "&hmr RSHFT J", "&hmr RCTRL K", "&hmr RALT L", "&hmr RGUI SEMI", "&kp SQT",
    ]
    require(layers["BASE"][2] == expected_base_home, "BASE bilateral home-row-mod contract changed")

    expected_home = {
        "NAV": {
            "A": "&kp HOME", "S": "&kp PG_DN", "D": "&kp PG_UP", "F": "&kp END",
            "G": "&kp LA(LEFT)", "H": "&kp LA(RIGHT)",
            "J": "&kp LEFT", "K": "&kp DOWN", "L": "&kp UP", ";": "&kp RIGHT",
        },
        "GLOBAL": {
            "A": "&kp LC(LS(F19))", "S": "&kp LC(LS(F20))", "D": "&kp LC(F20)", "F": "&kp LC(F19)",
            "G": "&kp LC(F17)", "H": "&kp LC(F18)",
            "J": "&kp LC(F13)", "K": "&kp LC(F14)", "L": "&kp LC(F15)", ";": "&kp LC(F16)",
        },
    }
    for name, expected in expected_home.items():
        for key, binding in expected.items():
            actual = layers[name][2][HOME_INDEX[key]]
            require(actual == binding, f"{name} {key}: expected {binding}, got {actual}")

    global_top = layers["GLOBAL"][0]
    require(global_top[1:6] + global_top[8:11] == [f"&kp F{number}" for number in range(13, 21)], "GLOBAL workspace carriers differ from F13-F20")
    require(layers["GLOBAL"][4][1:3] == ["&kp LC(F17)", "&kp LC(F18)"],
            "GLOBAL + [ / ] must emit previous/next workspace carriers")
    editor_carriers = ["&kp F21", "&kp F22", "&kp F23", "&kp F24"]
    require(layers["NAV"][1][8:12] == editor_carriers,
            "NAV Y/U/I/O must emit F21-F24 for editor pane focus")
    for name, rows in layers.items():
        carrier_uses = [binding for row in rows for binding in row if binding in editor_carriers]
        require(carrier_uses == (editor_carriers if name == "NAV" else []),
                f"{name}: F21-F24 editor carriers escaped the dedicated NAV bank")

    base_bindings = [binding for row in layers["BASE"] for binding in row]
    base = " ".join(base_bindings)
    expected_thumbs = (
        "&tlt_fast NAV ESC", "&tlt_fast SYM TAB", "&num_caps NUM 0",
        "&tlt_fast GLOBAL LA(F13)",
    )
    for binding in expected_thumbs:
        require(base.count(binding) == 1, f"BASE: expected exactly one {binding}")
    require(len(re.findall(r"&(tlt_fast|num_caps)\b", base)) == 4,
            "BASE must expose exactly four timed thumb layer-taps")
    for binding in ("&kp BSPC", "&kp DEL", "&kp ENTER", "&kp SPACE"):
        require(base_bindings.count(binding) == 1, f"BASE frequent thumb must remain plain: {binding}")
    require("&tlt_safe" not in clean, "frequent thumbs must not use a timed safe hold-tap")
    own_layer_activation_positions = {
        "NAV": (3, 6), "SYM": (3, 7), "NUM": (4, 7), "GLOBAL": (4, 8),
    }
    for name, (row, column) in own_layer_activation_positions.items():
        require(layers[name][row][column] == "&trans",
                f"{name}: own activation thumb must remain transparent/reachable")
    require(base.count("&sk_lazy LGUI") == 1 and base.count("&sk_lazy LCTRL") == 1, "lazy sticky GUI/Ctrl missing")

    for behavior in ("hml", "hmr"):
        body = node_body(text, behavior)
        for token in ('flavor = "balanced"', "tapping-term-ms = <180>", "quick-tap-ms = <150>",
                      "require-prior-idle-ms = <120>", "hold-trigger-on-release"):
            require(token in body, f"{behavior}: missing {token}")
    for behavior in ("tlt_fast", "num_caps"):
        body = node_body(text, behavior)
        require('flavor = "hold-preferred"' in body and "tapping-term-ms = <170>" in body,
                f"{behavior}: expected hold-preferred 170 ms")
    sticky = node_body(text, "sk_lazy")
    for token in ("release-after-ms = <1000>", "quick-release", "lazy", "bindings = <&kp>"):
        require(token in sticky, f"lazy sticky behavior missing {token}")

    combo_nodes = re.findall(r"\b(combo_[a-z0-9_]+)\s*\{(.*?)\};", clean, re.S)
    require(len(combo_nodes) == 3, f"expected 1 typing and 2 maintenance combos, got {len(combo_nodes)}")
    typing_combos = [(name, body) for name, body in combo_nodes if name not in {"combo_bt_clear", "combo_bootloader"}]
    require(len(typing_combos) == 1, "typing combo inventory mismatch")
    combo_map = dict(typing_combos)
    require("key-positions = <15 16>" in combo_map.get("combo_esc", ""),
            "Esc combo must use low-frequency Q+W, not a common home-row bigram")
    require("require-prior-idle-ms = <80>" in combo_map["combo_esc"],
            "Esc combo must require 80 ms prior idle")
    positions: set[tuple[int, ...]] = set()
    fanout: Counter[int] = Counter()
    for name, body in typing_combos:
        require("timeout-ms = <35>" in body, f"{name}: typing combo term must be 35 ms")
        require("layers = <BASE>" in body, f"{name}: typing combo must be BASE-only")
        require(re.search(r"bindings\s*=.*\b(?:LG|LC|LA)\(", body) is None,
                f"{name}: BASE typing combo must remain OS-neutral")
        match = re.search(r"key-positions\s*=\s*<([0-9 ]+)>", body)
        require(match is not None, f"{name}: key positions missing")
        assert match is not None
        pair = tuple(int(value) for value in match.group(1).split())
        require(len(pair) == 2 and pair not in positions, f"{name}: invalid or duplicate key positions {pair}")
        positions.add(pair)
        fanout.update(pair)
    require(max(fanout.values()) == 1, f"typing combo fan-out changed: {dict(fanout)}")

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
        1: ["&trans", "&trans", "&op_lte", "&op_gte", "&op_arrow", "&op_fatarrow", "&trans", "&trans", "&op_and", "&op_or", "&op_walrus", "&op_pow", "&op_floordiv", "&op_scope"],
        3: ["&kp LSHFT", "&ps_eq", "&ps_ne", "&ps_lt", "&ps_le", "&ps_gt", "&trans", "&trans", "&ps_ge", "&op_sql_ne", "&ps_current", "&op_comment", "&kp LT", "&kp RSHFT"],
    }
    for row_index, expected in expected_sym_rows.items():
        require(layers["SYM"][row_index] == expected, f"SYM row {row_index + 1}: speed macro placement changed")
    require(layers["SYM"][4][5:7] == ["&op_eqeq", "&op_neq"],
            "SYM Backspace/Delete must own == and !=")
    require(layers["SYM"][4][9:11] == ["&trans", "&trans"],
            "SYM Enter/Space must remain plain passthrough keys")

    nav = " ".join(binding for row in layers["NAV"] for binding in row)
    for binding in ("&msc SCRL_LEFT", "&msc SCRL_DOWN", "&msc SCRL_UP", "&msc SCRL_RIGHT",
                    "&mkp LCLK", "&mkp RCLK"):
        require(binding in nav, f"NAV pointer binding missing: {binding}")
    require("&mkp MCLK" not in nav, "low-value middle click must not displace the editor/scroll banks")
    require(layers["NAV"][4][11:15] == ["&msc SCRL_LEFT", "&msc SCRL_DOWN", "&msc SCRL_UP", "&msc SCRL_RIGHT"],
            "NAV physical arrow cluster must provide scrolling")
    require("&mmv" not in nav, "production NAV must not include unvalidated pointer movement")

    conf = uncomment((ROOT / "config/adv360.conf").read_text(), marker="#")
    for token in ("CONFIG_ZMK_HID_KEYBOARD_NKRO_EXTENDED_REPORT=y", "CONFIG_ZMK_POINTING=y",
                  "CONFIG_ZMK_STUDIO=n", "CONFIG_ZMK_BACKLIGHT_ON_START=n",
                  "CONFIG_ZMK_RGB_UNDERGLOW_ON_START=n"):
        require(token in conf, f"adv360.conf missing {token}")
    require("CONFIG_ZMK_COMBO_MAX_COMBOS_PER_KEY" not in conf, "single-combo profile must use default fan-out")
    require("&tog" not in clean, "production layers must be momentary, not toggled")
    print("PASS six-layer geometry, HRMs, one combo, four timed thumbs, thumb macros, editor carriers, scrolling, Studio, and power defaults")


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


def aerospace_bindings(text: str, label: str) -> dict[str, str]:
    try:
        section = text.split("[mode.main.binding]", 1)[1]
    except IndexError as error:
        raise AssertionError(f"{label}: missing mode.main.binding") from error
    section = section.split("\n[", 1)[0]
    bindings: dict[str, str] = {}
    for raw in section.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        match = re.fullmatch(r"([a-z0-9-]+)\s*=\s*(['\"])(.*?)\2", line)
        require(match is not None, f"{label}: cannot parse binding line: {raw}")
        assert match is not None
        key, value = match.group(1), match.group(3)
        require(key not in bindings, f"{label}: duplicate binding {key}")
        bindings[key] = value
    return bindings


def check_aerospace(path: Path, label: str) -> None:
    text = path.read_text()
    require("F13-F24" not in text and not re.search(r"\bF2[1-4]\b", text, re.I), f"{label}: retired F21-F24 carrier remains")
    for token in (
        "start-at-login = true",
        "auto-reload-config = true",
        "automatically-unhide-macos-hidden-apps = true",
        "[workspace-to-monitor-force-assignment]",
        "PG32UCDM",
        "P34WD-40",
    ):
        require(token in text, f"{label}: missing {token}")

    bindings = aerospace_bindings(text, label)

    expected: dict[str, str] = {}
    for slot in range(1, 9):
        key = 12 + slot
        expected[f"f{key}"] = f"workspace {slot}"
        expected[f"shift-f{key}"] = f"move-node-to-workspace --focus-follows-window {slot}"
    for slot, direction in enumerate(("left", "down", "up", "right"), start=13):
        expected[f"ctrl-f{slot}"] = f"focus {direction}"
        expected[f"ctrl-shift-f{slot}"] = f"move {direction}"
    expected.update({
        "ctrl-f17": "workspace --wrap-around prev",
        "ctrl-f18": "workspace --wrap-around next",
        "ctrl-f19": "fullscreen",
        "ctrl-f20": "layout floating tiling",
        "ctrl-shift-f19": "close",
        "ctrl-shift-f20": "layout h_tiles v_tiles",
    })
    action_path = "__ADV360_ACTION__" if "__ADV360_ACTION__" in text else str(Path.home() / ".local/bin/adv360-action")
    for slot, action in enumerate(ACTIONS, start=13):
        expected[f"alt-f{slot}"] = f"exec-and-forget {action_path} {action}"
    require(bindings == expected, f"{label}: binding contract mismatch")


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
    pattern = re.compile(r"vim\.keymap\.set\('([nit])',\s*'([^']+)',\s*'([^']+)'")
    for mode, lhs, rhs in pattern.findall(clean):
        key = (mode, lhs)
        require(key not in mappings, f"{path}: duplicate mapping for {mode} {lhs}")
        mappings[key] = rhs
    return mappings


def check_nvim(path: Path, label: str) -> None:
    mappings = parse_nvim_maps(path)
    directions = ((21, "h", "H"), (22, "j", "J"), (23, "k", "K"), (24, "l", "L"))
    expected: dict[tuple[str, str], str] = {}
    for number, direction, move in directions:
        carrier = f"<F{number}>"
        expected[("n", carrier)] = f"<C-w>{direction}"
        expected[("i", carrier)] = f"<C-o><C-w>{direction}"
        expected[("t", carrier)] = rf"<C-\\><C-n><C-w>{direction}"
        physical = {21: "J", 22: "K", 23: "L", 24: ";"}[number]
        expected[("n", f"<leader>w{physical}")] = f"<C-w>{move}"
    require(mappings == expected, f"{label}: mappings differ from the F21-F24 editor-pane contract")
    require("<C-;>" not in path.read_text(), f"{label}: terminal-ambiguous Ctrl+; mapping remains")


def check_vscode(path: Path, label: str, *, allow_extra: bool = False) -> None:
    try:
        entries = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise AssertionError(f"{label}: cannot read keybindings: {error}") from error
    require(isinstance(entries, list), f"{label}: keybindings root must be an array")
    expected = [
        {"key": "f21", "command": "workbench.action.focusLeftGroup"},
        {"key": "f22", "command": "workbench.action.focusBelowGroup"},
        {"key": "f23", "command": "workbench.action.focusAboveGroup"},
        {"key": "f24", "command": "workbench.action.focusRightGroup"},
    ]
    if not allow_extra:
        require(entries == expected, f"{label}: F21-F24 editor-pane bindings differ from the firmware contract")
        return

    managed_keys = {entry["key"] for entry in expected}
    managed: dict[str, dict[str, Any]] = {}
    for entry in entries:
        require(isinstance(entry, dict), f"{label}: every keybinding must be an object")
        key = entry.get("key")
        if key not in managed_keys:
            continue
        require(key not in managed, f"{label}: duplicate or conflicting {key} binding")
        managed[key] = entry
    require([managed.get(entry["key"]) for entry in expected] == expected,
            f"{label}: installed F21-F24 editor-pane bindings differ from the firmware contract")


def check_apps() -> None:
    defaults = read_json(ROOT / "host/apps.defaults.json")
    require(defaults.get("schema") == 1, "app defaults schema must be 1")
    for host in ("macos", "linux"):
        entries = defaults.get(host)
        require(isinstance(entries, dict), f"missing {host} app defaults")
        for action in ACTIONS:
            command = entries.get(action, {}).get("command")
            require(isinstance(command, list) and command and all(isinstance(arg, str) for arg in command), f"{host}.{action} command invalid")


def check_hammerspoon_runtime(hs: str) -> None:
    try:
        result = subprocess.run([hs, "-c", HAMMERSPOON_CARRIER_QUERY], capture_output=True, text=True, timeout=5)
    except subprocess.TimeoutExpired as error:
        raise AssertionError("Hammerspoon runtime carrier-registry check timed out") from error
    require(result.returncode == 0, f"Hammerspoon runtime carrier-registry check failed: {result.stderr or result.stdout}")
    try:
        conflicts = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise AssertionError("Hammerspoon runtime carrier registry returned invalid JSON") from error
    require(isinstance(conflicts, list) and all(isinstance(item, str) for item in conflicts),
            "Hammerspoon runtime carrier registry has invalid shape")
    require(not conflicts, f"Hammerspoon still registers F13-F20 hotkeys: {conflicts}")


def check_karabiner_carrier_conflicts(data: dict[str, Any], label: str) -> None:
    profiles = data.get("profiles")
    require(isinstance(profiles, list) and len(profiles) > 0, f"{label}: no profiles")
    assert isinstance(profiles, list) and profiles
    active = [profile for profile in profiles if isinstance(profile, dict) and profile.get("selected")]
    if not active:
        require(isinstance(profiles[0], dict), f"{label}: fallback profile is not an object")
        assert isinstance(profiles[0], dict)
        active = [profiles[0]]
    conflicts: list[str] = []
    carriers = {f"f{number}" for number in range(13, 21)}

    def collect_carriers(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if key == "key_code" and isinstance(child, str) and child.lower() in carriers:
                    conflicts.append(f"{child_path}={child.lower()}")
                collect_carriers(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                collect_carriers(child, f"{path}[{index}]")

    for index, profile in enumerate(active):
        require(isinstance(profile, dict), f"{label}: active profile is not an object")
        collect_carriers(profile, f"active_profile[{index}]")
    require(not conflicts, f"{label}: Karabiner active profile rewrites F13-F20: {conflicts}")


def check_lua_syntax() -> None:
    nvim = shutil.which("nvim")
    luac = shutil.which("luac5.4") or shutil.which("luac")
    paths = (ROOT / "host/hyprland-adv360.lua", ROOT / "host/nvim-adv360.lua")
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
    left_defconfig = (ROOT / "config/boards/arm/adv360/adv360_left_defconfig").read_text()
    right_defconfig = (ROOT / "config/boards/arm/adv360/adv360_right_defconfig").read_text()
    require("zmk,physical-layout = &physical_layout0" in board, "board lacks selected ZMK Studio physical layout")
    require('compatible = "zmk,physical-layout"' in layouts and "keys" in layouts,
            "ZMK Studio physical layout lacks key geometry")
    require("CONFIG_ZMK_USB=y" in left_defconfig, "central half must keep USB enabled")
    require("CONFIG_ZMK_USB=y" not in right_defconfig,
            "split peripheral must not request unsupported ZMK USB")
    require("CONFIG_ZMK_RGB_UNDERGLOW_AUTO_OFF_IDLE=y" in right_defconfig and
            "CONFIG_ZMK_RGB_UNDERGLOW_AUTO_OFF_IDLE=n" not in right_defconfig,
            "right-half RGB idle policy is stale or battery-hostile")

    readme = (ROOT / "README.md").read_text()
    protocol = (ROOT / "host/PROTOCOL.md").read_text()
    agent_contract = (ROOT / "AGENTS.md").read_text()
    optimization_log = (ROOT / "docs/optimization-log.md").read_text()
    for token in ("AeroSpace", "Alt+F13", "Alt+F20", "scroll", "Bluetooth", "seven"):
        require(token.lower() in (readme + protocol).lower(), f"documentation missing {token}")
    require("AeroSpace owns macOS" in readme and "AeroSpace owns macOS" in protocol,
            "documentation does not declare AeroSpace as the macOS owner")
    require((ROOT / "host/macos/aerospace.toml").exists(), "repository AeroSpace adapter missing")
    require(not (ROOT / "host/hammerspoon-adv360.lua").exists() and not (ROOT / "host/karabiner-adv360.json").exists(),
            "retired macOS protocol adapters remain in the supported host tree")
    for token in (
        "ASDF", "JKL;", "G and H are active", "six layers", "one BASE typing combo",
        "hold-preferred", "170 ms", "35 ms", "20/20 ms", "zero combo misfires", "make verify", "make",
    ):
        require(token in agent_contract, f"agent contract missing {token}")
    for token in (
        "speed-profile candidate", "independent spec re-review passed", "macro output errors",
        "six-layer production candidate", "accept / revert / iterate",
    ):
        require(token in optimization_log, f"optimization log missing {token}")
    for token in (
        "Six-layer architecture", "no `&none`", "only BASE typing combo", "SYM owns all 21",
        "NAV", "SYS", "35 ms", "20/20 ms",
    ):
        require(token in readme, f"README redesign documentation missing {token}")
    require("ZMK Studio" in readme and "SYS + U" in readme and "Restore Stock Settings" in readme,
            "README lacks ZMK Studio connection/unlock/persistence guidance")
    require("SYS + U" in agent_contract and "Studio edits" in agent_contract and "ZMK Studio remains disabled" not in agent_contract,
            "agent contract contradicts ZMK Studio support")
    require((ROOT / "docs/7-day-field-test.md").exists(), "field-test documentation missing")


def check_repository() -> None:
    require(sys.version_info >= (3, 9), "Python 3.9 or newer is required")
    check_protocol()
    check_keymap()
    check_aerospace(ROOT / "host/macos/aerospace.toml", "repository AeroSpace")
    check_hyprland()
    check_nvim(ROOT / "host/nvim-adv360.lua", "repository Neovim")
    check_vscode(ROOT / "host/vscode-adv360.json", "repository VS Code")
    check_apps()
    check_lua_syntax()
    check_build_and_docs()
    print("PASS protocol, AeroSpace, Hyprland, Neovim, VS Code, apps, build, and docs")


def check_active_macos() -> None:
    home = Path.home()
    aerospace_config = home / ".config/aerospace/aerospace.toml"
    nvim = home / ".config/nvim/init.lua"
    vscode = home / "Library/Application Support/Code/User/keybindings.json"
    hammerspoon = home / ".hammerspoon/init.lua"
    karabiner = home / ".config/karabiner/karabiner.json"
    action_link = home / ".local/bin/adv360-action"

    require(not (home / ".aerospace.toml").exists(), "legacy ~/.aerospace.toml would create config ambiguity")
    require(aerospace_config.exists(), "active AeroSpace configuration missing")
    expected = (ROOT / "host/macos/aerospace.toml").read_text().replace("__ADV360_ACTION__", str(action_link))
    require(aerospace_config.read_text() == expected, "active AeroSpace config differs from repository source")
    check_aerospace(aerospace_config, "active AeroSpace")
    require(action_link.is_symlink() and action_link.resolve() == (ROOT / "scripts/adv360_action.py").resolve(), "active adv360-action link is missing or stale")
    require(nvim.exists() and "nvim-adv360.lua" in nvim.read_text(), "active Neovim does not load the Advantage360 module")
    require(vscode.exists(), "active VS Code keybindings are missing")
    check_vscode(vscode, "active VS Code", allow_extra=True)

    if hammerspoon.exists():
        hammer_text = hammerspoon.read_text()
        require("ADV360 HOST ADAPTER" not in hammer_text and "hammerspoon-adv360.lua" not in hammer_text,
                "Hammerspoon still loads the retired Advantage360 adapter")
    if karabiner.exists():
        raw = karabiner.read_text()
        require("ADV360 normalize F14/F15 for Hammerspoon" not in raw and "ADV360 WM F21-F24" not in raw,
                "Karabiner still contains a retired Advantage360 protocol rule")
        check_karabiner_carrier_conflicts(read_json(karabiner), "active Karabiner")

    hammerspoon_process = subprocess.run(["/usr/bin/pgrep", "-x", "Hammerspoon"], capture_output=True, text=True)
    if hammerspoon_process.returncode == 0:
        hs = shutil.which("hs")
        require(hs is not None, "Hammerspoon is running but its CLI is unavailable for ownership verification")
        assert hs is not None
        check_hammerspoon_runtime(hs)

    aerospace = shutil.which("aerospace")
    require(aerospace is not None, "AeroSpace CLI is unavailable")
    assert aerospace is not None

    def run_aerospace(*arguments: str) -> str:
        result = subprocess.run([aerospace, *arguments], capture_output=True, text=True)
        require(result.returncode == 0, f"AeroSpace runtime check failed ({' '.join(arguments)}): {result.stderr or result.stdout}")
        return result.stdout

    loaded_config_path = Path(run_aerospace("config", "--config-path").strip()).resolve(strict=False)
    require(loaded_config_path == aerospace_config.resolve(strict=False),
            f"AeroSpace server loaded unexpected config path: {loaded_config_path}")
    run_aerospace("reload-config", "--dry-run")
    run_aerospace("reload-config")
    loaded_bindings = json.loads(run_aerospace("config", "--get", "mode.main.binding", "--json"))
    require(isinstance(loaded_bindings, dict), "AeroSpace loaded binding table is not an object")
    require(all(isinstance(key, str) and isinstance(value, str) for key, value in loaded_bindings.items()),
            "AeroSpace loaded binding table contains non-string entries")
    expected_bindings = aerospace_bindings(aerospace_config.read_text(), "active AeroSpace")
    normalized_loaded = {key: " ".join(value.split()) for key, value in loaded_bindings.items()}
    normalized_expected = {key: " ".join(value.split()) for key, value in expected_bindings.items()}
    require(normalized_loaded == normalized_expected, "AeroSpace runtime bindings differ from the installed repository config")

    workspaces = run_aerospace("list-workspaces", "--all").split()
    require(workspaces == [str(number) for number in range(1, 11)], f"unexpected active workspaces: {workspaces}")

    monitor_lines = run_aerospace("list-monitors").splitlines()
    monitor_ids: dict[str, str] = {}
    for line in monitor_lines:
        parts = [part.strip() for part in line.split("|", 1)]
        if len(parts) == 2:
            monitor_ids[parts[1]] = parts[0]
    require("PG32UCDM" in monitor_ids and "P34WD-40" in monitor_ids, f"expected monitors not active: {monitor_lines}")
    primary = run_aerospace("list-workspaces", "--monitor", monitor_ids["PG32UCDM"]).split()
    secondary = run_aerospace("list-workspaces", "--monitor", monitor_ids["P34WD-40"]).split()
    require(primary == ["1", "2", "3", "4", "5"], f"PG32UCDM workspace assignment mismatch: {primary}")
    require(secondary == ["6", "7", "8", "9", "10"], f"P34WD-40 workspace assignment mismatch: {secondary}")
    print("PASS active AeroSpace runtime parity, exclusive ownership, monitor assignment, Neovim include, and installed VS Code keybinding-file parity")


def check_active_linux() -> None:
    hypr = Path.home() / ".config/hypr/hyprland.lua"
    nvim = Path.home() / ".config/nvim/init.lua"
    vscode = Path.home() / ".config/Code/User/keybindings.json"
    require(hypr.exists() and "hyprland-adv360.lua" in hypr.read_text(), "active Hyprland Lua does not load Advantage360")
    require(nvim.exists() and "nvim-adv360.lua" in nvim.read_text(), "active Neovim does not load Advantage360")
    require(vscode.exists(), "active VS Code keybindings are missing")
    check_vscode(vscode, "active VS Code", allow_extra=True)
    print("PASS active Hyprland and Neovim includes plus installed VS Code keybinding-file parity")


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
