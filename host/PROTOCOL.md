# Advantage360 modified F13-F20 protocol

Firmware emits one versioned, host-neutral protocol. Hammerspoon owns macOS;
Hyprland owns Linux. `protocol.json` is the machine-readable contract.

## Window namespaces

| Signal | Physical gesture | Meaning |
|---|---|---|
| F13-F20 | GLOBAL + 1-8 | Workspace 1-8 |
| Shift+F13-F20 | Shift + GLOBAL + 1-8 | Move to workspace 1-8 and follow |
| Ctrl+F13-F16 | GLOBAL + J/K/L/; | Focus left/down/up/right |
| Ctrl+Shift+F13-F16 | Shift + GLOBAL + J/K/L/; | Move/place left/down/up/right |
| Ctrl+F17/F18 | GLOBAL + [/ ] | Previous/next workspace |
| Ctrl+F19/F20 | GLOBAL + F/D | Fullscreen-or-maximize / floating-or-restored |
| Ctrl+Shift+F19/F20 | GLOBAL + A/S | Close / toggle split |

Hammerspoon maps directional movement to screen halves, maximize to a saved
frame toggle, floating to centered 80% with restore, and split to horizontal or
vertical placement. Hyprland uses its native tiling dispatchers.

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

macOS Karabiner tags F14 and F15 with Command, for every protocol modifier
variant, before Hammerspoon consumes them. All other carriers remain direct.
The rule is restricted to vendor `7504`, product `24926`.

## Integration

- macOS: load `host/hammerspoon-adv360.lua` and install the device-scoped
  Karabiner rule from `host/karabiner-adv360.json`.
- Hyprland 0.55+: `dofile("/absolute/path/host/hyprland-adv360.lua")`.
- Hyprland 0.54 and older: install `adv360-action`, then source
  `host/hyprland-adv360.conf`.
- Neovim: `dofile("/absolute/path/host/nvim-adv360.lua")`.
- Optional app overrides: `~/.config/adv360/apps.json`, using the same shape as
  `host/apps.defaults.json`.

F21-F24 are deliberately absent. Extended NKRO reports and pointing remain
enabled in `config/adv360.conf`.
