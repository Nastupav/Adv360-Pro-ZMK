# Current overhaul note — 25 September 2026

A new full-repository/current-web review is recorded in
[`overhaul-20260925.md`](overhaul-20260925.md), with the active HRM follow-up in
[`hrm-profile-20260925.md`](hrm-profile-20260925.md). The original 20 September
audit below remains useful historical evidence for the five-layer baseline. The
current profile additionally uses bilateral fast-typing home-row mods while
retaining dedicated modifiers, removes the duplicated macOS app-shortcut bank,
keeps the 300 ms Bluetooth-clear idle gate, and regression-tests the JKL; contract.

# Design and firmware audit — 20 September 2026

## Baseline and scope

The authoritative baseline was the newest working checkout on
`codex/macos-engineering-workflow`, starting at repository commit `66d6b27`.
It already had substantial uncommitted September 6/8 work. Before editing, the
full config/tools/tests/docs/host/build files were archived locally at
`firmware/pre-daily-driver-20260920/working-tree.tar.gz`, with the original Git diff
and status. Existing firmware pairs and host configuration remain intact.
`profiles/previous/` preserves the newest ten-layer keymap and macros; historical
notes are in `docs/history/`. The active keymap is `config/adv360.keymap`.

The previous NUM grid already had the requested physical placement, but NUM
latched via a toggle, used source-dependent number-row digits and kept Space
rather than a thumb 0. NAV's ASDF sent editing shortcuts instead of modifiers.
The old bilateral bootloader combo did not clearly select a physical half.
The previous validator explicitly required the toggle, so validation had to
change along with the behavior rather than merely making the old checks pass.

Board definitions, matrix wiring, radio power, battery reporting, sleep and HID
settings were preserved. Pointing remains compiled in to retain the prior mouse
HID descriptor, although the five-layer profile has no pointer bindings. Old
GLOBAL/EDIT/POINTER/WIN banks are archived; host integration source remains
unchanged and is not installed or removed by this work.

## Exact firmware source

The manifest previously named the mutable `refil/zmk` branch `adv360-z3.5-2`.
The working Docker image and September 8 frozen manifest both resolve to:

- ZMK: `f1d5fc736bdbdde11df0ec77114c6a398ee1252b`.
- Zephyr: `dacab4875df72109b96cc8977547a0dc04875bcd`.

`config/west.yml` now pins that same ZMK commit. This is reproducibility work, not
an engine upgrade. A frozen manifest accompanies each build. The existing
Dockerfile, west process and both-half build entry point are retained.

The following checks used files inside that exact cached vendor source, not
assumptions based on today's upstream documentation:

| Feature | Inspected source | Consequence |
|---|---|---|
| Immediate layers | `app/src/behaviors/behavior_momentary_layer.c` | `&mo` activates on press, deactivates on release; no tapping term |
| Release dispatch | `app/src/keymap.c` | Remembers press-time layer state for the matching release |
| Caps Word | `app/src/behaviors/behavior_caps_word.c`, `app/dts/behaviors/caps_word.dtsi`, binding YAML | Supported; add keypad digits to continue-list because default numeric detection covers only number-row digits |
| Keypad and punctuation | `app/include/dt-bindings/zmk/keys.h` | Required keypad usages exist in this fork |
| Recovery | `app/src/behaviors/behavior_reset.c`, `app/src/behavior.c`, `app/dts/behaviors/reset.dtsi` | Event-source locality routes bootloader/reset to the originating half; direct left/right SYS keys |
| Indicators | `app/src/rgb_underglow.c` | Kinesis effect 4 reports highest layer and sends state to the peripheral |
| Bluetooth / output | vendor headers, config and successful compilation | Five host profiles, retained central connection budget and output switching |

Source links are pinned, for example
[momentary layers](https://github.com/refil/zmk/blob/f1d5fc736bdbdde11df0ec77114c6a398ee1252b/app/src/behaviors/behavior_momentary_layer.c),
[release dispatch](https://github.com/refil/zmk/blob/f1d5fc736bdbdde11df0ec77114c6a398ee1252b/app/src/keymap.c),
[Caps Word](https://github.com/refil/zmk/blob/f1d5fc736bdbdde11df0ec77114c6a398ee1252b/app/src/behaviors/behavior_caps_word.c),
and [reset locality](https://github.com/refil/zmk/blob/f1d5fc736bdbdde11df0ec77114c6a398ee1252b/app/src/behaviors/behavior_reset.c).

## Physical mapping and design choices

`adv360.dtsi` supplies the 76-entry transform; left/right DTS files wire each
matrix and the right applies column offset 10. `adv360-layouts.dtsi` gives exactly
76 matching positions, including tall keys 65/66/69/70 and rotated thumb clusters.
The diagrams use these vendor dimensions, not a generic rectangular keyboard.

Key positions: ASDF = 29/30/31/32; JKL; = 41/42/43/44; UIO = 23/24/25;
M comma period = 55/56/57; NUM hold = left thumb 66; numeric 0 = right thumb 70.
This specifically avoids the common one-column-left YUI/HJK/NM-comma grid.

The user identified large Backspace/Delete and Space/Enter as the easiest thumbs.
NUM gets the large Delete position; displaced Delete moves to adjacent 67 and
right 68. This sacrifices one large editing key for immediate held numeric access.
Backspace, Enter and Space stay plain on BASE. Existing NAV/SYM small middle
thumb holds remain; ordinary modifiers and two Shift keys are preserved.

Five layers are enough because function/media controls fit SYS. The previous
host-protocol and pointer banks would add learning and dependency costs; they
remain available as an archived previous profile. No unrequested host migration
or Windows base toggle is required for remote PowerShell.

NAV ASDF = Ctrl/Option/Command/Shift puts Command and Shift on middle/index
fingers. Word movement, selection and line edges can combine modifiers with
JKL; arrows. Duplicate dedicated motions on the right reduce chording when
selection is unnecessary. Mac commands, terminal behavior and remote Windows
are explicitly distinguished in `editor.md`.

SYM keeps mirrored curly/square/round pairs near ASDF/JKL;, colon on F,
underscore on J, angle brackets on G/H and equals on quote. Individual repeatable
keypresses cover the requested symbols and operator sequences (see cheat sheet).
Multi-character macros are not necessary; snippets and delimiter pairing remain
editor responsibilities. This favors predictable held keys and removes macro
report timing from normal programming. It is a design recommendation, not a
claim of measured ergonomic superiority.

## Host evidence and primary references

The local macOS UCKeyTranslate audit verified keypad digits/operators and ordinary
dot/comma under ABC, US and Czech, and demonstrated why unshifted N1–N0 and keypad
decimal are unsuitable for source-independent NUM. These are layout-table checks;
physical keyboard, app, remote forwarding and held-repeat acceptance remain
separate. No community layout was copied; vendor geometry retains its attribution.

Consulted primary sources:

- [Kinesis repository](https://github.com/KinesisCorporation/Adv360-Pro-ZMK): vendor fork, build, battery-reporting caveat and indicators.
- [ZMK layer behaviors](https://zmk.dev/docs/keymaps/behaviors/layers): general terminology; compatibility checked in the pinned fork. Newer layer-locking features are not assumed.
- [ZMK keycode caveats](https://zmk.dev/docs/keymaps/list-of-keycodes): HID codes depend on host layout and application.
- [ZMK Caps Word](https://zmk.dev/docs/keymaps/behaviors/caps-word): concept and usage, verified against the fork.
- [Apple shortcuts](https://support.apple.com/en-us/102650): Command/Option navigation, selection and input-source shortcuts.
- [VS Code keybindings](https://code.visualstudio.com/docs/configure/keybindings): contexts, layouts and troubleshooting.
- [Apple UCKeyTranslate](https://developer.apple.com/documentation/coreservices/1390584-uckeytranslate): local layout-table translation used by the audit.
- [Kinesis firmware instructions](https://kinesis-ergo.com/wp-content/uploads/Advantage360-Professional-Firmware-Update-Instructions-9.5.24-KB360-PRO.pdf): per-half flashing and physical bootloader recovery.

Documented behavior is identified above. Thumb assignments, five-layer scope and
symbol grouping are recommendations informed by the user's preferences. Hardware
comfort, reliability and editor-specific results are not inferred from popularity
or compilation.
