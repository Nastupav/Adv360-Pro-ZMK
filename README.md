# Advantage360 Pro six-layer developer workflow

Source-controlled ZMK firmware and host adapters for a Kinesis Advantage360 Pro.
The production candidate favors reliable daily typing over maximizing layer and
combo counts. macOS is primary; Linux is supported by the same firmware.

## Design contract

- Plain US QWERTY isolated taps on BASE.
- Bilateral home-row modifiers on `ASDF` and `JKL;`.
- G and H remain ordinary letters.
- Six-layer architecture: BASE, NAV, SYM, NUM, GLOBAL, SYS.
- Every layer has 76 bindings with no `&none`; deliberate `&trans` preserves
  momentary-layer release and modifier composition.
- Q+W -> Escape is the only BASE typing combo. It is BASE-only, 35 ms, and
  requires 80 ms of prior idle.
- Backspace, Delete, Enter, and Space remain plain. They are not timed layer
  keys.
- Only four thumbs are timed: Esc/NAV, Tab/SYM, Caps Word/NUM, and
  Alt+F13/GLOBAL.
- Layers are momentary. There are no layer toggles.
- AeroSpace owns macOS F13-F20 automation. Hyprland owns Linux automation.
- A clean build proves compatibility, not physical ergonomics. The seven-day
  field test remains mandatory before calling the layout optimized.

“Plain QWERTY” means isolated taps emit normal US QWERTY characters. Home-row
hold-taps and the Q+W combo remain timing-sensitive by design.

## BASE

```text
Home row
A             S             D             F        G
Cmd / A       Option / S    Ctrl / D      Shift / F  G

H        J             K             L             ;
H        Shift / J     Ctrl / K      Option / L    Cmd / ;
```

The mirrored plain Alt, Ctrl, and Cmd keys in the inner columns plus the outer
plain Shift keys are deterministic fallbacks when an HRM hold is undesirable.

HRM timing:

- balanced
- 180 ms tapping term
- 150 ms quick tap
- 120 ms prior idle
- opposite-hand positional hold trigger
- hold trigger on release

### Thumb controls

```text
Tap                         Hold
Esc                         NAV
Tab                         SYM
Caps Word                   NUM
Alt+F13 launcher carrier    GLOBAL
```

Plain frequent thumbs:

```text
Backspace    Delete    Enter    Space
```

`SYS` has three direct momentary keys: both top inner keys and the far-right
thumb key.

## Six-layer architecture

### BASE

US QWERTY, HRMs, plain frequent thumbs, physical arrows, and direct SYS access.

### NAV

Prime action zones:

```text
ASDF    Home / Page Down / Page Up / End
G/H     Option+Left / Option+Right (macOS word movement)
JKL;    Left / Down / Up / Right
YUIO    Scroll left / down / up / right
NM,.    Select left / down / up / right
```

Linux word movement remains composable with a plain Ctrl key plus NAV `J` or
`;`. The thumb area contains left/right/middle mouse clicks. Pointer movement is
intentionally omitted until real use shows that it is worth a dedicated control
surface.

### SYM

A direct symbol surface plus editor-independent literal developer tokens. SYM owns all 21 macros; CODE was merged into SYM.

Home row:

```text
A _    S :    D !    F ?    G =
H -    J +    K *    L &    ; |    ' "
```

Shared operators on the QWERTY row:

```text
Q ==    W !=    E <=    R >=    T ->
Y &&    U ||    I :=    O **    P //    \ ::
```

PowerShell, SQL, and shell tokens on the lower row:

```text
Z -eq   X -ne   C -lt   V -le   B -gt
N -ge   M <>    , $_    . --
```

All macros emit literal characters at 20/20 ms. They do not add spaces, move the
cursor, create pairs, or invoke editor shortcuts.

### NUM

- F1-F12 on the top row.
- Right-hand numpad.
- VS Code run/debug cluster on `ASDFG`:

```text
A F5    S F9    D F10    F F11    G F12
```

Standard Ctrl/Cmd chords remain composable from BASE; the former EDIT layer was
removed.

### GLOBAL

GLOBAL emits uncommon F13-F20 carriers. Firmware stays host-neutral; the host
adapter decides what each carrier means.

Application carriers:

```text
Tap GLOBAL thumb   Alt+F13   launcher
GLOBAL+T           Alt+F14   terminal
GLOBAL+W           Alt+F15   browser
GLOBAL+O           Alt+F16   files
GLOBAL+E           Alt+F17   editor
GLOBAL+P           Alt+F18   project
GLOBAL+U           Alt+F19   git
GLOBAL+I           Alt+F20   AI
```

Workspace and window controls use the existing protocol. Important physical
bindings:

```text
GLOBAL + [    Ctrl+F17    previous workspace
GLOBAL + ]    Ctrl+F18    next workspace
GLOBAL + J/K/L/;          focus left/down/up/right
```

See `host/PROTOCOL.md` and `host/protocol.json` for the complete contract.

### SYS

SYS merges Bluetooth, USB output, ZMK Studio, media, lighting, and protected
maintenance controls. MEDIA was merged into SYS.

## Bluetooth profiles and output control

Hold any direct SYS key, then press:

```text
SYS + 1..5    select Bluetooth profile 1..5
SYS + F       select the next Bluetooth profile
SYS + A       force USB output
SYS + S       force Bluetooth output
SYS + D       toggle USB/Bluetooth output
```

To pair a device:

1. Select a profile with `SYS + 1..5`.
2. On the host, open Bluetooth settings.
3. Pair with `Adv360 Dev`.

To clear the currently selected Bluetooth profile, hold SYS and chord `1+2`.
This is destructive. Select the intended profile first and do not press the
maintenance chord casually. Clearing one profile does not clear all profiles.

The right half is a Bluetooth peripheral. USB and ZMK Studio belong only to the
left/central half. Right-half RGB can turn off while idle to save battery; an
unlit indicator does not prove which profile is selected.

## ZMK Studio

1. Connect a data-capable USB cable to the left half.
2. Select USB output with `SYS + A`.
3. Open ZMK Studio and wait for its authorization prompt.
4. Press `SYS + U` only while Studio is requesting authorization.

Before flashing a source-controlled redesign, use **Restore Stock Settings** in
ZMK Studio. Persistent Studio edits can otherwise override the compiled keymap.
Studio edits are not automatically written back to this repository.

## Host ownership

AeroSpace owns macOS F13-F20 automation. Do not add another Hammerspoon or
Karabiner F13-F20 owner. Linux uses the Hyprland adapter.

Install or update the host adapters:

```sh
cd /Users/macbook/Desktop/kinesis360
python3 scripts/manage_host.py plan
python3 scripts/manage_host.py install
make verify-active
```

## Verify and build

```sh
cd /Users/macbook/Desktop/kinesis360
make verify
make verify-active
make clean_firmware
make
cd firmware
shasum -a 256 -c SHA256SUMS
```

`make` builds both halves in the pinned container. The resulting UF2 filenames
and source fingerprint are recorded in `firmware/build-manifest.json`.

Flash the left UF2 to the left half and the right UF2 to the right half. Do not
mix artifacts from different fingerprints.

## Seven-day physical acceptance

Initialize a fresh log after flashing:

```sh
python3 scripts/field_test.py init
```

Example session:

```sh
python3 scripts/field_test.py log \
  --os macos \
  --minutes 60 \
  --home-row-misfires 0 \
  --combo-misfires 0 \
  --macro-output-errors 0
```

Strict report:

```sh
python3 scripts/field_test.py report --strict
```

Acceptance requires the documented macOS/Linux coverage, no more than 0.5
home-row misfires per hour, zero combo misfires, zero macro-output errors, and
the required sustained usage. See `docs/7-day-field-test.md`. Until that passes,
this is a production candidate, not a proven ergonomic optimum.
