# Seven-day Advantage360 six-layer production-candidate field test

Compilation does not validate ergonomics. This protocol measures bilateral
home-row modifiers, the single Q+W Escape combo, four timed layer thumbs,
literal macros, merged NAV pointer controls, and host integration on macOS and
Linux.

The six-layer redesign requires a fresh log. Older logs are validated before
migration, backed up beside the original as `<log>.pre-migration.bak` (or the
first free numbered suffix when that name is occupied), and replaced atomically.
Migrated sessions are marked `aggressive_input_measured=no`, so they cannot pass
the strict gate.

## Start

```sh
python3 scripts/field_test.py init
python3 scripts/field_test.py log --os macos --minutes 60 \
  --home-row-misfires 0 --combo-misfires 0 --macro-output-errors 0
python3 scripts/field_test.py report
```

The default log is `~/.local/state/adv360-field-test.csv`. Override it with
`ADV360_FIELD_LOG=/path/to/log.csv` or `--log PATH` before or after the
subcommand.

## What to count

- `--thumb-misfires`: Esc, Tab, Caps Word, or Alt+F13 was interpreted as a layer
  hold, or a desired NAV/SYM/NUM/GLOBAL hold became its tap action.
- `--layer-errors`: the wrong layer activated or an intended momentary-layer
  action resolved incorrectly.
- `--home-row-misfires`: a letter became a modifier, a desired modifier became a
  letter, or a modified chord used the wrong modifier.
- `--combo-misfires`: unintended Q+W Escape, a deliberately pressed Q+W that
  failed, or any wrong combo output.
- `--shortcut-mismatches`: firmware gesture and host behavior disagreed.
- `--macro-output-errors`: a literal macro dropped, duplicated, or reordered a
  character.

The logger records explicit macro and aggressive-input measurement for every new
session. Do not enter zero without exercising those paths.

## Daily workload

1. **BASE prose and rolls**: ordinary English/Czech prose, repeated letters,
   same-hand rolls, cross-hand rolls, and punctuation. Exercise every HRM key as
   both tap and hold. Include `as`, `af`, `ag`, `sd`, `df`, `jk`, `kl`, and `l;`
   sequences to expose timing mistakes even though they are not combos.
2. **Home-row modifiers**: Cmd/Option/Ctrl/Shift with opposite-hand letters;
   compare against the plain inner modifiers. Test copy/paste, save, selection,
   terminal Ctrl commands, and modified arrows.
3. **The only typing combo**: press Q+W Escape at least 20 times over Bluetooth
   and USB. Then type realistic `qw`, `qwerty`, and mixed Q/W prose/code to detect
   false activation. Confirm the physical Esc and Esc/NAV tap remain reliable.
4. **Four timed thumbs**: test tap and hold for Esc/NAV, Tab/SYM, Caps Word/NUM,
   and Alt+F13/GLOBAL. Backspace, Delete, Enter, and Space are plain controls and
   should show no tap-hold delay.
5. **Neovim and NAV**: J/K/L/; directions, ASDF document movement, G/H word
   movement on macOS, Ctrl-composed word movement on Linux, selection, scrolling,
   and all three mouse clicks.
6. **VS Code and NUM**: F1-F12, numpad, and ASDFG debug keys
   `F5/F9/F10/F11/F12`. Exercise ordinary undo/redo, copy/paste, quick open,
   command palette, save, rename, definition, and references through standard
   Cmd/Ctrl composition rather than an EDIT layer.
7. **SYM language tokens**: Python/PySpark `== != <= >= -> := ** //`;
   PowerShell `-eq` through `-ge`, `$_`, `::`; SQL `<>` and comments; Bash pipes,
   redirects, quotes, and `&&/||`.
8. **GLOBAL and SYS**: application carriers, workspace/window actions,
   Bluetooth profile selection, USB/Bluetooth output switching, Studio unlock,
   media, lighting, and normal full-day use. Do not exercise destructive profile
   clear or bootloader chords merely to fill the log.

Each OS must receive at least one 60-minute session. At least one day must be a
normal workflow rather than a deliberate drill.

## Log an observation

```sh
python3 scripts/field_test.py log \
  --os macos --minutes 90 \
  --thumb-misfires 1 \
  --layer-errors 0 \
  --home-row-misfires 1 \
  --combo-misfires 0 \
  --shortcut-mismatches 0 \
  --macro-output-errors 0 \
  --awkward-symbols '_ :' \
  --notes 'A hold resolved as a letter during Cmd+P'
```

If an awkward symbol already has a concrete remapping plan:

```sh
python3 scripts/field_test.py log --os linux --minutes 60 \
  --home-row-misfires 0 --combo-misfires 0 \
  --awkward-symbols '_' --planned-corrections '_' \
  --notes 'Candidate swap documented; do not edit mid-trial'
```

Do not change timing or bindings during a trial. Any behavior change starts a
new measurement period.

## Acceptance thresholds

```sh
python3 scripts/field_test.py report --strict
```

The candidate passes only when:

- at least seven distinct test days are recorded;
- every recorded day has at least 30 minutes;
- total time is at least 420 minutes;
- macOS and Linux each have at least 60 minutes;
- thumb misfires are at most 0.5/hour;
- layer errors are at most 0.5/hour;
- home-row mod misfires are at most 0.5/hour;
- there are zero combo misfires;
- aggressive input was explicitly measured in every session;
- there are zero host shortcut mismatches;
- macro output was explicitly measured in every session;
- there are zero macro output errors;
- no symbol is reported awkward at least three times without an explicit
  planned correction.

## Failure response

- Any combo error: remove Q+W first or alter its idle requirement; do not widen
  the 35 ms timeout as a first response.
- Home-row error rate above 0.5/hour: change one of tapping term, prior-idle, or
  trigger positions at a time, preserve QWERTY taps, and restart.
- Thumb/layer error above 0.5/hour: change only the responsible behavior in 10 ms
  steps and restart.
- Any macro output error: raise all literal macro timings from 20/20 to 30/30 ms
  and restart.
- Any host mismatch: fix firmware/host protocol parity before further ergonomic
  testing.

Firmware builds and static checks cannot replace this trial. Only the user can
complete physical acceptance. The final decision is accept / revert / iterate.
