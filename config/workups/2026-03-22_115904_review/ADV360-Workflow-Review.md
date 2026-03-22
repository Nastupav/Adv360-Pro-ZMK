---
title: ADV360 Workflow Review
date: 2026-03-22
status: workup
tags:
  - keyboard
  - zmk
  - adv360
  - glazewm
  - windows
  - ergonomics
---

# ADV360 Workflow Review

> [!summary]
> This is a refinement problem, not a redesign problem.
> The core architecture is already strong: F13-F22 for GlazeWM, a clear 3-monitor model, and a direct Hyper app layer.
> The biggest wins are small, concrete, and high-ROI.

## Executive Summary

### What is already strong
- F13-F22 as the WM namespace is the right Windows strategy.
- GlazeWM responsibilities are separated cleanly from firmware responsibilities.
- The 3-monitor model is coherent and optimized around a center-hub workflow.
- The Hyper app layer is well matched to the real app stack.

### Biggest weaknesses
- WM directions were effectively shifted to `J/K/L/;` instead of a true `H/J/K/L` cluster.
- The APP entry key previously tapped `CAPS`, which is high-friction and low-value.
- The NAV layer was too sparse for real Windows/editor/browser work.

### Top 3 changes
1. Make the APP entry key tap `ESC`, not `CAPS`.
2. Put WM directions on `H/J/K/L`.
3. Densify NAV around `find`, `cut/copy/paste/select-all`, and prev/next tab.

### Verdict
- You do **not** need a full redesign.
- You need a focused cleanup of a few high-frequency paths.

---

## Environment Model

### Windows stack
- GlazeWM is the primary keyboard window-management layer.
- Yasb is active as the top bar and exposes GlazeWM workspaces/binding mode.
- PowerToys Run is active on `Alt+Space`.
- FancyZones is installed and active, but not overriding Windows snap hotkeys.
- VS Code appears mostly stock.
- Windows Terminal is lightly customized.
- WezTerm is installed and configured for PowerShell.

### Monitor model
- This is a **3-monitor hub-and-spoke** setup.
- Strongest inference:
  - Monitor `0` = center / primary dev monitor
  - Monitor `1` = top monitor
  - Monitor `2` = right monitor
- Workspace allocation confirms that:
  - `1..10` live on monitor `0`
  - `11..15` live on monitor `1`
  - `16..20` live on monitor `2`

### Workflow model
- Likely dominant activities:
  - coding
  - terminal work
  - browser/docs
  - chat/comms
  - notes/data/file management
  - cross-monitor focus switching
  - workspace targeting
- Likely highest-frequency actions per hour:
  - type / delete / shift
  - copy / paste / cut / undo / redo
  - find
  - tab switching
  - workspace focus
  - monitor refocus
  - directional window focus
  - app launch for the daily core set

### Ergonomic priorities
- Keep thumbs doing high-value layer work, not gimmicks.
- Avoid unnecessary right-pinky load.
- Avoid accidental `CAPS`.
- Keep WM access mnemonic and stable.
- Reduce fallbacks to awkward Windows shortcuts.

### Confidence
- Windows + GlazeWM model: high
- 3-monitor role model: high
- Exact physical monitor geometry: medium
- App/workflow inference: high
- Editor-specific mode inference: medium-high

---

## Current Architecture Review

### Base
- Good conservative HRM tuning.
- Thumb access pattern is mostly solid.
- Weak spots:
  - low-value keys in premium places
  - duplicated access paths
  - `CAPS` as APP tap was a bad trade

### Sym
- Serviceable, but not elite.
- Good enough for now.
- Some strong positions are spent on low-value system/media keys.

### Nav
- This was underbuilt for actual Windows use.
- It had arrows and word deletion, but not enough editor/browser support.
- This deserved more density.

### Mod
- Fine as-is.
- Low-frequency layer with low ergonomic cost.

### WM
- Structurally very good.
- Monitor focus, workspace focus, move/follow, and resize are well separated.
- The main flaw was physical placement, not architecture.

### Numpad
- Acceptable and low-priority.
- No urgent redesign needed.

### App
- Good concept.
- Strong ROI because it targets real daily apps.
- The problem was access, not the layer itself.

---

## Friction Map

### Ranked by likely daily impact
1. WM directions on `J/K/L/;` instead of `H/J/K/L`
2. APP key tapping `CAPS`
3. Sparse NAV layer
4. Potential `Alt` HRM interaction with PowerToys Run on `Alt+Space`
5. Dead or low-value premium keys
6. Too much low-value duplication in some access paths
7. Sym layer mixed mental model
8. FancyZones + GlazeWM conceptual overlap

---

## High-Leverage Recommendations

| Rank | Recommendation | Why it matters | Impact | Complexity | Retraining |
|---|---|---|---|---|---|
| 1 | Tap `ESC`, hold APP | Removes accidental `CAPS` with near-zero downside | High | Low | Low |
| 2 | Move WM directions to `H/J/K/L` | Better mnemonic cluster, less pinky abuse | High | Low | Low |
| 3 | Expand NAV for edit/tab/search ops | Matches real Windows/editor/browser frequency | High | Low | Medium |
| 4 | Keep the F13-F22 WM design | Already the correct Windows strategy | High | Low | None |
| 5 | Only move PowerToys Run if `Alt+Space` misfires appear | Real collision risk is possible, but not proven yet | Medium | Low | Low |
| 6 | Reclaim low-value keys only after usage observation | Likely worthwhile, but lower confidence | Medium | Low | Medium |

---

## Concrete Changes Made In The Workup Copy

### Files
- `config/workups/2026-03-22_115904_review/adv360.keymap`
- `config/workups/2026-03-22_115904_review/glazewm-config.local.yaml`
- `config/workups/2026-03-22_115904_review/glazewm-config.repo.yaml`

### Implemented now
- APP access key changed from tap `CAPS` to tap `ESC`
- NAV layer gained:
  - `Find`
  - `Cut`
  - `Copy`
  - `Paste`
  - `Select All`
  - previous tab
  - next tab
- WM direction cluster was normalized so `H/J/K/L` becomes left/down/up/right and `;` becomes the spare slot

### Patch summary
```diff
- &lt 6 CAPS
+ &lt 6 ESC

- sparse NAV row
+ K_FIND / LC(X) / LC(C) / LC(V) / LC(A) / prev-tab / next-tab / home / pgdn / pgup / end

- WM direction payload included a wasted premium slot before the cluster
+ WM bare row shifted so H/J/K/L become the active direction cluster
```

---

## Firmware vs GlazeWM Responsibilities

### Keep in GlazeWM
- directional window focus
- moving windows
- resizing windows
- workspace focus
- workspace send/follow
- monitor focus
- tiling utilities

### Keep in firmware
- physical access to WM namespace
- layer access
- Hyper app launches
- edit/navigation shortcuts
- symbol access

### Avoid duplication
- Do not let FancyZones become a second keyboard WM system.
- Do not move GlazeWM logic into random Windows shortcuts.
- Do not replace direct Hyper launch with fuzzy launch for daily apps.

---

## Migration Plan

### Stage 1
- Ship the 3 high-ROI changes.
- Practice:
  - WM `H/J/K/L`
  - APP tap=`ESC`
  - NAV find/cut/copy/paste/select-all/tab motion
- Watch:
  - accidental `CAPS`
  - wrong WM direction
  - NAV layer confusion

### Stage 2
- Observe which low-value keys are actually unused.
- Candidates:
  - `K_APP`
  - duplicated layer access keys
- Reclaim only one thing at a time.

### Stage 3
- Optional deeper cleanup:
  - symbol layer cleanup
  - parser-friendly ZMK key alias normalization
  - PowerToys Run hotkey change if `Alt+Space` collisions show up

---

## Validation Plan

### Test tasks
- code-edit loop
- browser-docs loop
- terminal-command loop
- monitor refocus + window move
- app-launch burst across the daily set

### Track
- accidental `CAPS`
- wrong WM direction
- wrong workspace target
- launcher pops from `Alt+Space`
- right-pinky fatigue
- thumb strain
- HRM misfires

### Keep or revert rule
- Keep a change if it is clearly better after 3 working days.
- Revert if errors remain high after day 3.

---

## Do Not Change Yet

- Do not redesign the F13-F22 WM architecture.
- Do not remove HRMs without evidence.
- Do not collapse the 20-workspace model.
- Do not replace Hyper launch with fuzzy launch.
- Do not add combos/tap-dances/one-shots just to make it feel more advanced.

---

## Open Questions

- Is `Alt+Space` ever firing accidentally from HRM behavior?
- Is `K_APP` genuinely used often enough to justify its current slot?
- Do you want the symbol layer optimized for a specific language stack?
- Is the top monitor mainly reference/docs or active execution work?

---

## Next Recommended Step

- Treat the workup copy as the candidate branch.
- Use it for a short trial.
- If it feels better after a few working days, port the changes into the live files.
