import sys
import os
from PySide6.QtWidgets import (
    QApplication, QTreeWidget, QTreeWidgetItem, QStyleFactory, QMessageBox,
    QWidget, QVBoxLayout, QLabel, QStyle
)
from PySide6.QtGui import QIcon, QFont
from PySide6.QtCore import Qt

def populate_tree(parent_item, path):
    try:
        for name in os.listdir(path):
            full_path = os.path.join(path, name)
            child_item = QTreeWidgetItem(parent_item)
            child_item.setText(0, name)
            if os.path.isdir(full_path):
                child_item.setIcon(0, folder_icon)
                populate_tree(child_item, full_path)  # 递归加载子目录
            else:
                child_item.setIcon(0, file_icon)
    except PermissionError:
        # 如果没有权限访问某些系统目录
        pass

app = QApplication(sys.argv)

custom_path = os.path.expanduser("C:\\Users\\Dell\\Desktop\\temp\\log")

if not os.path.exists(custom_path):
    QMessageBox.critical(None, "路径错误", f"目录不存在:\n{custom_path}")
    sys.exit(1)

# 设置样式
if sys.platform == "win32":
    style = QStyleFactory.create("windows")
    if style:
        app.setStyle(style)
    else:
        app.setStyleSheet("""
            QTreeWidget {
                background-color: #F0F0F0;
                alternate-background-color: #FFFFFF;
                color: #000000;
                font-family: "Segoe UI", sans-serif;
            }
            QTreeWidget::item { padding: 2px; }
        """)
else:
    app.setStyleSheet("""
        QTreeWidget {
            background-color: #F0F0F0;
            alternate-background-color: #FFFFFF;
            color: #000000;
            font-family: "Segoe UI", sans-serif;
        }
        QTreeWidget::item { padding: 2px; }
    """)

# 容器窗口
container = QWidget()
layout = QVBoxLayout(container)
layout.setContentsMargins(0, 0, 0, 0)
layout.setSpacing(0)

header = QLabel("Notebook")
header.setStyleSheet("background-color: #F0F0F0; padding: 2px; font-weight: bold;")
layout.addWidget(header)

tree = QTreeWidget()
tree.setHeaderHidden(True)
tree.setRootIsDecorated(True)
tree.setIndentation(14)

folder_icon = app.style().standardIcon(QStyle.SP_DirClosedIcon)
file_icon = app.style().standardIcon(QStyle.SP_FileIcon)

# 根节点
root = QTreeWidgetItem(tree)
root.setText(0, "notebook")
root.setIcon(0, folder_icon)
font = QFont("Segoe UI", 9)
font.setBold(True)
root.setFont(0, font)

# 调用递归加载函数
populate_tree(root, custom_path)

tree.setAnimated(True)
tree.setExpandsOnDoubleClick(False)
layout.addWidget(tree)

container.setWindowTitle(f"目录树：{custom_path}")
container.resize(300, 500)
container.show()

sys.exit(app.exec())
