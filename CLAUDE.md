# GénéaFan Pro — CLAUDE.md

Single-file PyQt6 desktop app: GEDCOM → fan chart interactif → export PDF A2.

```bash
pip install PyQt6 python-gedcom
python fan_chart_maker.py
python -m py_compile fan_chart_maker.py  # vérif syntaxe
```

## 4 classes dans fan_chart_maker.py (~440 lignes)

| Classe | Rôle |
|---|---|
| `ZoomableGraphicsView` | Zoom molette + drag-scroll |
| `FanCell(QGraphicsItem)` | Un arc : dessin, menu clic-droit, double-clic édition |
| `RootSearchDialog(QDialog)` | Recherche fuzzy prénom+nom pour choisir Sosa 1 |
| `FanChartApp(QMainWindow)` | Orchestrateur : parsing GEDCOM, construction arbre, panneau contrôles |

## Invariants à ne pas casser

- **Père = droite = angles élevés**, mère = gauche = angles bas.
- `draw_tree()` toujours débounce 150 ms — ne jamais appeler `_do_draw_tree()` directement.
- `tree_cache` (dict `ptr → node_data`) persiste `ratio/color/font_size` entre redraws. Seul `reset_tree()` l'efface.
- `FanCell.paint()` skip le label si arc < 1,2°.
- `_first_given_name()` garde les noms composés ("Jean-Luc" reste entier).

## node_data schema
```python
{'ptr': str, 'name': str, 'gen': int, 'ratio': float,  # 0.1–0.9
 'color': QColor,  # optionnel
 'font_size': int}  # optionnel
```

## Export PDF
`QPdfWriter` à 150 DPI + `scene.render(painter, QRectF(), scene.sceneRect())`. Ne pas revenir à `QPrinter` (décalage px logiques/device causait des polices écrasées).

## Idées / backlog
- Afficher année de naissance dans les arcs (parsing `BIRT/DATE`)
- Colorisation automatique branche paternelle/maternelle
- Panneau info individu (clic → nom complet, naissance, décès)
- Packaging PyInstaller `.exe`
- Export PDF portrait A2
