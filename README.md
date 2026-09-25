# Advantage360 Pro — macOS daily driver

Five layers, QWERTY with bilateral home-row modifiers, and immediate thumb holds
for ABC/US coding and Czech writing. HRMs are tuned for fast typing with a 150 ms
prior-idle gate; dedicated thumb/inner modifiers remain available for deterministic
zero-delay chords. No sticky modifiers or layer toggles.

**Start here:** [current HRM profile](docs/hrm-profile-20260925.md),
[baseline overhaul report](docs/overhaul-20260925.md), [cheat sheet](docs/cheat-sheet.md), [installation and rollback](docs/setup.md),
[editor/input-source notes](docs/editor.md), [validation results](docs/validation.md),
[design and source audit](docs/research.md).

## ZMK Studio

The left/central firmware enables ZMK Studio over USB and Bluetooth with locking
disabled, so no unlock key is needed. Build and flash the updated firmware before
connecting: existing firmware files do not pick up configuration changes.
Connect the left half by USB and open [ZMK Studio](https://zmk.studio/) in Chrome
or Edge. Select USB output on SYS when using Studio over USB. The native Studio
app also supports Bluetooth on macOS.

Studio saves keymap edits on the keyboard. To apply later changes from this
repository's keymap, use **Restore Stock Settings** in Studio; this discards saved
Studio edits. The diagrams here describe the repository keymap.

## Thumb controls

Positions are zero-based vendor positions, printed on the [layer images](docs/layers/all-layers.png).
Stock keycap names are useful landmarks; follow the actual diagrams after flashing.

| Thumb position | BASE action | Why |
|---|---|---|
| 65, large left Backspace | Backspace | Retains a preferred typing key |
| 66, large left Delete | Hold NUM | Immediate access on a preferred large key |
| 67, small lower left (End) | Delete | Adjacent replacement for displaced Delete |
| 52, small middle left (Home) | Hold NAV | Retains the newest layout's navigation access |
| 53, small middle right (Page Up) | Hold SYM | Left hand is free for symbols |
| 68, small lower right (Page Down) | Delete; NUM: Backspace | Editing beside the numeric grid |
| 69, large right Enter | Enter | Unchanged |
| 70, large right Space | Space; NUM: 0 | Comfortable zero while the left thumb holds NUM |
| 35/36, upper left | Command / Control | Plain dedicated modifiers |
| 37/38, upper right | Control / Command | Plain dedicated modifiers |

Option stays on the inner home-row keys (34/39); both outer Shift keys remain
ordinary Shift. BASE also adds mirrored HRMs: **A/S/D/F = Cmd/Option/Ctrl/Shift**
and **J/K/L/; = Shift/Ctrl/Option/Cmd**. Tapping still types the normal character.
The dedicated modifiers stay in place as the fast, timing-free fallback. Tab and
Escape stay on the outer left Q/home rows. Caps Word is on inner left Q-row key 20.
Inner right Q-row key 21 is a second Tab.

## Five layers

- **BASE (0):** physical US QWERTY with fast-typing bilateral HRMs plus dedicated modifiers and editing keys.
- **NAV (1):** hold 52. ASDF = **Ctrl / Option / Command / Shift**;
  JKL; = **Left / Down / Up / Right** — deliberately JKL;, never HJKL. H/quote =
  line start/end; U/P = word left/right; Y/backslash = document start/end; I/O =
  page down/up. App-specific Cmd shortcuts are intentionally not duplicated here.
- **SYM (2):** hold 53. ASDF = `{ [ ( :`; JKL; = `_ ) ] }`.
  G/H = `< >`; quote = `=`. Single keys combine into operators without macros.
- **NUM (3):** hold 66. **UIO = 789, JKL = 456, M comma period = 123**.
  Space thumb = 0; slash position = decimal point; backslash = comma.
  Y/P = divide/multiply; H/semicolon = minus/plus; quote = equals.
- **SYS (4):** hold bottom-right key 75. Function/media keys, five Bluetooth
  profiles, USB/BLE selection, lighting, and deliberate maintenance controls.

Higher numbered active layers take priority; transparent keys use the next active
layer underneath. Every layer keeps all four access keys and dedicated modifiers.
Release all holds to return to BASE. SYS + bottom-left-inner key 64 also cancels
active layers; release all keys before resuming. Escape always sends Escape.

The large left Delete key is deliberately spent on NUM. This favors immediate
number entry over keeping both large left editing keys. Delete remains on two
small thumb keys; NUM puts Backspace beside right Enter. Five layers keep the
core small; function/media share SYS. Previous desktop/editor/pointer banks are
preserved in [profiles/previous](profiles/previous/README.md), along with unchanged
host integrations, but are not active in this keymap.

## Input sources

NUM uses **keypad digits and operators**, verified against this Mac's ABC, US and
Czech layout tables. Ordinary `.` and `,` give a stable decimal point/comma in
those tables. Czech keypad decimal would produce `,`, so it is deliberately not
used. Live VS Code, Neovim, Windows Remote Desktop and keyboard transport checks
remain in the [hardware checklist](docs/setup.md#hardware-acceptance).

Select **ABC/US for SYM and coding**. The firmware sends keycodes, cannot detect
macOS's active source, and cannot make US symbol codes universal. Czech is QWERTZ
at the host (physical Y/Z swap), with diacritics on the number row; firmware does
not compensate or remove Option access. See [editor notes](docs/editor.md).

## Build

Run `make validate`, then `make` to compile **both halves** using the existing
Docker/Podman process. `make left` is an explicitly partial build. No flashing or
host configuration changes are automatic. The Kinesis fork is pinned to the
previously built commit `f1d5fc736bdbdde11df0ec77114c6a398ee1252b`; this is not a
firmware upgrade. Both effective configs, exact config source and a frozen
manifest accompany the UF2 pair. See [validation](docs/validation.md).

Render ASCII diagrams with `make render`; regenerate PNGs with
`python3 bin/render_layer_images.py` (Pillow required only for rendering).
`make validate` checks both generated forms without Pillow.

## Layer diagrams

The PNGs use the vendor's 76-key physical geometry, including stagger and tall
thumb keys: [BASE](docs/layers/00-base.png), [NAV](docs/layers/01-nav.png),
[SYM](docs/layers/02-sym.png), [NUM](docs/layers/03-num.png), [SYS](docs/layers/04-sys.png).

<!-- BEGIN GENERATED LAYERS -->

`^^` falls through to the highest active lower layer; `--` is inactive.
`C-` Ctrl, `S-` Shift, `A-` Option, `G-` Command; `#` marks keypad codes.
NAV/SYM/NUM/SYS are held; `=>BASE` cancels active layers. Left/right thumb
clusters appear in the middle, separated by `|`. See the PNGs for key shapes.

**BASE**

```text
  =     1     2     3     4     5    F11                                          F12    6     7     8     9     0     -
 Tab    Q     W     E     R     T    Caps                                         Tab    Y     U     I     O     P     \
 Esc   A/G   S/A   D/C   F/S    G    Alt         Cmd   Ctrl  |  Ctrl  Cmd         Alt    H    J/S   K/C   L/A   ;/G    '
 Shft   Z     X     C     V     B                      NAV   |  SYM                      N     M     ,     .     /    Shft
  `     [     ]     (     )                Bspc  NUM   Del   |  Del   Ent   Spc                <-    v     ^     ->   SYS
```

**NAV**

```text
   ^^      ^^      ^^      ^^      ^^      ^^      ^^                                                         ^^      ^^      ^^      ^^      ^^      ^^      ^^
   ^^      ^^      ^^      ^^      ^^      ^^      ^^                                                         ^^     G-^     A-<-    PgDn    PgUp    A-->    G-v
   ^^     Ctrl    Alt     Cmd     Shft     ^^      ^^              ^^      ^^    |    ^^      ^^              ^^     G-<-     <-      v       ^       ->     G-->
   ^^      ^^      ^^      ^^      ^^      ^^                              ^^    |    ^^                            A-Bspc  A-Del    Bspc    Del    G-Bspc    ^^
  Home    End    C-Home  C-End    Ins                      ^^      ^^      ^^    |    ^^      ^^      ^^                      ^^      ^^      ^^      ^^      ^^
```

**SYM**

```text
  ^^    !     @     #     $     %     ^^                                           ^^    ^     &     *     (     )     ^^
  ^^    ~     `     \     |     ;     ^^                                           ^^    "     '     ?     /     \     ^^
  ^^    {     [     (     :     <     ^^          ^^    ^^   |   ^^    ^^          ^^    >     _     )     ]     }     =
  ^^    !     $     -     +     *                       ^^   |   ^^                      /     |     ,     .     %     ^^
  @     #     &     ^     ~                 ^^    ^^    ^^   |   ^^    ^^    ^^                <     >     ;     =     ^^
```

**NUM**

```text
  ^^    ^^    ^^    ^^    ^^    ^^    ^^                                           ^^    ^^    ^^    ^^    ^^    ^^    ^^
  ^^    ^^    ^^    ^^    ^^    ^^    ^^                                           ^^    #/    #7    #8    #9    #*    ,
  ^^    ^^    ^^    ^^    ^^    ^^    ^^          ^^    ^^   |   ^^    ^^          ^^    #-    #4    #5    #6    #+    #=
  ^^    ^^    ^^    ^^    ^^    ^^                      ^^   |   ^^                      #0    #1    #2    #3    .     ^^
  ^^    ^^    ^^    ^^    ^^                ^^    ^^    ^^   |  Bspc   ^^    #0                #0    .     #=   Ent    ^^
```

**SYS**

```text
  USB     BT0     BT1     BT2     BT3     BT4     Boot                                                       Boot    BLE     Out~    BT>     BT<     Lum-    Lum+
   ^^      F1      F2      F3      F4      F5     Rset                                                       Rset     F6      F7      F8      F9     F10      --
   ^^     F11     F12      --      --      --      ^^              ^^      ^^    |    ^^      ^^              ^^      --      --      --      --      --      --
   ^^     BL~     BL-     BL+     RGB     EFF                              ^^    |    ^^                             Prev    Play    Next    Vol-    Vol+     ^^
  Caps    #Num    BRD     BRI    =>BASE                   Bspc     ^^     Del    |   Del     Ent     Spc                     Mute    Stop    Ejct    Lang     ^^
```

<!-- END GENERATED LAYERS -->
