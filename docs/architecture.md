# Architecture — GénéaFan Pro

## File layout

Everything lives in `fan_chart_maker.py`. No packages, no modules.

```
fan_chart_maker.py
├── _first_given_name()          # Pure helper: "Jean Luc" → "Jean"
├── ZoomableGraphicsView         # QGraphicsView subclass
├── FanCell                      # QGraphicsItem subclass (one arc)
├── RootSearchDialog             # QDialog: fuzzy search for Sosa 1
└── FanChartApp                  # QMainWindow (main orchestrator)
```

## Rendering pipeline

```
QGraphicsScene (FanChartApp.scene)
  └── FanCell items (one per visible ancestor)
        └── QPainterPath arc  ← _calculate_path() at construction time
```

`build_recursive()` walks the GEDCOM tree depth-first and adds a `FanCell` to the scene for each individual. The scene is **fully cleared and rebuilt** on every `draw_tree()` call — there is no incremental update.

### Angle coordinate system

- Angles are in **radians**, measured clockwise from the positive X axis (standard Qt).
- The full arc starts at `start_offset = 270° - amplitude/2` (top of circle).
- **Father** always occupies the `[pivot, end_angle]` half → higher angle values → right side of the fan.
- **Mother** always occupies the `[start_angle, pivot]` half → lower angle values → left side.
- `pivot = start_angle + (end_angle - start_angle) * node_data['ratio']`

### FanCell geometry

```
r_in  = gen * 90 px
r_out = (gen + 1) * 90 px
arc   = QPainterPath built from two arcTo calls + closeSubpath
```

Text is drawn at `(r_in + r_out) / 2` along the mid-angle, rotated to follow the arc. Labels on the left half (90°–270°) are flipped 180° to remain readable.

## node_data dict schema

```python
{
    'ptr':       str,        # GEDCOM pointer, e.g. "@I0042@"
    'name':      str,        # display name (editable)
    'gen':       int,        # generation (0 = Sosa 1)
    'ratio':     float,      # 0.1–0.9, father/mother angular split
    'color':     QColor,     # optional, set on edit
    'font_size': int,        # optional, set on edit
}
```

`tree_cache` maps `ptr → node_data`. Entries survive redraws; only `reset_tree()` clears it.

## GEDCOM access patterns

Uses `python-gedcom` library:

```python
self.gedcom.get_root_child_elements()  # all top-level elements
self.gedcom.get_families(indiv, 'FAMC')  # families where indiv is child
self.gedcom.get_family_members(fam, 'HUSB')  # father list
self.gedcom.get_family_members(fam, 'WIFE')  # mother list
indiv.get_name()  # → (given, surname)  surname wrapped in /slashes/ in raw GEDCOM
indiv.get_pointer()  # → "@I0042@"
```

## Highlight system

`FanCell.parent_cells = {'father': FanCell|None, 'mother': FanCell|None}` is populated by `build_recursive()` after child cells are returned. `FanChartApp` keeps a single `_highlighted_cell` ref and toggles `FanCell.set_highlight()`. The highlight is cleared on menu hide and on every full redraw.

## Debounce

`draw_tree()` always goes through a 150 ms `QTimer` (single-shot) to avoid redraw storms from `QSpinBox` scroll. `_do_draw_tree()` is the real entry point.

## Export

PDF export uses `QPrinter` in `PdfFormat` mode with an A2 `QPageSize`, landscape. `QGraphicsScene.render()` maps the full scene rect to the printer page rect.
