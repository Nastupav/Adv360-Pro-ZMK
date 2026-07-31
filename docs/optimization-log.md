# Advantage360 optimization log

Use one section per physical experiment. Static or compiler success is not ergonomic evidence.

## 2026-07-31 — speed-profile candidate

Status: static gates and independent spec re-review passed; physical field test pending.

Static evidence:

- `make test`: 26/26 tests passed.
- `make verify` and `make verify-active`: passed.
- Both firmware halves built from fingerprint `9d6b8465cdb1`; checksums passed.
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
