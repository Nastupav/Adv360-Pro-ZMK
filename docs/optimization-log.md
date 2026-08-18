# Advantage360 optimization log

Use one section per physical experiment. Static or compiler success is not ergonomic evidence.

## 2026-07-31 — speed-profile candidate

Status: static gates and independent spec re-review passed; physical field test pending.

Static evidence:

- `make test`: 27/27 tests passed.
- `make verify` and `make verify-active`: passed.
- Both firmware halves built from fingerprint `f6edf08e82b5`; ZMK Studio was
  compiled into the left/central half and both checksums passed.
- Independent review found and drove fixes for a stale F21-F24 AeroSpace
  reference and stale same-prefix right artifacts after `make left`.
- Pre-commit quality review drove fail-closed Lua parsing, safe Hyprland shell
  quoting, transactional/contained host rollback, measured macro-field gates,
  and dirty provenance for untracked inputs.
- Spec re-review: PASS with no blocking gaps.

Changed variables:

- Thumb layer resolution: balanced 180 ms → hold-preferred 170 ms.
- Literal macro timing: 40/40 ms → 20/20 ms.
- Added Python/PySpark tokens: `:=`, `**`, `//`.
- Added PowerShell tokens: `-eq`, `-ne`, `-lt`, `-le`, `-gt`, `-ge`, `$_`, `::`.
- Added SQL/shared tokens: `<>`, `--`.
- Kept BASE letters timing-free and retained the `ASDF`/`JKL;` action-zone contract.
- Added field-test rejection for any dropped, duplicated, or reordered macro output.

Rationale:

- Hold-preferred thumb behavior resolves a layer on the interrupting key-down, reducing chord latency without putting timing on letters.
- Literal macros reduce multi-keystroke punctuation while remaining editor-independent.
- No pair macros or cursor movement were added because editor auto-pairing and formatters already own context.

Required physical checks:

1. Type every macro at least 20 times over Bluetooth on macOS and Linux.
2. Test slow hold, fast chord, thumb-first release, and immediate thumb re-press for NAV, SYM, NUM, and GLOBAL.
3. Exercise Python type hints/comparisons, PySpark method chains, PowerShell comparisons/pipelines, and SQL predicates/comments.
4. Record all sessions with `scripts/field_test.py`; acceptance requires zero macro output errors.

Next decision rule:

- Any macro output error: increase all macro `wait-ms` and `tap-ms` to 30 ms; restart the seven-day test.
- Thumb misfires above 0.5/hour: change only the 170 ms tapping term by 10 ms; restart.
- A token reported awkward at least three times: use recorded frequency and reach evidence to swap positions, then update tests and restart.
- No additional macro should be added until an existing empty position and a measured high-frequency token justify it.

## 2026-08-15 — AeroSpace macOS owner migration

Status: repository, live host, and both-half build gates passed; no firmware behavior changed.

Evidence:

- `make test`: 39/39 tests passed.
- `make verify` and `make verify-active`: passed.
- AeroSpace dry-run/reload passed with workspaces 1-5 on `PG32UCDM` and 6-10 on `P34WD-40`.
- All 38 F13-F20 protocol bindings are repository-verified; all eight developer actions resolve to argv commands.
- Both firmware halves built with fingerprint `f6edf08e82b5`; manifest records `left=true` and `right=true`.
- `shasum -a 256 -c SHA256SUMS`: both artifacts passed.
- Dirty and prior clean UF2 hashes are byte-identical because this migration changed host integration only.

Changed host architecture:

- AeroSpace became the sole macOS protocol owner.
- The repository gained `host/macos/aerospace.toml` and active config-parity/runtime verification.
- The Hammerspoon adapter and Hammerspoon-only Karabiner normalization were retired.
- macOS launcher became a normal host-neutral `adv360-action` entry.
- Installer safety now rejects ambiguous AeroSpace configs, duplicate/unbalanced managed blocks, symlinked managed targets, and special-file rollback targets; writes/restores use randomized fsynced atomic files while preserving existing mode/ownership.
- Active ownership verification structurally rejects selected-profile Karabiner F13-F20 rewrites and inspects Hammerspoon's live hotkey registry independent of adapter filenames or sentinels.

Physical acceptance: existing firmware trial requirements are unchanged; this host-only migration still requires normal real-workflow shortcut observation, but it does not restart the firmware timing trial.

## 2026-08-16 — aggressive-home-row candidate

Status: static gates, active-host verification, both-half firmware build, and bounded independent follow-up review passed; physical field test not started.

Requested design change:

- Replaced the six-layer deterministic profile with ten useful layers.
- Added bilateral ASDF/JKL; home-row modifiers while preserving plain US QWERTY taps.
- Activated G and H on every layer and removed all `&none` bindings.
- Added 16 BASE-only home-row combos at 35 ms.
- Expanded thumb access to NAV, SYM, NUM, CODE, EDIT, MOUSE, GLOBAL, and MEDIA.
- Preserved the F13-F20 AeroSpace/Hyprland protocol and left-only ZMK Studio support.
- Extended physical logging with home-row and combo measurement; previous logs cannot validate the new aggressive input model.

Acceptance status:

- `make verify`: 51/51 tests passed; semantic verifier and `git diff --check` passed.
- `make verify-active`: active AeroSpace reload, runtime binding parity, exclusive ownership, monitor assignment, and Neovim include passed.
- Both halves compiled from firmware fingerprint `8bbbc11f1a71`; manifest records left/right=true and both SHA-256 checks passed.
- UF2 structure checks passed: left 553,984 bytes/1,082 blocks; right 363,520 bytes/710 blocks.
- Independent review found and drove fixes for destructive GLOBAL bracket drift, incorrect macOS Replace, unsafe legacy-log migration, and stale/symlink backup collisions. The bounded final backup review passed with no remaining issue.
- Seven-day physical trial: pending and required before any optimization claim.

Decision rule:

- Zero combo misfires are required.
- Home-row, thumb, and layer misfires must remain at or below 0.5/hour.
- Any firmware macro output error blocks acceptance.
- Failed criteria trigger a single-variable iteration, rebuild, and fresh trial.

## 2026-08-16 — six-layer production candidate

Status: static gates, active-host verification, both-half build, and bounded
independent review passed; the physical trial remains pending.

Reason for superseding the ten-layer candidate:

- Eight timed thumbs and sixteen typing combos competed with the HRM timing
  system and increased ordinary typing risk without physical evidence.
- CODE duplicated SYM, EDIT duplicated composable modifiers and NUM F-keys,
  MOUSE duplicated NAV, and MEDIA duplicated SYS.
- The user selected the bounded production design before flashing.

Authoritative changes:

- Restored six layers: BASE, NAV, SYM, NUM, GLOBAL, SYS.
- Kept bilateral ASDF/JKL; HRMs and active G/H letters.
- Kept only Q+W -> Escape as the one BASE typing combo: 35 ms with 80 ms prior
  idle.
- Kept only four timed layer thumbs: Esc/NAV, Tab/SYM, Caps Word/NUM, and
  Alt+F13/GLOBAL.
- Restored plain Backspace, Delete, Enter, and Space.
- Merged all 21 literal developer macros into SYM, scroll/click controls into
  NAV, VS Code debug keys into NUM, and media/lighting into SYS.
- Removed layer toggles; all six layers are momentary.
- Preserved the F13-F20 host protocol and left-only ZMK Studio support.

Acceptance status:

- `make verify`: 51/51 tests, semantic verifier, and `git diff --check` passed.
- `make verify-active`: active AeroSpace reload/runtime parity, exclusive carrier
  ownership, monitor assignment, and Neovim include passed.
- Both halves built from fingerprint `8d592f94fd9c`; manifest records
  left/right=true and matches the current firmware inputs.
- SHA-256 checks passed. Left: 536,576 bytes/1,048 valid UF2 blocks,
  `2f73d58ed4838d6006c933736ae1157d42ce7cf315331e25b9d3d95084202db5`.
  Right: 363,520 bytes/710 valid UF2 blocks,
  `b0837fe0294aac6d183697aa3bb8b82157aceffbb61777c7474019dbde5e68fa`.
- Independent final review found one stale README host-install command pair. The
  commands now use `scripts/manage_host.py plan/install`, a regression test
  guards both paths, and the bounded follow-up review passed with no remaining
  blocker/high/medium defect.
- A fresh seven-day trial remains required. The decision is accept / revert / iterate.

## 2026-08-16 — editor-pane and thumb-macro revision

Reason:

- `==` and `!=` were on the outer Tab/Q positions despite the opposite left
  thumb being free while the right-thumb SYM key is held.
- The Neovim adapter depended on terminal-ambiguous `Ctrl+;`, and VS Code had no
  matching pane-focus contract.

Changes:

- Moved `==` and `!=` to SYM Backspace/Delete. BASE Backspace/Delete remain plain;
  SYM Enter/Space remain passthrough keys.
- NAV Y/U/I/O now emits editor-local F21-F24 in left/down/up/right order.
- Moved scrolling to the physical arrow cluster and retained left/right click;
  removed low-value middle click.
- Added matching Neovim normal/insert/terminal mappings and VS Code editor-group
  focus bindings.

Status:

- `make verify`: 54/54 tests, semantic verifier, and whitespace checks passed.
- `make verify-active`: AeroSpace runtime parity, exclusive F13-F20 ownership,
  Neovim loading, and installed VS Code F21-F24 keybinding-file parity passed.
- Both halves built from fingerprint `c0a742d7855e`; SHA-256 and every 512-byte
  UF2 frame passed validation.
- Left SHA-256: `ee7886962ba1658fc0d739dfbb845431d24d8920444594459e9b5a1f4e5d9802`.
- Right SHA-256: `b0837fe0294aac6d183697aa3bb8b82157aceffbb61777c7474019dbde5e68fa`.
- The 5000×4550 layout image contains 456 key shapes, 21 macro cards, the four
  editor carriers, and both thumb macros; full-image and focused visual QA passed.
- A fresh seven-day physical trial remains required for ergonomic acceptance.

## Template for the next iteration

Date:
Agent/reviewer:
Baseline commit/config hash:
Single variable changed:
Reason:
Static verification:
Both-half build:
Physical minutes by OS:
Before/after error rates:
Macro output errors:
Decision: accept / revert / iterate
Follow-up:
