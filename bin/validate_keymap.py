#!/usr/bin/env python3
"""Structural validation for config/adv360.keymap.

Checks that are cheap here and expensive on the keyboard:
  1. Every keymap layer binds exactly KEY_COUNT positions.
  2. The expected layers exist, in the expected order, with matching #defines.
  3. KEYS_L / KEYS_R / THUMBS partition 0..KEY_COUNT-1 exactly once.
  4. hold-trigger-key-positions on each home-row-mod behavior references the
     opposite hand plus the thumbs (never its own hand).
  5. Combo key-positions are in range.
  6. Runtime keymap editing (studio_unlock) is not exposed.
  7. Braces and angle brackets balance.
  8. Every text macro is defined and every defined macro is used.
  9. No dead &none keys.
 10. Every consumer key the keymap binds is actually sendable under the
     consumer usage range selected in adv360.conf.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

KEY_COUNT = 76
EXPECTED_LAYERS = [
    ("layer_mac", "MAC", 0),
    ("layer_win", "WIN", 1),
    ("layer_nav", "NAV", 2),
    ("layer_sym", "SYM", 3),
    ("layer_num", "NUM", 4),
    ("layer_global", "GLOBAL", 5),
    ("layer_sys", "SYS", 6),
    ("layer_nav_win", "NAV_WIN", 7),
    ("layer_macro", "MACRO", 8),
]

ROOT = Path(__file__).resolve().parent.parent
KEYMAP = ROOT / "config" / "adv360.keymap"
MACROS = ROOT / "config" / "macros.dtsi"

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def extract_block(text: str, header_re: str) -> str | None:
    """Return the body of the first `<name> {` block matching header_re."""
    m = re.search(header_re, text)
    if not m:
        return None
    start = text.index("{", m.end() - 1) if "{" not in m.group(0) else m.end() - 1
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : i]
    return None


def parse_int_list(raw: str) -> list[int]:
    return [int(tok) for tok in re.findall(r"\b\d+\b", raw)]


raw = KEYMAP.read_text()
src = strip_comments(raw)

# --- 7. bracket balance -----------------------------------------------------
for open_ch, close_ch in (("{", "}"), ("<", ">")):
    if open_ch == "<":
        # only count angle brackets that delimit property values
        opens = len(re.findall(r"=\s*<", src)) + len(re.findall(r">\s*,\s*<", src))
        closes = len(re.findall(r">\s*;", src)) + len(re.findall(r">\s*,\s*<", src))
    else:
        opens, closes = src.count(open_ch), src.count(close_ch)
    if opens != closes:
        fail(f"unbalanced {open_ch}{close_ch}: {opens} open vs {closes} close")

# --- 6. no runtime keymap editing ------------------------------------------
if "studio_unlock" in src:
    fail("studio_unlock present; git must stay the sole keymap authority")

# --- 2/3. #defines ----------------------------------------------------------
defines = dict(re.findall(r"^#define\s+(\w+)\s+(.+)$", src, flags=re.M))

for _node, name, index in EXPECTED_LAYERS:
    if name not in defines:
        fail(f"missing #define {name}")
    elif defines[name].strip() != str(index):
        fail(f"#define {name} is {defines[name].strip()}, expected {index}")

hands: dict[str, set[int]] = {}
for group in ("KEYS_L", "KEYS_R", "THUMBS"):
    if group not in defines:
        fail(f"missing #define {group}")
        hands[group] = set()
        continue
    values = parse_int_list(defines[group])
    if len(values) != len(set(values)):
        fail(f"{group} contains duplicate positions")
    hands[group] = set(values)

union = hands["KEYS_L"] | hands["KEYS_R"] | hands["THUMBS"]
total = sum(len(v) for v in hands.values())
if total != KEY_COUNT or union != set(range(KEY_COUNT)):
    missing = sorted(set(range(KEY_COUNT)) - union)
    overlap = total - len(union)
    fail(
        f"KEYS_L/KEYS_R/THUMBS must partition 0..{KEY_COUNT - 1}: "
        f"{len(union)} unique, {overlap} overlapping, missing {missing}"
    )

# --- 4. home-row-mod hold-trigger sets --------------------------------------
behaviors = extract_block(src, r"behaviors\s*\{")
if behaviors is None:
    fail("no behaviors node found")
else:
    expected_trigger = {
        "home_row_mod_left": ("KEYS_R", "KEYS_L"),
        "home_row_mod_right": ("KEYS_L", "KEYS_R"),
    }
    for node, (want, forbid) in expected_trigger.items():
        body = extract_block(behaviors, rf"{node}\s*\{{")
        if body is None:
            fail(f"behavior {node} not found")
            continue
        trig = re.search(r"hold-trigger-key-positions\s*=\s*<([^>]*)>", body)
        if not trig:
            fail(f"{node} has no hold-trigger-key-positions")
            continue
        tokens = set(trig.group(1).split())
        if tokens != {want, "THUMBS"}:
            fail(f"{node} hold-trigger set is {sorted(tokens)}, expected [{want}, THUMBS]")
        if forbid in tokens:
            fail(f"{node} allows same-hand ({forbid}) hold resolution")
        if "hold-trigger-on-release" not in body:
            fail(f"{node} is missing hold-trigger-on-release")
        if "require-prior-idle-ms" not in body:
            fail(f"{node} is missing require-prior-idle-ms")

# --- 5. combos --------------------------------------------------------------
# Behaviors that lose data or drop the keyboard off the bus. A combo bound to
# one of these must span both hands, so a fumbled one-handed press can never
# reach it.
DESTRUCTIVE = ("bt BT_CLR", "bt BT_CLR_ALL", "sys_reset", "bootloader")

combos = extract_block(src, r"combos\s*\{")
if combos:
    for node, body in re.findall(r"(\w+)\s*\{(.*?)\}\s*;", combos, flags=re.S):
        pos_match = re.search(r"key-positions\s*=\s*<([^>]*)>", body)
        bind_match = re.search(r"bindings\s*=\s*<\s*&([^>]*)>", body)
        if not pos_match:
            fail(f"combo {node} has no key-positions")
            continue
        positions = parse_int_list(pos_match.group(1))
        for pos in positions:
            if not 0 <= pos < KEY_COUNT:
                fail(f"combo {node} key-position {pos} out of range")

        binding = bind_match.group(1).strip() if bind_match else ""
        if any(binding.startswith(d) for d in DESTRUCTIVE):
            left = [p for p in positions if p in hands["KEYS_L"]]
            right = [p for p in positions if p in hands["KEYS_R"]]
            if not (left and right):
                fail(
                    f"combo {node} triggers &{binding} but its positions "
                    f"{positions} are all on one hand; destructive combos must "
                    f"span both hands"
                )

# --- 1. layer binding counts ------------------------------------------------
keymap = extract_block(src, r"keymap\s*\{")
if keymap is None:
    fail("no keymap node found")
    print("\n".join(f"FAIL: {e}" for e in errors), file=sys.stderr)
    sys.exit(1)

found = re.findall(
    r"(\w+)\s*\{[^{}]*?bindings\s*=\s*<(.*?)>\s*;",
    keymap,
    flags=re.S,
)

if [name for name, _ in found] != [node for node, _, _ in EXPECTED_LAYERS]:
    fail(
        "layer order mismatch:\n"
        f"  found:    {[n for n, _ in found]}\n"
        f"  expected: {[n for n, _, _ in EXPECTED_LAYERS]}"
    )

# Source-level argument counts for behaviors whose arguments are not macros
# that expand to several device-tree cells. bt/bl/rgb_ug are excluded because
# e.g. BT_CLR expands to two cells from one source token.
ARITY = {
    "trans": 0, "none": 0, "caps_word": 0, "key_repeat": 0,
    "bootloader": 0, "sys_reset": 0,
    "kp": 1, "mo": 1, "to": 1, "tog": 1, "sl": 1, "sk": 1, "out": 1,
    "hml": 2, "hmr": 2, "tlt": 2, "sms": 2,
}

# Text macros take no parameters. Collect their labels so a typo in a macro
# name, or a macro used but never defined, fails here.
macro_src = strip_comments(MACROS.read_text()) if MACROS.exists() else ""
defined_macros = set(re.findall(r"TEXT_MACRO\(\s*(m_\w+)", macro_src))
if not defined_macros:
    fail("no text macros found in config/macros.dtsi")
ARITY.update({name: 0 for name in defined_macros})

counts: list[tuple[str, int]] = []
for name, body in found:
    bindings = [b.split() for b in body.split("&") if b.strip()]
    counts.append((name, len(bindings)))
    if len(bindings) != KEY_COUNT:
        fail(
            f"layer {name} has {len(bindings)} bindings, "
            f"expected {KEY_COUNT} ({len(bindings) - KEY_COUNT:+d})"
        )
    for pos, tokens in enumerate(bindings):
        behavior, args = tokens[0], tokens[1:]
        want = ARITY.get(behavior)
        if want is None:
            continue
        if len(args) != want:
            fail(
                f"layer {name} position {pos}: &{behavior} takes {want} "
                f"argument(s), got {len(args)} ({' '.join(tokens)})"
            )

# --- 8. macros are all defined and all used --------------------------------
used_macros = set(re.findall(r"&(m_\w+)", keymap))
for name in sorted(used_macros - defined_macros):
    fail(f"&{name} is used in the keymap but not defined in macros.dtsi")
for name in sorted(defined_macros - used_macros):
    fail(f"&{name} is defined in macros.dtsi but never used")

# --- 9. no dead keys -------------------------------------------------------
# Design rule: every position does something or falls through on purpose.
# &trans is content (it exposes the layer below); &none is wasted space.
dead = {name: [i for i, t in enumerate(b.split() for b in
               [x for x in body.split("&") if x.strip()]) if t[0] == "none"]
        for name, body in found}
for name, positions in dead.items():
    if positions:
        fail(
            f"layer {name} has {len(positions)} dead &none key(s) at "
            f"{positions}; bind them or use &trans"
        )

conf = ROOT / "config" / "adv360.conf"
conf_text = conf.read_text() if conf.exists() else ""

# --- 11. macro length against the BLE report queue -------------------------
# Each &kp in a macro produces a press report and a release report. If a macro
# is longer than the BLE keyboard report queue, ZMK drops the overflow instead
# of erroring, so the macro types a truncated string over Bluetooth and the
# full string over USB. MAX_TAPS is the documented authoring cap; the assert
# below keeps it honest if anyone lowers the queue size.
MAX_TAPS = 15

queue = re.search(
    r"^CONFIG_ZMK_BLE_KEYBOARD_REPORT_QUEUE_SIZE=(\d+)\s*$", conf_text, flags=re.M
)
queue_size = int(queue.group(1)) if queue else 20

if MAX_TAPS * 2 > queue_size:
    fail(
        f"MAX_TAPS is {MAX_TAPS} ({MAX_TAPS * 2} reports) but "
        f"CONFIG_ZMK_BLE_KEYBOARD_REPORT_QUEUE_SIZE is {queue_size}; raise the "
        f"queue or lower the cap"
    )

for name, body in re.findall(
    r"TEXT_MACRO\(\s*(m_\w+)\s*,(.*?)\)\s*$", macro_src, flags=re.M | re.S
):
    taps = len(re.findall(r"&kp\b", body))
    if taps > MAX_TAPS:
        fail(
            f"macro &{name} is {taps} taps ({taps * 2} HID reports), over the "
            f"{MAX_TAPS}-tap cap; shorten it or let an editor snippet do it"
        )

# --- 10. consumer usages are sendable --------------------------------------
# ZMK's basic consumer report can only carry usages 0x00-0xFF. A key bound to
# a higher usage under CONFIG_ZMK_HID_CONSUMER_REPORT_USAGES_BASIC does not
# error anywhere - it just silently does nothing on the host, which is the one
# failure mode this repo's validators exist to catch.
#
# Usages are from USB HID Usage Tables, Consumer Page (0x0C). Any C_* used in
# the keymap must appear here; add the usage when you bind a new one.
CONSUMER_USAGE = {
    "C_BRI_UP": 0x06F, "C_BRI_DN": 0x070,
    "C_NEXT": 0x0B5, "C_PREV": 0x0B6, "C_STOP": 0x0B7, "C_EJECT": 0x0B8,
    "C_PP": 0x0CD, "C_MUTE": 0x0E2, "C_VOL_UP": 0x0E9, "C_VOL_DN": 0x0EA,
    "C_AL_CALC": 0x192, "C_AL_FILES": 0x194, "C_AL_LOCK": 0x19E,
    "C_AC_SEARCH": 0x221,
}
BASIC_MAX_USAGE = 0xFF

full_range = re.search(
    r"^CONFIG_ZMK_HID_CONSUMER_REPORT_USAGES_FULL=y\s*$", conf_text, flags=re.M
) is not None

for name in sorted(set(re.findall(r"&kp\s+(C_\w+)", keymap))):
    usage = CONSUMER_USAGE.get(name)
    if usage is None:
        fail(
            f"&kp {name} has no usage recorded in validate_keymap.py; add it "
            f"to CONSUMER_USAGE so the report-range check can cover it"
        )
    elif usage > BASIC_MAX_USAGE and not full_range:
        fail(
            f"&kp {name} is consumer usage 0x{usage:03X}, above the basic "
            f"range limit of 0x{BASIC_MAX_USAGE:02X}; set "
            f"CONFIG_ZMK_HID_CONSUMER_REPORT_USAGES_FULL=y in adv360.conf or "
            f"the key will silently do nothing"
        )

if errors:
    for e in errors:
        print(f"FAIL: {e}", file=sys.stderr)
    sys.exit(1)

width = max(len(n) for n, _ in counts)
for name, n in counts:
    print(f"  ok  {name:<{width}}  {n} bindings")
print(f"\nadv360.keymap: {len(counts)} layers x {KEY_COUNT} keys, all checks passed")
