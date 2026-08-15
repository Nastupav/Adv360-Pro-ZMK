# Advantage360 agent contract

This repository is an evidence-driven, speed-focused Kinesis Advantage360 Pro configuration. Do not call a layout "optimized" solely because it compiles. Static verification makes it test-ready; the seven-day physical protocol decides whether an iteration is accepted.

## Non-negotiable user contract

- BASE is plain US QWERTY. Letters never use hold-taps, home-row mods, or combos.
- Non-BASE home-row actions use only physical `ASDF` and `JKL;`.
- Physical `G` and `H` are inactive on every non-BASE layer.
- Never use Esc in a combo.
- Frequent GUI/Cmd and Ctrl paths stay plain or sticky and composable.
- Firmware macros emit literal tokens only: no cursor movement, trailing spaces, editor commands, or auto-pairs.
- ZMK Studio is enabled only on the left/central half; preserve the USB RPC
  snippet, `SYS + U` unlock, and Studio-free right peripheral. Studio edits
  override Git keymap changes until **Restore Stock Settings** is used.

## Current speed profile

- Six layers: BASE, NAV, SYM, NUM, GLOBAL, SYS.
- Four thumb-only hold-taps use `hold-preferred` at 170 ms.
- SYM contains 21 literal language macros at 20/20 ms for Python, PowerShell, SQL, shell, and PySpark.
- F13-F20 plus modifiers form the host protocol. Do not change firmware carriers without updating and testing every host adapter.
- AeroSpace owns macOS. Keep `host/macos/aerospace.toml`, the installer, active verifier, and protocol docs synchronized; Hammerspoon and Karabiner must not translate or bind these carriers.

The exact macro sequences and positions are enforced by `tests/test_workflow.py` and `scripts/verify_workflow.py`. Update code, tests, README, and this contract together when intentionally changing the design.

## Mandatory iteration loop

1. Run `git fetch origin --prune`, inspect `git status`, and preserve unrelated worktree changes.
2. Read `README.md`, this file, `docs/7-day-field-test.md`, and the keymap header before proposing changes.
3. Change one ergonomic variable per iteration. Add or update a failing test first.
4. Run `make test` and `make verify`.
5. Run `git diff --check` and inspect the full diff.
6. Build both halves with `make`. Require both `Board: adv360_left` and `Board: adv360_right`, linked `zmk.elf`, converted UF2 output, checksums, and a manifest.
7. Run an independent review against the contract. Fix concrete compiler, geometry, macro-sequence, reachability, protocol, or documentation defects; do not replace the design with reviewer preferences.
8. Flash only after static gates pass. Complete the physical trial with `python3 scripts/field_test.py report --strict`.
9. Record the experiment and evidence in `docs/optimization-log.md`. Do not claim improvement without before/after physical evidence.

## Release gates

```sh
make test
make verify
git diff --check
make
(cd firmware && shasum -a 256 -c SHA256SUMS)
python3 scripts/field_test.py report --strict  # requires real user data
```

A release is blocked by any macro output error. If 20/20 ms drops, duplicates, or reorders a character, raise both macro timings to 30 ms and restart the field test. If thumb errors exceed 0.5/hour, adjust only the tapping term by 10 ms and restart. Never compensate by adding timing behavior to letters.

## Review priorities

1. Lost or reordered characters, typing delays, and layer misfires.
2. Exact physical positions and complete `[14,14,18,14,16]` row shape.
3. Macro definition, output sequence, timing, and exactly one active binding.
4. Modifier and held-layer composability.
5. F13-F20 firmware/host semantic parity.
6. Documentation accuracy and reproducible build provenance.

Generated `firmware/` artifacts are gitignored. Their names include the commit,
the complete firmware-input fingerprint from `scripts/firmware_fingerprint.py`,
and `-dirty` when built from tracked worktree changes.
