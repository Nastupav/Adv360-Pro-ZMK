-- Open Spotlight, then select its native clipboard-history view.
-- Never send Cmd+4 unless Spotlight itself owns keyboard focus.
use framework "AppKit"
use scripting additions

on run argv
set clipboardMode to true
if (count of argv) > 0 then set clipboardMode to (item 1 of argv is "clipboard")
-- Spotlight is a system panel on current macOS, not a normally launchable app.
-- Verify its configured shortcut before using the default Command-Space.
set shortcutPreferences to current application's NSUserDefaults's alloc()'s initWithSuiteName:"com.apple.symbolichotkeys"
set hotkeyTable to shortcutPreferences's objectForKey:"AppleSymbolicHotKeys"
set hotkey to hotkeyTable's objectForKey:"64"
if hotkey is missing value then error "Cannot verify Spotlight shortcut; no shortcut was sent."
set shortcutEnabled to (hotkey's objectForKey:"enabled") as boolean
set shortcutParameters to ((hotkey's objectForKey:"value")'s objectForKey:"parameters") as list
if not shortcutEnabled or item 2 of shortcutParameters is not 49 or item 3 of shortcutParameters is not 1048576 then error "Spotlight shortcut differs from Command-Space; no shortcut was sent."
set focusedApp to current application's NSWorkspace's sharedWorkspace()'s frontmostApplication()
if (focusedApp's bundleIdentifier() as text) is not "com.apple.Spotlight" then
    with timeout of 2 seconds
        tell application "System Events" to key code 49 using command down
    end timeout
end if
if not clipboardMode then return
set ready to false
repeat 40 times
    set focusedApp to current application's NSWorkspace's sharedWorkspace()'s frontmostApplication()
    if (focusedApp's bundleIdentifier() as text) is "com.apple.Spotlight" then
        with timeout of 2 seconds
        tell application "System Events"
            if exists process "Spotlight" then
                tell process "Spotlight"
                    if (count of windows) > 0 then set ready to true
                end tell
            end if
        end tell
        end timeout
    end if
    if ready then exit repeat
    delay 0.05
end repeat
if not ready then error "Spotlight did not acquire focus; no shortcut was sent. Open Spotlight and press Command-4 manually."
-- Recheck immediately before dispatch; a focus change cancels the action.
set focusedApp to current application's NSWorkspace's sharedWorkspace()'s frontmostApplication()
if (focusedApp's bundleIdentifier() as text) is not "com.apple.Spotlight" then error "Spotlight lost focus; no shortcut was sent."
with timeout of 2 seconds
tell application "System Events"
    tell process "Spotlight"
        if not frontmost then error "Spotlight lost focus; no shortcut was sent."
        keystroke "4" using command down
    end tell
end tell
end timeout

end run
