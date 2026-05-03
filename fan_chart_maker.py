import sys
import math
from PyQt6.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
                             QGraphicsItem, QVBoxLayout, QHBoxLayout, QWidget,
                             QPushButton, QFileDialog, QSpinBox, QLabel,
                             QColorDialog, QInputDialog, QComboBox, QMenu, QStatusBar,
                             QDialog, QLineEdit, QListWidget, QListWidgetItem, QDialogButtonBox)
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QFont, QPainterPath, QPageSize, QPageLayout
from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtPrintSupport import QPrinter
from gedcom.parser import Parser

_MIN_ZOOM = 0.05
_MAX_ZOOM = 20.0


def _first_given_name(given: str) -> str:
    """
    "Jean Luc Marc" → "Jean"
    "Jean-Luc Marc" → "Jean-Luc"
    "Jean-Luc"      → "Jean-Luc"
    """
    tokens = given.strip().split()
    return tokens[0] if tokens else ""


class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def wheelEvent(self, event):
        current_scale = self.transform().m11()
        factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        if _MIN_ZOOM <= current_scale * factor <= _MAX_ZOOM:
            self.scale(factor, factor)


class FanCell(QGraphicsItem):
    def __init__(self, node_data, start_a, end_a, app_ref):
        super().__init__()
        self.node_data = node_data
        self.start_a = start_a
        self.end_a = end_a
        self.app_ref = app_ref
        self.r_in = node_data['gen'] * 90
        self.r_out = (node_data['gen'] + 1) * 90
        self.path = self._calculate_path()
        self.color = node_data.get('color', QColor(245, 245, 245) if node_data['gen'] % 2 == 0 else QColor(225, 235, 245))
        self.font_size = node_data.get('font_size', max(4, 9 - node_data['gen']))
        self.highlighted = False
        # Populated by build_recursive after children are created
        self.parent_cells: dict[str, 'FanCell | None'] = {}

    def _calculate_path(self):
        path = QPainterPath()
        span = math.degrees(self.end_a - self.start_a)
        start = -math.degrees(self.start_a)
        path.arcMoveTo(QRectF(-self.r_out, -self.r_out, self.r_out * 2, self.r_out * 2), start)
        path.arcTo(QRectF(-self.r_out, -self.r_out, self.r_out * 2, self.r_out * 2), start, -span)
        path.arcTo(QRectF(-self.r_in, -self.r_in, self.r_in * 2, self.r_in * 2), start - span, span)
        path.closeSubpath()
        return path

    def boundingRect(self): return self.path.boundingRect()
    def shape(self): return self.path

    def set_highlight(self, active: bool):
        if self.highlighted != active:
            self.highlighted = active
            self.update()

    def paint(self, painter, option, widget):
        fill = self.color.lighter(150) if self.highlighted else self.color
        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(QColor(80, 80, 80), 0.5))
        painter.drawPath(self.path)
        if math.degrees(self.end_a - self.start_a) > 1.2:
            mid_a = (self.start_a + self.end_a) / 2
            painter.save()
            painter.rotate(math.degrees(mid_a))
            painter.translate((self.r_in + self.r_out) / 2, 0)
            if 90 < (math.degrees(mid_a) % 360) < 270:
                painter.rotate(180)
            painter.setFont(QFont("Segoe UI", int(self.font_size)))
            painter.setPen(Qt.GlobalColor.black)
            painter.drawText(QRectF(-45, -45, 90, 90), Qt.AlignmentFlag.AlignCenter, self.node_data['name'])
            painter.restore()

    def contextMenuEvent(self, event):
        menu = QMenu()
        ex_f = menu.addAction("♂️ Élargir Paternelle")
        ex_m = menu.addAction("♀️ Élargir Maternelle")
        reset = menu.addAction("🔄 Ratio 50/50")
        menu.addSeparator()
        edit = menu.addAction("🎨 Personnaliser")

        def on_hover(action):
            self.app_ref.clear_highlights()
            if action == ex_f:
                target = self.parent_cells.get('father')
            elif action == ex_m:
                target = self.parent_cells.get('mother')
            else:
                target = None
            if target:
                self.app_ref.set_highlight(target)

        menu.hovered.connect(on_hover)
        menu.aboutToHide.connect(self.app_ref.clear_highlights)

        action = menu.exec(event.screenPos())
        if action == ex_f:
            self.node_data['ratio'] = max(0.1, self.node_data['ratio'] - 0.05)  # pivot ← → père (droite) grandit
        elif action == ex_m:
            self.node_data['ratio'] = min(0.9, self.node_data['ratio'] + 0.05)  # pivot → → mère (gauche) grandit
        elif action == reset:
            self.node_data['ratio'] = 0.5
        elif action == edit:
            self._show_edit_dialog()
            return
        self.app_ref.draw_tree()

    def mouseDoubleClickEvent(self, event):
        self._show_edit_dialog()

    def _show_edit_dialog(self):
        text, ok = QInputDialog.getText(None, "Éditer le nom", "Nom :", text=self.node_data['name'])
        if ok:
            self.node_data['name'] = text
        color = QColorDialog.getColor(self.color, title="Couleur de fond")
        if color.isValid():
            self.color = color
            self.node_data['color'] = color
        size, ok = QInputDialog.getInt(None, "Taille de police", "Taille :", self.font_size, 1, 60)
        if ok:
            self.font_size = size
            self.node_data['font_size'] = size
        # Redessine la scène entière — self.update() planterait si la scène
        # a été reconstruite pendant l'ouverture des dialogs modaux
        self.app_ref.draw_tree()


class RootSearchDialog(QDialog):
    """Dialogue de recherche d'un individu racine par prénom et nom."""

    def __init__(self, individuals, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choisir la personne racine (Sosa 1)")
        self.setMinimumWidth(560)
        self.setMinimumHeight(420)
        self.resize(560, 480)

        self._entries = []
        for indiv in individuals:
            first, last = indiv.get_name()
            first_name = _first_given_name(first)
            last_name = last.replace("/", "").strip()
            display = f"{first_name} {last_name}".strip() or "(sans nom)"
            self._entries.append({
                'first': first_name.lower(),
                'last': last_name.lower(),
                'ptr': indiv.get_pointer(),
                'label': f"{display}  [{indiv.get_pointer()}]",
            })

        self._selected_ptr = None

        layout = QVBoxLayout(self)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Prénom :"))
        self.edit_first = QLineEdit()
        self.edit_first.setPlaceholderText("ex. Jean")
        self.edit_first.setClearButtonEnabled(True)
        search_row.addWidget(self.edit_first)
        search_row.addWidget(QLabel("Nom :"))
        self.edit_last = QLineEdit()
        self.edit_last.setPlaceholderText("ex. Dupont")
        self.edit_last.setClearButtonEnabled(True)
        search_row.addWidget(self.edit_last)
        layout.addLayout(search_row)

        self.result_label = QLabel()
        layout.addWidget(self.result_label)

        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        layout.addWidget(self.list_widget)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self.edit_first.textChanged.connect(self._filter)
        self.edit_last.textChanged.connect(self._filter)
        self.list_widget.itemDoubleClicked.connect(self._on_accept)

        self._filter()
        self.edit_first.setFocus()

    def _filter(self):
        first_q = self.edit_first.text().strip().lower()
        last_q = self.edit_last.text().strip().lower()
        self.list_widget.clear()
        for entry in self._entries:
            if first_q and first_q not in entry['first']:
                continue
            if last_q and last_q not in entry['last']:
                continue
            item = QListWidgetItem(entry['label'])
            item.setData(Qt.ItemDataRole.UserRole, entry['ptr'])
            self.list_widget.addItem(item)
        count = self.list_widget.count()
        self.result_label.setText(f"{count} résultat(s)")
        if count > 0:
            self.list_widget.setCurrentRow(0)

    def _on_accept(self):
        current = self.list_widget.currentItem()
        if current:
            self._selected_ptr = current.data(Qt.ItemDataRole.UserRole)
            self.accept()

    def selected_ptr(self):
        return self._selected_ptr


class FanChartApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GénéaFan Pro - v7")
        self.setGeometry(100, 100, 1300, 900)
        self.gedcom = None
        self.tree_cache = {}
        self.tree_initialized = False
        self.root_ptr = None
        self._highlighted_cell: 'FanCell | None' = None

        self.scene = QGraphicsScene()
        self.view = ZoomableGraphicsView(self.scene)

        # Debounce : évite les redessins en rafale lors du scroll du spinbox
        self._redraw_timer = QTimer()
        self._redraw_timer.setSingleShot(True)
        self._redraw_timer.setInterval(150)
        self._redraw_timer.timeout.connect(self._do_draw_tree)

        controls = QVBoxLayout()
        self.btn_load = QPushButton("📂 Charger GEDCOM")
        self.btn_load.clicked.connect(self.load_gedcom)

        self.combo_angle = QComboBox()
        self.combo_angle.addItems(["360°", "345°", "270°", "180°"])
        self.combo_angle.currentIndexChanged.connect(self.draw_tree)

        self.gen_spin = QSpinBox()
        self.gen_spin.setRange(1, 15)
        self.gen_spin.setValue(5)
        self.gen_spin.valueChanged.connect(self.draw_tree)

        self.btn_change_root = QPushButton("🔍 Changer la racine")
        self.btn_change_root.clicked.connect(self.change_root)
        self.btn_change_root.setEnabled(False)

        self.btn_reset = QPushButton("🔄 Réinitialiser l'Arbre")
        self.btn_reset.clicked.connect(self.reset_tree)
        self.btn_reset.setStyleSheet("color: #d32f2f;")

        self.btn_export = QPushButton("💾 Export PDF A2")
        self.btn_export.clicked.connect(self.export_pdf)
        self.btn_export.setFixedHeight(40)

        controls.addWidget(self.btn_load)
        controls.addWidget(self.btn_change_root)
        controls.addWidget(QLabel("Amplitude :"))
        controls.addWidget(self.combo_angle)
        controls.addWidget(QLabel("Générations :"))
        controls.addWidget(self.gen_spin)
        controls.addSpacing(10)
        controls.addWidget(self.btn_reset)
        controls.addSpacing(20)
        controls.addWidget(self.btn_export)
        controls.addStretch()

        layout = QHBoxLayout()
        layout.addLayout(controls, 1)
        layout.addWidget(self.view, 5)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Prêt — chargez un fichier GEDCOM pour commencer.")

    # --- Highlight helpers ---

    def set_highlight(self, cell: 'FanCell'):
        self.clear_highlights()
        self._highlighted_cell = cell
        try:
            cell.set_highlight(True)
        except RuntimeError:
            self._highlighted_cell = None

    def clear_highlights(self):
        if self._highlighted_cell is not None:
            try:
                self._highlighted_cell.set_highlight(False)
            except RuntimeError:
                pass
            self._highlighted_cell = None

    # --- GEDCOM loading ---

    def load_gedcom(self):
        path, _ = QFileDialog.getOpenFileName(self, "GEDCOM", "", "*.ged")
        if not path:
            return
        self.status_bar.showMessage("Chargement en cours…")
        QApplication.processEvents()
        self.gedcom = Parser()
        self.gedcom.parse_file(path)

        individuals = [i for i in self.gedcom.get_root_child_elements() if i.get_tag() == "INDI"]
        self.root_ptr = self._ask_root_individual(individuals)
        self.btn_change_root.setEnabled(True)
        self.reset_tree()
        self.status_bar.showMessage(f"Fichier chargé — {len(individuals)} individu(s) trouvé(s).")

    def _ask_root_individual(self, individuals):
        if not individuals:
            return None
        dlg = RootSearchDialog(individuals, self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_ptr():
            return dlg.selected_ptr()
        return individuals[0].get_pointer()

    def change_root(self):
        if not self.gedcom:
            return
        individuals = [i for i in self.gedcom.get_root_child_elements() if i.get_tag() == "INDI"]
        new_ptr = self._ask_root_individual(individuals)
        if new_ptr and new_ptr != self.root_ptr:
            self.root_ptr = new_ptr
            self.reset_tree()

    # --- Tree management ---

    def reset_tree(self):
        self.tree_cache = {}
        self.tree_initialized = False
        self.draw_tree()

    def get_node_data(self, indiv, gen):
        ptr = indiv.get_pointer()
        if ptr not in self.tree_cache:
            first, last = indiv.get_name()
            first_name = _first_given_name(first)
            last_name = last.replace("/", "").strip()
            name = f"{first_name} {last_name}".strip()
            self.tree_cache[ptr] = {'name': name, 'gen': gen, 'ratio': 0.5, 'ptr': ptr}
        node_data = self.tree_cache[ptr]
        node_data['gen'] = gen
        return node_data

    def draw_tree(self):
        self._redraw_timer.start()

    def _do_draw_tree(self):
        if not self.gedcom:
            return
        self._highlighted_cell = None
        self.scene.clear()
        angle_val = [360, 345, 270, 180][self.combo_angle.currentIndex()]
        total_rad = math.radians(angle_val)
        start_offset = math.radians(270) - (total_rad / 2)

        all_indivs = self.gedcom.get_root_child_elements()
        if self.root_ptr:
            root_indiv = next((i for i in all_indivs if i.get_tag() == "INDI" and i.get_pointer() == self.root_ptr), None)
        else:
            root_indiv = next((i for i in all_indivs if i.get_tag() == "INDI"), None)

        if root_indiv:
            self.build_recursive(root_indiv, 0, self.gen_spin.value(), start_offset, start_offset + total_rad, set())
            self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-100, -100, 100, 100))
            if not self.tree_initialized:
                self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
                self.tree_initialized = True

    def build_recursive(self, indiv, gen, max_g, s_a, e_a, visited) -> 'FanCell | None':
        if gen >= max_g:
            return None
        ptr = indiv.get_pointer()
        if ptr in visited:
            return None  # protection contre les cycles dans un GEDCOM incohérent
        node_data = self.get_node_data(indiv, gen)
        cell = FanCell(node_data, s_a, e_a, self)
        self.scene.addItem(cell)
        fam_c = self.gedcom.get_families(indiv, 'FAMC')
        if fam_c:
            husb = self.gedcom.get_family_members(fam_c[0], 'HUSB')
            wife = self.gedcom.get_family_members(fam_c[0], 'WIFE')
            pivot = s_a + ((e_a - s_a) * node_data['ratio'])
            child_visited = visited | {ptr}
            # Convention : père (husb) → droite (angles élevés), mère (wife) → gauche (angles bas)
            father_cell = self.build_recursive(husb[0], gen + 1, max_g, pivot, e_a, child_visited) if husb else None
            mother_cell = self.build_recursive(wife[0], gen + 1, max_g, s_a, pivot, child_visited) if wife else None
            cell.parent_cells = {'father': father_cell, 'mother': mother_cell}
        return cell

    def export_pdf(self):
        if not self.scene.items():
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "Arbre.pdf", "*.pdf")
        if not path:
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A2))
        printer.setPageOrientation(QPageLayout.Orientation.Landscape)
        printer.setOutputFileName(path)
        painter = QPainter(printer)
        self.scene.render(painter, QRectF(printer.pageRect(QPrinter.Unit.DevicePixel)), self.scene.sceneRect())
        painter.end()
        self.status_bar.showMessage(f"PDF exporté : {path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FanChartApp()
    window.show()
    sys.exit(app.exec())
