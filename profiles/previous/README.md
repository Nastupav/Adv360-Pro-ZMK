# Previous profile, saved 20 September 2026

This is the newest working keymap at the start of the daily-driver overhaul,
including uncommitted September 8 changes. It preserves MAC/WIN/NAV/SYM/NUM/
GLOBAL/SYS/NAVWIN/EDIT/POINTER and the host protocols. It is a reference and
rollback source, not an additional active keymap. Host files remain unchanged.

The exact pre-edit repository snapshot, including its tools, tests and diagrams,
is locally archived at `firmware/pre-daily-driver-20260920/working-tree.tar.gz`.
The existing September 8 left/right UF2 pair and matching source/manifest remain
in `firmware/`. See the current `docs/setup.md` for recovery and rollback.

`bin/validate_protocol.py` checks this saved profile against the retained host
files. It does not claim that the five-layer daily driver emits the old protocol.
