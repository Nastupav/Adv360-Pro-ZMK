# macOS, Czech, VS Code, Neovim and remote Windows

## Input-source behavior

The confirmed macOS source is **Czech**, `com.apple.keylayout.Czech`, alongside ABC.
The read-only `bin/check_macos_layouts.c` probe calls Apple's UCKeyTranslate on
installed layout tables; [macos-layout-audit.txt](macos-layout-audit.txt) records
ABC, US and Czech results. It does not select an input source or type into an app.

| Keycode family | ABC / US | Czech | Decision |
|---|---|---|---|
| Number row N1…N0 | `1234567890` | `+ěščřžýáíé` | BASE remains normal; do not use for NUM |
| Keypad KP_N1…KP_N0 | `1234567890` | `1234567890` | NUM digits, including thumb 0 |
| Keypad + − × ÷ = | `+ - * / =` | `+ - * / =` | NUM operators |
| Ordinary DOT / COMMA | `. ,` | `. ,` | Explicit decimal point and comma |
| KP_DOT | `.` | `,` | Not used |
| EQUAL / SEMI | `= ;` | `' ů` | SYM requires ABC / US |
| Physical Y / Z | `y z` | `z y` | Host Czech is QWERTZ; no firmware compensation |

These are unmodified layout translations for this Mac's keyboard type 198, not
proof of text entry through a flashed Advantage360 or every application. Caps
Lock, modifiers, terminal keypad mode and remote keyboard handling may affect
results. Keep modifiers released for ordinary numeric entry.

The firmware never knows which input source is active. Use the macOS input menu
or your configured switching shortcut and verify its menu-bar label before coding.
Option and the normal Czech number row are preserved; US-specific BASE punctuation
shortcuts (such as dedicated parentheses) are also source-dependent.

Apple documents Control-Space / Control-Option-Space as input-source shortcuts.
The read-only preference check on this Mac found symbolic hotkeys 60/61 disabled,
so those two configured system shortcuts currently do not consume Control-Space.
Other utilities or editor bindings were not exhaustively audited. VS Code commonly
uses Control-Space for suggestions, and Neovim completion plugins may use it too.
If you enable macOS switching shortcuts, choose another unused shortcut there,
or use the input menu; do not assign the same shortcut to both switching and
completion. SYS + Globe is available, but depends on macOS's Globe-key setting
and is not a promise to select ABC specifically. No host settings were changed.

## macOS editors and VS Code

NAV emits real arrows. Shift combines with them for selection; Option+Left/Right
moves by word, Command+Left/Right by line, and Command+Up/Down by document in
standard macOS text editing. Dedicated NAV keys send the same chords. ASDF's
Ctrl/Option/Command/Shift order puts frequent Command and Shift on middle/index
fingers; Control and Option remain available for combined operations.

VS Code uses contextual keybindings and extensions can override them. Test in a
normal text editor tab first, then with the VSCode Neovim extension enabled.
Use **Developer: Toggle Keyboard Shortcuts Troubleshooting** to inspect an action
that differs. NUM is intended for text entry rather than number-row shortcuts;
a keybinding to `7` may differ from `numpad7`.

No VS Code configuration is required for this firmware. Existing `host/vscode`
files belong to the preserved previous EDIT/F21–F24 profile; they were left intact
and are not installed by this task. The previous host installer can change editor
profiles, so it is not part of daily-driver setup.

## Neovim and terminals

On BASE, J/K/L/semicolon remain ordinary keys, preserving Neovim's normal-mode
commands. NAV JKL; sends arrow keys in any mode. Use Escape to return to normal
mode; Ctrl is available on both thumbs and NAV A. Native `w`, `b`, `0`, `^`, `$`,
`gg`, `G`, `v`, `V` and Ctrl-V remain the predictable route for Vim motions and
selections. NAV does not redefine them or force insert mode.

Terminal emulators may intercept Command arrows or turn Option into Meta/escape
sequences. Shift arrows may move the cursor without selecting text in Neovim.
macOS word/line chords are therefore not claimed to be universal Vim commands.
Use native Vim motions or inspect your terminal's actual key sequence before
adding mappings. NAV's bottom-left Home/End and Ctrl+Home/End are alternatives
where the application supports them.

Test NUM in **insert mode**. A terminal in application-keypad mode may send keypad
sequences; if Neovim recognizes `<k0>`…`<k9>` but does not insert digits, this optional
snippet addresses that specific problem without changing normal-mode mappings:

```lua
for n = 0, 9 do
  vim.keymap.set('i', '<k' .. n .. '>', tostring(n), { noremap = true })
end
```

Only add it after observing that problem; unrecognized raw escape sequences need
a terminal/keypad configuration fix. The safe fallback for coding is ABC/US plus
the ordinary BASE number row. No Neovim or terminal settings were modified.

## PowerShell through Windows remote sessions

Keep the remote Windows input layout at US for the documented SYM output and
check the client keyboard forwarding mode: a remote client may translate local
text or forward physical keycodes. macOS source translation alone cannot prove
what the remote application receives.

NUM uses keypad digits; **Windows Num Lock must be on**. SYS + bottom-left key 61
sends Num Lock when the client forwards it; otherwise use Windows's on-screen
keyboard or remote settings. If digits navigate instead, check Num Lock before
editing firmware. The Mac usually treats keypad digits as numeric without Num
Lock, but a remote session can retain its own lock state.

For Windows word navigation, hold NAV A (Ctrl) with J/semicolon, and add F (Shift)
for selection. For line boundaries use NAV bottom-left Home/End; Ctrl+Home/End
are beside them. NAV's Command/Option shortcuts remain macOS shortcuts, and
Windows/PSReadLine can use different semantics. Plain thumb Control provides
Ctrl-C/Ctrl-V where appropriate; do not rely on remote Command remapping.

Use SYM `$`, `@`, braces, quotes, backtick and pipe as individual characters.
PSReadLine's editing mode and the remote terminal determine editing/completion;
no shell-specific text-expansion macros are baked into the keyboard.

Primary references: [Apple shortcuts](https://support.apple.com/en-us/102650),
[UCKeyTranslate](https://developer.apple.com/documentation/coreservices/1390584-uckeytranslate),
[VS Code keybindings](https://code.visualstudio.com/docs/configure/keybindings),
[Neovim key notation](https://neovim.io/doc/user/intro.html#key-notation),
[PSReadLine key handlers](https://learn.microsoft.com/en-us/powershell/module/psreadline/about/about_psreadline).
