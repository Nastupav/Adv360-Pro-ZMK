#!/usr/bin/env python3
"""Render config/adv360.keymap as ASCII layer diagrams.

The README embeds this output between BEGIN/END markers, so the documentation
is generated from the keymap rather than maintained alongside it.

    bin/render_keymap.py            # print diagrams
    bin/render_keymap.py --check    # non-zero exit if README is stale
    bin/render_keymap.py --write    # regenerate the README block
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYMAP = ROOT / "config" / "adv360.keymap"
MACROS = ROOT / "config" / "macros.dtsi"
README = ROOT / "README.md"

MACRO_CELL = 8  # grid labels are truncated to this many characters

BEGIN = "<!-- BEGIN GENERATED LAYERS -->"
END = "<!-- END GENERATED LAYERS -->"

# Physical rows as (left positions, left thumbs, right thumbs, right positions).
ROWS = [
    (range(0, 7), [], [], range(7, 14)),
    (range(14, 21), [], [], range(21, 28)),
    (range(28, 35), [35, 36], [37, 38], range(39, 46)),
    (range(46, 52), [52], [53], range(54, 60)),
    (range(60, 65), [65, 66, 67], [68, 69, 70], range(71, 76)),
]

KEY = {
    "EQUAL": "=", "MINUS": "-", "UNDER": "_", "PLUS": "+",
    "GRAVE": "`", "TILDE": "~", "BSLH": "\\", "PIPE": "|",
    "SEMI": ";", "COLON": ":", "SQT": "'", "DQT": '"',
    "COMMA": ",", "DOT": ".", "FSLH": "/", "QMARK": "?",
    "EXCL": "!", "AT": "@", "HASH": "#", "DLLR": "$", "PRCNT": "%",
    "CARET": "^", "AMPS": "&", "ASTRK": "*",
    "LPAR": "(", "RPAR": ")", "LBKT": "[", "RBKT": "]",
    "LBRC": "{", "RBRC": "}", "LT": "<", "GT": ">",
    "N0": "0", "N1": "1", "N2": "2", "N3": "3", "N4": "4",
    "N5": "5", "N6": "6", "N7": "7", "N8": "8", "N9": "9",
    "LEFT": "<-", "RIGHT": "->", "UP": "^", "DOWN": "v",
    "BSPC": "Bspc", "DEL": "Del", "ENTER": "Ent", "SPACE": "Spc",
    "ESC": "Esc", "TAB": "Tab", "INS": "Ins", "HOME": "Home", "END": "End",
    "PG_UP": "PgUp", "PG_DN": "PgDn",
    "LSHFT": "Shft", "RSHFT": "Shft", "LCTRL": "Ctrl", "RCTRL": "Ctrl",
    "LALT": "Alt", "RALT": "Alt", "LGUI": "Cmd", "RGUI": "Cmd",
    "C_PREV": "Prev", "C_NEXT": "Next", "C_PP": "Play",
    "C_MUTE": "Mute", "C_VOL_UP": "Vol+", "C_VOL_DN": "Vol-",
    "C_BRI_UP": "Lum+", "C_BRI_DN": "Lum-", "C_STOP": "Stop",
    "C_EJECT": "Ejct", "C_AL_CALC": "Calc", "C_AL_FILES": "File",
    "C_AC_SEARCH": "Srch", "C_AL_LOCK": "Lock", "GLOBE": "Lang",
    "PSCRN": "PrtSc", "SLCK": "ScLk", "PAUSE_BREAK": "Paus",
    "K_APP": "Menu", "CAPS": "Caps", "KP_NUM": "#Num",
}

MOD_SHORT = {"LGUI": "G", "RGUI": "G", "LCTRL": "C", "RCTRL": "C",
             "LALT": "A", "RALT": "A", "LSHFT": "S", "RSHFT": "S"}

MOD_WRAP = {"LC": "C-", "LS": "S-", "LA": "A-", "LG": "G-",
            "RC": "C-", "RS": "S-", "RA": "A-", "RG": "G-"}

# Keypad keycodes render with a leading '#'.
KP = {"DIVIDE": "/", "MULTIPLY": "*", "MINUS": "-", "PLUS": "+",
      "ENTER": "Ent", "DOT": ".", "EQUAL": "=",
      **{f"N{d}": str(d) for d in range(10)}}

BEHAVIOR_ARG = {
    "BT_SEL": "BT", "BT_NXT": "BT>", "BT_PRV": "BT<", "BT_CLR": "BTclr",
    "BT_DISC": "BTx",
    "OUT_USB": "USB", "OUT_BLE": "BLE", "OUT_TOG": "Out~",
    "BL_TOG": "BL~", "BL_DEC": "BL-", "BL_INC": "BL+",
}


def keyname(tok: str) -> str:
    if tok in KEY:
        return KEY[tok]
    m = re.fullmatch(r"(\w+)\((.*)\)", tok)
    if m and m.group(1) in MOD_WRAP:
        return MOD_WRAP[m.group(1)] + keyname(m.group(2))
    if tok.startswith("KP_"):
        rest = tok[3:]
        return "#" + KP.get(rest, KEY.get(rest, rest.title()))
    return tok


# Keys that only reposition the caret; they are part of the macro but not part
# of the text it produces, so they are omitted from the rendered preview.
CURSOR_KEYS = {"LEFT", "RIGHT", "UP", "DOWN", "HOME", "END"}

# Macros that reposition the caret inside the text they type.
CARET_MACROS = {"m_print", "m_fstring", "m_subexp", "m_psarray", "m_pshash",
                "m_blockcmt"}


def decode_macro(bindings: str) -> str:
    """Turn a macro's `&kp` sequence into the text it types."""
    out = []
    for tok in re.findall(r"&kp\s+([A-Za-z0-9_()]+)", bindings):
        shifted = re.fullmatch(r"LS\((\w+)\)", tok)
        base = shifted.group(1) if shifted else tok
        if base in CURSOR_KEYS:
            continue
        if base == "SPACE":
            out.append(" ")
        elif len(base) == 1 and base.isalpha():
            out.append(base if shifted else base.lower())
        elif base in KEY:
            out.append(KEY[base])
        else:
            out.append(f"<{base}>")
    return "".join(out)


def load_macros() -> tuple[dict[str, str], list[tuple[str, list[str]]]]:
    """Return {label: typed text} and the section groupings from macros.dtsi."""
    if not MACROS.exists():
        return {}, []
    raw = MACROS.read_text()
    texts: dict[str, str] = {}
    sections: list[tuple[str, list[str]]] = []
    current: list[str] = []
    for line in raw.splitlines():
        head = re.match(r"\s*/\* ---- (.+?) -+ \*/", line)
        if head:
            current = []
            sections.append((head.group(1).strip(), current))
            continue
        m = re.match(r"\s*TEXT_MACRO\(\s*(m_\w+)\s*,(.*)\)\s*$", line)
        if m:
            texts[m.group(1)] = decode_macro(m.group(2))
            current.append(m.group(1))
    return texts, sections


MACRO_TEXT, MACRO_SECTIONS = load_macros()


def label(binding: str) -> str:
    parts = binding.split()
    if not parts:
        return ""
    behavior, args = parts[0], parts[1:]
    if behavior in MACRO_TEXT:
        text = MACRO_TEXT[behavior].strip() or MACRO_TEXT[behavior]
        return text if len(text) <= MACRO_CELL else text[: MACRO_CELL - 1] + ">"
    if behavior == "trans":
        return "^^"
    if behavior == "none":
        return "--"
    if behavior == "kp":
        return keyname(args[0])
    if behavior in ("hml", "hmr"):
        return f"{keyname(args[1])}/{MOD_SHORT.get(args[0], args[0])}"
    if behavior == "tlt":
        return f"{keyname(args[1])}/{args[0]}"
    if behavior in ("mo", "to", "tog", "sl"):
        prefix = {"mo": "", "to": "=>", "tog": "~", "sl": "."}[behavior]
        return prefix + args[0]
    if behavior == "caps_word":
        return "Caps"
    if behavior == "key_repeat":
        return "Rept"
    if behavior == "bootloader":
        return "Boot"
    if behavior == "sys_reset":
        return "Rset"
    if behavior in ("bt", "out", "bl"):
        head = BEHAVIOR_ARG.get(args[0], args[0])
        return head + "".join(args[1:])
    if behavior == "rgb_ug":
        return "RGB" if args[0] == "RGB_TOG" else args[0].replace("RGB_", "")
    return behavior


def parse_layers(text: str) -> list[tuple[str, list[str]]]:
    body = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    body = re.sub(r"//[^\n]*", "", body)
    keymap = body[body.index("keymap {") :]
    out = []
    for name, block in re.findall(
        r"(\w+)\s*\{[^{}]*?bindings\s*=\s*<(.*?)>\s*;", keymap, flags=re.S
    ):
        bindings = [b.strip() for b in block.split("&") if b.strip()]
        display = re.search(rf"{name}\s*\{{\s*display-name\s*=\s*\"([^\"]+)\"", keymap)
        out.append((display.group(1) if display else name, bindings))
    return out


def render(name: str, b: list[str]) -> str:
    """Lay the 76 bindings out on the physical grid.

    Each half is 7 columns wide. Row 1 drops the innermost left/right column
    and row 0 drops two, matching the real key field; the left half stays
    left-aligned and the right half stays right-aligned so columns line up.
    The thumb clusters sit in a fixed-width centre gutter.
    """
    labels = [label(x) for x in b]
    w = max(max(len(x) for x in labels), 4) + 2
    gutter = 6 * w + 3

    def cells(idxs) -> str:
        return "".join(labels[i].center(w) for i in idxs)

    lines: list[str] = []
    for left, lthumb, rthumb, right in ROWS:
        left, right = list(left), list(right)
        if lthumb or rthumb:
            mid = (cells(lthumb) + " | " + cells(rthumb)).center(gutter)
        else:
            mid = " " * gutter
        row = (
            cells(left)
            + " " * ((7 - len(left)) * w)
            + mid
            + " " * ((7 - len(right)) * w)
            + cells(right)
        )
        lines.append(row.rstrip())
    return "\n".join(lines)


LEGEND = """`^^` transparent — falls through to the layer below &nbsp;&middot;&nbsp;
`X/S` tap X, hold Shift &nbsp;&middot;&nbsp; `C-` Ctrl `S-` Shift `A-` Alt
`G-` Cmd/Gui &nbsp;&middot;&nbsp; `#` keypad &nbsp;&middot;&nbsp; `=>` switch
base layer &nbsp;&middot;&nbsp; `>` truncated macro (see the reference below)"""


def macro_reference() -> str:
    """Every macro and the exact text it types, grouped as in macros.dtsi."""
    if not MACRO_SECTIONS:
        return ""
    lines = [
        "**Macro reference** — full contents of the `MACRO` layer. A trailing",
        "space is part of the keyword macros. `^` marks where the caret lands",
        "when the macro repositions it.",
        "",
    ]
    for title, names in MACRO_SECTIONS:
        if not names:
            continue
        cells = []
        for n in names:
            cells.append(f"`{MACRO_TEXT[n]}`" + (" ^" if n in CARET_MACROS else ""))
        lines += [f"*{title}*", "", " &nbsp;&middot;&nbsp; ".join(cells), ""]
    return "\n".join(lines).rstrip()


def build() -> str:
    layers = parse_layers(KEYMAP.read_text())
    chunks = [LEGEND]
    for name, bindings in layers:
        chunks.append(f"**{name}**\n\n```text\n" + render(name, bindings) + "\n```")
    ref = macro_reference()
    if ref:
        chunks.append(ref)
    return "\n\n".join(chunks)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    block = build()

    if not (args.check or args.write):
        print(block)
        return 0

    readme = README.read_text()
    if BEGIN not in readme or END not in readme:
        print(f"README is missing the {BEGIN} / {END} markers", file=sys.stderr)
        return 1

    head, rest = readme.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    updated = f"{head}{BEGIN}\n\n{block}\n\n{END}{tail}"

    if args.check:
        if updated != readme:
            print("README layer diagrams are stale; run bin/render_keymap.py --write",
                  file=sys.stderr)
            return 1
        print("README layer diagrams are up to date")
        return 0

    README.write_text(updated)
    print("README layer diagrams regenerated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
