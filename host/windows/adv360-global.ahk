#Requires AutoHotkey v2.0
; ---------------------------------------------------------------------------
; Adv360 GLOBAL layer consumer for Windows.
;
; The keyboard emits a host-neutral F13-F20 protocol; this script turns it into
; window-manager actions, mirroring the AeroSpace (macOS) and Hyprland (Linux)
; configs in ../macos and ../linux.
;
; Window management is delegated to komorebi (https://lgug2z.github.io/komorebi).
; Set USE_KOMOREBI := false to fall back to native Windows virtual desktops,
; which supports only previous/next workspace and no directional focus.
;
; Install: put this file in shell:startup, or run it and pin it.
; ---------------------------------------------------------------------------

USE_KOMOREBI := true
KOMOREBIC    := "komorebic.exe"

; --- Applications launched by Alt+F13..F20 --------------------------------
; Adjust the right-hand side to taste; anything Run() accepts works.
APPS := Map(
    "F13", "wt.exe",                                          ; terminal
    "NumpadDiv", "msedge.exe",                                      ; browser
    "NumpadMult", "code",                                            ; code editor
    "F16", "explorer.exe",                                    ; files
    "F17", "",                                                ; launcher (see below)
    "F18", "ms-teams.exe",                                    ; chat
    "F19", "obsidian.exe",                                    ; notes
    "F20", "lazygit"                                          ; git
)

; Neovim, launched by Alt+Shift+F17 inside the terminal above.
NVIM := "wt.exe nvim"

; ---------------------------------------------------------------------------
; Helpers
; ---------------------------------------------------------------------------

Kmb(args*) {
    global USE_KOMOREBI, KOMOREBIC
    if (!USE_KOMOREBI)
        return false
    try {
        Run(KOMOREBIC " " Trim(Join(args)), , "Hide")
        return true
    } catch as e {
        TrayTip("komorebic failed", e.Message, 3)
        return false
    }
}

Join(parts) {
    out := ""
    for p in parts
        out .= p " "
    return out
}

Workspace(n) {
    ; komorebi workspaces are 0-indexed; the keyboard sends 1-8.
    if (Kmb("focus-workspace", n - 1))
        return
    ; Native fallback: no direct numbered switch exists, so do nothing rather
    ; than guess and land the user on the wrong desktop.
    TrayTip("Workspace " n, "Enable komorebi for numbered workspaces", 2)
}

MoveToWorkspace(n) {
    if (Kmb("move-to-workspace", n - 1))
        return
    TrayTip("Move to workspace " n, "Requires komorebi", 2)
}

Focus(dir) {
    if (Kmb("focus", dir))
        return
    ; Native fallback: cycle windows.
    Send("!{Tab}")
}

MoveWindow(dir) {
    if (Kmb("move", dir))
        return
    TrayTip("Move window " dir, "Requires komorebi", 2)
}

CycleWorkspace(dir) {
    if (Kmb("cycle-workspace", dir))
        return
    Send(dir = "previous" ? "^#{Left}" : "^#{Right}")
}

Launch(key) {
    global APPS
    target := APPS.Has(key) ? APPS[key] : ""
    if (target = "") {
        ; F17 is the launcher: Windows Search is the closest native analogue.
        Send("#s")
        return
    }
    try Run(target)
    catch
        TrayTip("Could not launch", target, 3)
}

; ---------------------------------------------------------------------------
; Protocol bindings
; ---------------------------------------------------------------------------

; F13-F20 -> workspace 1-8
F13:: Workspace(1)
NumpadDiv:: Workspace(2)
NumpadMult:: Workspace(3)
F16:: Workspace(4)
F17:: Workspace(5)
F18:: Workspace(6)
F19:: Workspace(7)
F20:: Workspace(8)

; Shift+F13-F20 -> move active window to workspace 1-8
+F13:: MoveToWorkspace(1)
+NumpadDiv:: MoveToWorkspace(2)
+NumpadMult:: MoveToWorkspace(3)
+F16:: MoveToWorkspace(4)
+F17:: MoveToWorkspace(5)
+F18:: MoveToWorkspace(6)
+F19:: MoveToWorkspace(7)
+F20:: MoveToWorkspace(8)

; Ctrl+F13-F16 -> focus left/down/up/right
^F13:: Focus("left")
^NumpadDiv:: Focus("down")
^NumpadMult:: Focus("up")
^F16:: Focus("right")

; Ctrl+Shift+F13-F16 -> move window left/down/up/right
^+F13:: MoveWindow("left")
^+NumpadDiv:: MoveWindow("down")
^+NumpadMult:: MoveWindow("up")
^+F16:: MoveWindow("right")

; Ctrl+F17/F18 -> previous/next workspace
^F17:: CycleWorkspace("previous")
^F18:: CycleWorkspace("next")

; Ctrl+Shift+F17/F18 -> move window to previous/next workspace
^+F17:: Kmb("cycle-move-to-workspace", "previous")
^+F18:: Kmb("cycle-move-to-workspace", "next")

; Ctrl+Alt+F13-F16 -> resize left/down/up/right
^!F13:: Kmb("resize-axis", "horizontal", "decrease")
^!NumpadDiv:: Kmb("resize-axis", "vertical", "increase")
^!NumpadMult:: Kmb("resize-axis", "vertical", "decrease")
^!F16:: Kmb("resize-axis", "horizontal", "increase")

; Ctrl+Alt+F17/F18 -> focus previous/next monitor
^!F17:: Kmb("cycle-monitor", "previous")
^!F18:: Kmb("cycle-monitor", "next")

; Ctrl+Alt+Shift+F17/F18 -> move window to previous/next monitor
^!+F17:: Kmb("cycle-move-to-monitor", "previous")
^!+F18:: Kmb("cycle-move-to-monitor", "next")

; Ctrl+Alt+F19 balance/reset layout, Ctrl+Alt+F20 pin window
^!F19:: Kmb("retile")
^!F20:: WinSetAlwaysOnTop(-1, "A")

; Alt+Shift+F13-F16 -> screenshot region, screenshot window, clipboard, picker
!+F13:: Send("#+s")            ; Snipping Tool region capture
!+NumpadDiv:: Send("!{PrintScreen}") ; active window to clipboard
!+NumpadMult:: Send("#v")             ; clipboard history
!+F16:: Run("ms-screenclip:")  ; nearest built-in colour/screen tool

; Alt+Shift+F17 -> Neovim in a terminal
!+F17:: Run(NVIM)

; Ctrl+F19 fullscreen, Ctrl+Shift+F19 close window
^F19:: Kmb("toggle-monocle")
^+F19:: WinClose("A")

; Ctrl+F20 float, Ctrl+Shift+F20 toggle layout
^F20:: Kmb("toggle-float")
^+F20:: Kmb("flip-layout", "horizontal")

; Alt+F13-F20 -> applications
!F13:: Launch("F13")
!NumpadDiv:: Launch("NumpadDiv")
!NumpadMult:: Launch("NumpadMult")
!F16:: Launch("F16")
!F17:: Launch("F17")
!F18:: Launch("F18")
!F19:: Launch("F19")
!F20:: Launch("F20")
