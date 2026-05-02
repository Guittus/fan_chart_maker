import sys
import math
from PyQt6.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView, 
                             QGraphicsItem, QVBoxLayout, QHBoxLayout, QWidget, 
                             QPushButton, QFileDialog, QSpinBox, QLabel, 
                             QColorDialog, QInputDialog, QComboBox, QMenu)
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QFont, QPainterPath, QPageSize
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtPrintSupport import QPrinter # Correction Import
from gedcom.parser import Parser

class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def wheelEvent(self, event):
        factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.scale(factor, factor)

class FanCell(QGraphicsItem):
    def __init__(self, node_data, start_a, end_a, app_ref):
        super().__init__()
        self.node_data = node_data
        self.start_a = start_a
        self.end_a = end_a
        self.app_ref = app_ref
        self.r_in, self.r_out = node_data['gen'] * 90, (node_data['gen'] + 1) * 90
        self.path = self._calculate_path()
        
        # Style persistant
        self.color = node_data.get('color', QColor(245, 245, 245) if node_data['gen'] % 2 == 0 else QColor(225, 235, 245))
        self.font_size = node_data.get('font_size', max(4, 9 - node_data['gen']))

    def _calculate_path(self):
        path = QPainterPath()
        span = math.degrees(self.end_a - self.start_a)
        start = -math.degrees(self.start_a)
        path.arcMoveTo(QRectF(-self.r_out, -self.r_out, self.r_out*2, self.r_out*2), start)
        path.arcTo(QRectF(-self.r_out, -self.r_out, self.r_out*2, self.r_out*2), start, -span)
        path.arcTo(QRectF(-self.r_in, -self.r_in, self.r_in*2, self.r_in*2), start - span, span)
        path.closeSubpath()
        return path

    def boundingRect(self): return self.path.boundingRect()
    def shape(self): return self.path

    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(QColor(80, 80, 80), 0.5))
        painter.drawPath(self.path)
        if math.degrees(self.end_a - self.start_a) > 1.2:
            mid_a = (self.start_a + self.end_a) / 2
            painter.save()
            painter.rotate(math.degrees(mid_a))
            painter.translate((self.r_in + self.r_out)/2, 0)
            if 90 < (math.degrees(mid_a) % 360) < 270: painter.rotate(180)
            painter.setFont(QFont("Segoe UI", int(self.font_size)))
            painter.setPen(Qt.GlobalColor.black)
            painter.drawText(QRectF(-45, -45, 90, 90), Qt.AlignmentFlag.AlignCenter, self.node_data['name'])
            painter.restore()

    def contextMenuEvent(self, event):
        menu = QMenu()
        ex_f = menu.addAction("♂️ Élargir Paternelle"); ex_m = menu.addAction("♀️ Élargir Maternelle")
        reset = menu.addAction("🔄 Ratio 50/50"); menu.addSeparator()
        edit = menu.addAction("🎨 Personnaliser")
        action = menu.exec(event.screenPos())
        if action == ex_f: self.node_data['ratio'] = min(0.9, self.node_data['ratio'] + 0.05)
        elif action == ex_m: self.node_data['ratio'] = max(0.1, self.node_data['ratio'] - 0.05)
        elif action == reset: self.node_data['ratio'] = 0.5
        elif action == edit: self.mouseDoubleClickEvent(None); return
        self.app_ref.draw_tree()

    def mouseDoubleClickEvent(self, event):
        text, ok = QInputDialog.getText(None, "Editer", "Nom :", text=self.node_data['name'])
        if ok: self.node_data['name'] = text
        color = QColorDialog.getColor(self.color)
        if color.isValid(): self.color = color; self.node_data['color'] = color
        size, ok = QInputDialog.getInt(None, "Police", "Taille :", self.font_size, 1, 60)
        if ok: self.font_size = size; self.node_data['font_size'] = size
        self.update()

class FanChartApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GénéaFan Pro - v7")
        self.setGeometry(100, 100, 1300, 900)
        self.gedcom = None
        self.tree_cache = {}

        self.scene = QGraphicsScene()
        self.view = ZoomableGraphicsView(self.scene)

        controls = QVBoxLayout()
        self.btn_load = QPushButton("📂 Charger GEDCOM")
        self.btn_load.clicked.connect(self.load_gedcom)

        self.combo_angle = QComboBox()
        self.combo_angle.addItems(["360°", "345°", "270°", "180°"])
        self.combo_angle.currentIndexChanged.connect(self.draw_tree)

        self.gen_spin = QSpinBox()
        self.gen_spin.setRange(1, 15); self.gen_spin.setValue(5)
        self.gen_spin.valueChanged.connect(self.draw_tree)

        self.btn_reset = QPushButton("🔄 Réinitialiser l'Arbre")
        self.btn_reset.clicked.connect(self.reset_tree)
        self.btn_reset.setStyleSheet("color: #d32f2f;")

        self.btn_export = QPushButton("💾 Export PDF A2")
        self.btn_export.clicked.connect(self.export_pdf)
        self.btn_export.setFixedHeight(40)

        controls.addWidget(self.btn_load)
        controls.addWidget(QLabel("Amplitude :")); controls.addWidget(self.combo_angle)
        controls.addWidget(QLabel("Générations :")); controls.addWidget(self.gen_spin)
        controls.addSpacing(10); controls.addWidget(self.btn_reset)
        controls.addSpacing(20); controls.addWidget(self.btn_export)
        controls.addStretch()

        layout = QHBoxLayout(); layout.addLayout(controls, 1); layout.addWidget(self.view, 5)
        container = QWidget(); container.setLayout(layout); self.setCentralWidget(container)

    def load_gedcom(self):
        path, _ = QFileDialog.getOpenFileName(self, "GEDCOM", "", "*.ged")
        if path:
            self.gedcom = Parser(); self.gedcom.parse_file(path)
            self.reset_tree()

    def reset_tree(self):
        self.tree_cache = {}
        self.scene.setProperty("init", False)
        self.draw_tree()

    def get_node_data(self, indiv, gen):
        ptr = indiv.get_pointer()
        if ptr not in self.tree_cache:
            name = f"{indiv.get_name()[0]} {indiv.get_name()[1]}".replace("/", "").strip()
            self.tree_cache[ptr] = {'name': name, 'gen': gen, 'ratio': 0.5}
        return self.tree_cache[ptr]

    def draw_tree(self):
        if not self.gedcom: return
        self.scene.clear()
        angle_val = [360, 345, 270, 180][self.combo_angle.currentIndex()]
        total_rad = math.radians(angle_val)
        start_offset = math.radians(270) - (total_rad / 2)
        
        all_indivs = self.gedcom.get_root_child_elements()
        root_indiv = next((i for i in all_indivs if i.get_tag() == "INDI"), None)
        if root_indiv:
            self.build_recursive(root_indiv, 0, self.gen_spin.value(), start_offset, start_offset + total_rad)
            self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-100, -100, 100, 100))
            if not self.scene.property("init"):
                self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
                self.scene.setProperty("init", True)

    def build_recursive(self, indiv, gen, max_g, s_a, e_a):
        if gen >= max_g: return
        node_data = self.get_node_data(indiv, gen)
        cell = FanCell(node_data, s_a, e_a, self)
        self.scene.addItem(cell)
        fam_c = self.gedcom.get_families(indiv, 'FAMC')
        if fam_c:
            husb, wife = self.gedcom.get_family_members(fam_c[0], 'HUSB'), self.gedcom.get_family_members(fam_c[0], 'WIFE')
            pivot = s_a + ((e_a - s_a) * node_data['ratio'])
            if husb: self.build_recursive(husb[0], gen+1, max_g, pivot, e_a)
            if wife: self.build_recursive(wife[0], gen+1, max_g, s_a, pivot)

    def export_pdf(self):
        if not self.scene.items(): return
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "Arbre.pdf", "*.pdf")
        if path:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A2)) # Fix PyQt6
            printer.setPageOrientation(QPrinter.PageOrientation.Landscape)
            printer.setOutputFileName(path)
            painter = QPainter(printer)
            self.scene.render(painter, QRectF(printer.pageRect(QPrinter.Unit.DevicePixel)), self.scene.sceneRect())
            painter.end()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FanChartApp(); window.show()
    sys.exit(app.exec())