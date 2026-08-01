# Advantage360 Pro developer keymap

Source-controlled ZMK firmware for a Kinesis Advantage360 Pro, tuned for
Python, SQL, PowerShell and Vim-shaped editing across macOS, Windows and
Linux.

Two ideas carry the whole layout:

1. **Home-row mods do the chording, thumbs do the commanding.** Holding
   `A S D F` / `J K L ;` gives Cmd/Alt/Ctrl/Shift without leaving the home
   row. The inner thumb keys stay *real* Cmd and Ctrl, because a same-hand
   home-row mod cannot produce `Cmd+C`, `Cmd+V`, `Cmd+Z`, `Cmd+S` or
   `Cmd+A` — all left-hand letters.
2. **The command modifier never moves.** `MAC` is the default base. `WIN` is
   a thin overlay that swaps GUI and Ctrl on both the home row and the
   thumbs, so the same physical key means "command" on every host.

## Layer model

| Layer | Access | Purpose |
|---|---|---|
| `MAC` | Default | QWERTY, home-row mods, Cmd on inner thumbs |
| `WIN` | `SYS` + `W` (back via `SYS` + `A`) | GUI/Ctrl swapped; everything else falls through to `MAC` |
| `NAV` | Hold left middle thumb | Motion, clipboard, editor verbs |
| `SYM` | Hold right middle thumb | Programming symbols |
| `NUM` | Hold left bottom thumb | Numpad and F1-F12 |
| `GLOBAL` | Hold right bottom thumb | Host-neutral window-manager protocol |
| `SYS` | Hold either inner top key, or bottom-right | Bluetooth, output, lighting, maintenance |
| `NAV_WIN` | Automatic (`WIN` + `NAV`) | Windows-flavoured overrides for `NAV` |
| `MACRO` | Hold **both** middle thumbs | Text macros: SQL, Python, operators, shell, comments |

Two of these are conditional layers you never select directly.

`NAV_WIN` fires when the `WIN` base is active and you hold `NAV`. `Cmd+C`
becomes `Ctrl+C`, Option-word-motion becomes Ctrl-word-motion, document
start/end become `Ctrl+Home`/`Ctrl+End`, and browser history moves to
`Alt+Left`/`Alt+Right`. Muscle memory stays identical on both operating
systems.

`MACRO` fires when `NAV` and `SYM` are held together — both middle thumbs.
That costs no dedicated key, and the two thumbs are already the ones your
hands rest against, so the whole macro bank is one chord away.

Every position on every layer is bound. `&trans` is content, not emptiness: it
exposes the layer underneath, which is exactly what makes `WIN` a thin overlay
instead of a duplicated base. What the layout does not contain is `&none` —
`make validate` fails if a dead key appears.

## Home-row mods

```text
hold:   A     S      D      F           J       K      L      ;
        Cmd   Alt    Ctrl   Shift       Shift   Ctrl   Alt    Cmd     (MAC)
        Ctrl  Alt    Cmd    Shift       Shift   Cmd    Alt    Ctrl    (WIN)
```

Three properties keep these from misfiring during fast typing:

- `require-prior-idle-ms = 150` — if you pressed another key within the last
  150 ms, the hold is abandoned outright and the key is a plain letter. This is
  what stops rolls like `sd` or `kl` becoming modifiers.
- `hold-trigger-key-positions` — only the *opposite* hand and the thumbs can
  resolve a hold. Same-hand rolls always stay letters.
- `quick-tap-ms = 175` — tap then hold the same key within 175 ms to repeat the
  letter instead of engaging the modifier.

Two consequences worth internalising:

- **Shift right-hand letters with left-hand Shift** (`F`), and vice versa.
  Same-hand shifting is deliberately suppressed. `:` therefore is `F` held +
  `;`, or just `SYM`+`G`.
- **Same-hand `Cmd`/`Ctrl` combos use the thumb**, not the home row.
  `Cmd+C` is inner-left-thumb + `C`.

If the timings do not suit you, they are the four numbers in the `hml`/`hmr`
behaviors at the top of `config/adv360.keymap`. Raise `require-prior-idle-ms`
toward 200 if you still get accidental mods; lower `tapping-term-ms` toward 200
if holds feel sluggish.

The outer pinky `Shift` keys remain real Shifts. They are the ones to use for
shift-clicking and for Shift-modified `GLOBAL` signals.

## Symbols

The `SYM` home row is an enclosure ladder, mirrored around the centre, with the
two highest-frequency Python/SQL characters on the index stretches:

```text
   <   {   [   (   :   |   _   )   ]   }   >   =
```

The number row keeps the familiar US shifted-number symbols, the upper row
carries `~ \` \ | ;` and `" ' ? / \`, and the fourth row carries the
shell/PowerShell set `^ $ - _ *` and `& | !`.

`=` and `-` also keep their unshifted home on the base number row, so they are
available without a layer at all.

## Macros

The nine multi-character operators you reach for hourly sit on `SYM`'s bottom
row, one thumb away:

```text
   <>  ->  =>  !=  ==    |    <=  >=  ::  __
```

with `**` and `:=` just above them. The full bank — SQL keywords, Python
keywords, PowerShell fragments, comment openers and comment tags — lives on
`MACRO`, reached by holding both middle thumbs.

Macros are plain tap sequences defined in `config/macros.dtsi`. None of them
hold a modifier across the sequence, so none can leave a modifier stuck. The
ones that wrap a cursor position — `print()`, `f""`, `$()`, `@()`, `@{}`,
`/*  */` — end with `Left` taps so the caret lands inside.

To add one, copy a `TEXT_MACRO(...)` line and bind it somewhere. `make
validate` fails on a macro that is defined but never used, and on one that is
used but never defined.

## GLOBAL host protocol

`GLOBAL` never sends application-specific shortcuts. It emits F13-F20 with
modifiers, and each host translates:

| Signal | Action |
|---|---|
| `F13`-`F20` | Workspace 1-8 |
| `Shift+F13`-`F20` | Move window to workspace 1-8 |
| `Ctrl+F13`-`F16` | Focus left/down/up/right |
| `Ctrl+Shift+F13`-`F16` | Move window left/down/up/right |
| `Ctrl+F17`/`F18` | Previous/next workspace |
| `Ctrl+Shift+F17`/`F18` | Move window to previous/next workspace |
| `Ctrl+F19` / `Ctrl+Shift+F19` | Fullscreen / close window |
| `Ctrl+F20` / `Ctrl+Shift+F20` | Float / toggle layout |
| `Ctrl+Alt+F13`-`F16` | Resize left/down/up/right |
| `Ctrl+Alt+F17`/`F18` | Focus previous/next monitor |
| `Ctrl+Alt+Shift+F17`/`F18` | Move window to previous/next monitor |
| `Ctrl+Alt+F19` | Balance / reset layout |
| `Ctrl+Alt+F20` | Pin (sticky) window |
| `Alt+Shift+F13`-`F16` | Screenshot region, screenshot window, clipboard history, colour picker |
| `Alt+F13`-`F20` | Terminal, browser, code, files, launcher, chat, notes, git |

The pattern is consistent: adding `Shift` to a "go there" signal turns it into
"take the window there".

Ready-to-use consumers live in `host/`:

| Host | File | Requires |
|---|---|---|
| macOS | `host/macos/aerospace.toml` | AeroSpace |
| Linux | `host/linux/hyprland.conf` | Hyprland |
| Windows | `host/windows/adv360-global.ahk` | AutoHotkey v2, komorebi |

The Windows script degrades gracefully without komorebi: previous/next
workspace falls back to native virtual desktops and focus falls back to
`Alt+Tab`, but numbered workspaces and directional movement need komorebi.

Because the keyboard applies the modifiers itself, `Shift`+workspace and
`Shift`+focus are free — the same physical key does "go there" and "take the
window there" depending on whether a pinky Shift is down.

## Layers

<!-- BEGIN GENERATED LAYERS -->

`^^` transparent — falls through to the layer below &nbsp;&middot;&nbsp;
`X/S` tap X, hold Shift &nbsp;&middot;&nbsp; `C-` Ctrl `S-` Shift `A-` Alt
`G-` Cmd/Gui &nbsp;&middot;&nbsp; `#` keypad &nbsp;&middot;&nbsp; `=>` switch
base layer &nbsp;&middot;&nbsp; `>` truncated macro (see the reference below)

**MAC**

```text
   =       1       2       3       4       5      SYS                                                        SYS      6       7       8       9       0       -
  Tab      Q       W       E       R       T      Caps                                                       Rept     Y       U       I       O       P       \
  Esc     A/G     S/A     D/C     F/S      G      Alt             Ctrl    Cmd    |   Cmd     Ctrl            Alt      H      J/S     K/C     L/A     ;/G      '
  Shft     Z       X       C       V       B                              NAV    |   SYM                              N       M       ,       .       /      Shft
   `       [       ]       (       )                      Bspc    Del     NUM    |  GLOBAL   Ent     Spc                      <-      v       ^       ->     SYS
```

**WIN**

```text
  ^^    ^^    ^^    ^^    ^^    ^^    ^^                                           ^^    ^^    ^^    ^^    ^^    ^^    ^^
  ^^    ^^    ^^    ^^    ^^    ^^    ^^                                           ^^    ^^    ^^    ^^    ^^    ^^    ^^
  ^^   A/C   S/A   D/G   F/S    ^^    ^^         Cmd   Ctrl  |  Ctrl  Cmd          ^^    ^^   J/S   K/G   L/A   ;/C    ^^
  ^^    ^^    ^^    ^^    ^^    ^^                      ^^   |   ^^                      ^^    ^^    ^^    ^^    ^^    ^^
  ^^    ^^    ^^    ^^    ^^                ^^    ^^    ^^   |   ^^    ^^    ^^                ^^    ^^    ^^    ^^    ^^
```

**NAV**

```text
  G-`     G-1     G-2     G-3     G-4     G-5      ^^                                                         ^^     G-6     G-7     G-8     G-9     G-0     G-W
   ^^     G-A     G-S     G-F    G-S-F    G-P      ^^                                                         ^^     A-<-    PgDn    PgUp    A-->    G-^     G-v
   ^^     G-Z     G-X     G-C     G-V    G-S-Z     ^^              ^^      ^^    |    ^^      ^^              ^^      <-      v       ^       ->     Home    End
   ^^      F2     F12    S-F12     F3     S-F3                             ^^    |    ^^                            A-Bspc  A-Del    Bspc    Del     Ins      ^^
  G--     G-[     G-]     G-=    G-S-T                     ^^      ^^      ^^    |    ^^      ^^      ^^                      ^^      ^^      ^^      ^^      ^^
```

**SYM**

```text
  ^^    !     @     #     $     %     ^^                                           ^^    ^     &     *     (     )     ^^
  ^^    ~     `     \     |     ;     ^^                                           ^^    "     '     ?     /     \     ^^
  ^^    <     {     [     (     :     ^^          ^^    ^^   |   ^^    ^^          ^^    _     )     ]     }     >     =
  ^^    ^     $     -     _     *                       ^^   |   ^^                      &     |     **    :=    !     ^^
  <>    ->    =>    !=    ==                ^^    ^^    ^^   |   ^^    ^^    ^^                <=    >=    ::    __    ^^
```

**NUM**

```text
  F1    F2    F3    F4    F5    F6    ^^                                           ^^    ^^    ^^    ^^    ^^    ^^    ^^
  F7    F8    F9   F10   F11   F12    ^^                                           ^^    #7    #8    #9    #/    #*   Bspc
  ^^    A     B     C     D     E     ^^          ^^    ^^   |   ^^    ^^          ^^    #4    #5    #6    #-    #+   #Ent
  ^^    F     0x    =     <     >                       ^^   |   ^^                      #1    #2    #3    #.    ,     ^^
  %     ^     *     (     )                 ^^    ^^    ^^   |   ^^    ^^    ^^                #0    #.    #=   #Ent   ^^
```

**GLOBAL**

```text
  C-S-F17      F13        F14        F15        F16        F17         ^^                                                                              ^^        F18        F19        F20     C-A-S-F17  C-A-S-F18   C-S-F18
  A-S-F13    C-S-F19     C-F20      A-F16     C-A-F19     A-F13        ^^                                                                              ^^      C-S-F13    C-S-F14    C-S-F15    C-S-F16    C-S-F20    C-A-F20
     ^^       A-F17      A-F18      A-F19      C-F19      A-F20        ^^                    ^^         ^^     |      ^^         ^^                    ^^       C-F13      C-F14      C-F15      C-F16      C-F17      C-F18
     ^^      A-S-F14    A-S-F15     A-F15     A-S-F16     A-F14                                         ^^     |      ^^                                       C-A-F13    C-A-F14    C-A-F15    C-A-F16    C-S-F19       ^^
   C-F19      C-F17      C-F18     C-A-F17    C-A-F18                             ^^         ^^         ^^     |      ^^         ^^         ^^                             C-F13      C-F14      C-F15      C-F16        ^^
```

**SYS**

```text
     USB          BT0          BT1          BT2          BT3          BT4           ^^                                                                                            ^^          BLE          Out~         BT>          BT<        C_BRI_DN     C_BRI_UP
     BL~          BL-         =>WIN         BL+           ON          OFF           ^^                                                                                            ^^        BT_DISC0     BT_DISC1     BT_DISC2     BT_DISC3     BT_DISC4       SPD
      ^^         =>MAC         HUD          HUI          SAD          SAI           ^^                        ^^           ^^      |       ^^           ^^                        ^^          RGB          BRD          BRI          EFF          EFR          SPI
      ^^         PSCRN         SLCK     PAUSE_BREAK     K_APP         CAPS                                                 ^^      |       ^^                                                 Prev         Play         Next         Vol-         Vol+          ^^
    C_STOP      C_EJECT     C_AL_CALC    C_AL_FILES  C_AC_SEARCH                                 ^^           ^^           ^^      |       ^^           ^^           ^^                                    Mute         #Num        GLOBE      C_AL_LOCK        ^^
```

**NAVWIN**

```text
 C-Tab    C-1     C-2     C-3     C-4     C-5      ^^                                                         ^^     C-6     C-7     C-8     C-9     C-0     C-W
   ^^     C-A     C-S     C-F    C-S-F    C-P      ^^                                                         ^^     C-<-     ^^      ^^     C-->   C-Home  C-End
   ^^     C-Z     C-X     C-C     C-V     C-Y      ^^              ^^      ^^    |    ^^      ^^              ^^      ^^      ^^      ^^      ^^      ^^      ^^
   ^^      ^^      ^^      ^^      ^^      ^^                              ^^    |    ^^                            C-Bspc  C-Del     ^^      ^^      ^^      ^^
  C--     A-<-    A-->    C-=    C-S-T                     ^^      ^^      ^^    |    ^^      ^^      ^^                      ^^      ^^      ^^      ^^      ^^
```

**MACRO**

```text
  SELECT     FROM     WHERE    GROUP BY  ORDER BY    JOIN       ^^                                                                       ^^     LEFT JO>     ON        AS     IS NULL   IS NOT >  COUNT(*)
   def      class     import     from     return    self.       ^^                                                                       ^^     print()     f""      lambda     None      True     False
    ^^        ->        =>        !=        ==        :=        ^^                  ^^        ^^     |     ^^        ^^                  ^^        <=        >=        <>        ::        __        **
    ^^        $_       $()       @()       @{}        |                                       ^^     |     ^^                                     -eq       -ne       ../        ~/       2>&1       ^^
    #         --      /*  */     """       ...                            ^^        ^^        ^^     |     ^^        ^^        ^^                          TODO:     FIXME:    NOTE:     HACK:       ^^
```

**Macro reference** — full contents of the `MACRO` layer. A trailing
space is part of the keyword macros. `^` marks where the caret lands
when the macro repositions it.

*SQL keywords*

`SELECT ` &nbsp;&middot;&nbsp; `FROM ` &nbsp;&middot;&nbsp; `WHERE ` &nbsp;&middot;&nbsp; `GROUP BY ` &nbsp;&middot;&nbsp; `ORDER BY ` &nbsp;&middot;&nbsp; `JOIN ` &nbsp;&middot;&nbsp; `LEFT JOIN ` &nbsp;&middot;&nbsp; `ON ` &nbsp;&middot;&nbsp; `AS ` &nbsp;&middot;&nbsp; `IS NULL` &nbsp;&middot;&nbsp; `IS NOT NULL` &nbsp;&middot;&nbsp; `COUNT(*)`

*Python*

`def ` &nbsp;&middot;&nbsp; `class ` &nbsp;&middot;&nbsp; `import ` &nbsp;&middot;&nbsp; `from ` &nbsp;&middot;&nbsp; `return ` &nbsp;&middot;&nbsp; `self.` &nbsp;&middot;&nbsp; `print()` ^ &nbsp;&middot;&nbsp; `f""` ^ &nbsp;&middot;&nbsp; `lambda ` &nbsp;&middot;&nbsp; `None` &nbsp;&middot;&nbsp; `True` &nbsp;&middot;&nbsp; `False`

*Operators*

`->` &nbsp;&middot;&nbsp; `=>` &nbsp;&middot;&nbsp; `!=` &nbsp;&middot;&nbsp; `==` &nbsp;&middot;&nbsp; `:=` &nbsp;&middot;&nbsp; `<=` &nbsp;&middot;&nbsp; `>=` &nbsp;&middot;&nbsp; `<>` &nbsp;&middot;&nbsp; `::` &nbsp;&middot;&nbsp; `__` &nbsp;&middot;&nbsp; `**`

*PowerShell and shell*

`$_` &nbsp;&middot;&nbsp; `$()` ^ &nbsp;&middot;&nbsp; `@()` ^ &nbsp;&middot;&nbsp; `@{}` ^ &nbsp;&middot;&nbsp; `| ` &nbsp;&middot;&nbsp; `-eq ` &nbsp;&middot;&nbsp; `-ne ` &nbsp;&middot;&nbsp; `../` &nbsp;&middot;&nbsp; `~/` &nbsp;&middot;&nbsp; `2>&1` &nbsp;&middot;&nbsp; `0x`

*Comments and wrappers*

`# ` &nbsp;&middot;&nbsp; `-- ` &nbsp;&middot;&nbsp; `/*  */` ^ &nbsp;&middot;&nbsp; `"""` &nbsp;&middot;&nbsp; `...` &nbsp;&middot;&nbsp; `TODO: ` &nbsp;&middot;&nbsp; `FIXME: ` &nbsp;&middot;&nbsp; `NOTE: ` &nbsp;&middot;&nbsp; `HACK: `

<!-- END GENERATED LAYERS -->

## Bluetooth and firmware safety

Profiles are assigned consistently:

1. Profile 0: Mac
2. Profile 1: Windows
3. Profile 2: Linux
4. Profiles 3-4: spare

`SYS` exposes explicit USB, BLE and output-toggle keys. Destructive actions are
combos, and only on `SYS`:

| Combo (on `SYS`) | Action |
|---|---|
| `1` + `2` | Clear all Bluetooth bonds |
| `4` + `5` | Soft reset |
| Both inner top keys | Enter bootloader |

Use the physical reset button for the right half when necessary. Runtime ZMK
Studio/Clique keymap editing is disabled; git is the source of truth.

The base layer is **not** persisted across power cycles — the keyboard always
boots into `MAC`. If keys behave as though the wrong host is selected, press
`SYS` + `A` for Mac or `SYS` + `W` for Windows.

## Build

Podman is preferred when both Podman and Docker are installed.

```sh
make            # both halves
make left       # left half only
make validate   # structural checks, no toolchain required
```

Firmware and `SHA256SUMS` are written to `firmware/`. Pushes and pull requests
run the same validation and build in GitHub Actions.

### Tooling

```sh
bin/validate_keymap.py          # 76 bindings per layer, hand sets, combos
bin/render_keymap.py            # print the layer diagrams
bin/render_keymap.py --write    # regenerate the diagrams in this README
bin/render_keymap.py --check    # fail if the diagrams are stale
```

The diagrams above are generated from `config/adv360.keymap`, so they cannot
drift from the firmware. CI fails if they do.

## Clean first installation

1. Build and archive the firmware from the previous known-good commit.
2. Download the current V3 `settings-reset.uf2` from the official Kinesis
   Advantage360 Pro repository and verify its source.
3. Follow Kinesis's reset instructions; this clears all Bluetooth bonds.
4. Flash the new left UF2, power both halves off, then power the left half on.
5. Flash the right UF2 using its physical reset button, unplug it, and power it
   on.
6. Pair profile 0 to the Mac, profile 1 to Windows, profile 2 to Linux.
7. Allow the keyboard to enter its normal idle state after selecting a profile
   so the startup selection is persisted.

Follow the vendor procedure rather than copying both files while both halves
are running: <https://github.com/KinesisCorporation/Adv360-Pro-ZMK#flashing-firmware>

## Acceptance checklist

- `make validate` passes and both halves compile.
- Fast prose typing produces no stray modifiers; `sd`, `kl`, `df`, `jk` roll
  cleanly.
- `Cmd+C`/`Cmd+V` work from the inner thumb; cross-hand home-row mods work in
  both directions.
- `SYS` + `W` makes Windows shortcuts land correctly, and `NAV` word motion
  changes with it; `SYS` + `A` restores macOS behaviour.
- All `GLOBAL` signals work in AeroSpace, Hyprland and komorebi.
- Caps Word and repeat work; editors handle automatic bracket pairs.
- Layer indicators are dim, the white backlight starts off, and LEDs stop while
  idle.
- USB/BLE output and profiles 0-2 work after the clean reset.
