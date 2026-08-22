# Advantage360 Pro developer keymap

Source-controlled ZMK firmware for a Kinesis Advantage360 Pro, tuned for Python
and data engineering — SQL, PySpark, Databricks — with Vim-shaped editing.
macOS and Linux are the primary hosts; Windows is supported and kept working.
PowerShell is served by the symbol layout rather than by macros.

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
| `NAV` | Hold left middle thumb, or hold `Del` | Motion, clipboard, editor verbs |
| `SYM` | Hold right middle thumb, or hold `Enter` | Programming symbols |
| `NUM` | Hold left bottom thumb; tap that key again to lock | Numpad and F1-F12 |
| `GLOBAL` | Hold right bottom thumb | Host-neutral window-manager protocol |
| `SYS` | Hold bottom-right | Bluetooth, output, lighting, maintenance |
| `NAV_WIN` | Automatic (`WIN` + `NAV`) | Ctrl-flavoured overrides for `NAV` — used by Linux *and* Windows |

`NAV_WIN` is a conditional layer you never select directly.

`NAV_WIN` fires when the `WIN` base is active and you hold `NAV`. `Cmd+C`
becomes `Ctrl+C`, Option-word-motion becomes Ctrl-word-motion, document
start/end become `Ctrl+Home`/`Ctrl+End`, and browser history moves to
`Alt+Left`/`Alt+Right`. Muscle memory stays identical on both operating
systems.

Every position on every layer is bound. `&trans` is content, not emptiness: it
exposes the layer underneath, which is exactly what makes `WIN` a thin overlay
instead of a duplicated base. What the layout does not contain is `&none` —
`make validate` fails if a dead key appears.

## Home-row mods

```text
hold:   A     S      D      F           J       K      L      ;
        Cmd   Alt    Ctrl   —           —       Ctrl   Alt    Cmd     (MAC)
        Ctrl  Alt    Cmd    —           —       Cmd    Alt    Ctrl    (WIN)
```

**`F` and `J` are plain letters.** Shift is not a home-row mod here — it lives
on the outer pinkies, for reasons in the next section. That also keeps a hold
decision off the two homing-bump keys your index fingers rest on.

Three properties keep these from misfiring during fast typing:

- `require-prior-idle-ms = 150` — if you pressed another key within the last
  150 ms, the hold is abandoned outright and the key is a plain letter. This is
  what stops rolls like `sd` or `kl` becoming modifiers.
- `hold-trigger-key-positions` — only the *opposite* hand and the thumbs can
  resolve a hold. Same-hand rolls always stay letters.
- `quick-tap-ms = 175` — tap then hold the same key within 175 ms to repeat the
  letter instead of engaging the modifier.

Two consequences worth internalising:

- **Shift comes from the outer pinkies**, not the home row, so there is no
  same-hand suppression to work around. `:` is `SYM`+`F`.
- **Same-hand `Cmd`/`Ctrl` combos use the thumb**, not the home row.
  `Cmd+C` is inner-left-thumb + `C`.

If the timings do not suit you, they are the four numbers in the `hml`/`hmr`
behaviors at the top of `config/adv360.keymap`. Raise `require-prior-idle-ms`
toward 200 if you still get accidental mods; lower `tapping-term-ms` toward 200
if holds feel sluggish.

### Smart shift on the outer pinkies

This is where all Shift lives, and the reason it is not on the home row.

`require-prior-idle-ms` makes a capital *mid-word* impossible from the home
row: the hold starts inside the 150 ms window and gets abandoned. That costs
nothing in `snake_case`, but it shows up constantly in PascalCase and after a
hyphen — `Get-ChildItem` would come out `Get-childitem`, and `DataFrame` and
`StructType` are the same shape. A home-row Shift that fails on the most
common capital in the language is not worth the finger it sits on.

The two outer `Shift` keys run `&sms`:

| Action | Result |
|---|---|
| **Hold** | real `Shift` — Shift+click, Shift+arrow selection, Shift-modified `GLOBAL` signals |
| **Tap** | sticky `Shift` — the next character is capitalised, with no timing window to hit |

`hold-preferred` flavour means any other key pressed during the term resolves
the hold, so held-Shift behaviour is byte-for-byte what it was before. Only a
tap with nothing else pressed produces the sticky. For a whole run of capitals,
`Caps Word` is still on the inner top-left key.

## Thumbs

`NAV` and `SYM` each have two routes. The small middle thumb keys are plain
`&mo` — instant, and incapable of misfiring. The large `Del` and `Enter` keys
are layer-taps (`tlt`) onto the same layers, for when your thumb is already
resting there.

The layer-taps use `tap-preferred`, so only the timer resolves the hold:
rolling `Del` or `Enter` into the next key always types the key. Reaching the
layer that way costs about 200 ms, which is why the instant `&mo` keys stay.
`quick-tap-ms` preserves auto-repeat, so holding `Del` to eat a run of text
still works.

`Space` and `Backspace` are deliberately *not* layer-taps. Space rolls into the
following letter constantly, and the protection that makes the home-row mods
safe — `require-prior-idle-ms` — cannot be used here: it would disable the hold
for exactly the mid-sentence case where the layer is wanted. Backspace needs
plain hold-to-repeat. On a 36-key board you would have no choice; the
Advantage 360 has six thumb keys per hand, so there is no reason to gamble on
the two highest-frequency ones.

## Symbols

> **Every host must be set to a US keyboard layout.** The keyboard sends HID
> usages, not characters; the host layout decides what each usage prints. On a
> Czech, Polish or other non-US layout the entire `SYM` layer and every text
> macro produce the wrong characters — `[` becomes `ú`, `:` becomes `"`, and
> so on. This is a host setting, not something the firmware can compensate for.
> Use a US layout on every profile and get national characters from a host-side
> compose key or input switcher.

The `SYM` home row is an enclosure ladder, mirrored around the centre:

```text
   {   [   (   :   <   │   >   _   )   ]   }   =
   A   S   D   F   G       H   J   K   L   ;   '
```

The `│` is the mirror axis, not a key — it marks the gap where the thumb
cluster sits. `|` itself lives on the upper row and again on the fourth row.

The ladder is rotated one position outward from the arrangement you might
expect, and the rotation is the whole point:

- `:` and `_` are the two highest-frequency punctuation marks in Python and
  SQL — every block header, every `snake_case` identifier — so they sit on `F`
  and `J`, index home, the strongest fingers on the row.
- `<` and `>` are the rarest, so they take `G` and `H`, which are index
  *stretches* into the bowl and the two worst positions on the row.
- The closing brackets sit outboard of the openers because editors auto-close:
  you type `(` and receive `()`. `)`, `]` and `}` are pressed far less often
  than the ladder's symmetry suggests, so they do not need prime keys.

The number row keeps the familiar US shifted-number symbols, the upper row
carries `~ \` \ | ;` and `" ' ? / \`, and the fourth row carries the
shell/PowerShell set `^ $ - _ *` and `& | !`.

`=` and `-` also keep their unshifted home on the base number row, so they are
available without a layer at all.

## Macros

The macro bank is twelve multi-character operators, and it lives entirely on
`SYM` — one thumb away, no dedicated layer:

```text
   <>  ->  ||  !=  ==    │    <=  >=  ::  __
```

with `**` and `:=` just above them, and `0x` on `NUM`. `||` is SQL string
concatenation; it replaced `=>`, which nothing in Python, SQL or PowerShell
uses.

### What earns a slot

**A multi-character operator that no editor completes for you.** `->`, `:=`,
`**`, `!=` are single tokens to the language but two keystrokes to you, and no
LSP offers them from a prefix, because there is no prefix to offer from.

**Anything with autocomplete behind it does not.** There used to be a
sixty-macro bank here — `SELECT`, `FROM`, `PARTITION BY`, `F.col("")`,
`dbutils.`, `TODO:` and forty more — on a dedicated `MACRO` layer. It was
removed. Every SQL surface in use completes keywords from two characters with
schema awareness that firmware cannot have, and Pylance does the same for the
Python and PySpark side. Each macro saved about two keystrokes and cost a
memorised position on a layer that had to be chorded into.

Removing the bank also removed its failure mode. `MACRO` was reached by
holding both middle thumbs, which is where the thumbs *rest* — so an
accidental rest silently typed text, giving you `f""` where you wanted `[`.
Resting a thumb on a key shaped for resting is not a habit you can train away.

### No PowerShell macros

PowerShell is fast without them. `-` is unshifted on the base number row, so
`-match`, `-replace`, `-split` and `-join` are plain typing with no layer hop.
Every PowerShell symbol already sits on `SYM` — `$` `_` `@` `{}` `()` `|` `~` —
so `$_`, `$()`, `@()` and `@{}` are a single `SYM` hold. Only `2>&1` needs two
`SYM` transitions, and it is rare enough not to earn a key.

### Rules

Macros are plain tap sequences defined in `config/macros.dtsi`. None hold a
modifier across the sequence, so none can leave a modifier stuck.

**Keep sequences at or under 15 taps.** Each tap is two HID reports and
`CONFIG_ZMK_BLE_KEYBOARD_REPORT_QUEUE_SIZE` is 40; past that ZMK drops the
overflow silently, so an over-long macro types correctly over USB and
truncated over Bluetooth. `make validate` enforces both halves of that
arithmetic, including the case where someone lowers the queue size. Nothing in
the bank comes close now — the longest is two taps — but the check is what
makes it safe to add one later.

To add one, copy a `TEXT_MACRO(...)` line and bind it somewhere. `make
validate` fails on a macro that is defined but never used, and on one that is
used but never defined.

## GLOBAL host protocol

`GLOBAL` never sends application-specific shortcuts. It emits F13-F20 with
modifiers, and each host translates:

Two of those slots are not literally F14/F15 on the wire. macOS treats those
two keycodes as display brightness below application delivery and regardless
of modifiers, so all fourteen signals containing them fired the brightness OSD
alongside the real action. They are sent as the keypad divide and multiply
keys instead - `KP_DIVIDE`/`KP_MULTIPLY` in the keymap, `keypadDivide`/
`keypadMultiply` on macOS, `KP_Divide`/`KP_Multiply` on Linux,
`NumpadDiv`/`NumpadMult` on Windows. The keypad range is the only range this
keymap never otherwise touches. The table below keeps the F14/F15 names as
protocol slot labels.

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
| `Ctrl+Alt+F20` | Pin (sticky) window — macOS substitutes fullscreen |
| `Alt+Shift+F13`-`F16` | Screenshot region, screenshot window, clipboard history, colour picker |
| `Alt+Shift+F17` | Neovim in a terminal |
| `Alt+F13`-`F20` | Terminal, browser, code, files, launcher, chat, notes, git |

The pattern is consistent: adding `Shift` to a "go there" signal turns it into
"take the window there".

### Moving between displays

Display work is one cluster on the right hand. The home row is focus, the row
directly above it is move-window, so the same finger does both and the row
decides whether the window comes with you:

```text
upper row    move win  L  D  U  R  │  move win to prev monitor / next monitor
home row     focus     L  D  U  R  │  focus       prev monitor / next monitor
```

The monitor keys sit immediately right of the `HJKL` focus cluster, so "throw
this window to the other screen, then follow it" is two adjacent keys under one
hand rather than two corners of the board. The bottom row mirrors focus and
monitors onto the left hand, so the layer stays usable one-handed.

The number row is workspaces end to end — 1-8, then previous and next.

### Neovim

`Alt+Shift+F17` opens Neovim in the terminal each host already uses for the
`Alt+F13` terminal slot and the `Alt+F20` lazygit slot, so the three share one
terminal definition. Change it in one place per host: `$nvim` in
`hyprland.conf`, the `alt-shift-f17` line in `aerospace.toml`, `NVIM` in
`adv360-global.ahk`.

Nothing else about Neovim needs firmware support: `Esc` is already left of `A`,
`Ctrl` is a real key on the thumbs so `Ctrl+D`/`Ctrl+U`/`Ctrl+W` work without
the home row, `NAV`'s arrows are on `HJKL`, and `Insert` is on `NAV` for
`Shift+Insert` paste in Linux terminals.

Ready-to-use consumers live in `host/`:

| Host | File | Requires |
|---|---|---|
| macOS | `host/macos/aerospace.toml` | AeroSpace |
| Linux | `host/linux/hyprland.conf` | Hyprland |
| Windows | `host/windows/adv360-global.ahk` | AutoHotkey v2, komorebi |

`make validate` checks both that each host binds every signal *and* that its
command matches the documented intent — 126 assertions across the movement
family. Presence alone is not enough: macOS ran `move-workspace-to-monitor` for
`Ctrl+Shift+F17` for a long time, moving the whole workspace to another display
while Linux and Windows moved the window to the adjacent workspace, and every
presence check passed throughout.

Three bindings are deliberate approximations, listed in `APPROXIMATIONS` in
`bin/validate_protocol.py` so they stay visible: Hyprland has no balance-layout
command, AeroSpace has no pin — it fullscreens instead, duplicating `Ctrl+F19`
rather than mislabelling `layout floating` as pinning — and komorebi's monocle
stands in for fullscreen.
The app-launcher and screenshot banks are excluded from the intent check —
Ghostty, `wt.exe` and a Hyprland variable are all correct answers to
"terminal".

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
    =        1        2        3        4        5       Esc                                                               Tab       6        7        8        9        0        -
   Tab       Q        W        E        R        T       Caps                                                              Rept      Y        U        I        O        P        \
   Esc      A/G      S/A      D/C       F        G       Alt               Ctrl     Cmd    |    Cmd      Ctrl              Alt       H        J       K/C      L/A      ;/G       '
   Shft      Z        X        C        V        B                                  NAV    |    SYM                                  N        M        ,        .        /       Shft
    `        [        ]        (        )                         Bspc   Del/NAV    NUM    |   GLOBAL  Ent/SYM    Spc                         <-       v        ^        ->      SYS
```

**WIN**

```text
  ^^    ^^    ^^    ^^    ^^    ^^    ^^                                           ^^    ^^    ^^    ^^    ^^    ^^    ^^
  ^^    ^^    ^^    ^^    ^^    ^^    ^^                                           ^^    ^^    ^^    ^^    ^^    ^^    ^^
  ^^   A/C   S/A   D/G    ^^    ^^    ^^         Cmd   Ctrl  |  Ctrl  Cmd          ^^    ^^    ^^   K/G   L/A   ;/C    ^^
  ^^    ^^    ^^    ^^    ^^    ^^                      ^^   |   ^^                      ^^    ^^    ^^    ^^    ^^    ^^
  ^^    ^^    ^^    ^^    ^^                ^^    ^^    ^^   |   ^^    ^^    ^^                ^^    ^^    ^^    ^^    ^^
```

**NAV**

```text
  G-`     G-1     G-2     G-3     G-4     G-5      ^^                                                         ^^     G-6     G-7     G-8     G-9     G-0     G-W
   ^^     G-A     G-S     G-F    G-S-F    G-P      ^^                                                         ^^     A-<-    PgDn    PgUp    A-->    G-^     G-v
   ^^     G-Z     G-X     G-C     G-V    G-S-Z     ^^              ^^      ^^    |    ^^      ^^              ^^      <-      v       ^       ->     Home    End
   ^^      F2     F12    S-F12     F3     S-F3                             ^^    |    ^^                            A-Bspc  A-Del    Bspc    Del     Ins      ^^
  G--     G-[     G-]     G-=    G-S-T                     ^^      ^^      ^^    |    ^^      ^^      ^^                     G-/     A-v     A-^    G-S-K     ^^
```

**SYM**

```text
  ^^    !     @     #     $     %     ^^                                           ^^    ^     &     *     (     )     ^^
  ^^    ~     `     \     |     ;     ^^                                           ^^    "     '     ?     /     \     ^^
  ^^    {     [     (     :     <     ^^          ^^    ^^   |   ^^    ^^          ^^    >     _     )     ]     }     =
  ^^    ^     $     -     _     *                       ^^   |   ^^                      &     |     **    :=    !     ^^
  <>    ->    ||    !=    ==                ^^    ^^    ^^   |   ^^    ^^    ^^                <=    >=    ::    __    ^^
```

**NUM**

```text
  F1    F2    F3    F4    F5    F6    ^^                                           ^^    ^^    ^^    ^^    ^^    ^^    ^^
  F7    F8    F9   F10   F11   F12    ^^                                           ^^    7     8     9     /     *    Bspc
  ^^    A     B     C     D     E     ^^          ^^    ^^   |   ^^    ^^          ^^    4     5     6     -     +    Ent
  ^^    F     0x    =     <     >                       ^^   |   ^^                      1     2     3     .     ,     ^^
  %     ^     *     (     )                 ^^    ^^   ~NUM  |   ^^    ^^    ^^                0     .     =    Ent    ^^
```

**GLOBAL**

```text
  C-S-F17      F13         #/         #*        F16        F17         ^^                                                                              ^^        F18        F19        F20       C-F17      C-F18     C-S-F18
  A-S-F13    C-S-F19     C-F20      A-F16     C-A-F19     A-F13     A-S-F17                                                                            ^^      C-S-F13     C-S-#/     C-S-#*    C-S-F16   C-A-S-F17  C-A-S-F18
     ^^       A-F17      A-F18      A-F19      C-F19      A-F20        ^^                    ^^         ^^     |      ^^         ^^                    ^^       C-F13       C-#/       C-#*      C-F16     C-A-F17    C-A-F18
     ^^       A-S-#/     A-S-#*      A-#*     A-S-F16      A-#/                                         ^^     |      ^^                                       C-A-F13     C-A-#/     C-A-#*    C-A-F16    C-A-F20       ^^
  C-S-F20     C-F17      C-F18     C-A-F17    C-A-F18                             ^^         ^^         ^^     |      ^^         ^^         ^^                             C-F13       C-#/       C-#*      C-F16        ^^
```

**SYS**

```text
      USB            BT0            BT1            BT2            BT3            BT4             ^^                                                                                                          ^^            BLE            Out~           BT>            BT<            Lum-           Lum+
      BL~            BL-           =>WIN           BL+             ON            OFF             ^^                                                                                                          ^^            BTx0           BTx1           BTx2           BTx3           BTx4           SPD
 studio_unlock      =>MAC           HUD            HUI            SAD            SAI             ^^                            ^^             ^^       |        ^^             ^^                            ^^            RGB            BRD            BRI            EFF            EFR            SPI
       ^^           PrtSc           ScLk           Paus           Menu           Caps                                                         ^^       |        ^^                                                         Prev           Play           Next           Vol-           Vol+            ^^
      Stop           Ejct           Calc           File           Srch                                          ^^             ^^             ^^       |        ^^             ^^             ^^                                          Mute           #Num           Lang           Lock            ^^
```

**NAVWIN**

```text
 C-Tab    C-1     C-2     C-3     C-4     C-5      ^^                                                         ^^     C-6     C-7     C-8     C-9     C-0     C-W
   ^^     C-A     C-S     C-F    C-S-F    C-P      ^^                                                         ^^     C-<-     ^^      ^^     C-->   C-Home  C-End
   ^^     C-Z     C-X     C-C     C-V    C-S-Z     ^^              ^^      ^^    |    ^^      ^^              ^^      ^^      ^^      ^^      ^^      ^^      ^^
   ^^      ^^      ^^      ^^      ^^      ^^                              ^^    |    ^^                            C-Bspc  C-Del     ^^      ^^      ^^      ^^
  C--     A-<-    A-->    C-=    C-S-T                     ^^      ^^      ^^    |    ^^      ^^      ^^                     C-/      ^^      ^^    C-S-K     ^^
```

**Macro reference** — full contents of the `MACRO` layer. A trailing
space is part of the keyword macros. `^` marks where the caret lands
when the macro repositions it.

*Comparison*

`==` &nbsp;&middot;&nbsp; `!=` &nbsp;&middot;&nbsp; `<=` &nbsp;&middot;&nbsp; `>=` &nbsp;&middot;&nbsp; `<>`

*Assignment, arithmetic, scope*

`:=` &nbsp;&middot;&nbsp; `->` &nbsp;&middot;&nbsp; `**` &nbsp;&middot;&nbsp; `||` &nbsp;&middot;&nbsp; `::` &nbsp;&middot;&nbsp; `__`

*Literals*

`0x`

<!-- END GENERATED LAYERS -->

## Bluetooth and firmware safety

Profiles are assigned consistently:

1. Profile 0: Mac
2. Profile 1: Windows
3. Profile 2: Linux
4. Profiles 3-4: spare

**Linux runs on the `WIN` base.** Press `SYS` + `W` after selecting profile 2.
Linux and Windows both use `Ctrl` where macOS uses `Cmd`, so `WIN` is really
"the Ctrl base" and `NAV_WIN` is the Ctrl-flavoured editing layer for both. The
bindings that differ between the two — redo, and the editor cluster — are set
to the Linux-correct form, which is also what VS Code accepts on Windows.

Four `SYS` keys are Linux-only: calculator, files, search and lock are HID
consumer usages that GNOME and KDE honour and macOS ignores entirely. `PrtSc`
and `Menu` are the same. All of them are reachable host-neutrally through
`GLOBAL`'s app bank instead, which is the layer built for it. `Globe` is
macOS-only and worth verifying on your machine — macOS often will not accept it
from a third-party keyboard.

`SYS` exposes explicit USB, BLE and output-toggle keys. Destructive actions are
combos, and only on `SYS`:

| Combo (on `SYS`) | Action |
|---|---|
| `=` + `-` (outer ends of the number row) | Clear all Bluetooth bonds |
| Both outer `Shift` keys | Soft reset |
| `Caps Word` + `Repeat` (the inner pair on the upper row) | Enter bootloader |

Each one spans both hands and uses opposite ends of a row, so none can fire
from a fumbled one-handed press. Deliberately, none of them sit on the
Bluetooth profile keys: chording two adjacent profile selectors is exactly what
you do when switching hosts, and that must never be able to wipe your bonds.
`make validate` rejects any destructive combo placed on a single hand.

Five profiles plus the split link to the right half means the central needs six
BLE connections, so `CONFIG_BT_MAX_CONN` and `CONFIG_BT_MAX_PAIRED` are both
set to 6 in `adv360_left_defconfig`. ZMK defaults both to 5, which starves the
last profile. Per ZMK's split guidance they are set on the central only.

Use the physical reset button for the right half when necessary. Runtime ZMK
Studio/Clique keymap editing is disabled; git is the source of truth.

### HID descriptor changes

`adv360.conf` selects the extended NKRO keyboard report (needed for F13-F24)
and the full consumer usage range (needed for the `SYS` calculator, files,
search and lock keys, which live above `0x0FF`). Both alter the HID report
descriptor. Hosts cache that descriptor per bond, so after changing either
setting you must remove the keyboard on each host and re-pair, or the host
keeps using the old descriptor and the new keys appear dead.

The extended keyboard report is known to break Android hosts. No profile here
is an Android device; if one becomes one, that profile loses F13-F24.

`make validate` fails if the keymap binds a consumer key that the configured
usage range cannot send.

## Power

The board is wireless, so idle behaviour matters more than it would on a
tethered keyboard.

| Setting | Value | Why |
|---|---|---|
| `CONFIG_ZMK_SLEEP` | `y` | ZMK ships deep sleep **off**. This is the single largest idle drain. |
| `CONFIG_ZMK_IDLE_TIMEOUT` | 30 s | Lighting and scanning wind down; the next keypress brings them back. |
| `CONFIG_ZMK_IDLE_SLEEP_TIMEOUT` | 1 hour | Radio and peripherals off; the first keypress wakes and reconnects. |
| `CONFIG_ZMK_RGB_UNDERGLOW_ON_START` | `y` | Underglow is lit at boot. |
| `CONFIG_ZMK_BACKLIGHT_ON_START` | `n` | The white key backlight stays off; reach it from `SYS`. |

An hour of idle before deep sleep rather than ZMK's 15-minute default, because
15 minutes is reachable during a working day and the battery difference is
small. Nearly all the saving comes from sleeping overnight and at weekends, so
waiting an extra 45 minutes out of a 16-hour idle stretch gives up roughly 5%
of it. Shorten `CONFIG_ZMK_IDLE_SLEEP_TIMEOUT` if you would rather have the
battery than the instant wake.

Battery level is reported to the host for both halves: the central owns the
battery service, and `CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING` plus
`..._PROXY` pull the right half's level across the split link and republish it.
Windows needs `CONFIG_BT_GATT_ENFORCE_SUBSCRIPTION=n` to deliver those
notifications; it is harmless on macOS and Linux.

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
bin/validate_keymap.py          # layer shape, arity, dead keys, macros, combos,
                                # consumer usage range, macro length vs BLE queue
bin/validate_protocol.py        # GLOBAL layer vs. the three host configs
bin/render_keymap.py            # print the layer diagrams
bin/render_keymap.py --write    # regenerate the diagrams in this README
bin/render_keymap.py --check    # fail if the diagrams are stale
```

`validate_protocol.py` is the one that catches the quiet failures: it parses
the `GLOBAL` layer and all three host files and fails if a signal is emitted
but unhandled, handled but unreachable, or handled by two hosts and forgotten
by the third.

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
- Focus-monitor and move-window-to-monitor sit next to each other; throwing a
  window to the other display and following it is two adjacent keys.
- `Ctrl+Shift+F17`/`F18` moves the *window* to the adjacent workspace on all
  three hosts — macOS used to move the whole workspace to another display.
- `Alt+Shift+F17` opens Neovim.
- Caps Word and repeat work; editors handle automatic bracket pairs.
- Every host is on a US keyboard layout; `SYM` and the macros print the
  characters they name.
- Tapping an outer `Shift` capitalises the next character; holding it still
  Shift+clicks and still extends a selection with the arrows.
- On Linux, `SYS` + `W` is set, `NUM`'s digits type digits with NumLock **off**,
  and redo is `Ctrl+Shift+Z`.
- `SYM`'s operator macros print `-> := ** != == <= >= || :: <>` correctly over
  BLE on every profile.
- Holding the `NUM` thumb and tapping it again locks the layer; tapping once
  more leaves it. A long column of figures needs no sustained hold.
- The two inner top keys type `Esc` and `Tab`; `SYS` still answers to the
  bottom-right key alone.
- `F` and `J` type `f` and `j` at speed with no modifier misfire, including
  when rolled into from the previous letter.
- `NAV` + the arrow cluster toggles a comment, moves a line up and down, and
  deletes a line, on both bases.
- `SYS` media keys work, **and** so do calculator, files, search and lock —
  those four need the full consumer usage range and a re-pair after the HID
  descriptor change.
- Underglow is lit at boot, dims out after 30 s idle and returns on the next
  keypress; the white backlight starts off and is reachable from `SYS`.
- The board is still awake after a 20-minute meeting.
- The host shows a battery level for both halves, Windows included.
- The keyboard wakes from deep sleep on the first keypress and reconnects to
  the selected profile.
- USB/BLE output and profiles 0-4 work after the clean reset.
