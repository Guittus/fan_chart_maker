# Technical Decisions — GénéaFan Pro

## Single-file architecture

**Decision:** Everything in `fan_chart_maker.py`, no package structure.  
**Why:** The app is a personal tool, not a library. A single file is simpler to distribute ("just run this script") and there's no logic complex enough to warrant splitting.  
**If the project grows:** Extract into `src/fan_chart/` with `__main__.py`, `widgets.py`, `gedcom_utils.py` when the file exceeds ~800 lines or a second entry point is needed.

## Full scene rebuild on every redraw

**Decision:** `scene.clear()` + full `build_recursive()` on every `draw_tree()`.  
**Why:** Simplicity. Incremental updates with a QGraphicsScene are error-prone when the tree depth or root changes. The rebuild is fast enough (< 50 ms even at 15 generations).  
**Trade-off:** Loses hover/selection state on each redraw. Acceptable for the use case.

## `tree_cache` persists ratio/color/font

**Decision:** `node_data` dict is shared between redraws via `tree_cache[ptr]`.  
**Why:** User edits (ratio adjustments, colors, font sizes) must survive a redraw triggered by changing generation count or amplitude. Without the cache, every spinbox tick would reset customizations.  
**Implication:** `reset_tree()` is the only correct way to start fresh — it clears the cache.

## Father = right, mother = left (angle convention)

**Decision:** Father branch always occupies higher arc angles (right side of fan), mother always lower (left side).  
**Why:** Matches French genealogy convention and makes the elastic ratio intuitive (increase ratio → mother's side grows to the left).  
**Do not change** without updating all comments, the context menu labels, and `decisions.md`.

## `ratio` stored on node_data, not on the family

**Decision:** The angular split is a property of the child cell (`node_data['ratio']`), not of the GEDCOM family object.  
**Why:** The same individual can theoretically appear multiple times in a GEDCOM (cousin marriages). Attaching ratio to the cell avoids conflicts.

## python-gedcom library

**Decision:** Using `python-gedcom` (pip package `python-gedcom`).  
**Why:** Simple API, sufficient for read-only parsing of standard GEDCOM 5.5 files.  
**Known limitation:** Does not handle all GEDCOM 7.0 extensions. Not a concern for typical genealogy software exports (Ancestris, Heredis, Geneanet).

## PyQt6 over PySide6 or tkinter

**Decision:** PyQt6.  
**Why:** Better documentation ecosystem, `QGraphicsScene`/`QGraphicsItem` are essential for the fan chart rendering (path-based hit testing, per-item context menus). tkinter cannot do this cleanly.

## RootSearchDialog — dual field search (not a combo box)

**Decision:** Two `QLineEdit` fields (first name + last name) with live filtering over a `QListWidget`, replacing the original `QInputDialog.getItem` combo box.  
**Why:** GEDCOM files can have thousands of individuals. A flat dropdown is unusable at scale. Separate fields allow finding "Jean DUPONT" without knowing whether to search "Jean Dupont" or "DUPONT Jean".  
**Branch:** `choose_sosa`
