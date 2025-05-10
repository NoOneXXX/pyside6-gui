import sys
from PySide6.QtWidgets import QApplication, QTreeView, QFileSystemModel, QStyleFactory

app = QApplication(sys.argv)
style = QStyleFactory.create("windowsxp")
if style:
    app.setStyle(style)
else:
    print("Windows XP style not available. Using default style with basic stylesheet.")
    ## 128px 图片选择大小
    app.setStyleSheet("""
        QTreeView {
            background-color: #F0F0F0;
            alternate-background-color: #FFFFFF;
            color: #000000;
            font-family: "Segoe UI", "Tahoma", sans-serif;
        }
        QTreeView::item { padding: 2px; }
        QTreeView::branch:has-siblings:!adjoins-item { border-image: url(WechatIMG489.jpg) 0; }
        QTreeView::branch:has-siblings:adjoins-item { border-image: url(img_4.png) 0; }
        QTreeView::branch:!has-children:!has-siblings:adjoins-item { border-image: url(img.png) 0; }
        QTreeView::branch:has-children:!has-siblings:closed,
        QTreeView::branch:closed:has-children:has-siblings {
            border-image: none; image: url(plus_icon.png);
        }
        QTreeView::branch:open:has-children:!has-siblings,
        QTreeView::branch:open:has-children:has-siblings {
            border-image: none; image: url(minus_icon.png);
        }
    """)

tree = QTreeView()
model = QFileSystemModel()
model.setRootPath("/")
tree.setModel(model)
tree.setRootIndex(model.index("/"))
tree.setWindowTitle("Windows XP Style Tree View")
tree.resize(1200, 400)
tree.show()
sys.exit(app.exec())