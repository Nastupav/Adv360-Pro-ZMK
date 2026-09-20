# Validation record · NUM refinement · 8 September 2026

## Delivered revision

Matched firmware prefix: **`adv360-202609081228-66d6b27`**. The suffix identifies
its starting Git revision; the exact modified source is in `-source.tar.gz`.
The previous September 6 pair, source, effective configs and checksums are preserved
in `firmware/rollback-20260906-num/`. Neither pair is claimed to be hardware-tested.

- Only 15 NUM bindings changed. All other layer bindings, host files, board
  definitions and power/USB/Bluetooth settings were compared with the pre-revision
  snapshot and remain unchanged. Both effective `.config` files are byte-identical
  to the previous build's settings.
- NUM: U/I/O = 7/8/9; J/K/L = 4/5/6; M/comma/period = 1/2/3; N = 0;
  slash = decimal; backslash = comma; quote = equals. Thumb editing keys remain.
- `make validate` passed: 22 regression cases, ten 76-key layers, cross-platform
  desktop and editor protocol checks, and both generated reference checks.
- Plain `make` successfully compiled both halves. Current and rollback checksums
  verified; the current source archive matches the working configuration exactly.
- All three actual ZMK simulations passed: NUM toggle/Escape restores U after
  producing 7, immediate Shift and NAV-release behavior, and mouse-button release
  across both POINTER exits. The simulator's frozen dependency manifest is
  **byte-identical** to the firmware build manifest. An initially newer cached
  simulator was replaced for this run by the build's frozen manifest.
- ZMK: `f1d5fc736bdbdde11df0ec77114c6a398ee1252b`; Zephyr:
  `dacab4875df72109b96cc8977547a0dc04875bcd`. Other revisions are in the frozen manifest.
- All ten PNGs use the vendor's 76-position geometry, including stagger, rotations
  and double-height thumbs. Checked inherited contexts, inactive keys and host action
  labels; visually reviewed the overview and enlarged NUM, GLOBAL, SYS and EDIT.
  `docs/layers/manifest.json` records source and artifact fingerprints.

**Hardware flashing is still outstanding.** Use the matching new left/right UF2s
and the acceptance checklist in [setup.md](setup.md). This revision does not change
the HID descriptor or host settings from the September 6 firmware; it does not
itself require another pairing reset if that firmware was already paired.
The original Spotlight and monitor follow-ups below were not changed by this revision.

---

# Historical baseline · 6 September 2026

## Completed

- `make validate`: ten layers × 76 positions; 55 desktop signals and 126 intent
  checks; complete 28-command editor protocol; 13 Python regression cases;
  generated layer-reference consistency.
- Plain `make`: successfully validated and compiled **both** Advantage360 halves
  using the preserved vendor board definitions and firmware branch.
- Actual vendor ZMK `native_posix_64` event simulations passed NUM toggle/Escape
  exit, immediate Shift with a following letter, navigation release after leaving
  NAV, and left/right mouse-button release after both POINTER exit routes.
  These tests use four selected production positions and preserve layer numbers;
  hardware maintenance actions are masked in the simulator. They exercise ZMK
  event/HID state, not USB/Bluetooth transport or physical switch scanning.
- Effective left configuration: pointing, extended NKRO and USB boot protocol
  enabled; host-facing BLE BAS and central peripheral battery fetching/proxy
  disabled. Internal battery sensing remains for the keyboard's indicators.
  Both halves retain the configured sleep/lighting defaults.
- Exact config archive compared byte-for-byte with the working tree. Current
  and rollback package SHA-256 checksums all verified.
- Installed host files match the installer output; repeat preview shows no file
  changes. Backup/restore and refusal to overwrite later edits pass isolated tests.
- AeroSpace successfully reloaded. Workspaces 1–10 and existing window rules remain
  configured; an additional live workspace 11 was left untouched.
- Advantage360 Native was copied using VS Code's profile interface. Its 45
  extensions match the original 46 minus Neovim. The original settings and Neovim
  association remain intact. All 34 configured command IDs (28 editor + 6 list)
  exist in the installed VS Code build. The local `.code-profile` export passed
  structural checks.
- Ordinary Keyboard Navigation is enabled (`AppleKeyboardUIMode` includes bit 2).
  Hammerspoon files and bindings were not modified.
- Spotlight AppleScript compiles and verifies the configured Spotlight shortcut.

## Firmware provenance

September 6 pair prefix: `adv360-202609061517-66d6b27`.
The commit portion identifies the starting revision; this is a modified working
configuration, captured exactly in the accompanying `-source.tar.gz`.

- ZMK: `f1d5fc736bdbdde11df0ec77114c6a398ee1252b` (`refil/zmk`).
- Zephyr: `dacab4875df72109b96cc8977547a0dc04875bcd`.
- All other active dependency revisions are in the frozen `-manifest.yml`.
- Rollback prefix: `adv360-202609061436-66d6b27-rollback`, rebuilt from the prior
  repository configuration. It is not represented as hardware-tested firmware.
- The archive contains current and rollback pairs, their source/configuration
  manifests and checksums, reference documents, host integration source, and the
  personal importable VS Code profile. Keep that profile local if sharing firmware.

## Live checks still needed

The keyboard has **not been flashed**. Complete the hardware acceptance list in
[setup.md](setup.md), especially pointer drag/release, rapid typing, both monitors,
USB/BLE switching, reconnect and overnight sleep. Neither compilation nor the
simulator establishes comfort, actual pointer speed, or host sleep reliability.

Spotlight automation returned AppleEvent timeout `-1712` when contacting System
Events; it stopped before sending Cmd+4. Clipboard integration remains unverified.
Check macOS Automation/Accessibility permissions for the invoking application,
then test the helper from AeroSpace. Spotlight → Cmd+4 remains the manual route.

Saved workspaces 9–10 name `P34WD-40`, while the currently connected second display
is `BenQ PD3205U`; without a matching assignment AeroSpace places 9–10 on PG32UCDM.
The saved assignments were retained as requested. Add BenQ as a fallback when
that is the intended second-monitor arrangement.

## Local host rollback

Apply backups, newest first:

1. `~/.local/state/adv360/backups/20260906T151726.720462Z`
2. `~/.local/state/adv360/backups/20260906T142534.882687Z`

Run `python3 bin/manage_host.py restore <directory>` in that order to restore the
pre-install files and Keyboard Navigation preference. Reload AeroSpace afterward.
Switch VS Code back to the original profile independently; restore does not delete
or change profile registry entries.
