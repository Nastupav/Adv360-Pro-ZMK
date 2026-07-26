# Advantage360 Pro developer keymap

Source-controlled ZMK firmware for a Kinesis Advantage360 Pro. The layout is
US-QWERTY, deterministic, and shared by macOS and Linux hosts.

The keymap intentionally has no home-row mods, typing combos, layer-taps,
editor macros, or firmware-generated bracket pairs. Editors own contextual
actions; firmware provides reliable keys and layers.

## Layer model

| Layer | Dedicated key | Purpose |
|---|---|---|
| BASE | Default | QWERTY, plain modifiers, Caps Word, repeat |
| NAV | Left middle thumb | Vim-shaped navigation |
| SYM | Right middle thumb | Paired programming symbols |
| NUM | Left bottom thumb | Numpad and F1-F12 |
| GLOBAL | Right bottom thumb | Host-neutral desktop commands |
| SYS | Either top-inner key | Bluetooth, output, lighting, maintenance |

The upper thumb keys are mirrored `Alt`, `Ctrl`, `GUI`, with `GUI` nearest the
center. The large thumb keys remain Backspace/Delete on the left and
Enter/Space on the right. The outer Shift keys are always plain Shift keys.

### BASE

```text
 =  1 2 3 4 5  SYS | SYS  6 7 8 9 0 -
Tab Q W E R T  Caps | Rep  Y U I O P \
Esc A S D F G  A C G|G C A  H J K L ; '
Shf Z X C V B    NAV|SYM    N M , . / Shf
 `  [ ] ( )  Bsp Del NUM|GLOBAL Ent Spc  Left Down Up Right SYS
```

### NAV

`H/J/K/L` are Left/Down/Up/Right. Home, End, Page Up, Page Down,
Backspace, and Delete surround them. Hold a plain Shift thumb/outer key to
select, or compose navigation with Ctrl/Alt/GUI as the host expects.

### SYM

The home row mirrors pairs around the center:

```text
<  {  [  (  =    |    +  )  ]  }  >  -
```

The top row follows US-QWERTY shifted-number symbols. Quotes, slash,
backslash, pipe, colon, and semicolon are available without Shift.

### NUM

The right hand is a standard `789 / *`, `456 - +`, `123 . ,` numpad. The
left number row is F1-F6 and the left upper-alpha row is F7-F12.

## GLOBAL host protocol

Hyprland and AeroSpace consume the same extended function-key protocol:

| Signal | Action |
|---|---|
| F13-F20 | Workspace 1-8 |
| Shift+F13-F20 | Move window to workspace 1-8 |
| Ctrl+F13-F16 | Focus left/down/up/right |
| Ctrl+Shift+F13-F16 | Move left/down/up/right |
| Ctrl+F17/F18 | Previous/next workspace |
| Ctrl+F19/F20 | Fullscreen/toggle floating |
| Ctrl+Shift+F19/F20 | Close/toggle split |
| Alt+F13-F19 | Terminal, project picker, browser, files, launcher, VS Code, Lazygit |
| Alt+F20 | Reserved |

On the physical GLOBAL layer, `1-8` select workspaces, `H/J/K/L` focus,
`[/]` move between workspaces, `F/R` control window state, and `Q/P` close or
toggle the split. Enter/T/B/E/Space/V/G launch the seven core applications.

## Bluetooth and firmware safety

Profiles are assigned consistently:

1. Profile 0: Mac
2. Profile 1: Linux
3. Profile 2: phone/tablet
4. Profiles 3-4: spare

SYS exposes explicit USB, BLE, and output-toggle keys. Bluetooth clear requires
the SYS `1+2` chord. Bootloader requires the two otherwise-unused inner keys on
SYS. Use the physical reset button for the right half when necessary.

Runtime ZMK Studio/Clique keymap editing is disabled. Git is the source of
truth.

## Build

Podman is preferred when both Podman and Docker are installed.

```sh
make       # both halves
make left  # left half only
```

Firmware and `SHA256SUMS` are written to `firmware/`. Pushes and pull requests
run the same plain left/right build in GitHub Actions.

## Clean first installation

1. Build and archive the firmware from the previous known-good commit.
2. Download the current V3 `settings-reset.uf2` from the official Kinesis
   Advantage360 Pro repository and verify its source.
3. Follow Kinesis's reset instructions; this clears all Bluetooth bonds.
4. Flash the new left UF2, power both halves off, then power the left half on.
5. Flash the right UF2 using its physical reset button, unplug it, and power it
   on.
6. Pair profile 0 to the Mac, profile 1 to Linux, and profile 2 to mobile.
7. Allow the keyboard to enter its normal idle state after selecting a profile
   so the startup selection is persisted.

Follow the vendor procedure rather than copying both files while both halves
are running: <https://github.com/KinesisCorporation/Adv360-Pro-ZMK#flashing-firmware>

## Acceptance checklist

- Every layer contains exactly 76 bindings and both halves compile.
- BASE letters and modifiers never wait for a timing decision.
- Caps Word and repeat work; editors handle automatic pairs.
- All GLOBAL signals work in both Hyprland and AeroSpace.
- Layer indicators are dim, the white backlight starts off, and LEDs stop while
  idle.
- USB/BLE output and profiles 0-2 work after the clean reset.
