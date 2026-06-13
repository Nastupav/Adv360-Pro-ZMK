# Adv360 Pro ZMK — Personal Keymap

macOS-primary developer keymap for the Kinesis Advantage360 Pro.

**7 layers**: BASE, NAV, SYM, NUM, FUN, SYS, APP
**Home-row mods**: positional hold-tap (Cmd/Alt/Ctrl/Shift)
**Home-row combos**: `=` `|` `_` `()` `[]` `{}` all chordable from home row

## Build

```sh
make          # local Docker build (both halves, Clique+Studio)
make left     # left half only
```

Or push to trigger GitHub Actions.

## Flash

UF2 files land in `firmware/`. Press the reset button on each half, drag the `.uf2` file to the mounted drive.

## Keymap

See `config/adv360.keymap` — fully commented with ASCII layer diagrams.
