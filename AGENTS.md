# AGENTS.md — Advantage360 repository contract

## Scope

This repository owns the Kinesis Advantage360 Pro firmware, its F13-F20 host
protocol, macOS AeroSpace integration, Linux Hyprland integration, Neovim
bindings, and physical acceptance tooling.

## Authoritative production-candidate contract

- The keymap has exactly six layers, in this order:
  `BASE`, `NAV`, `SYM`, `NUM`, `GLOBAL`, `SYS`.
- Every layer has physical row counts `[14, 14, 18, 14, 16]`, totaling 76.
- No layer may contain `&none`; deliberate `&trans` is allowed and required for
  momentary-layer reachability and modifier composition.
- BASE isolated taps are plain US QWERTY. G and H are active letters.
- Home-row mods are bilateral:
  - `ASDF` = GUI, Alt, Ctrl, Shift
  - `JKL;` = Shift, Ctrl, Alt, GUI
- HRMs remain balanced at 180 ms, quick-tap 150 ms, prior-idle 120 ms, with
  opposite-half triggers and `hold-trigger-on-release`.
- The only timed layer thumbs are:
  - Esc/NAV
  - Tab/SYM
  - Caps Word/NUM
  - Alt+F13/GLOBAL
- These use hold-preferred behavior with a 170 ms tapping term.
- Backspace, Delete, Enter, and Space are plain keys, never layer-taps.
- There is one BASE typing combo: Q+W -> Escape. It is BASE-only, 35 ms, and
  requires 80 ms prior idle.
- Protected SYS-only Bluetooth-clear and bootloader combos remain separate from
  the typing-combo inventory.
- Layers are momentary; do not add `&tog` without explicit user approval and a
  physical trial.
- SYM owns exactly 21 literal macros with 20/20 ms timing.
- NAV owns scroll and mouse-click controls; do not add pointer movement without
  measured need.
- NUM owns F1-F12, the right numpad, and VS Code `F5/F9/F10/F11/F12` on ASDFG.
- GLOBAL preserves the F13-F20 host protocol. `GLOBAL + [` and `GLOBAL + ]`
  must emit Ctrl+F17 and Ctrl+F18.
- SYS owns Bluetooth, output selection, ZMK Studio, media, lighting, and guarded
  maintenance.

## Host ownership

AeroSpace is the only macOS owner of F13-F20 carriers. Do not reintroduce a
Hammerspoon or Karabiner owner. Hyprland owns the Linux side. Firmware emits
host-neutral carriers; host adapters own application, workspace, and window
semantics.

## ZMK Studio

- Studio RPC and USB are enabled only on the left/central build.
- `SYS + U` authorizes Studio only while Studio is requesting authorization.
- `SYS + A` selects USB output.
- Studio edits are persistent runtime overrides, not source changes. Instruct
  users to use Restore Stock Settings before evaluating newly flashed source.
- The right split peripheral must not request `CONFIG_ZMK_USB=y`.

## Bluetooth safety

`SYS + 1..5` selects a profile. The SYS-only `1+2` chord clears the currently
selected profile and is destructive. Never change or invoke it casually. An
idle-dark RGB indicator is not reliable profile evidence.

## Required verification

After any firmware, board, verifier, or documentation change:

```sh
make verify
git diff --check
```

When the active macOS host contract changes or is part of the claim:

```sh
make verify-active
```

After every hold-tap, combo, macro, layer, DTS, Kconfig, or build-input change:

```sh
make clean_firmware
make
cd firmware && shasum -a 256 -c SHA256SUMS
```

The current `scripts/firmware_fingerprint.py` value must equal
`config_sha256` in `firmware/build-manifest.json`. Validate both UF2 files as
non-empty 512-byte-block files with valid UF2 framing.

## Physical acceptance

Build success makes the keymap test-ready, not optimized. Use
`docs/7-day-field-test.md` and `scripts/field_test.py`. Strict acceptance
requires real macOS and Linux sessions, measured aggressive input, no more than
0.5 home-row misfires per hour, zero combo misfires, zero macro output errors,
and the required sustained duration. Migrated logs are not physical evidence
for the new profile.

The decision after the trial is explicitly: accept / revert / iterate.

## Change discipline

- Keep macros literal: no cursor movement, spaces, auto-pairs, or editor state.
- Keep ordinary editor shortcuts composable from modifiers; do not recreate an
  EDIT layer.
- Keep CODE merged into SYM, click/scroll controls in NAV, and media in SYS.
- Keep documentation, tests, verifier expectations, protocol files, and active
  host configuration synchronized.
- Never hand off firmware built from a fingerprint that differs from the final
  source.
- Do not claim physical optimization without a passing fresh field-test log.
