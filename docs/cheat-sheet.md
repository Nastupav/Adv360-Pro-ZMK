# Daily-driver cheat sheet

**BASE:** QWERTY with bilateral home-row mods. Tap normally; hold for modifiers:
**A/S/D/F = Cmd / Option / Ctrl / Shift** and **J/K/L/; = Shift / Ctrl / Option / Cmd**.
The 150 ms prior-idle gate makes rapid rolls resolve immediately as taps. Dedicated
thumb Cmd/Ctrl, inner Option, and outer Shift remain timing-free fallbacks. Escape
is left of A; Tab is left of Q.

| Hold | Location | Main actions |
|---|---|---|
| NAV | Left middle thumb, 52 | J left · K down · L up · ; right |
| SYM | Right middle thumb, 53 | ASDF `{ [ ( :` · JKL; `_ ) ] }` |
| NUM | Large left Delete thumb, 66 | UIO `789` · JKL `456` · M,. `123` |
| SYS | Bottom-right key, 75 | Function/media, Bluetooth, output, recovery |

**NUM:** Space thumb = `0`; Enter stays Enter; right small lower thumb = Backspace;
slash position = `.`; backslash = `,`; Y/P = `/ *`; H/semicolon = `- +`; quote = `=`.
Release NUM to restore Space and typing. BASE Delete is on small lower thumbs 67/68.

**NAV modifiers on ASDF:** Ctrl / Option / Command / Shift. Hold F + JKL; to
select; S + J/semicolon for words; D + J/semicolon for line edges; D + K/L for
document edges. Add F for selection. These are macOS editing chords; terminals,
Neovim and remote Windows may interpret them differently.

**NAV extras:** H/quote = line start/end; U/P = word left/right; I/O = page down/up;
Y/backslash = document start/end. N/M = delete word backward/forward; comma/period =
Backspace/Delete. QWERT, G and ZXCVB intentionally fall through to BASE: use the
home-row mods or the dedicated thumb Command/Control keys with normal letters for
app shortcuts instead of memorizing a second shortcut bank. Bottom-left five = Home, End, Ctrl+Home, Ctrl+End,
Insert for remote/terminal use.

**SYM operators** (physical BASE keys, while holding SYM):

| Output | Keys | Output | Keys |
|---|---|---|---|
| `==` | quote, quote | `!=` | Z, quote |
| `<=` | G, quote | `>=` | H, quote |
| `->` | C, H | `:=` | F, quote |
| `::` | F, F | `**` | B, B |
| `//` | N, N | `\|>` | M, H |

Tap inner-left Q-row key 20 for **Caps Word**, then type SQL keywords or
`CONSTANT_NAMES`; underscore, digit and Backspace continue it. Space ends it;
tap Caps Word again to cancel. It does not light the host Caps Lock indicator.

**SYS:** 1–5 select BT profiles 0–4; outer left top = USB; 6 = BLE;
7 = output toggle; 8/9 = next/previous profile. QWERT + YUIOP + AS = F1–F12.
M = play/pause; N/comma = previous/next; period/slash = volume down/up;
bottom-left right-hand key (71) = mute. Z = backlight; X/C = dim/bright.
V toggles indicators; B cycles lighting effects (default Kinesis effect is 4).

**Maintenance, only while SYS is held:** inner left/right number-row keys 6/7
boot the respective half; inner left/right Q-row keys 20/21 reset that half.
After at least 300 ms without an ordinary keypress, both outer number-row keys together
clear the selected Bluetooth bond while SYS is held. The idle gate plus bilateral chord
reduces accidental bond loss. SYS + position 64 returns to BASE; then release all keys. Physical reset buttons
remain the recovery path if the halves cannot communicate.

Use **ABC/US for code and SYM**, **Czech for Czech writing**. NUM digits/operators
and ordinary decimal point/comma passed local layout-table checks for both.
Windows remote sessions need Num Lock on and an appropriate remote keyboard layout.
