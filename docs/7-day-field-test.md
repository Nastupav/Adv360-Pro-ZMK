# Seven-day Advantage360 field test

A layout is not optimized until it survives real typing on both operating
systems. Record every session with `scripts/field_test.py`.

## Start

```sh
python3 scripts/field_test.py init
python3 scripts/field_test.py log --os macos --minutes 60
python3 scripts/field_test.py report
```

The default log is `~/.local/state/adv360-field-test.csv`. Override it with
`ADV360_FIELD_LOG=/path/to/log.csv` or put `--log PATH` either before or after
the subcommand. Logs created before macro-output tracking are migrated but
marked unmeasured, so they cannot satisfy the current strict gate.

## Daily workload

1. macOS prose and browser editing; exercise Hammerspoon Spaces, sticky Command, NAV selection, scrolling, and all three clicks.
2. Neovim coding; test hold-preferred thumb rolls, pane focus, leader-based pane movement, and symbols.
3. Linux terminal and Neovim; test Ctrl composition, Hyprland workspaces, and all eight developer actions.
4. Python/PySpark: decorators, type hints, comparisons, `:=`, `**`, `//`, method chains, containers, and f-strings.
5. PowerShell/SQL/shell: `-eq` through `-ge`, `$_`, `::`, `<>`, `--`, quotes, pipes, redirects, `&&`, and `||`.
6. Mixed OS day; repeat the same workspace, navigation, and application tasks.
7. Normal full-day workflow with no deliberate drills.

Log mistakes immediately:

```sh
python3 scripts/field_test.py log \
  --os macos --minutes 90 \
  --thumb-misfires 1 --layer-errors 0 --shortcut-mismatches 0 \
  --macro-output-errors 0 \
  --awkward-symbols '_ :' \
  --notes 'NAV thumb released early once'
```

If a symbol has a concrete remapping plan, record it explicitly:

```sh
python3 scripts/field_test.py log --os linux --minutes 60 \
  --awkward-symbols '_' --planned-corrections '_' \
  --notes 'Move underscore after the seven-day test'
```

## Acceptance thresholds

Run `python3 scripts/field_test.py report --strict`. The layout passes when:

- at least seven distinct test days are recorded;
- every recorded day contains at least 30 minutes;
- total physical test time is at least 420 minutes;
- macOS and Linux each contain at least 60 minutes;
- thumb misfires are at most 0.5 per hour;
- layer errors are at most 0.5 per hour;
- host shortcut mismatches are zero;
- macro output was explicitly measured in every qualifying session;
- macro output errors (dropped, duplicated, or reordered characters) are zero;
- no symbol is reported awkward at least three times without being listed in
  `--planned-corrections`.

Firmware builds and static checks cannot replace this test. Only the user can
complete the physical seven-day acceptance period.

If thumb errors exceed the threshold, adjust only `tapping-term-ms` in 10 ms
steps and restart the seven-day measurement. If any macro output error occurs,
raise both macro timings from 20 ms to 30 ms and restart. Do not add timing
behavior to letter keys.
