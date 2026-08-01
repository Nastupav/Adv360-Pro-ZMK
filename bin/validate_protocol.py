#!/usr/bin/env python3
"""Cross-check the GLOBAL layer against the host consumers in host/.

The keyboard emits F13-F20 with modifiers; three separate files decide what
those mean. Nothing but this script stops them drifting apart, which is the
exact failure mode where a key silently does nothing on one machine.

Checks:
  1. Every signal the GLOBAL layer emits is handled by all three hosts.
  2. No host binds a signal that is unreachable from the keyboard.
  3. The three hosts handle the same set of signals as each other.

Shift-derived signals are reachable without appearing in the keymap: the
layer emits F13, and a pinky Shift turns it into Shift+F13. Those are added
to the reachable set automatically.
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
errors: list[str] = []


def sig(mods: set[str], key: str) -> str:
    return "-".join([m for m in MOD_ORDER if m in mods] + [key.upper()])


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
        if re.fullmatch(r"F1[3-9]|F20", tok):
            out.add(sig(mods, tok))
    return out


def from_aerospace(text: str) -> set[str]:
    out = set()
    for line in text.splitlines():
        m = re.match(r"\s*((?:ctrl|alt|shift|cmd)(?:-(?:ctrl|alt|shift|cmd))*-)?"
                     r"(f1[3-9]|f20)\s*=", line)
        if m:
            names = (m.group(1) or "").rstrip("-").split("-")
            mods = {"ctrl": "C", "alt": "A", "shift": "S"}
            out.add(sig({mods[n] for n in names if n in mods}, m.group(2)))
    return out


def from_hyprland(text: str) -> set[str]:
    out = set()
    for m in re.finditer(r"^bind\s*=\s*([A-Z ]*),\s*(F1[3-9]|F20)\s*,", text, re.M):
        names = m.group(1).split()
        mods = {"CTRL": "C", "ALT": "A", "SHIFT": "S"}
        out.add(sig({mods[n] for n in names if n in mods}, m.group(2)))
    return out


def from_ahk(text: str) -> set[str]:
    out = set()
    for m in re.finditer(r"^([\^!+#]*)(F1[3-9]|F20)\s*::", text, re.M):
        mods = {"^": "C", "!": "A", "+": "S"}
        out.add(sig({mods[c] for c in m.group(1) if c in mods}, m.group(2)))
    return out


PARSERS = {"macos": from_aerospace, "linux": from_hyprland, "windows": from_ahk}

emitted = from_keymap()
# A pinky Shift can be added to any emitted signal by hand.
reachable = emitted | {sig(set(s.split("-")[:-1]) | {"S"}, s.split("-")[-1])
                       for s in emitted}

handled: dict[str, set[str]] = {}
for name, path in HOSTS.items():
    if not path.exists():
        errors.append(f"missing host config {path.relative_to(ROOT)}")
        handled[name] = set()
        continue
    handled[name] = PARSERS[name](path.read_text())

for name, sigs in handled.items():
    for missing in sorted(emitted - sigs):
        errors.append(f"{name}: GLOBAL emits {missing} but the host ignores it")
    for extra in sorted(sigs - reachable):
        errors.append(f"{name}: handles {extra}, which the keyboard cannot send")

common = set.union(*handled.values()) if handled else set()
for name, sigs in handled.items():
    for gap in sorted(common - sigs):
        errors.append(f"{name}: other hosts handle {gap} but this one does not")

if errors:
    for e in errors:
        print(f"FAIL: {e}", file=sys.stderr)
    sys.exit(1)

print(f"  ok  GLOBAL layer emits {len(emitted)} distinct signals")
for name in sorted(handled):
    print(f"  ok  {name:<8} handles {len(handled[name])}")
print("\nF13-F20 protocol: keymap and all host consumers agree")
