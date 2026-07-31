-- Advantage360 F13-F20 protocol adapter for Hammerspoon.
-- Load with: dofile("/absolute/path/host/hammerspoon-adv360.lua").setup(...)

local M = {}
local source = debug.getinfo(1, "S").source:gsub("^@", "")
local repoRoot = source:match("^(.*)/host/hammerspoon%-adv360%.lua$")
assert(repoRoot, "cannot resolve Advantage360 repository root")

local registry = {}
local tasks = {}
local windowModes = {}
local splitModes = {}
local defaultChooser
local configured = false

local units = {
    left = { x = 0, y = 0, w = 0.5, h = 1 },
    down = { x = 0, y = 0.5, w = 1, h = 0.5 },
    up = { x = 0, y = 0, w = 1, h = 0.5 },
    right = { x = 0.5, y = 0, w = 0.5, h = 1 },
    centered = { x = 0.1, y = 0.1, w = 0.8, h = 0.8 },
    maximize = { x = 0, y = 0, w = 1, h = 1 },
}

local function alert(message)
    hs.alert.closeAll()
    hs.alert.show(message, 0.9)
end

local function focusedWindow()
    local window = hs.window.focusedWindow()
    if not window then alert("Adv360: no focused window") end
    return window
end

local function setUnit(window, unit)
    local screen = window:screen():frame()
    window:setFrame({
        x = screen.x + screen.w * unit.x,
        y = screen.y + screen.h * unit.y,
        w = screen.w * unit.w,
        h = screen.h * unit.h,
    })
end

local function copyFrame(frame)
    return { x = frame.x, y = frame.y, w = frame.w, h = frame.h }
end

local function toggleFrame(mode, unit)
    local window = focusedWindow()
    if not window then return end
    local id = window:id()
    local state = windowModes[id]
    if state and state.mode == mode then
        window:setFrame(state.frame)
        windowModes[id] = nil
        alert("Adv360: restored")
        return
    end
    windowModes[id] = { mode = mode, frame = copyFrame(window:frame()) }
    setUnit(window, unit)
    alert("Adv360: " .. mode)
end

local function canonical(modifiers, key)
    local values = {}
    for _, modifier in ipairs(modifiers) do table.insert(values, modifier) end
    table.sort(values)
    return table.concat(values, "+") .. "+" .. key
end

local function bind(modifiers, key, label, callback)
    local identity = canonical(modifiers, key)
    assert(not registry[identity], "duplicate Advantage360 hotkey: " .. identity)
    local hotkey = hs.hotkey.bind(modifiers, key, callback)
    assert(hotkey, "cannot enable Advantage360 hotkey: " .. identity)
    registry[identity] = { hotkey = hotkey, label = label }
end

-- Karabiner adds Command to F14/F15 so macOS never handles them as brightness.
local function carrierModifiers(slot, modifiers)
    local result = {}
    for _, modifier in ipairs(modifiers) do table.insert(result, modifier) end
    if slot == 2 or slot == 3 then table.insert(result, "cmd") end
    return result
end

local function bindCarrier(modifiers, slot, label, callback)
    bind(carrierModifiers(slot, modifiers), "f" .. tostring(12 + slot), label, callback)
end

local function targetScreen()
    local window = hs.window.focusedWindow()
    return window and window:screen() or hs.screen.mainScreen()
end

local function userSpaces(screen)
    local values, errorMessage = hs.spaces.spacesForScreen(screen)
    if not values then
        alert("Adv360 Spaces: " .. tostring(errorMessage))
        return nil
    end
    local result = {}
    for _, id in ipairs(values) do
        if hs.spaces.spaceType(id) == "user" then table.insert(result, id) end
    end
    if #result < 8 then
        alert("Adv360: create 8 user Spaces on this display")
        return nil
    end
    return result
end

local function selectWorkspace(index, moveWindow)
    local window = hs.window.focusedWindow()
    local screen = window and window:screen() or targetScreen()
    local spaces = userSpaces(screen)
    if not spaces then return end
    local id = spaces[index]
    if moveWindow then
        if not window then alert("Adv360: no window to move"); return end
        local ok, errorMessage = hs.spaces.moveWindowToSpace(window, id)
        if not ok then alert("Adv360 move: " .. tostring(errorMessage)); return end
    end
    local ok, errorMessage = hs.spaces.gotoSpace(id)
    if not ok then alert("Adv360 workspace: " .. tostring(errorMessage)) end
end

local function cycleWorkspace(delta)
    local screen = targetScreen()
    local spaces = userSpaces(screen)
    if not spaces then return end
    local current = hs.spaces.activeSpaceOnScreen(screen)
    local index = 1
    for candidate, id in ipairs(spaces) do
        if id == current then index = candidate; break end
    end
    index = ((index - 1 + delta) % #spaces) + 1
    local ok, errorMessage = hs.spaces.gotoSpace(spaces[index])
    if not ok then alert("Adv360 workspace: " .. tostring(errorMessage)) end
end

local focusMethods = {
    function(window) window:focusWindowWest() end,
    function(window) window:focusWindowSouth() end,
    function(window) window:focusWindowNorth() end,
    function(window) window:focusWindowEast() end,
}

local directionNames = { "left", "down", "up", "right" }

local function focusDirection(index)
    local window = focusedWindow()
    if window then focusMethods[index](window) end
end

local function placeDirection(index)
    local window = focusedWindow()
    if not window then return end
    setUnit(window, units[directionNames[index]])
    alert("Adv360: " .. directionNames[index])
end

local function closeWindow()
    local window = focusedWindow()
    if window then window:close() end
end

local function toggleSplit()
    local window = focusedWindow()
    if not window then return end
    local id = window:id()
    local horizontal = not splitModes[id]
    splitModes[id] = horizontal
    setUnit(window, horizontal and units.left or units.up)
    alert(horizontal and "Adv360: horizontal split" or "Adv360: vertical split")
end

local function runAction(action)
    local executable = "/usr/bin/env"
    local arguments = { "python3", repoRoot .. "/scripts/adv360_action.py", action }
    local task
    task = hs.task.new(executable, function(exitCode, _, standardError)
        tasks[task] = nil
        if exitCode ~= 0 then alert("Adv360 " .. action .. ": " .. standardError) end
    end, arguments)
    if not task then alert("Adv360: could not start " .. action); return end
    tasks[task] = true
    task:start()
end

function M.setup(options)
    assert(not configured, "Advantage360 Hammerspoon adapter already configured")
    configured = true
    options = options or {}

    for slot = 1, 8 do
        local workspace = slot
        bindCarrier({}, slot, "workspace " .. slot, function() selectWorkspace(workspace, false) end)
        bindCarrier({ "shift" }, slot, "move to workspace " .. slot, function() selectWorkspace(workspace, true) end)
    end

    for slot = 1, 4 do
        local direction = slot
        bindCarrier({ "ctrl" }, slot, "focus " .. directionNames[slot], function() focusDirection(direction) end)
        bindCarrier({ "ctrl", "shift" }, slot, "place " .. directionNames[slot], function() placeDirection(direction) end)
    end

    bindCarrier({ "ctrl" }, 5, "previous workspace", function() cycleWorkspace(-1) end)
    bindCarrier({ "ctrl" }, 6, "next workspace", function() cycleWorkspace(1) end)
    bindCarrier({ "ctrl" }, 7, "maximize/restore", function() toggleFrame("maximized", units.maximize) end)
    bindCarrier({ "ctrl" }, 8, "float/restore", function() toggleFrame("floating", units.centered) end)
    bindCarrier({ "ctrl", "shift" }, 7, "close", closeWindow)
    bindCarrier({ "ctrl", "shift" }, 8, "toggle split", toggleSplit)

    local actions = { "launcher", "terminal", "browser", "files", "editor", "project", "git", "ai" }
    if not options.chooser then
        local choices = {}
        for _, name in ipairs(actions) do
            if name ~= "launcher" then table.insert(choices, { text = name, action = name }) end
        end
        defaultChooser = hs.chooser.new(function(choice)
            if choice then runAction(choice.action) end
        end)
        defaultChooser:choices(choices)
        options.chooser = function() defaultChooser:show() end
    end
    for slot, action in ipairs(actions) do
        local selected = action
        bindCarrier({ "alt" }, slot, selected, function()
            if selected == "launcher" then options.chooser() else runAction(selected) end
        end)
    end

    _G.ADV360_STATUS = { ready = true, bindings = 38, protocol = "F13-F20/v1" }
    alert("Advantage360 protocol loaded")
    return M
end

function M.status()
    return _G.ADV360_STATUS
end

return M
