# Advantage360 modified F13-F20 protocol

Firmware emits one versioned, host-neutral protocol. AeroSpace owns macOS;
Hyprland owns Linux. `protocol.json` is the machine-readable signal contract.

## Window namespaces

| Signal | Physical gesture | Meaning |
|---|---|---|
| F13-F20 | GLOBAL + 1-8 | Workspace 1-8 |
| Shift+F13-F20 | Shift + GLOBAL + 1-8 | Move to workspace 1-8 and follow |
| Ctrl+F13-F16 | GLOBAL + J/K/L/; | Focus left/down/up/right |
| Ctrl+Shift+F13-F16 | Shift + GLOBAL + J/K/L/; | Move left/down/up/right |
| Ctrl+F17/F18 | GLOBAL + [ / ] | Previous/next workspace, wrapping at boundaries |
| Ctrl+F19/F20 | GLOBAL + F/D | Fullscreen / floating-or-tiling |
| Ctrl+Shift+F19/F20 | GLOBAL + A/S | Close / toggle split orientation |

AeroSpace uses native tiling commands. Hyprland uses its native dispatchers; any
host-specific boundary or layout difference must be documented and tested rather
than hidden behind a shared action name.

## Developer namespace

| Signal | Gesture | Action |
|---|---|---|
| Alt+F13 | Tap GLOBAL | Launcher |
| Alt+F14 | GLOBAL+T | Terminal |
| Alt+F15 | GLOBAL+W | Browser |
| Alt+F16 | GLOBAL+O | Files |
| Alt+F17 | GLOBAL+E | Editor |
| Alt+F18 | GLOBAL+P | Project picker |
| Alt+F19 | GLOBAL+U | Git UI |
| Alt+F20 | GLOBAL+I | AI chat |

All hosts dispatch these names through `scripts/adv360_action.py`. Defaults live
in `host/apps.defaults.json`; optional overrides live in
`~/.config/adv360/apps.json`. Commands are argv arrays and never shell strings.

## Integration

- macOS: install `host/macos/aerospace.toml` with
  `python3 scripts/manage_host.py install`. No Karabiner translation is required.
  Hammerspoon must not load an Advantage360 adapter.
- Hyprland 0.55+: `dofile("/absolute/path/host/hyprland-adv360.lua")`.
- Hyprland 0.54 and older: install `adv360-action`, then source
  `host/hyprland-adv360.conf`.
- Neovim: `dofile("/absolute/path/host/nvim-adv360.lua")`.

## Editor-local namespace

F21-F24 are deliberately excluded from AeroSpace and Hyprland. On NAV they are
local editor carriers emitted by physical `Y/U/I/O` in left/down/up/right order.
Neovim and VS Code consume them for pane/editor-group focus; the window manager
must let them pass through unchanged.

Extended NKRO reports and pointing remain enabled in `config/adv360.conf`.
