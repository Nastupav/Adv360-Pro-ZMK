#!/usr/bin/env python3
"""Cross-check the GLOBAL layer against the host consumers in host/.

The keyboard emits F13-F20 with modifiers; three separate files decide what
those mean. Nothing but this script stops them drifting apart, which is the
exact failure mode where a key silently does nothing on one machine.

Checks:
  1. Every signal the GLOBAL layer emits is handled by all three hosts.
  2. No host binds a signal that is unreachable from the keyboard.
  3. The three hosts handle the same set of signals as each other.
  4. Each host's *command* for a signal matches the documented intent.

Check 4 exists because checks 1-3 only prove a binding is present. macOS ran
`move-workspace-to-monitor` for Ctrl+Shift+F17 for a long time - it moved the
whole workspace to another display while Linux and Windows moved the window to
the adjacent workspace. Every presence check passed the whole time.

Shift-derived signals are reachable without appearing in the keymap: the
layer emits F13, and a pinky Shift turns it into Shift+F13. Those are added
to the reachable set automatically.

The app-launcher and screenshot banks are deliberately excluded from check 4:
Ghostty, wt.exe and a Hyprland variable are all correct answers to "terminal",
so there is no shared intent to compare.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYMAP = ROOT / "config" / "adv360.keymap"
HOSTS = {
    "macos": ROOT / "host" / "macos" / "aerospace.toml",
    "linux": ROOT / "host" / "linux" / "hyprland.conf",
    "windows": ROOT / "host" / "windows" / "adv360-global.ahk",
}

MOD_ORDER = ["C", "A", "S"]

# Slots 2 and 3 of the protocol are named F14/F15 throughout this file, the
# README and the intent table, but they are not sent as F14/F15 any more.
# macOS treats those two keycodes as display brightness at a level below
# application delivery, and does so regardless of modifiers - so every one of
# the fourteen signals containing them fired the brightness OSD alongside the
# real action. Nothing suppresses that but not emitting the keycodes, and
# AeroSpace binds f1-f20 only, so there is no spare function key to move to.
# The keypad range is the one range this keymap never touches.
#
# The canonical signal names stay F14/F15 so the protocol vocabulary, the
# intent table and the documentation are unchanged; only the wire code differs
# per host. Each parser maps its host's spelling back to the canonical name.
WIRE = {
    "keymap":  {"KP_DIVIDE": "F14", "KP_MULTIPLY": "F15"},
    "macos":   {"keypaddivide": "F14", "keypadmultiply": "F15"},
    "linux":   {"KP_Divide": "F14", "KP_Multiply": "F15"},
    "windows": {"NumpadDiv": "F14", "NumpadMult": "F15"},
}
errors: list[str] = []


def sig(mods: set[str], key: str) -> str:
    return "-".join([m for m in MOD_ORDER if m in mods] + [key.upper()])


DIRS = {"F13": "left", "F14": "down", "F15": "up", "F16": "right"}

# Axis and sign matter here - a flipped sign is exactly the kind of drift this
# check exists to catch, so the patterns pin both.
RESIZE = {
    "F13": (r"resize width -", r"resizeactive,\s*-\d+\s+0", r"horizontal.*decrease"),
    "F14": (r"resize height \d", r"resizeactive,\s*0\s+\d", r"vertical.*increase"),
    "F15": (r"resize height -", r"resizeactive,\s*0\s+-\d", r"vertical.*decrease"),
    "F16": (r"resize width \d", r"resizeactive,\s*\d+\s+0", r"horizontal.*increase"),
}

# Signals where a window manager has no equivalent primitive and the binding is
# a deliberate substitute. Listed so they stay visible rather than being
# mistaken for exact parity.
APPROXIMATIONS = {
    ("linux", "C-A-F19"): "Hyprland has no balance command; cycles orientation",
    ("macos", "C-A-F20"): "AeroSpace has no sticky/pin; fullscreens the window",
    ("windows", "C-F19"): "komorebi monocle stands in for fullscreen",
}


def build_intents() -> dict[str, tuple[str, dict[str, str]]]:
    intent: dict[str, tuple[str, dict[str, str]]] = {}
    for n, key in enumerate(["F13", "F14", "F15", "F16",
                             "F17", "F18", "F19", "F20"], start=1):
        intent[key] = (f"workspace-{n}", {
            "macos": rf"workspace {n}\b",
            "linux": rf"workspace,\s*{n}\b",
            "windows": rf"Workspace\({n}\)",
        })
        intent["S-" + key] = (f"move-window-to-workspace-{n}", {
            "macos": rf"move-node-to-workspace {n}\b",
            "linux": rf"movetoworkspace,\s*{n}\b",
            "windows": rf"MoveToWorkspace\({n}\)",
        })
    for key, name in DIRS.items():
        intent["C-" + key] = (f"focus-{name}", {
            "macos": rf"focus {name}\b",
            "linux": rf"movefocus,\s*{name[0]}\b",
            "windows": rf'Focus\("{name}"\)',
        })
        intent["C-S-" + key] = (f"move-window-{name}", {
            "macos": rf"move {name}\b",
            "linux": rf"movewindow,\s*{name[0]}\b",
            "windows": rf'MoveWindow\("{name}"\)',
        })
        mac_r, lin_r, win_r = RESIZE[key]
        intent["C-A-" + key] = (f"resize-{name}", {
            "macos": mac_r, "linux": lin_r, "windows": win_r,
        })
    intent.update({
        "C-F17": ("workspace-prev", {
            "macos": r"workspace prev", "linux": r"workspace,\s*e-1",
            "windows": r'CycleWorkspace\("previous"\)'}),
        "C-F18": ("workspace-next", {
            "macos": r"workspace next", "linux": r"workspace,\s*e\+1",
            "windows": r'CycleWorkspace\("next"\)'}),
        "C-S-F17": ("move-window-to-workspace-prev", {
            "macos": r"move-node-to-workspace .*prev",
            "linux": r"movetoworkspace,\s*e-1",
            "windows": r'cycle-move-to-workspace".*"previous"'}),
        "C-S-F18": ("move-window-to-workspace-next", {
            "macos": r"move-node-to-workspace .*next",
            "linux": r"movetoworkspace,\s*e\+1",
            "windows": r'cycle-move-to-workspace".*"next"'}),
        "C-A-F17": ("focus-monitor-prev", {
            "macos": r"focus-monitor .*prev", "linux": r"focusmonitor,\s*l\b",
            "windows": r'cycle-monitor".*"previous"'}),
        "C-A-F18": ("focus-monitor-next", {
            "macos": r"focus-monitor .*next", "linux": r"focusmonitor,\s*r\b",
            "windows": r'cycle-monitor".*"next"'}),
        "C-A-S-F17": ("move-window-to-monitor-prev", {
            "macos": r"move-node-to-monitor .*prev",
            "linux": r"movewindow,\s*mon:l\b",
            "windows": r'cycle-move-to-monitor".*"previous"'}),
        "C-A-S-F18": ("move-window-to-monitor-next", {
            "macos": r"move-node-to-monitor .*next",
            "linux": r"movewindow,\s*mon:r\b",
            "windows": r'cycle-move-to-monitor".*"next"'}),
        "C-F19": ("fullscreen", {
            "macos": r"fullscreen", "linux": r"fullscreen",
            "windows": r"toggle-monocle"}),
        "C-S-F19": ("close-window", {
            "macos": r"\bclose\b", "linux": r"killactive",
            "windows": r"WinClose"}),
        "C-F20": ("float", {
            "macos": r"layout floating tiling", "linux": r"togglefloating",
            "windows": r"toggle-float"}),
        "C-S-F20": ("toggle-layout", {
            "macos": r"layout horizontal vertical", "linux": r"togglesplit",
            "windows": r"flip-layout"}),
        "C-A-F19": ("balance-layout", {
            "macos": r"balance-sizes", "linux": r"orientationnext",
            "windows": r"retile"}),
        "C-A-F20": ("pin-window", {
            "macos": r"fullscreen", "linux": r"\bpin\b",
            "windows": r"AlwaysOnTop"}),
    })
    return intent


INTENT = build_intents()


def from_keymap() -> set[str]:
    src = re.sub(r"/\*.*?\*/", "", KEYMAP.read_text(), flags=re.S)
    src = re.sub(r"//[^\n]*", "", src)
    block = re.search(
        r"layer_global.*?bindings\s*=\s*<(.*?)>\s*;", src, flags=re.S
    )
    if not block:
        errors.append("no layer_global bindings found")
        return set()
    out = set()
    for binding in re.findall(r"&kp\s+([A-Za-z0-9_()]+)", block.group(1)):
        mods: set[str] = set()
        tok = binding
        while (m := re.fullmatch(r"[LR]([CASG])\((.*)\)", tok)):
            mods.add(m.group(1))
            tok = m.group(2)
        tok = WIRE["keymap"].get(tok, tok)
        if re.fullmatch(r"F1[3-9]|F20", tok):
            out.add(sig(mods, tok))
    return out


def from_aerospace(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        m = re.match(r"\s*((?:ctrl|alt|shift|cmd)(?:-(?:ctrl|alt|shift|cmd))*-)?"
                     r"(f1[3-9]|f20|keypadDivide|keypadMultiply)\s*=\s*(.*)",
                     line, re.I)
        if m:
            names = (m.group(1) or "").rstrip("-").split("-")
            mods = {"ctrl": "C", "alt": "A", "shift": "S"}
            key = WIRE["macos"].get(m.group(2).lower(), m.group(2))
            out[sig({mods[n] for n in names if n in mods}, key)] = m.group(3)
    return out


def from_hyprland(text: str) -> dict[str, str]:
    out = {}
    for m in re.finditer(
            r"^bind\s*=\s*([A-Z ]*),\s*(F1[3-9]|F20|KP_Divide|KP_Multiply)\s*,(.*)$",
            text, re.M):
        names = m.group(1).split()
        mods = {"CTRL": "C", "ALT": "A", "SHIFT": "S"}
        key = WIRE["linux"].get(m.group(2), m.group(2))
        out[sig({mods[n] for n in names if n in mods}, key)] = m.group(3)
    return out


def from_ahk(text: str) -> dict[str, str]:
    out = {}
    for m in re.finditer(
            r"^([\^!+#]*)(F1[3-9]|F20|NumpadDiv|NumpadMult)\s*::(.*)$", text, re.M):
        mods = {"^": "C", "!": "A", "+": "S"}
        key = WIRE["windows"].get(m.group(2), m.group(2))
        out[sig({mods[c] for c in m.group(1) if c in mods}, key)] = m.group(3)
    return out


PARSERS = {"macos": from_aerospace, "linux": from_hyprland, "windows": from_ahk}

emitted = from_keymap()
# A pinky Shift can be added to any emitted signal by hand.
reachable = emitted | {sig(set(s.split("-")[:-1]) | {"S"}, s.split("-")[-1])
                       for s in emitted}

handled: dict[str, dict[str, str]] = {}
for name, path in HOSTS.items():
    if not path.exists():
        errors.append(f"missing host config {path.relative_to(ROOT)}")
        handled[name] = {}
        continue
    handled[name] = PARSERS[name](path.read_text())

for name, cmds in handled.items():
    for missing in sorted(emitted - set(cmds)):
        errors.append(f"{name}: GLOBAL emits {missing} but the host ignores it")
    for extra in sorted(set(cmds) - reachable):
        errors.append(f"{name}: handles {extra}, which the keyboard cannot send")

common = set.union(*(set(c) for c in handled.values())) if handled else set()
for name, cmds in handled.items():
    for gap in sorted(common - set(cmds)):
        errors.append(f"{name}: other hosts handle {gap} but this one does not")

# --- 4. semantics -----------------------------------------------------------
checked = 0
for signal, (intent_name, patterns) in sorted(INTENT.items()):
    for name, pattern in patterns.items():
        cmd = handled.get(name, {}).get(signal)
        if cmd is None:
            continue
        checked += 1
        if not re.search(pattern, cmd, re.I):
            errors.append(
                f"{name}: {signal} should mean '{intent_name}' but runs "
                f"{cmd.strip()!r}; expected something matching /{pattern}/"
            )

if errors:
    for e in errors:
        print(f"FAIL: {e}", file=sys.stderr)
    sys.exit(1)

print(f"  ok  GLOBAL layer emits {len(emitted)} distinct signals")
for name in HOSTS:
    print(f"  ok  {name:<8} handles {len(handled[name])}")
print(f"  ok  {checked} host commands match their documented intent")
for (name, signal), why in sorted(APPROXIMATIONS.items()):
    print(f"  ~~  {name:<8} {signal}: {why}")

print("\nF13-F20 protocol: keymap and all host consumers agree")
