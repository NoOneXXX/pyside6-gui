from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QListWidget, QMenu, QMessageBox
)
from PySide6.QtGui import QCursor, QIcon, QKeySequence, QAction
from PySide6.QtCore import Qt
import sys
from gui.ui import resource_rc
class ContextMenuDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("右键菜单 - 图标顶头示例")
        self.resize(400, 300)
        layout = QVBoxLayout(self)

        # 示例控件：列表
        self.list_widget = QListWidget()
        self.list_widget.addItems(["文档1.html", "图像2.png", "数据3.csv"])
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.list_widget)

    def show_context_menu(self, position):
        menu = QMenu()

        #  设置更美观的样式
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                padding: 4px;
                font-size: 14px;
                font-family: 'Microsoft YaHei', 'Arial', sans-serif;
            }
            QMenu::item {
                padding: 6px 24px 6px 8px;
                border-radius: 4px;
                color: #333333;
            }
            QMenu::item:selected {
                background-color: #e6f7ff;
                color: #1890ff;
            }
            QMenu::icon {
                padding-left: 0px;
                margin-left: 0px;
            }
            QMenu::separator {
                height: 1px;
                background: #f0f0f0;
                margin: 4px 0px;
            }
        """)

        new_file = QAction(QIcon(":images/scissors.png"), "新建文件", self)
        new_folder = QAction(QIcon(":images/question.png"), "新建文件夹", self)

        rename = QAction(QIcon(":images/question.png"), "重命名", self)
        rename.setShortcut(QKeySequence("F2"))

        delete = QAction(QIcon(":images/question.png"), "删除", self)
        delete.setShortcut(QKeySequence.Delete)

        open_folder = QAction(QIcon(":images/question.png"), "打开所在目录", self)
        refresh = QAction(QIcon(":images/question.png"), "刷新", self)

        sub_menu = QMenu("导出为", self)
        sub_menu.setStyleSheet(menu.styleSheet())  # 子菜单也继承样式
        sub_menu.addAction(QAction(QIcon(":images/question.png"), "PDF", self))
        sub_menu.addAction(QAction(QIcon(":images/question.png"), "Word", self))
        sub_menu.addAction(QAction(QIcon(":images/question.png"), "Markdown", self))

        menu.addAction(new_file)
        menu.addAction(new_folder)
        menu.addSeparator()
        menu.addAction(rename)
        menu.addAction(delete)
        menu.addSeparator()
        menu.addAction(open_folder)
        menu.addAction(refresh)
        menu.addSeparator()
        menu.addMenu(sub_menu)

        if not self.list_widget.currentItem():
            rename.setEnabled(False)
            delete.setEnabled(False)

        action = menu.exec(QCursor.pos())

        if action == new_file:
            QMessageBox.information(self, "提示", "新建文件")
        elif action == rename:
            QMessageBox.information(self, "提示", "重命名")
        elif action == delete:
            QMessageBox.warning(self, "提示", "删除")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo = ContextMenuDemo()
    demo.show()
    sys.exit(app.exec())
