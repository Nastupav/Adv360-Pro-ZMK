# ADV360 Ergonomic Review

## Scope

This review covers `/Users/macbook/Downloads/adv360-3.keymap` and the local macOS consumers that depend on it:

- `/Users/macbook/Downloads/skhdrc`
- `/Users/macbook/Downloads/karabiner_wm_layers.json`
- `/Users/macbook/.config/aerospace/aerospace.toml`

No personal key-frequency logs were provided. The "ML" component below is therefore a heuristic prior model, not a trained personal model.

## Layer Analysis

`BASE`

- QWERTY base with mirrored home-row mods.
- Thumb access is already strong: `SYM`, `NAV`, `WM`, `APP`, `NUM`.
- Clipboard on the center columns is optimized for mixed keyboard/mouse use.

`SYM`

- Strong coding-symbol placement already existed: `[] {}` on the left home row and `: ; < > | \` on the right.
- F-keys are flattened behind a single `BSPC` hold.
- Revised: direct `DQUOTE` on the right inner qwerty position to reduce `Shift` dependence for JSON/JSX/string-heavy work.

`NAV`

- This was the main ergonomic miss.
- Before the revision, the file comments described home-row navigation, but the actual arrow cluster lived on the row above the home row.
- Revised: actual character navigation now lives on `H/J/K/L`, with word navigation above it and page/document navigation above that.
- Revised: `LA(BSPC)` was promoted into the primary NAV path to flatten "delete previous word".

`MOD`

- Purely administrative layer for Bluetooth, RGB, backlight, and bootloader.
- Transparent positions are intentional and not a problem.

`WM`

- Already well-optimized conceptually because it converts expensive OS/window-manager chords into a single layer hold plus one key.
- The right home row direct AeroSpace chords are good and were preserved.
- Revised: the destructive quit action on the left DEL thumb is now tap-only instead of hold-tap, removing timing ambiguity.

`NUM`

- Good split: right-hand numpad, left-hand tab switching with `Cmd+1..0`.
- No change needed.

`APP`

- Good flattening layer for launchers and system actions.
- The firmware side is intentionally generic because the real semantics live in `skhdrc`/Karabiner.

## Findings

1. NAV comments and NAV implementation were out of sync.
2. The highest-frequency navigation action set, character movement, was not on the actual home row.
3. Two low-value `INSERT` positions occupied prime NAV real estate.
4. The WM quit key used hold-tap timing on a destructive action, which is avoidable risk.
5. The SYM layer lacked direct `"` even though string-heavy engineering workflows use it constantly.
6. `PRINTSCREEN`, `K_CONTEXT_MENU`, keyboard-layout toggle, play/pause, and `KP_NUM` are still low-priority mappings. They were left in place to avoid unnecessary downstream churn, but they are the next reclaimable positions.
7. The duplicate next-tab path on NAV was left intact intentionally. If it goes unused, it is the cleanest next slot to reclaim.
8. APP and WM intentionally share the same host chord family. That is fine only because the current host config leaves APP `H/J/K/L/;` unused. Those slots should stay reserved unless WM is redesigned.

## Before / After

| Area | Before | After | Benefit |
|---|---|---|---|
| NAV home row | `H/J/K/L/;/' = INSERT, Cmd-Left, PgDn, PgUp, Cmd-Right, INSERT` | `H/J/K/L = Left/Down/Up/Right`, `;/' = line start/end`, inner = `delete previous word` | Real modal-nav ergonomics on the true home row |
| NAV qwerty row | `U/I/O/P = Left/Down/Up/Right` | `U/I/O/P = word-left/Home/End/word-right` | Better movement hierarchy and less finger travel |
| NAV num row | word nav lived here | `PgUp/Home/End/PgDn` | Coarse movement pushed to lower-priority row |
| SYM right inner qwerty | `INS` | `DQUOTE` | Flattens high-frequency string entry |
| WM left DEL thumb | hold-tap `LEFT_SHIFT` / tap `Shift+F24` | tap-only `Shift+F24` | Safer destructive action, less accidental quit risk |

## Cheat Sheet

`BASE`

- Hold left `BSPC` thumb for `SYM`
- Hold right `SPACE` thumb or left inner thumb for `NAV`
- Hold right `ENTER` thumb for `WM`
- Hold `CAPS` for `APP`, tap for `ESC`
- Hold top-left `NUM` or left thumb `DEL` for `NUMPAD`

`NAV`

- `H J K L` = left, down, up, right
- `; '` = line start, line end
- Right home inner = delete previous word
- `U I O P` = word-left, Home, End, word-right
- Right num-row cluster = `PgUp Home End PgDn`
- Right inner qwerty = previous tab
- `Y` = next tab

`SYM`

- Left home row = `[ ] { } \``
- Right home row = `: ; < > | \`
- Right inner qwerty = `"`
- Left shift row = `~ \` ( )`

`WM`

- Right home row = direct AeroSpace focus on `H/J/K/L/;`
- Left thumb `BSPC` = close window
- Left thumb `DEL` = quit app
- Left thumb `END` = float toggle
- Right thumb `K_APP` = tiling-direction toggle
- Right thumb `SPACE` = balance/equalize

## ML Summary

### Prior Model

Without personal telemetry, I used a weighted prior for a high-output modal engineer:

| Action family | Weight |
|---|---:|
| Character navigation and small edits | 0.30 |
| Symbol entry for code and markup | 0.25 |
| Word and line movement | 0.20 |
| Tab, pane, and workspace switching | 0.15 |
| Numeric entry | 0.05 |
| System and media actions | 0.05 |

### Context Signals Used

- Neovim/modal editing implies `H/J/K/L`-style movement should be privileged.
- Terminal and IDE use make `word-left/right`, `line-start/end`, and tab switching much more frequent than `Insert`.
- The local `skhdrc` and `aerospace.toml` show heavy keyboard-centric workspace and app-launch workflows, so WM and APP flattening were preserved instead of redesigned.
- JSON/JSX/TS and shell-heavy work make direct `"` materially more valuable than `Insert` on the SYM layer.

### What the Model Changed

- Promoted char-nav into the true home row.
- Demoted low-value `Insert` from prime NAV slots.
- Promoted a high-frequency code symbol, `DQUOTE`, into a low-friction SYM slot.
- Removed hold-tap ambiguity from a destructive WM action.

## Scenario Check

Editing code:

- Hold `NAV`, keep the right hand on `H/J/K/L`, move by characters, jump to line edges on `;/'`, delete previous word on the inner home key.

Moving through terminals, browser tabs, or IDE tabs:

- Hold `NAV`, use right inner qwerty plus `Y` for previous/next tab without leaving the layer.

Typing JSON/JSX/strings:

- Hold `SYM`, hit right inner qwerty for direct `"` instead of reaching for `Shift`.

Window management:

- Hold `WM`, use the right home row for focus and thumbs for close/quit/float/balance without constructing any OS-level chord manually.

## Iterative Improvement Plan

1. Collect real usage for 2-3 weeks.
2. Track:
   - Neovim keyfreq or similar plugin output
   - Karabiner EventViewer counts for WM and APP paths
   - AeroSpace action frequency from command history or logs
   - Terminal tab-switch, delete-word, and line-jump usage
3. Re-rank reclaimable keys.
4. If NAV outer next-tab is rarely used, reclaim that slot first for one of:
   - delete-next-word
   - search-next
   - pane-next
5. If `PRINTSCREEN` and `K_CONTEXT_MENU` remain unused on base, move them to `MOD` and promote a higher-value action into those positions.
6. Only test pair-insertion macros like `""`, `()`, `{}`, `[]` if your editor is not already handling autopairs cleanly.
7. If home-row mods still misfire, tune `require-prior-idle-ms` and `tapping-term-ms` from measured error cases, not feel alone.
