-- Advantage360 F13-F20 protocol for Hyprland 0.55+.
-- Load from ~/.config/hypr/hyprland.lua with:
--   dofile("/absolute/path/to/Adv360-Pro-ZMK/host/hyprland-adv360.lua")

local source = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(source:match("^(.*)/host/hyprland%-adv360%.lua$"), "cannot resolve Advantage360 repository")
local actionScript = root .. "/scripts/adv360_action.py"

local function shellQuote(value)
    return "'" .. value:gsub("'", [['"'"']]) .. "'"
end

local function action(name)
    return "python3 " .. shellQuote(actionScript) .. " " .. shellQuote(name)
end

hl.config({
    dwindle = {
        preserve_split = true,
    },
})

local function workspace(signal, number)
    hl.bind(signal, hl.dsp.focus({ workspace = number }))
    hl.bind("SHIFT + " .. signal, hl.dsp.window.move({ workspace = number, follow = true }))
end

for number = 1, 8 do
    workspace("F" .. (12 + number), number)
end

hl.bind("CTRL + F13", hl.dsp.focus({ direction = "l" }))
hl.bind("CTRL + F14", hl.dsp.focus({ direction = "d" }))
hl.bind("CTRL + F15", hl.dsp.focus({ direction = "u" }))
hl.bind("CTRL + F16", hl.dsp.focus({ direction = "r" }))

hl.bind("CTRL + SHIFT + F13", hl.dsp.window.move({ direction = "l" }))
hl.bind("CTRL + SHIFT + F14", hl.dsp.window.move({ direction = "d" }))
hl.bind("CTRL + SHIFT + F15", hl.dsp.window.move({ direction = "u" }))
hl.bind("CTRL + SHIFT + F16", hl.dsp.window.move({ direction = "r" }))

hl.bind("CTRL + F17", hl.dsp.focus({ workspace = "-1" }))
hl.bind("CTRL + F18", hl.dsp.focus({ workspace = "+1" }))
hl.bind("CTRL + F19", hl.dsp.window.fullscreen({ mode = "fullscreen", action = "toggle" }))
hl.bind("CTRL + F20", hl.dsp.window.float({ action = "toggle" }))
hl.bind("CTRL + SHIFT + F19", hl.dsp.window.close())
hl.bind("CTRL + SHIFT + F20", hl.dsp.layout("togglesplit"))

local actions = { "launcher", "terminal", "browser", "files", "editor", "project", "git", "ai" }
for slot, name in ipairs(actions) do
    hl.bind("ALT + F" .. (12 + slot), hl.dsp.exec_cmd(action(name)))
end
