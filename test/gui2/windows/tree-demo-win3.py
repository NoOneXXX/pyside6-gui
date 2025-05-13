
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTreeWidget,
    QTreeWidgetItem, QStyleFactory, QMessageBox, QHeaderView
)
from PySide6.QtGui import QIcon, QPixmap, QFont, QPalette, QColor
from PySide6.QtCore import Qt
import sys
import os

class XPNotebookTree(QWidget):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.custom_path = os.path.expanduser(path)

        # 图标资源
        self.folder_closed_icon = QIcon(QPixmap("folder-orange.png"))
        self.folder_open_icon = QIcon(QPixmap("folder-orange-open.png"))
        self.file_icon = QIcon(QPixmap("note.png"))

        self.tree = None
        self.setup_ui()

    def populate_tree(self, parent_item, path):
        try:
            for name in os.listdir(path):
                full_path = os.path.join(path, name)
                if os.path.isdir(full_path):
                    folder_item = QTreeWidgetItem(parent_item)
                    folder_item.setText(0, name)

                    if name.lower() == "python":
                        icon = QIcon(QPixmap("folder-python.png"))
                    elif name in ("我的垃圾桶", "trash"):
                        icon = QIcon(QPixmap("trash.png"))
                    else:
                        icon = self.folder_closed_icon

                    folder_item.setIcon(0, icon)
                    folder_item.setFont(0, QFont("Microsoft YaHei", 12))

                    # 懒加载标记项
                    folder_item.addChild(QTreeWidgetItem())
                    folder_item.setData(0, Qt.UserRole, full_path)
                else:
                    file_item = QTreeWidgetItem(parent_item)
                    file_item.setText(0, os.path.splitext(name)[0])
                    file_item.setIcon(0, self.file_icon)
        except PermissionError:
            pass

    def setup_ui(self):
        if not os.path.exists(self.custom_path):
            QMessageBox.critical(self, "路径错误", f"目录不存在:\n{self.custom_path}")
            return

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("Notebook")
        header.setStyleSheet("background-color: #F0F0F0; padding: 2px; font-weight: bold;")
        layout.addWidget(header)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setIndentation(16)
        self.tree.setSelectionBehavior(QTreeWidget.SelectRows)
        self.tree.setAllColumnsShowFocus(True)
        self.tree.header().setStretchLastSection(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)

        if sys.platform == "win32":
            style = QStyleFactory.create("windows")
            if style:
                self.tree.setStyle(style)
            palette = self.tree.palette()
            palette.setColor(QPalette.Highlight, QColor("#E6F0FA"))
            palette.setColor(QPalette.HighlightedText, QColor("#000000"))
            self.tree.setPalette(palette)
        else:
            style = QStyleFactory.create("windows")
            if style:
                self.tree.setStyle(style)
            palette = self.tree.palette()
            palette.setColor(QPalette.Highlight, QColor("#E6F0FA"))
            palette.setColor(QPalette.HighlightedText, QColor("#000000"))
            self.tree.setPalette(palette)
            # self.tree.setStyleSheet("""
            #     QTreeWidget {
            #         background-color: #F0F0F0;
            #         alternate-background-color: #FFFFFF;
            #         color: #000000;
            #         font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
            #         font-size: 12pt;
            #     }
            #     QTreeWidget::item {
            #         padding-top: 8px;
            #         padding-bottom: 8px;
            #     }
            #     QTreeWidget::item:selected {
            #         background-color: #E6F0FA;
            #         color: #000000;
            #     }
            #     QTreeWidget::item:hover {
            #         background-color: #EDF6FF;
            #     }
            # """)

        self.tree.itemExpanded.connect(self.handle_item_expanded)
        self.tree.itemCollapsed.connect(self.handle_item_collapsed)

        root = QTreeWidgetItem(self.tree)
        root.setText(0, "notebook")
        root.setIcon(0, self.folder_closed_icon)
        font = QFont("Segoe UI", 12)
        font.setBold(True)
        root.setFont(0, font)
        root.setData(0, Qt.UserRole, self.custom_path)
        root.addChild(QTreeWidgetItem())  # 懒加载标记

        self.tree.setAnimated(True)
        self.tree.setExpandsOnDoubleClick(False)
        layout.addWidget(self.tree)

    def handle_item_expanded(self, item):
        item.setIcon(0, self.folder_open_icon)
        if item.childCount() == 1 and item.child(0).text(0) == "":
            item.takeChild(0)
            path = item.data(0, Qt.UserRole)
            if path:
                self.populate_tree(item, path)

    def handle_item_collapsed(self, item):
        item.setIcon(0, self.folder_closed_icon)

def main():
    app = QApplication(sys.argv)
    # widget = XPNotebookTree("C:/Users/Dell/Desktop/temp/log")  # 替换为你自己的路径
    #mac /Users/echo/Desktop/temp
    widget = XPNotebookTree("/Users/echo/Desktop/temp")  # 替换为你自己的路径
    widget.resize(300, 500)
    widget.setWindowTitle(f"目录树：{widget.custom_path}")
    widget.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
