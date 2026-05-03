# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project in one sentence

**GénéaFan Pro** — single-file PyQt6 desktop app that renders GEDCOM genealogy files as interactive fan charts and exports them as A2 PDF.

## Run & install

```bash
pip install PyQt6 python-gedcom   # one-time
python fan_chart_maker.py          # launch
```

No build step, no tests, no linter configured. Syntax check only:

```bash
python -m py_compile fan_chart_maker.py
```

## Architecture — 4 classes in one file

`fan_chart_maker.py` is self-contained (~430 lines). Read `docs/architecture.md` for full detail.

| Class | Role |
|---|---|
| `ZoomableGraphicsView` | Wheel zoom + drag-scroll wrapper |
| `FanCell(QGraphicsItem)` | One arc cell: draws itself, owns right-click menu & double-click edit |
| `RootSearchDialog(QDialog)` | Fuzzy search dialog (first name + last name) to pick Sosa 1 |
| `FanChartApp(QMainWindow)` | Orchestrator: GEDCOM parsing, tree build, controls panel |

### Critical data flow

```
load_gedcom() → RootSearchDialog → root_ptr
draw_tree() → [150ms debounce] → _do_draw_tree() → build_recursive()
build_recursive() → FanCell (added to QGraphicsScene), wires cell.parent_cells
```

### Key shared state

- `tree_cache` dict `{ptr → node_data}` — persists `ratio`, `color`, `font_size` across redraws. Never cleared except by `reset_tree()`.
- `node_data['ratio']` (0.1–0.9) — angular split point between father (right/high angles) and mother (left/low angles).
- `root_ptr` — GEDCOM pointer string of the Sosa 1 individual.

## Conventions

- **Father = right = higher angles**, mother = left = lower angles. This is an invariant throughout the code.
- `_first_given_name()` keeps hyphenated names whole ("Jean-Luc" stays "Jean-Luc") but drops extra given names.
- `draw_tree()` is always debounced (150 ms). Never call `_do_draw_tree()` directly.
- `reset_tree()` wipes `tree_cache` and re-renders from scratch. Use it after changing `root_ptr`.
- `FanCell.paint()` skips label rendering when arc span < 1.2°.

## Docs index

→ [`docs/INDEX.md`](docs/INDEX.md) — full table of contents  
→ [`docs/architecture.md`](docs/architecture.md) — detailed class & data flow  
→ [`docs/decisions.md`](docs/decisions.md) — why things are built the way they are  
→ [`docs/roadmap.md`](docs/roadmap.md) — current branch work & planned features  

## Starting a new task quickly

1. Read this file (already done).
2. For UI/rendering work → also read `docs/architecture.md`.
3. For "why was X done this way" → `docs/decisions.md`.
4. For what's in progress → `docs/roadmap.md`.
5. Then read only the relevant section of `fan_chart_maker.py` (the file is short enough to read in full if needed).
