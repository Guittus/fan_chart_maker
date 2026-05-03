# Roadmap — GénéaFan Pro

## Current branch: `choose_sosa`

**Status:** In progress  
**Goal:** Replace the root-individual dropdown with a smart search dialog.

- [x] Add `RootSearchDialog` with live dual-field filtering (first name + last name)
- [x] Add "🔍 Changer la racine" button in the controls panel (enabled after GEDCOM load)
- [x] `change_root()` method: opens dialog, calls `reset_tree()` if selection changes

## Merged features (on `main`)

From branch `analyze` (merged via PR #1):
- Debounce on `draw_tree()` (150 ms QTimer)
- `_first_given_name()` helper preserving hyphenated names
- Cycle protection in `build_recursive()` via `visited` set
- Hover highlight for parent cells in context menu
- Zoom clamp (`_MIN_ZOOM` / `_MAX_ZOOM` constants)

## Planned / ideas

| Feature | Notes |
|---|---|
| Date display in cells | Show birth year below name; needs GEDCOM `BIRT/DATE` parsing |
| Color by branch | Auto-color paternal line blue, maternal line red (with override) |
| Individual info panel | Click → side panel with full name, birth, death, spouse |
| GEDCOM 7.0 support | Upgrade or replace `python-gedcom` |
| Packaging | PyInstaller `.exe` for Windows distribution |
| Portrait mode PDF | A2 portrait option in addition to landscape |
| Search highlight | Highlight a searched individual in the rendered tree |

## Known limitations

- No undo/redo for edits (name, color, font size, ratio).
- Exporting resets the viewport fit (minor UX issue).
- Very large GEDCOM files (> 50k individuals) may slow the search dialog's initial population.
