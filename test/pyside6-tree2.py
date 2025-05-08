from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
    QStyleOption, QStyle, QProxyStyle
)
from PySide6.QtGui import QPainter, QPen, QIcon, QBrush, QColor, QFont
from PySide6.QtCore import Qt, QRect, QSize
import sys


def is_last_sibling(item):
    parent = item.parent()
    if parent:
        return parent.indexOfChild(item) == parent.childCount() - 1
    else:
        tree = item.treeWidget()
        return tree.indexOfTopLevelItem(item) == tree.topLevelItemCount() - 1


class XPStyleProxy(QProxyStyle):
    def drawPrimitive(self, element, option, painter, widget=None):
        if element == QStyle.PE_IndicatorBranch:
            rect = option.rect
            painter.save()

            mid_x = rect.center().x() - 2
            mid_y = rect.center().y()
            pen = QPen(QColor(160, 160, 160), 1, Qt.DotLine)
            painter.setPen(pen)

            item = None
            if widget and rect.isValid():
                check_point = rect.center()
                check_point.setX(rect.left() + 8)
                index = widget.indexAt(check_point)
                if index.isValid():
                    item = widget.itemFromIndex(index)

            last = is_last_sibling(item) if item else False

            # ✅ 跳过最左根节点竖线
            is_leftmost_root = False
            if item and not item.parent():
                tree = item.treeWidget()
                if tree and tree.indexOfTopLevelItem(item) == 0:
                    is_leftmost_root = True

            # ✅ 自绘竖线（跳过最左根节点）
            if not is_leftmost_root:
                painter.drawLine(mid_x, rect.top(), mid_x, mid_y)
                if not last:
                    painter.drawLine(mid_x, mid_y, mid_x, rect.bottom())

            # ✅ 横线（非根节点）
            if item and item.parent():
                h_end = rect.left() + 16
                painter.drawLine(mid_x, mid_y, h_end, mid_y)

            # ✅ 展开符号（+/-）
            if item and item.childCount() > 0:
                box_size = 9
                half = box_size // 2
                box_rect = QRect(mid_x - half, mid_y - half, box_size, box_size)

                painter.setPen(QPen(QColor(102, 102, 102), 1))
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                painter.drawRect(box_rect)

                h_len = 5
                painter.drawLine(mid_x - h_len // 2, mid_y, mid_x + h_len // 2, mid_y)
                if not item.isExpanded():
                    painter.drawLine(mid_x, mid_y - h_len // 2, mid_x, mid_y + h_len // 2)

            painter.restore()
        else:
            super().drawPrimitive(element, option, painter, widget)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XP Explorer Style - Final Effective Fix")
        self.resize(500, 600)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)

        # ✅ 关键：关闭 Qt 自带装饰线
        self.tree.setRootIsDecorated(False)

        self.tree.setIndentation(16)
        self.tree.setStyle(XPStyleProxy())
        self.tree.setIconSize(QSize(16, 16))

        self.tree.setStyleSheet("""
            QTreeWidget::item {
                padding: 2px;
                min-height: 18px;
            }
            QTreeWidget::item:selected {
                background-color: #cce8ff;
                border: 1px solid #3399ff;
                padding-left: 2px;
                padding-right: 2px;
            }
        """)

        self.folder_closed = self.style().standardIcon(QStyle.SP_DirClosedIcon)
        self.folder_open = self.style().standardIcon(QStyle.SP_DirOpenIcon)
        self.file_icon = self.style().standardIcon(QStyle.SP_FileIcon)

        self.populate_tree()
        layout.addWidget(self.tree)
        self.tree.expandAll()
        self.tree.itemExpanded.connect(self.on_item_expanded)
        self.tree.itemCollapsed.connect(self.on_item_collapsed)

    def populate_tree(self):
        root = self.create_folder("My Software Notes", bold=True)
        mysql = self.create_folder("mysql", parent=root)
        mysql_senior = self.create_folder("Mysql|高级篇", parent=root)
        self.create_folder("Mysql|高级篇", parent=mysql_senior)
        self.create_folder("Mysql|高级篇", parent=root)
        self.create_folder("Mysql|高级篇", parent=root)

    def create_folder(self, name, parent=None, bold=False):
        item = QTreeWidgetItem(self.tree if parent is None else parent)
        item.setText(0, name)
        item.setIcon(0, self.folder_closed)
        if bold:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
        return item

    def create_file(self, name, parent=None):
        item = QTreeWidgetItem(self.tree if parent is None else parent)
        item.setText(0, name)
        item.setIcon(0, self.file_icon)
        return item

    def on_item_expanded(self, item):
        if item.childCount() > 0:
            item.setIcon(0, self.folder_open)

    def on_item_collapsed(self, item):
        if item.childCount() > 0:
            item.setIcon(0, self.folder_closed)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
