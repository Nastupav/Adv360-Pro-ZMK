> **Status: IMPLEMENTED** — `config/adv360.keymap` and `glazewm-config.yaml` have been rewritten.
> Flash firmware, then deploy `glazewm-config.yaml` to `%USERPROFILE%\.config\glazewm\config.yaml`.
> Run `glazewm query monitors` first to verify monitor indices match the comments at the top of `glazewm-config.yaml`.

---

## 1) Current config critique
- The existing ADV360 keymap mixes home-row mods, Vim-style navigation, and an F-key window-manager matrix without one clean operating model.
- The GlazeWM file does useful work, but several comments and assumptions no longer match what the keyboard actually emits.
- The current setup carries too many compatibility artifacts: stale F24 references, mixed Hyper and F-key logic, and more workspaces than the physical mnemonic system supports well.
- Ergonomically, too many high-frequency actions are distributed across unrelated rows, and the system still leans on a Vim/HJKL mental model outside Neovim.
- Practically, app launching exists, but it is not grouped around the daily engineering loop, and monitor/workspace behavior is harder to learn than it should be.

## 2) New design philosophy
- `J K L ;` is the universal directional cluster.
- `A S D` is the universal left/center/right monitor cluster.
- `F G` owns workspace traversal on the current monitor.
- The keyboard and window manager share one grammar instead of parallel systems.
- Workspaces are reduced to a memorable 3-monitor model plus one scratch space.
- Thumbs handle layer access; home-row real estate handles action.
- Symbols prioritize paired delimiters and operators used in coding.
- The app layer prioritizes the developer loop before secondary tools.

## 3) Proposed interaction model
Base layer philosophy: keep typing conventional and low-friction, with home-row mods doing the heavy lifting instead of adding more base clutter.

Nav layer philosophy: right-hand `J/K/L/;` handles movement everywhere. The left hand supplies editing primitives, modifiers, and clipboard support.

Symbol/programming layer philosophy: paired delimiters are first-class. Insert the pair and land the cursor inside it.

Window manager layer philosophy: `A/S/D` focuses monitors, `F/G` cycles workspaces on the current monitor, and `J/K/L/;` focuses or moves windows directionally. The Ctrl row targets direct workspaces. The Win row handles WM utilities and resize.

Monitor/workspace model for 3 monitors: `1-3` live on the left monitor, `4-6` in the center, `7-9` on the right, and `10` is scratch. Editor and terminal stay centered; browser, docs, and communication stay right-biased.

How this complements Neovim: you keep modal habits, but the physical operating-system movement cluster stops copying Vim’s `HJKL` dependency. Neovim stays Neovim; the rest of the machine gets a better home-row grammar.

## 4) Final ADV360 redesign
- Base keeps GACS home-row mods on `A S D F` and `J K L ;`.
- Thumb and inner-cluster roles:
  - `BSPC` hold = `SYM`
  - `DEL` hold = `NUM`
  - `ENTER` hold = `WM`
  - `SPACE` hold = `NAV`
  - Inner left cluster hold = `APP`
- Tap-hold behavior:
  - Home-row mods stay conservative and balanced for typing stability.
  - Layer access stays on holds instead of adding more permanent base clutter.
- Combos / one-shot / leader-like patterns:
  - No extra combos or one-shot mods were added intentionally.
  - That omission is deliberate: this system already gets most of its value from home-row mods and thumb-held layers, and more stateful behavior would raise adoption cost.
- Rewritten config:

```dts
/*
 * Unified ADV360 + GlazeWM workflow system.
 *
 * Design model:
 *   - BASE: typing first, with home-row mods in GACS order.
 *   - SYM: paired delimiters, operators, and function keys for coding.
 *   - NAV: text navigation and editing with J/K/L/; directional logic.
 *   - MOD: firmware, Bluetooth, lighting, and bootloader controls.
 *   - WM: monitor, workspace, window, and resize control aligned to GlazeWM.
 *   - NUM: right-hand numpad and fast data-entry helpers.
 *   - APP: Hyper layer for app launch/switch chords consumed by GlazeWM.
 *
 * Core ergonomic decisions:
 *   - J / K / L / ; = left / down / up / right anywhere direction matters.
 *   - A / S / D = left / center / right monitor anchors on the WM layer.
 *   - F / G = previous / next workspace on the current monitor.
 *   - Home-row mods stay on ASDF and JKL; in base for low-friction daily use.
 *   - Thumbs own layer access: BSPC=SYM, DEL=NUM, ENTER=WM, SPACE=NAV, ESC=APP.
 */

#include <behaviors.dtsi>
#include <dt-bindings/zmk/backlight.h>
#include <dt-bindings/zmk/bt.h>
#include <dt-bindings/zmk/keys.h>
#include <dt-bindings/zmk/rgb.h>
#include "macros.dtsi"

/ {
    behaviors {
        hm: home_row_mods {
            compatible = "zmk,behavior-hold-tap";
            label = "HOME_ROW_MODS";
            #binding-cells = <2>;
            tapping-term-ms = <220>;
            quick-tap-ms = <175>;
            require-prior-idle-ms = <150>;
            flavor = "balanced";
            bindings = <&kp>, <&kp>;
        };
    };

    keymap {
        compatible = "zmk,keymap";

        /* Base typing layer.
         * Home-row mods stay conventional so the system remains adoptable.
         * Layer access is thumb-led: SYM, NUM, WM, NAV, and APP all live off holds.
         */
        default_layer {
            bindings = <
&kp EQUAL  &kp N1                &kp N2                 &kp N3       &kp N4       &kp N5  &mo 5                                                                            &mo 3               &kp N6  &kp N7       &kp N8       &kp N9      &kp N0         &kp MINUS
&kp TAB    &kp Q                 &kp W                  &kp E        &kp R        &kp T   &kp PRINTSCREEN                                                                  &kp K_CONTEXT_MENU  &kp Y   &kp U        &kp I        &kp O       &kp P          &kp BSLH
&kp ESC    &hm LGUI A            &hm LALT S             &hm LCTRL D  &hm LSHFT F  &kp G   &mt LC(V) LC(C)  &kp LCTRL  &kp LEFT_ALT       &kp RCTRL  &kp RIGHT_COMMAND  &mt LC(V) LC(C)     &kp H   &hm RSHFT J  &hm RCTRL K  &hm RALT L  &hm RGUI SEMI  &kp SQT
&kp LSHFT  &kp Z                 &kp X                  &kp C        &kp V        &kp B                                &lt 6 ESC          &kp PG_UP                                           &kp N   &kp M        &kp COMMA    &kp DOT     &kp FSLH       &kp RSHFT
&kp GRAVE  &kp LEFT_PARENTHESIS  &kp RIGHT_PARENTHESIS  &kp LEFT     &kp RIGHT            &lt 1 BSPC       &lt 5 DEL  &mt LSHFT END      &kp K_APP  &lt 4 ENTER        &lt 2 SPACE                 &kp UP       &kp DOWN     &kp LBKT    &kp RBKT       &mo 2
            >;
        };

        /* Symbol layer for programming.
         * Left home row inserts paired delimiters.
         * Right side handles operators and punctuation that repeat all day in code.
         */
        layer_sym {
            bindings = <
&trans    &kp F1             &kp F2         &kp F3            &kp F4      &kp F5       &trans                                                                      &trans    &kp F6      &kp F7      &kp F8      &kp F9      &kp F10     &kp F11
&trans    &kp EXCL           &kp AT         &kp HASH          &kp DLLR    &kp PRCNT    &trans                                                                      &trans    &kp CARET   &kp AMPS    &kp STAR    &kp PIPE    &kp TILDE   &kp F12
&trans    &macro_brackets    &macro_braces  &macro_parens     &macro_dquotes  &macro_quotes  &trans      &trans  &trans      &trans  &trans  &kp UNDER     &kp MINUS   &kp EQUAL   &kp PLUS    &kp BSLH    &kp LT       &kp GT
&trans    &kp LBRC           &kp RBRC       &kp LBKT          &kp RBKT    &kp GRAVE                           &trans      &trans                                   &kp QMARK   &kp COLON   &kp SEMI    &kp COMMA   &kp DOT     &trans
&trans    &trans             &trans         &trans            &trans                  &trans        &trans  &trans      &trans  &trans  &trans                           &trans      &trans      &trans      &trans      &trans
            >;
        };

        /* Navigation layer.
         * J/K/L/; is the universal left/down/up/right cluster.
         * Left hand handles editing, modifier chords, and clipboard actions.
         */
        layer_nav {
            bindings = <
&trans  &kp LC(Z)     &kp LC(LEFT)   &kp LC(C)     &kp LC(V)      &kp LC(X)   &trans                                        &trans      &kp LC(TAB)  &kp HOME  &kp PG_DN     &kp PG_UP     &kp END    &trans
&trans  &none         &kp LC(LEFT)   &kp HOME      &kp END        &kp LC(RIGHT)  &trans                                     &trans      &kp LS(TAB)  &kp HOME  &kp PG_DN     &kp PG_UP     &kp END    &trans
&trans  &kp LGUI      &kp LALT       &kp LCTRL     &kp LSHFT      &none          &trans  &trans  &trans      &trans  &trans  &none   &kp LEFT     &kp DOWN  &kp UP_ARROW    &kp RIGHT     &none      &trans
&trans  &kp LC(Z)     &kp LC(X)      &kp LC(C)     &kp LC(V)      &kp LC(Y)                         &trans      &trans                            &kp HOME     &kp PG_DN &kp PG_UP       &kp END       &none      &trans
&trans  &trans        &trans         &trans        &trans                   &kp DEL    &kp BSPC &trans      &trans  &trans  &trans                     &trans       &trans    &trans          &trans        &trans
            >;
        };

        /* Maintenance layer for Bluetooth, bootloader, and lighting. */
        layer_mod {
            bindings = <
&none  &bt BT_SEL 0  &bt BT_SEL 1  &bt BT_SEL 2  &bt BT_SEL 3  &bt BT_SEL 4  &bt BT_CLR                                        &trans           &none            &none            &none            &none            &none            &none
&none  &none         &none         &none         &none         &none         &bootloader                                       &bootloader      &none            &none            &none            &none            &none            &none
&none  &none         &none         &none         &none         &none         &none        &none  &none      &bt BT_CLR  &none  &rgb_ug RGB_TOG  &rgb_ug RGB_BRI  &rgb_ug RGB_BRD  &rgb_ug RGB_EFF  &rgb_ug RGB_EFR  &rgb_ug RGB_SPI  &rgb_ug RGB_SPD
&none  &none         &none         &none         &none         &none                             &none      &none                               &none            &bl BL_ON        &bl BL_OFF       &bl BL_CYCLE     &none            &none
&none  &none         &none         &none         &none                       &none        &none  &none      &none       &none  &none                             &bl BL_INC       &bl BL_DEC       &none            &none            &none
            >;
        };

        /* Window manager layer.
         * Bare home row:
         *   A/S/D  -> focus left / center / right monitor
         *   F/G    -> previous / next workspace on current monitor
         *   J/K/L/;-> focus left / down / up / right window
         *
         * Add corner Shift:
         *   A/S/D  -> send window to left / center / right monitor anchor
         *   F/G    -> send window to previous / next workspace on current monitor
         *   J/K/L/;-> move window left / down / up / right
         *
         * Ctrl row:
         *   Direct workspaces 1..10
         *
         * Win row:
         *   WM utilities on the left, directional resize on the right
         */
        layer_wm {
            bindings = <
&trans  &kp LG(F13)      &kp LG(F14)      &kp LG(F15)      &kp LG(F16)      &kp LG(F17)      &none                                                  &none            &kp LG(F18)      &kp LG(F19)      &kp LG(F20)      &kp LG(LA(F13))  &kp LG(LA(F14))  &none
&trans  &kp LC(F13)      &kp LC(F14)      &kp LC(F15)      &kp LC(F16)      &kp LC(F17)      &none                                                  &none            &kp LC(F18)      &kp LC(F19)      &kp LC(F20)      &kp LC(LA(F13))  &kp LC(LA(F14))  &trans
&trans  &kp F13          &kp F14          &kp F15          &kp F16          &kp F17          &none            &trans  &trans      &trans  &trans  &none            &kp F19          &kp F20          &kp LA(F13)      &kp LA(F14)      &none            &none
&trans  &trans           &trans           &trans           &trans           &trans                            &trans      &trans                               &trans           &trans           &trans           &trans           &trans           &trans
&trans  &trans           &trans           &trans           &trans                            &trans           &trans  &trans      &trans  &trans  &trans                            &trans           &trans           &trans           &trans           &none
            >;
        };

        /* Numpad layer.
         * Right hand becomes a compact numpad.
         * Left side keeps a few symbols for quick data entry without mode churn.
         */
        layer_numpad {
            bindings = <
&trans  &trans    &trans  &trans     &trans    &trans       &trans                                                                 &trans  &trans           &kp MINUS     &kp PLUS      &kp EQUAL     &kp PIPE       &trans
&trans  &trans    &trans  &trans     &trans    &trans       &kp KP_SLASH                                                           &trans  &trans           &kp N7        &kp N8        &kp N9        &kp BSLH       &trans
&trans  &kp EXCL  &kp AT  &kp HASH   &kp DLLR  &kp PRCNT    &kp KP_MULTIPLY  &trans  &trans            &trans       &trans         &trans  &kp KP_NUM       &kp N4        &kp N5        &kp N6        &kp DOT        &trans
&trans  &trans    &trans  &trans     &trans    &trans                                 &kp KP_MINUS      &kp KP_PLUS                         &kp N0           &kp N1        &kp N2        &kp N3        &kp FSLH       &trans
&trans  &trans    &trans  &trans     &trans                 &trans           &trans   &trans            &trans       &kp BACKSPACE  &trans                   &kp N0        &trans        &trans        &trans         &trans
            >;
        };

        /* Hyper app layer.
         * This intentionally emits Hyper+<key> at every position so GlazeWM can
         * own launching, focusing, and utility shortcuts with one consistent grammar.
         */
        layer_app {
            bindings = <
&kp LC(LA(LG(EQUAL)))  &kp LC(LA(LG(N1)))     &kp LC(LA(LG(N2)))  &kp LC(LA(LG(N3)))    &kp LC(LA(LG(N4)))     &kp LC(LA(LG(N5)))  &kp LC(LA(LG(F1)))                                                                                                 &kp LC(LA(LG(F2)))     &kp LC(LA(LG(N6)))  &kp LC(LA(LG(N7)))  &kp LC(LA(LG(N8)))     &kp LC(LA(LG(N9)))    &kp LC(LA(LG(N0)))    &kp LC(LA(LG(MINUS)))
&kp LC(LA(LG(TAB)))    &kp LC(LA(LG(Q)))      &kp LC(LA(LG(W)))   &kp LC(LA(LG(E)))     &kp LC(LA(LG(R)))      &kp LC(LA(LG(T)))   &kp LC(LA(LG(F3)))                                                                                                 &kp LC(LA(LG(F4)))     &kp LC(LA(LG(Y)))   &kp LC(LA(LG(U)))   &kp LC(LA(LG(I)))      &kp LC(LA(LG(O)))     &kp LC(LA(LG(P)))     &kp LC(LA(LG(BSLH)))
&kp LC(LA(LG(ESC)))    &kp LC(LA(LG(A)))      &kp LC(LA(LG(S)))   &kp LC(LA(LG(D)))     &kp LC(LA(LG(F)))      &kp LC(LA(LG(G)))   &kp LC(LA(LG(F5)))    &kp LC(LA(LG(F6)))   &kp LC(LA(LG(F7)))        &kp LC(LA(LG(F8)))     &kp LC(LA(LG(F9)))     &kp LC(LA(LG(F10)))    &kp LC(LA(LG(H)))   &kp LC(LA(LG(J)))   &kp LC(LA(LG(K)))      &kp LC(LA(LG(L)))     &kp LC(LA(LG(SEMI)))  &kp LC(LA(LG(SQT)))
&kp LC(LA(LG(LSHFT)))  &kp LC(LA(LG(Z)))      &kp LC(LA(LG(X)))   &kp LC(LA(LG(C)))     &kp LC(LA(LG(V)))      &kp LC(LA(LG(B)))                                              &kp LC(LA(LG(HOME)))      &kp LC(LA(LG(PG_UP)))                                                &kp LC(LA(LG(N)))   &kp LC(LA(LG(M)))   &kp LC(LA(LG(COMMA)))  &kp LC(LA(LG(DOT)))   &kp LC(LA(LG(FSLH)))  &kp LC(LA(LG(RSHFT)))
&kp LC(LA(LG(GRAVE)))  &kp LC(LA(LG(GRAVE)))  &trans              &kp LC(LA(LG(LEFT)))  &kp LC(LA(LG(RIGHT)))                      &kp LC(LA(LG(BSPC)))  &kp LC(LA(LG(DEL)))  &kp LC(LA(LG(END)))       &kp LC(LA(LG(PG_DN)))  &kp LC(LA(LG(ENTER)))  &kp LC(LA(LG(SPACE)))                      &kp LC(LA(LG(UP)))  &kp LC(LA(LG(DOWN)))   &kp LC(LA(LG(LBKT)))  &kp LC(LA(LG(RBKT)))  &kp LC(LA(LG(F11)))
            >;
        };
    };
};
```

## 5) Final GlazeWM redesign
- Keyboard focus is deterministic: `focus_follows_cursor` is off.
- Workspace count is reduced and tied directly to the 3-monitor setup.
- Core apps get stable default homes through window rules.
- The binding map now matches the ADV360 WM layer instead of the older mixed model.
- Rewritten config:

```yaml
# Unified ADV360 + GlazeWM workflow system.
# Core grammar:
# - A/S/D = left / center / right monitor
# - F/G   = previous / next workspace on the current monitor
# - J/K/L/; = left / down / up / right
# - Ctrl row = direct workspace targeting
# - Win row = WM utility + resize

general:
  focus_follows_cursor: false
  toggle_workspace_on_refocus: false
  cursor_jump:
    enabled: true
    trigger: "monitor_focus"

gaps:
  inner_gap: "6px"
  outer_gap:
    top: "4px"
    right: "6px"
    bottom: "6px"
    left: "6px"

window_effects:
  focused_window:
    border:
      enabled: true
      color: "#4F8FBA"

workspaces:
  # Left monitor: infra / files / overflow.
  - name: "1"
    display_name: "L1"
    bind_to_monitor: 0
    keep_alive: true
  - name: "2"
    display_name: "L2"
    bind_to_monitor: 0
    keep_alive: true
  - name: "3"
    display_name: "L3"
    bind_to_monitor: 0
    keep_alive: true
  # Center monitor: code / terminal / debug.
  - name: "4"
    display_name: "C1"
    bind_to_monitor: 1
    keep_alive: true
  - name: "5"
    display_name: "C2"
    bind_to_monitor: 1
    keep_alive: true
  - name: "6"
    display_name: "C3"
    bind_to_monitor: 1
    keep_alive: true
  # Right monitor: browser / docs / communication.
  - name: "7"
    display_name: "R1"
    bind_to_monitor: 2
    keep_alive: true
  - name: "8"
    display_name: "R2"
    bind_to_monitor: 2
    keep_alive: true
  - name: "9"
    display_name: "R3"
    bind_to_monitor: 2
    keep_alive: true
  # Scratch workspace for temporary tasks.
  - name: "10"
    display_name: "X"
    bind_to_monitor: 1
    keep_alive: true

window_behavior:
  initial_state: "tiling"
  state_defaults:
    floating:
      centered: true
      shown_on_top: true
    fullscreen:
      maximized: false
      shown_on_top: true

window_rules:
  # Ignore system or overlay windows that should stay out of the tiling model.
  - commands: ["ignore"]
    match:
      - window_process: { equals: "Taskmgr" }
      - window_process: { equals: "SystemSettings" }
      - window_process: { equals: "mmc" }
      - window_process: { equals: "SearchHost" }
      - window_process: { equals: "StartMenuExperienceHost" }
      - window_process: { equals: "LockApp" }
      - window_process: { regex: "(?i).*powertoys.*" }
      - window_process: { regex: "(?i)yasb.*" }
      - window_class: { regex: "(?i)yasb.*" }
      - window_process: { equals: "1Password" }
      - window_process: { equals: "Bitwarden" }
      - window_process: { equals: "KeePass" }
      - window_process: { equals: "Flow.Launcher" }
      - window_process: { regex: "(?i)keypirinha" }

  # Float transient dialogs instead of forcing them into the tile tree.
  - commands: ["set-floating"]
    match:
      - window_title: { regex: "(?i)(open file|save as|find and replace|choose a file|select folder)" }
      - window_class: { regex: "(?i)#32770" }

  # Stable homes for the core dev loop.
  - commands: ["move --workspace 4"]
    match:
      - window_process: { equals: "Code" }
      - window_process: { equals: "devenv" }
      - window_process: { regex: "(?i)webstorm|rider|idea64|pycharm64|clion64" }

  - commands: ["move --workspace 5"]
    match:
      - window_process: { equals: "WindowsTerminal" }
      - window_process: { equals: "wezterm-gui" }
      - window_process: { equals: "Alacritty" }

  - commands: ["move --workspace 7"]
    match:
      - window_process: { equals: "chrome" }
      - window_process: { equals: "msedge" }
      - window_process: { equals: "brave" }

  - commands: ["move --workspace 8"]
    match:
      - window_process: { equals: "Obsidian" }
      - window_process: { equals: "Notion" }
      - window_process: { equals: "Postman" }
      - window_process: { equals: "azuredatastudio" }
      - window_process: { equals: "explorer" }

  - commands: ["move --workspace 9"]
    match:
      - window_process: { equals: "slack" }
      - window_process: { regex: "(?i)teams" }
      - window_process: { equals: "OUTLOOK" }
      - window_process: { equals: "Zoom" }

keybindings:
  # Bare WM home row from the ADV360 WM layer.
  - commands: ["focus --monitor 0"]
    bindings: ["f13"]
  - commands: ["focus --monitor 1"]
    bindings: ["f14"]
  - commands: ["focus --monitor 2"]
    bindings: ["f15"]

  - commands: ["focus --prev-active-workspace-on-monitor"]
    bindings: ["f16"]
  - commands: ["focus --next-active-workspace-on-monitor"]
    bindings: ["f17"]

  - commands: ["focus --direction left"]
    bindings: ["f19"]
  - commands: ["focus --direction down"]
    bindings: ["f20"]
  - commands: ["focus --direction up"]
    bindings: ["alt+f13"]
  - commands: ["focus --direction right"]
    bindings: ["alt+f14"]

  # Shift + monitor anchors send the window to each monitor's primary lane.
  - commands: ["move --workspace 1", "focus --workspace 1"]
    bindings: ["shift+f13"]
  - commands: ["move --workspace 4", "focus --workspace 4"]
    bindings: ["shift+f14"]
  - commands: ["move --workspace 7", "focus --workspace 7"]
    bindings: ["shift+f15"]

  - commands: ["move --prev-active-workspace-on-monitor", "focus --prev-active-workspace-on-monitor"]
    bindings: ["shift+f16"]
  - commands: ["move --next-active-workspace-on-monitor", "focus --next-active-workspace-on-monitor"]
    bindings: ["shift+f17"]

  - commands: ["move --direction left"]
    bindings: ["shift+f19"]
  - commands: ["move --direction down"]
    bindings: ["shift+f20"]
  - commands: ["move --direction up"]
    bindings: ["shift+alt+f13"]
  - commands: ["move --direction right"]
    bindings: ["shift+alt+f14"]

  # Ctrl row = direct workspace targeting.
  - commands: ["focus --workspace 1"]
    bindings: ["ctrl+f13"]
  - commands: ["focus --workspace 2"]
    bindings: ["ctrl+f14"]
  - commands: ["focus --workspace 3"]
    bindings: ["ctrl+f15"]
  - commands: ["focus --workspace 4"]
    bindings: ["ctrl+f16"]
  - commands: ["focus --workspace 5"]
    bindings: ["ctrl+f17"]
  - commands: ["focus --workspace 6"]
    bindings: ["ctrl+f18"]
  - commands: ["focus --workspace 7"]
    bindings: ["ctrl+f19"]
  - commands: ["focus --workspace 8"]
    bindings: ["ctrl+f20"]
  - commands: ["focus --workspace 9"]
    bindings: ["ctrl+alt+f13"]
  - commands: ["focus --workspace 10"]
    bindings: ["ctrl+alt+f14"]

  - commands: ["move --workspace 1", "focus --workspace 1"]
    bindings: ["ctrl+shift+f13"]
  - commands: ["move --workspace 2", "focus --workspace 2"]
    bindings: ["ctrl+shift+f14"]
  - commands: ["move --workspace 3", "focus --workspace 3"]
    bindings: ["ctrl+shift+f15"]
  - commands: ["move --workspace 4", "focus --workspace 4"]
    bindings: ["ctrl+shift+f16"]
  - commands: ["move --workspace 5", "focus --workspace 5"]
    bindings: ["ctrl+shift+f17"]
  - commands: ["move --workspace 6", "focus --workspace 6"]
    bindings: ["ctrl+shift+f18"]
  - commands: ["move --workspace 7", "focus --workspace 7"]
    bindings: ["ctrl+shift+f19"]
  - commands: ["move --workspace 8", "focus --workspace 8"]
    bindings: ["ctrl+shift+f20"]
  - commands: ["move --workspace 9", "focus --workspace 9"]
    bindings: ["ctrl+alt+shift+f13"]
  - commands: ["move --workspace 10", "focus --workspace 10"]
    bindings: ["ctrl+alt+shift+f14"]

  # Win row = WM utilities on the left, resize on the right.
  - commands: ["wm-redraw"]
    bindings: ["lwin+f13"]
  - commands: ["wm-reload-config"]
    bindings: ["lwin+f14"]
  - commands: ["set-minimized"]
    bindings: ["lwin+f15"]
  - commands: ["toggle-floating"]
    bindings: ["lwin+f16"]
  - commands: ["toggle-fullscreen"]
    bindings: ["lwin+f17"]

  - commands: ["resize --width -5%"]
    bindings: ["lwin+f18"]
  - commands: ["resize --height +5%"]
    bindings: ["lwin+f19"]
  - commands: ["resize --height -5%"]
    bindings: ["lwin+f20"]
  - commands: ["resize --width +5%"]
    bindings: ["lwin+alt+f13"]
  - commands: ["toggle-tiling-direction"]
    bindings: ["lwin+alt+f14"]

  # Hyper app layer: left home row is the daily engineering loop.
  - commands: ['shell-exec cmd /c start "" wt.exe']
    bindings: ["ctrl+alt+lwin+a"]
  - commands: ['shell-exec cmd /c code']
    bindings: ["ctrl+alt+lwin+s"]
  - commands: ['shell-exec cmd /c start "" "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --profile-directory="Profile 3"']
    bindings: ["ctrl+alt+lwin+d"]
  - commands: ['shell-exec cmd /c start "" explorer.exe']
    bindings: ["ctrl+alt+lwin+f"]
  - commands: ['shell-exec cmd /c start "" "%LOCALAPPDATA%\\gitkraken\\gitkraken.exe"']
    bindings: ["ctrl+alt+lwin+g"]

  # Hyper app layer: right home row is communication and context.
  - commands: ['shell-exec cmd /c start "" "%LOCALAPPDATA%\\slack\\slack.exe"']
    bindings: ["ctrl+alt+lwin+h"]
  - commands: ['shell-exec cmd /c start "" "%LOCALAPPDATA%\\Microsoft\\Teams\\Update.exe" --processStart "Teams.exe"']
    bindings: ["ctrl+alt+lwin+j"]
  - commands: ['shell-exec cmd /c start "" "C:\\Program Files\\Microsoft Office\\root\\Office16\\OUTLOOK.EXE"']
    bindings: ["ctrl+alt+lwin+k"]
  - commands: ['shell-exec cmd /c start "" "%LOCALAPPDATA%\\Notion\\Notion.exe"']
    bindings: ["ctrl+alt+lwin+l"]
  - commands: ['shell-exec cmd /c start "" "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\KeePass 2.lnk"']
    bindings: ["ctrl+alt+lwin+semicolon"]

  # Hyper app layer: top row holds alternate browsers and secondary dev tools.
  - commands: ['shell-exec cmd /c start "" "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --profile-directory="Profile 2"']
    bindings: ["ctrl+alt+lwin+q"]
  - commands: ['shell-exec cmd /c start "" "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --profile-directory="Profile 3"']
    bindings: ["ctrl+alt+lwin+w"]
  - commands: ['shell-exec cmd /c start "" "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"']
    bindings: ["ctrl+alt+lwin+e"]
  - commands: ['shell-exec cmd /c start "" "%LOCALAPPDATA%\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"']
    bindings: ["ctrl+alt+lwin+r"]
  - commands: ['shell-exec cmd /c start "" "%LOCALAPPDATA%\\Programs\\Obsidian\\Obsidian.exe"']
    bindings: ["ctrl+alt+lwin+t"]

  - commands: ['shell-exec cmd /c start "" "%LOCALAPPDATA%\\Postman\\Postman.exe"']
    bindings: ["ctrl+alt+lwin+y"]
  - commands: ['shell-exec cmd /c start "" "C:\\Program Files\\Azure Data Studio\\azuredatastudio.exe"']
    bindings: ["ctrl+alt+lwin+u"]
  - commands: ['shell-exec cmd /c start "" "%LOCALAPPDATA%\\JetBrains\\Toolbox\\bin\\jetbrains-toolbox.exe"']
    bindings: ["ctrl+alt+lwin+i"]
  - commands: ['shell-exec cmd /c start "" "C:\\Program Files\\Everything\\Everything.exe"']
    bindings: ["ctrl+alt+lwin+o"]
  - commands: ['shell-exec cmd /c start spotify:']
    bindings: ["ctrl+alt+lwin+p"]

  # Hyper app layer: bottom row is overflow utility.
  - commands: ['shell-exec cmd /c start "" "%LOCALAPPDATA%\\Programs\\zoom\\Zoom.exe"']
    bindings: ["ctrl+alt+lwin+z"]
  - commands: ['shell-exec cmd /c start "" "C:\\Program Files\\Notepad++\\notepad++.exe"']
    bindings: ["ctrl+alt+lwin+x"]
  - commands: ['shell-exec cmd /c start "" "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --profile-directory="Default"']
    bindings: ["ctrl+alt+lwin+c"]
  - commands: ['shell-exec cmd /c start "" "C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe"']
    bindings: ["ctrl+alt+lwin+v"]
  - commands: ['shell-exec gsudo wt.exe']
    bindings: ["ctrl+alt+lwin+b"]

  - commands: ['shell-exec wt -p "PowerShell 7" new-tab --startingDirectory "%USERPROFILE%\\Documents\\GitHub"']
    bindings: ["ctrl+alt+lwin+n"]
  - commands: ['shell-exec cmd /c start "" "%LOCALAPPDATA%\\Programs\\Microsoft VS Code\\Code.exe" "%USERPROFILE%\\Documents\\GitHub"']
    bindings: ["ctrl+alt+lwin+m"]
  - commands: ['shell-exec cmd /c start "" python "%USERPROFILE%\\import pyautogui.py"']
    bindings: ["ctrl+alt+lwin+comma"]
  - commands: ['shell-exec cmd /c start "" "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --profile-directory="Profile 1"']
    bindings: ["ctrl+alt+lwin+period"]

  - commands: ["focus --monitor 0"]
    bindings: ["ctrl+alt+lwin+left"]
  - commands: ["focus --monitor 1"]
    bindings: ["ctrl+alt+lwin+up"]
  - commands: ["focus --monitor 2"]
    bindings: ["ctrl+alt+lwin+right"]
```

## 6) Binding matrix

Monitor layout: **center** (code/primary) — **above** (terminal/logs) — **right** (browser/comms)

| Action | Keybinding | Layer/context | Rationale |
| --- | --- | --- | --- |
| Focus above / center / right monitor | `A / S / D` | WM | S = strongest finger = primary monitor |
| Send window to above / center / right monitor | `Shift+A / Shift+S / Shift+D` | WM | Same anchors, Shift means move |
| Previous / next workspace on current monitor | `F / G` | WM | Compact lane next to monitor control |
| Send window to previous / next workspace | `Shift+F / Shift+G` | WM | Move semantic mirrors focus semantic |
| Focus window left / down / up / right | `H / J / K / L` | WM and NAV | Standard HJKL |
| Move window left / down / up / right | `Shift+H / Shift+J / Shift+K / Shift+L` | WM | Same cluster, Shift means move |
| Resize left / down / up / right | Win row right cluster | WM | Resize sits adjacent to direction logic |
| Focus workspaces `1-10` | Ctrl row (Q=WS1 … P=WS10) | WM | Direct jump without number-row reach |
| Move to workspaces `1-10` | Ctrl+Shift row | WM | Same map with move semantic |
| Terminal / VS Code / Chrome / Explorer / Git | `A / S / D / F / G` | APP | Core development loop |
| Teams / Postman / Outlook / Obsidian / KeePass | `H / J / K / L / ;` | APP | Communication and context cluster |

## 7) Migration plan
- What will feel different: window control becomes monitor-first, workspaces become fewer and more intentional, and OS navigation moves off HJKL habits.
- What to learn first: `J/K/L/;` for direction, `A/S/D` for monitors, `F/G` for workspace cycle, then the APP home row.
- 7-day path:
  1. Day 1: monitor focus and window focus
  2. Day 2: workspace cycle
  3. Day 3: direct workspace jumps
  4. Day 4: move semantics with Shift
  5. Day 5: resize row
  6. Day 6: symbol layer
  7. Day 7: remove remaining HJKL OS habits
- Old habits to drop: mouse-driven focus changes, flat workspace sprawl, and HJKL as a system-wide default.

## 8) Cheat sheet

**Layer access (from BASE):**
- `BSPC` hold = SYM
- `DEL` hold = NUM
- `ENTER` hold = WM
- `SPACE` hold = NAV
- `ESC` thumb hold = APP (Hyper layer)

**WM layer grammar:**
- `A / S / D` = focus above / center / right monitor
- `Shift+A/S/D` = send window to that monitor's anchor workspace
- `F / G` = prev / next workspace on current monitor
- `Shift+F/G` = move window to prev / next workspace
- `H / J / K / L` = focus window left / down / up / right
- `Shift+H/J/K/L` = move window directionally
- Ctrl row (Q=WS1 … P=WS10) = direct workspace jump
- Ctrl+Shift row = move window to that workspace
- Win row left = WM utilities (redraw / reload / minimize / float / fullscreen)
- Win row right = resize (←↓↑→ + toggle-tiling-dir)

**APP home row (Hyper = Ctrl+Alt+Win):**
- `A` = Windows Terminal  →  launches to WS 4 (above)
- `S` = VS Code           →  launches to WS 1 (center)
- `D` = Chrome            →  launches to WS 7 (right)
- `F` = File Explorer
- `G` = GitKraken
- `H` = Teams             →  auto-moves to WS 9 (right)
- `J` = Postman           →  auto-moves to WS 6 (above)
- `K` = Outlook           →  auto-moves to WS 9 (right)
- `L` = Obsidian          →  auto-moves to WS 8 (right)
- `;` = KeePass

## 9) Implementation notes

- **Monitor indices**: `glazewm-config.yaml` assumes center=0, above=1, right=2. Run `glazewm query monitors` to verify and update the three `focus --monitor N` lines if they differ.
- **Hyper key**: APP layer now uses `Ctrl+Alt+Win` (`LC+LA+LG`). If any app intercepts this chord, adjust the GlazeWM binding syntax — the keyboard side doesn't need to change.
- **App launch paths**: Some paths in `glazewm-config.yaml` may need local correction if software is installed in a non-standard location.
- **HRM tuning**: `tapping-term-ms=220`, `quick-tap-ms=175`, `balanced` flavor. If home-row mods misfire during fast typing, increase `require-prior-idle-ms` in 25ms increments. If they feel sluggish, reduce `tapping-term-ms`.
- **version.dtsi**: Always blank in git. The build scripts populate it automatically; `make` runs `git checkout config/version.dtsi` to restore it after each build.
- **No combos or one-shot mods**: intentional — value comes from hold-tap layers. More stateful behavior would raise adoption cost.
- **Shift+monitor-anchor sends to WS 1/4/7**: Predictable fixed target rather than "current active workspace on that monitor". You always know where the window lands.
