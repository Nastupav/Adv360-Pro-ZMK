# Fast-typing home-row-mod profile — 25 September 2026

This is the active follow-up to the baseline overhaul. The user explicitly chose
home-row modifiers and asked that **fast typing take priority**.

## BASE mapping

| Key | Tap | Hold |
|---|---|---|
| A | A | Command / GUI |
| S | S | Option / Alt |
| D | D | Control |
| F | F | Shift |
| J | J | Shift |
| K | K | Control |
| L | L | Option / Alt |
| ; | ; | Command / GUI |

The dedicated thumb Command/Control keys, inner Option keys and outer Shift keys
remain unchanged. They are the deterministic fallback for same-hand chords, very
fast shortcuts, mouse-modifier use, and any situation where timing should not be
involved. NAV remains **J K L ; = Left / Down / Up / Right**.

## Timing profile

The two bilateral hold-taps use:

```text
flavor                 balanced
tapping-term-ms        280
quick-tap-ms            175
require-prior-idle-ms   150
hold-trigger-on-release enabled
left triggers           KEYS_R + THUMBS
right triggers          KEYS_L + THUMBS
```

This follows the current ZMK/urob-style “timeless HRM” pattern. The 150 ms
`require-prior-idle-ms` gate is the primary fast-typing safeguard: an HRM pressed
soon after ordinary typing resolves immediately as its tap character instead of
waiting for a tap/hold decision. The positional trigger lists prevent same-hand
rolls from becoming modifiers when the firmware honors positional hold-taps, and
`hold-trigger-on-release` allows multiple modifiers to be combined.

Primary references:

- https://zmk.dev/docs/keymaps/behaviors/hold-tap
- https://github.com/urob/zmk-config/blob/main/config/base.keymap
- https://github.com/KinesisCorporation/Adv360-Pro-ZMK/issues/596

## Kinesis-fork caveat

Kinesis issue #596 remains open and reports `hold-trigger-key-positions` being
ignored on an Advantage360 Pro build, causing a fast roll such as `l-i` to become
a modifier chord. Because this repository pins a Kinesis/refil fork, the profile
**does not assume positional filtering is proven on hardware**. The prior-idle
gate and retained dedicated modifiers reduce the risk, but actual fast-typing
acceptance must be tested after flashing.

If false modifier activations occur, tune in this order:

1. Increase `HRM_PRIOR_IDLE_MS` from 150 to 175 ms. This is the strongest typing-first adjustment.
2. If modifiers then become too difficult to invoke during normal flow, return toward 150/125 ms.
3. Do not shorten the tapping term first; that makes accidental long holds easier.
4. If positional filtering is demonstrably broken on the pinned fork, use the dedicated modifiers while evaluating a tap-preferred HRM fallback.

## Validation contract

Repository validation now enforces exactly eight HRMs at the positions above,
checks the three timing constants, requires the two bilateral positional trigger
sets and `hold-trigger-on-release`, rejects arbitrary additional hold-taps, and
keeps the dedicated modifiers accessible through all 16 simultaneous layer
combinations. Physical layer images are regenerated from the firmware source.
