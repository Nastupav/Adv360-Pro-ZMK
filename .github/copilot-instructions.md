# Copilot Instructions — Adv360 Pro ZMK Config

## What this repo is

A ZMK firmware configuration for the Kinesis Advantage 360 Pro split keyboard. It does **not** contain the ZMK source — it contains only the config files. The actual ZMK fork used is [`ReFil/zmk` @ `adv360-z3.5-2`](https://github.com/ReFil/zmk/tree/adv360-z3.5-2), pinned in `config/west.yml`.

## Build commands

### Local (Docker/Podman required, run inside WSL2 on Windows)

```sh
make          # build both left.uf2 and right.uf2
make left     # build left half only
make clean_firmware   # delete compiled .uf2 files
make clean_image      # remove the Docker image
make clean            # both of the above
```

Output goes to `firmware/`. The Makefile auto-detects `podman` vs `docker`.

### CI (GitHub Actions)

Pushing any commit triggers `.github/workflows/build.yml`, which produces two artifacts:
- `firmware-no-clique` — standard build
- `firmware-clique` — ZMK Studio-enabled build (left side gets `-S studio-rpc-usb-uart` and `CONFIG_ZMK_STUDIO=y`)

The west build commands used by CI are:
```sh
west build -s zmk/app -d build/left  -b adv360_left  -- -DZMK_CONFIG="$PWD/config"
west build -s zmk/app -d build/right -b adv360_right -- -DZMK_CONFIG="$PWD/config"
```

## Key files and their roles

| File | Purpose |
|---|---|
| `config/adv360.keymap` | All layer definitions and behavior nodes |
| `config/macros.dtsi` | Named macros included by the keymap |
| `config/adv360.conf` | Runtime Kconfig overrides (NKRO, keyboard name) |
| `config/west.yml` | Points to the ZMK fork + revision |
| `config/version.dtsi` | Auto-generated at build time; committed state is empty |
| `config/boards/arm/adv360/adv360_left_defconfig` | Left-half hardware Kconfig (BT, RGB, backlight, USB VID/PID) |
| `config/boards/arm/adv360/adv360_right_defconfig` | Right-half hardware Kconfig |
| `bin/get_version.sh` | Called by CI to populate `version.dtsi` with branch/commit |
| `bin/get_version_local.sh` | Same, called by `make` before docker run |

## Layer map

| # | Name | Access |
|---|---|---|
| 0 | BASE | always active |
| 1 | SYM | hold left `BSPC` thumb (`lt 1 BSPC`) |
| 2 | NAV | hold right `SPACE` thumb (`lt 2 SPACE`) |
| 3 | MOD | hold top-left `NUM` key (`mo 3`) |
| 4 | WM | hold right `ENTER` thumb (`lt 4 ENTER`) |
| 5 | NUM | hold left `DEL` thumb or top-left key (`lt 5 DEL` / `mo 5`) |
| 6 | APP | hold `ESC` thumb key — tap = ESC, hold = Hyper layer (`lt 6 ESC`) |

## Key conventions

### `hm` behavior (home_row_mods)

`hold-tap`, `balanced`, tapping-term 220 ms, quick-tap 175 ms, require-prior-idle 150 ms. Used on `A/S/D/F` (left GACS) and `J/K/L/;` (right GACS) in BASE. The `app` behavior from older versions is removed — ESC thumb now uses standard `&lt 6 ESC`.

### Macro availability

`config/boards/arm/adv360/macros.dtsi` is included by the board DTS and defines all macros used in the SYM layer (`macro_brackets`, `macro_braces`, `macro_parens`, `macro_dquotes`, `macro_quotes`). These are available in `adv360.keymap` without any additional `#include`. `config/macros.dtsi` is a duplicate of the board file — do not include it in the keymap.

### Kconfig toggle points

- **F13–F24 with NKRO**: `CONFIG_ZMK_HID_KEYBOARD_EXTENDED_REPORT=n` → `y` in `adv360_left_defconfig`
- **BLE battery reporting**: `CONFIG_BT_BAS=n` → `y` (can cause spurious host wake-ups)
- **Modifier indicator color**: `CONFIG_ZMK_RGB_UNDERGLOW_MOD_COLOR=0xRRGGBB` (set in **both** left and right defconfig)

### `version.dtsi` lifecycle

`config/version.dtsi` is intentionally blank in the committed state. Build scripts write timestamp/branch/commit data into it before compiling; `make` runs `git checkout config/version.dtsi` to restore it afterward. Do not commit a populated `version.dtsi`.

### Upgrading the ZMK fork

Change `revision:` in `config/west.yml`. For beta testing, see the README beta section.

## Workflow system (GlazeWM integration)

This repo also includes `glazewm-config.yaml` — the GlazeWM window manager config that pairs with the WM and APP layers.

**Deploy**: copy `glazewm-config.yaml` to `%USERPROFILE%\.config\glazewm\config.yaml`.

**Before deploying**: run `glazewm query monitors` to verify which monitor index (0/1/2) corresponds to the physical center/above/right displays, and update the three `focus --monitor N` lines at the top of the bindings section if needed.

### Monitor layout

| Physical screen | Default monitor index | Workspaces | Apps |
|---|---|---|---|
| Center (primary) | 0 | 1–3 | VS Code, IDEs |
| Above center | 1 | 4–6 | Windows Terminal, tools |
| Right | 2 | 7–9 | Browser, Obsidian, Teams/Outlook |
| Scratch | (center) | 10 | floating/temporary |

### WM layer grammar (hold ENTER)

- `A/S/D` = focus above/center/right monitor; `Shift+A/S/D` = send window there
- `F/G` = prev/next workspace on current monitor; `Shift+F/G` = move window
- `H/J/K/L` = focus window left/down/up/right; `Shift+H/J/K/L` = move window
- Ctrl row (Q=WS1…P=WS10) = direct workspace jump; Ctrl+Shift = move window
- Win row left = WM utilities; Win row right = resize

### APP layer grammar (hold ESC = Hyper/Ctrl+Alt+Win)

Left home row (dev loop): `A`=Terminal `S`=VS Code `D`=Chrome `F`=Explorer `G`=GitKraken  
Right home row (comms): `H`=Teams `J`=Postman `K`=Outlook `L`=Obsidian `;`=KeePass
