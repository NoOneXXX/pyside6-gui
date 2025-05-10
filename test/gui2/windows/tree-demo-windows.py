import sys
import os
from PySide6.QtWidgets import QApplication, QTreeView, QFileSystemModel, QStyleFactory
from PySide6.QtCore import QDir

app = QApplication(sys.argv)

# 检测系统并选择合适的样式
if sys.platform == "win32":
    style = QStyleFactory.create("windows")
    if style:
        app.setStyle(style)
    else:
        print("Windows style not available. Using default style with basic stylesheet.")
        app.setStyleSheet("""
            QTreeView {
                background-color: #F0F0F0;
                alternate-background-color: #FFFFFF;
                color: #000000;
                font-family: "Segoe UI", sans-serif;
            }
            QTreeView::item { padding: 2px; }
            QTreeView::branch:has-siblings:!adjoins-item { border-image: none; }
            QTreeView::branch:has-siblings:adjoins-item { border-image: none; }
            QTreeView::branch:!has-children:!has-siblings:adjoins-item { border-image: none; }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {
                border-image: none; image: url(plus_icon.png);
            }
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {
                border-image: none; image: url(minus_icon.png);
            }
        """)
else:
    app.setStyleSheet("""
        QTreeView {
            background-color: #F0F0F0;
            alternate-background-color: #FFFFFF;
            color: #000000;
            font-family: "Segoe UI", sans-serif;
        }
        QTreeView::item { padding: 2px; }
    """)

# 创建树形视图
tree = QTreeView()
model = QFileSystemModel()
model.setRootPath(QDir.rootPath() if sys.platform != "win32" else "C:/")
tree.setModel(model)
tree.setRootIndex(model.index(QDir.rootPath() if sys.platform != "win32" else "C:/"))
tree.setWindowTitle("Windows Compatible Tree View")
tree.resize(1200, 400)

# 扩展到根目录下的部分节点（可选优化性能）
tree.setAnimated(True)
tree.setExpandsOnDoubleClick(False)

tree.show()
sys.exit(app.exec())