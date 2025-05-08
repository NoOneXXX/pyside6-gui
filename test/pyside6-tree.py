from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QStyleOption, QStyle, QProxyStyle
)
from PySide6.QtGui import QPainter, QPen, QIcon, QBrush, QColor, QFont
from PySide6.QtCore import Qt, QRect
import sys

class FinalPerfectStyle(QProxyStyle):
    def drawPrimitive(self, element, option, painter, widget=None):
        if element == QStyle.PE_IndicatorBranch:
            rect = option.rect
            is_open = option.state & QStyle.State_Open
            has_children = option.state & QStyle.State_Children
            is_sibling = option.state & QStyle.State_Sibling

            painter.save()

            mid_x = rect.left() + 10
            mid_y = rect.center().y()

            # 虚线画主干
            pen = QPen(Qt.blue, 1, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawLine(mid_x, rect.top(), mid_x, mid_y)

            if is_sibling:
                painter.drawLine(mid_x, mid_y, mid_x, rect.bottom())

            # 横向短连线
            painter.drawLine(mid_x, mid_y, mid_x + 10, mid_y)

            # 自己手动画 + 或 - 符号
            if has_children:
                pen = QPen(Qt.red, 2, Qt.DotLine)
                painter.setPen(pen)

                # 横线 -
                painter.drawLine(mid_x - 4, mid_y, mid_x + 4, mid_y)
                if not is_open:
                    # 竖线 |
                    painter.drawLine(mid_x, mid_y - 4, mid_x, mid_y + 4)

            painter.restore()
        else:
            super().drawPrimitive(element, option, painter, widget)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tree Structure with Files")
        self.resize(500, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(True)

        # 关键：缩进
        self.tree.setIndentation(22)

        # 设置最终完美风格
        self.tree.setStyle(FinalPerfectStyle())

        # 设置选中项高亮背景
        self.tree.setStyleSheet("""
            QTreeWidget::item:selected {
                background-color: lightblue;
            }
        """)

        # 图标准备（系统默认的文件夹和文件图标）
        self.folder_closed = self.style().standardIcon(QStyle.SP_DirClosedIcon)
        self.folder_open = self.style().standardIcon(QStyle.SP_DirOpenIcon)
        self.file_icon = self.style().standardIcon(QStyle.SP_FileIcon)

        self.populate_tree()
        layout.addWidget(self.tree)

        self.tree.expandAll()

        # 动态绑定展开/收起事件，切换图标
        self.tree.itemExpanded.connect(self.on_item_expanded)
        self.tree.itemCollapsed.connect(self.on_item_collapsed)

    def populate_tree(self):
        root = self.create_folder("My Software Notes", bold=True)

        # mysql 目录
        mysql = self.create_folder("mysql", parent=root)
        mysql_senior = self.create_folder("Mysql高级篇", parent=root)
        # mysql_senior1 = self.create_folder("Mysql高级篇", parent=mysql_senior)
        # mysql_senior2 = self.create_folder("Mysql高级篇", parent=root)
        # mysql_senior3 = self.create_folder("Mysql高级篇", parent=root)




    def create_folder(self, name, parent=None, bold=False):
        if parent is None:
            item = QTreeWidgetItem(self.tree)
        else:
            item = QTreeWidgetItem(parent)

        item.setText(0, name)
        item.setIcon(0, self.folder_closed)

        if bold:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)

        return item

    def create_file(self, name, parent=None):
        if parent is None:
            item = QTreeWidgetItem(self.tree)
        else:
            item = QTreeWidgetItem(parent)

        item.setText(0, name)
        item.setIcon(0, self.file_icon)
        return item

    def on_item_expanded(self, item):
        if item.childCount() > 0:  # 仅文件夹切换图标
            item.setIcon(0, self.folder_open)

    def on_item_collapsed(self, item):
        if item.childCount() > 0:  # 仅文件夹切换图标
            item.setIcon(0, self.folder_closed)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())