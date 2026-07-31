# Advantage360 Pro developer workflow

Source-controlled ZMK firmware and host adapters for a Kinesis Advantage360 Pro.
The layout is deterministic US QWERTY and speed-focused for Python, PowerShell,
SQL, shell, and PySpark work, with Hammerspoon on macOS and Hyprland on Linux.

Normal letters never wait on timing. There are no home-row mods or typing
combos; only four dedicated thumb keys are dual-role.

## Thumb and layer model

```text
Left upper:   Alt  Ctrl  GUI      Right upper:  GUI  Ctrl  Alt
Layer thumbs: tap Esc / hold NAV  | tap Tab / hold SYM
Lower thumbs: Bsp  Del  CapsWord/NUM  | Launcher/GLOBAL  Enter  Space
```

The four layer thumbs use hold-preferred 170 ms behavior, so a layer resolves
on the next key-down instead of waiting for release. The two central keys are
lazy sticky GUI and Ctrl with quick release and a one-second timeout.

| Layer | Activation | Purpose |
|---|---|---|
| BASE | Default | QWERTY, plain/sticky modifiers, direct brackets |
| NAV | Hold Esc/NAV | Navigation, selection, scroll, mouse buttons |
| SYM | Hold Tab/SYM | Python/SQL/shell symbols and operators |
| NUM | Hold CapsWord/NUM | Numpad and F1-F12 |
| GLOBAL | Hold Launcher/GLOBAL | Host-neutral desktop protocol |
| SYS | Either top-inner SYS | Bluetooth, output, lighting, maintenance |

### Developer layers

NAV keeps the ergonomic home zones and leaves G/H inactive:

```text
A       S        D       F       J      K       L     ;
Home    PageDn   PageUp  End     Left   Down    Up    Right
```

NAV+Y/U/I/O scroll left/down/up/right. While NAV is held, the right GLOBAL,
Enter, and Space thumbs click middle, left, and right respectively. Firmware
does not provide cursor movement.

SYM places common symbols on the same zones:

```text
A   S   D   F       J   K   L   ;
_   :   !   ?       +   *   &   |
```

The upper-alpha row emits language-neutral operators:

```text
Q   W   E   R   T        Y   U   I   O   P   \
==  !=  <=  >=  ->       =>  &&  ||  :=  **  //
```

The lower-alpha row groups PowerShell comparisons and shared SQL tokens:

```text
Z    X    C    V    B        N    M   ,   .   /
-eq  -ne  -lt  -le  -gt      -ge  <>  ::  $_  --
```

All 21 literal macros use 20/20 ms timing and contain no trailing spaces or
cursor movement, so editor auto-pairs and formatters remain authoritative.
NUM puts F1-F12 on the left and a J-starting numpad on the right.

## F13-F20 desktop protocol

`host/protocol.json` is the machine-readable contract. Firmware never emits
F21-F24.

| Signal | Meaning |
|---|---|
| F13-F20 | Workspace 1-8 |
| Shift+F13-F20 | Move window to workspace 1-8 and follow |
| Ctrl+F13-F16 | Focus left/down/up/right |
| Ctrl+Shift+F13-F16 | Move/place left/down/up/right |
| Ctrl+F17/F18 | Previous/next workspace |
| Ctrl+F19/F20 | Fullscreen/maximize and floating/restore |
| Ctrl+Shift+F19/F20 | Close and toggle split |
| Alt+F13-F20 | Eight developer actions |

Developer gestures are mnemonic:

```text
tap GLOBAL  launcher       GLOBAL+T  terminal
GLOBAL+W    browser        GLOBAL+O  files
GLOBAL+E    editor         GLOBAL+P  project picker
GLOBAL+U    Git UI         GLOBAL+I  AI chat
```

Default applications are defined in `host/apps.defaults.json`. Override any
entry in `~/.config/adv360/apps.json`; commands are argv arrays and are launched
without shell interpolation. Test one without opening it:

```sh
python3 scripts/adv360_action.py terminal --dry-run
```

## Host integration

Preview, install, or roll back versioned host includes with:

```sh
python3 scripts/manage_host.py plan
python3 scripts/manage_host.py install
python3 scripts/manage_host.py rollback latest
```

Installation is idempotent. Before changing a live file it stores a timestamped
copy and manifest under `~/.local/state/adv360-host-backups/`.

### macOS

Hammerspoon owns workspaces, window placement, the launcher, and application
actions. It requires Accessibility permission and eight existing user Spaces on
each display where the protocol is used. The adapter reports an error instead
of creating or deleting Spaces automatically.

Karabiner applies only to the Advantage360 device (`7504:24926`) and tags F14
and F15 with Command so macOS does not consume those carriers. Hammerspoon
removes this implementation detail when decoding the protocol.

```lua
local adv360 = dofile('/absolute/path/host/hammerspoon-adv360.lua')
adv360.setup({ chooser = function() chooser:show() end })
```

AeroSpace is unsupported in this profile and must not run alongside Hammerspoon.

### Linux

Hyprland 0.55+ uses Lua:

```lua
dofile('/absolute/path/host/hyprland-adv360.lua')
```

For Hyprland 0.54 and older, install `adv360-action` on PATH and source
`host/hyprland-adv360.conf`.

### Neovim

```lua
dofile('/absolute/path/host/nvim-adv360.lua')
```

Ctrl+J/K/L/`;` focuses panes. `<leader>w` followed by J/K/L/`;` moves panes;
this avoids unreliable Ctrl+Shift letter distinctions in terminal protocols.

## Build and verification

Python 3.9 or newer is supported. Podman is preferred when both container
runtimes are installed.

```sh
make test            # unit tests
make verify          # semantic, protocol, host, syntax, and provenance checks
make verify-active   # additionally verify live Hammerspoon/Karabiner/Neovim
make                 # build both firmware halves
make left            # build only the left half
```

`make left` writes `right=false` in the manifest and removes any right-hand UF2
with the same commit/fingerprint prefix, preventing stale pairings.

The build pins both the ZMK source commit and container digest. Firmware names
contain the Git commit, a fingerprint of every file under `config/` plus the
Dockerfile and build script, and `-dirty` when tracked inputs differ.
`firmware/SHA256SUMS` and `firmware/build-manifest.json` record the result.

## Flashing and Bluetooth

Pointing changes the HID descriptor, so the first installation requires a
clean reset and re-pair:

1. Archive the previous known-good firmware.
2. Obtain the V3 `settings-reset.uf2` from the official Kinesis repository.
3. Follow Kinesis's reset procedure, which clears Bluetooth bonds.
4. Flash the left and right UF2 files using the vendor procedure.
5. Forget the old keyboard on each host and pair profile 0 to macOS, profile 1
   to Linux, and profile 2 to mobile.

Vendor procedure:
<https://github.com/KinesisCorporation/Adv360-Pro-ZMK#flashing-firmware>

Studio/Clique runtime keymap editing remains disabled; Git is the sole keymap
authority. RGB and the white backlight start off to protect battery life.

## Seven-day field test

Static checks cannot prove ergonomics. Follow `docs/7-day-field-test.md` and
record at least seven days, 420 minutes total, and 60 minutes on each OS:

```sh
python3 scripts/field_test.py init
python3 scripts/field_test.py log --os macos --minutes 60
python3 scripts/field_test.py report --strict
```

The 170 ms thumb term and 20/20 ms macro timing are test baselines, not proven
ergonomic optima. Change only one variable per field-test cycle.
