# Build, install and roll back

## Build and artifacts

From the repository root:

```sh
make validate
make
```

`make` validates and builds **both** halves through the repository's Docker/Podman
workflow. It needs a running container engine and network access for uncached
images/modules. `make left` is a partial build, not the normal installation path.
GitHub Actions runs the same validation, the native event scenarios, then both
boards. The pinned vendor source and build results are in [validation.md](validation.md).

The prepared final pair is **`adv360-202609201003-66d6b27-left.uf2`** and
**`adv360-202609201003-66d6b27-right.uf2`**.

Each build emits a matched `adv360-<UTC timestamp>-<starting commit>-left.uf2` and
`-right.uf2`, effective `.config` files, frozen dependency manifest, exact config
source archive, and `SHA256SUMS`. The commit suffix is the starting commit, not a
claim that uncommitted changes were committed. Keep the source archive with its
firmware. The prepared delivery zip also includes this guide and the diagrams.

Verify the checksum manifest from inside the firmware directory:

```sh
cd firmware
shasum -a 256 -c SHA256SUMS
```

Do not use `make clean` or `make clean_firmware` while relying on local rollback
UF2s; the existing cleanup targets remove firmware files.

## Flash both halves yourself

Flashing was intentionally left to you. Keep the old matched pair before starting.
Use the physical buttons for the first install because the current firmware may
have different key bindings.

1. Connect the **left** module by USB; disconnect and power down the right.
2. Quickly double-click the left module's physical bootloader/reset button with
   a paperclip. The button sits inside the thumb cluster; locate it in the
   [Kinesis instructions](https://kinesis-ergo.com/wp-content/uploads/Advantage360-Professional-Firmware-Update-Instructions-9.5.24-KB360-PRO.pdf).
   Wait for the `ADV360PRO` removable drive.
3. Copy only the new **left** UF2 to that drive. Wait for flashing to finish and
   the drive to disappear. Do not interrupt power during the transfer.
4. Turn on the left battery and disconnect its USB cable. Keep the left awake
   while updating the right (tap the dedicated left NAV key 52 as needed).
5. Connect the **right** module over USB. Double-click its own physical button;
   copy only the matching **right** UF2. Wait for flashing and drive disappearance.
6. Turn the right battery on and reconnect normally. Power the left first and
   turn it off last. Hold NUM and check both layer indicators agree; release it
   and confirm ordinary typing returns.

A macOS eject warning can occur when the bootloader disconnects itself. It is
not sufficient evidence of a failed or successful flash: confirm completion and
test the keyboard. Open only one bootloader drive at a time to avoid mixing halves.

Once this layout is installed and the split link is working, hold SYS (75), then
press **6 for the left bootloader or 7 for the right**. These are the innermost
number-row keys (BASE F11/F12), not the keycaps marked 6/7. Connect the target
half's USB cable first. SYS + 20/21 resets left/right without entering bootloader.
The fork routes these behaviors to the physical source half. The physical buttons
work independently of the keymap and are the recovery path when the split link
is unavailable. Keyboard recovery shortcuts require a live central/split path.

## Bluetooth, output and indicators

SYS + number-row 1–5 chooses profiles **0–4**. Existing pairing storage is retained;
profile selection does not clear a bond. SYS + outer-left number key 0 selects USB;
SYS + position 8 (BASE 6) selects Bluetooth; position 9 toggles the preferred output.
Positions 10/11 select next/previous profile. USB host data is through the left
module; the right remains the split peripheral even when charged by USB.

Only when intentionally replacing a host pairing: select its profile, hold SYS,
then press both outermost number-row keys (0 + 13) within 150 ms. This clears
**only the selected host bond**. Forget that pairing on the host and pair again.
It does not repair the inter-half bond. Ordinary flashing does not require a
settings reset. Follow the vendor's matching-version settings-reset instructions
only if power cycling and correct matched firmware do not restore operation.

Kinesis lighting effect **4** shows the highest active layer and Bluetooth state.
The existing indicator/backlight configuration is retained. SYS + V toggles RGB;
SYS + B cycles effects, including the battery display at effect 5; cycle back to 4
for layer indications. SYS + Z toggles white key lighting; X/C adjusts it. Indicator
colors are BASE off, NAV white, SYM blue, NUM green and SYS red,
so old ten-layer color expectations no longer apply. Caps Word does not turn on Caps Lock. Host BLE battery reporting remains
disabled, as before; physical battery indication remains available.

## Rollback

The previous matched pair is still in `firmware/`:

- `adv360-202609081228-66d6b27-left.uf2`
- `adv360-202609081228-66d6b27-right.uf2`

Use the same two-half flashing steps with that pair to restore the previous
layout. Its source archive and frozen manifest remain beside it; the delivery zip
contains a `rollback/` copy. That pair is a prior build, not a newly claimed
hardware-tested recovery image. Do not mix its halves with the new pair.

To inspect or rebuild the entire pre-edit working source without overwriting
this checkout, extract `firmware/pre-daily-driver-20260920/working-tree.tar.gz`
into a **new empty directory**. It contains the prior config, scripts, tests,
README, docs, workflow and host files, including uncommitted changes. This active
repository also preserves the old keymap/macros under `profiles/previous/`.

No macOS, AeroSpace, VS Code, Neovim or remote Windows settings were changed by
this overhaul, so no host rollback is required. Existing host files and earlier
host backups belong to the previous work and are left in place.

## Hardware acceptance

Use an empty text buffer, then your normal editors. Compilation and simulation
cannot complete these checks for you.

- [ ] BASE: type `asdf jkl; qwerty`, rapid alternating letters, Shift+letters,
      Space, Enter, Backspace, Delete, Escape, Tab, Command, Control and Option.
      Check all 76 positions against the BASE diagram.
- [ ] NUM: hold large left key 66 and immediately type UIO, JKL, M-comma-period;
      expect `789456123`. Space thumb gives `0`; Enter and right-thumb Backspace
      work. Hold a digit long enough for host repeat, then release it: no sticking.
- [ ] Release NUM before a held digit, and after it; type U afterward. Escape
      while NUM is held sends Escape and leaves NUM active until its hold releases.
- [ ] Hold/release NAV, SYM and NUM in different orders. Highest layer wins;
      release all and confirm BASE. Check SYS + 64 cancellation and release all
      keys afterward. Ensure Command/Shift do not stick across layer release.
- [ ] ABC/US: type all SYM characters and `== != <= >= -> := :: ** // |>`. Hold
      a repeatable symbol. Check Caps Word through underscore and NUM digits,
      then Space; confirm normal lowercase resumes.
- [ ] Czech: NUM still types `7894561230`, `1.25`, `1,25`, `+ - * / =`. Check Czech
      diacritics, physical Y/Z behavior, Option and source switching. SYM is not
      expected to preserve US characters in Czech; switch back to ABC for code.
- [ ] VS Code: repeat numeric/symbol entry under both sources; JKL; arrows,
      Shift selection, Option word movement and Command line/document edges.
      Check completion/source-switching conflicts and both native/Neovim workflows.
- [ ] Neovim: BASE normal-mode commands unchanged; NAV arrows in normal/insert
      mode; NUM in insert mode under both sources; Escape and Ctrl combinations.
      Check terminal keypad mode if numbers produce navigation/escape sequences.
- [ ] Remote Windows PowerShell: verify US remote layout, Num Lock, NUM digits,
      decimal point/comma, `$ @ |` and backtick. Check Ctrl+arrows, Home/End,
      Ctrl+Home/End, selection and the client's keyboard forwarding mode.
- [ ] Wireless: test each used BT profile, left/right reconnection, USB/BLE output
      changes, reconnect after host sleep and keyboard idle/sleep. Check battery
      display and layer indicators on both halves. Test repeat over USB and BLE.
- [ ] Recovery: with each target half connected by USB, confirm its physical
      bootloader button works. After installation, verify the SYS left/right
      bootloader controls separately when the split link is live. Do not clear a
      working Bluetooth bond just to test the clear chord.

Stop and note the exact source, app, held layer and keys if a check fails; the
prepared old pair provides a route back while the configuration is adjusted.
