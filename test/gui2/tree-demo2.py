import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QStyleOption, QStyle, QProxyStyle,
    QStyleFactory, QMenuBar, QToolBar
)
from PySide6.QtGui import QAction
from PySide6.QtGui import QPainter, QPen, QIcon, QFont, QBrush, QColor
from PySide6.QtCore import Qt, QRect

app = QApplication(sys.argv)

# 检测系统并选择合适的样式
if sys.platform == "win32":
    style = QStyleFactory.create("windows")
    if style:
        app.setStyle(style)
    else:
        print("Windows style not available. Using fallback stylesheet.")
        app.setStyleSheet("""
            QTreeWidget {
                background-color: #FFFFFF;
                color: #000000;
                font-family: "Segoe UI", sans-serif;
                font-size: 9pt;
            }
            QTreeWidget::item:selected {
                background-color: #ADD8E6;
                color: #000000;
            }
            QTreeWidget::item { padding: 1px; }
        """)
else:
    app.setStyleSheet("""
        QTreeWidget {
            background-color: #FFFFFF;
            color: #000000;
            font-family: "Segoe UI", sans-serif;
            font-size: 9pt;
        }
        QTreeWidget::item:selected {
            background-color: #ADD8E6;
            color: #000000;
        }
        QTreeWidget::item { padding: 1px; }
    """)

# 自定义样式类，用于绘制树形结构的分支指示器
class CustomTreeStyle(QProxyStyle):
    def drawPrimitive(self, element, option, painter, widget=None):
        if element == QStyle.PE_IndicatorBranch:
            rect = option.rect
            is_open = option.state & QStyle.State_Open
            has_children = option.state & QStyle.State_Children
            is_sibling = option.state & QStyle.State_Sibling
            is_selected = option.state & QStyle.State_Selected

            painter.save()

            mid_x = rect.left() + 9  # 调整线的位置以匹配 Windows 风格
            mid_y = rect.center().y()

            # 绘制主干虚线（黑色虚线）
            pen = QPen(Qt.black, 1, Qt.DotLine)
            painter.setPen(pen)
            painter.drawLine(mid_x, rect.top(), mid_x, mid_y)

            # 如果有兄弟节点，绘制从中心到底部的虚线
            if is_sibling:
                painter.drawLine(mid_x, mid_y, mid_x, rect.bottom())

            # 绘制横向实线（连接节点）
            pen = QPen(Qt.black, 1, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawLine(mid_x, mid_y, mid_x + 9, mid_y)

            # 绘制 +/- 符号
            if has_children:
                # 绘制小矩形框
                if is_selected:
                    painter.setPen(QPen(Qt.black, 1))
                    painter.setBrush(QBrush(QColor("#ADD8E6")))  # 选中时的背景色
                else:
                    painter.setPen(QPen(Qt.black, 1))
                    painter.setBrush(QBrush(Qt.white))
                painter.drawRect(mid_x - 4, mid_y - 4, 8, 8)

                # 绘制 +/- 符号的线条
                pen = QPen(Qt.black, 1, Qt.SolidLine)
                painter.setPen(pen)
                painter.drawLine(mid_x - 2, mid_y, mid_x + 2, mid_y)  # 横线
                if not is_open:
                    painter.drawLine(mid_x, mid_y - 2, mid_x, mid_y + 2)  # 竖线（未展开时）

            painter.restore()
        else:
            super().drawPrimitive(element, option, painter, widget)

# 主窗口类
class TreeDemoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Software Notes")
        self.resize(500, 700)

        # 添加菜单栏
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        edit_menu = menubar.addMenu("Edit")
        search_menu = menubar.addMenu("Search")
        view_menu = menubar.addMenu("View")
        go_menu = menubar.addMenu("Go")
        tools_menu = menubar.addMenu("Tools")

        # 添加工具栏
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        back_action = QAction(QIcon("back_icon.png"), "Back", self)
        forward_action = QAction(QIcon("forward_icon.png"), "Forward", self)
        up_action = QAction(QIcon("up_icon.png"), "Up", self)
        toolbar.addAction(back_action)
        toolbar.addAction(forward_action)
        toolbar.addAction(up_action)

        # 设置中心部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 创建树形控件
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setIndentation(14)  # 调整缩进以匹配 Windows 风格

        # 应用自定义样式
        self.tree.setStyle(CustomTreeStyle())

        # 设置文件夹和文件的图标（使用系统默认图标）
        self.folder_closed = self.style().standardIcon(QStyle.SP_DirClosedIcon)
        self.folder_open = self.style().standardIcon(QStyle.SP_DirOpenIcon)
        self.trash_icon = self.style().standardIcon(QStyle.SP_TrashIcon)

        # 填充树形结构
        self.populate_tree()
        layout.addWidget(self.tree)

        # 默认展开根节点
        self.tree.expandToDepth(0)

        # 绑定展开/收起事件以切换图标
        self.tree.itemExpanded.connect(self.on_item_expanded)
        self.tree.itemCollapsed.connect(self.on_item_collapsed)

    def populate_tree(self):
        # 创建根节点
        root = self.create_folder("My Software Notes", bold=True)

        # 创建子目录
        dir1 = self.create_folder("osint", parent=root)
        dir2 = self.create_folder("java interview", parent=root)
        dir3 = self.create_folder("project", parent=root)
        dir4 = self.create_folder("keepnote", parent=root)
        trash = self.create_trash("Trash", parent=root)

    def create_folder(self, name, parent=None, bold=False):
        item = QTreeWidgetItem(parent if parent else self.tree)
        item.setText(0, name)
        item.setIcon(0, self.folder_closed)

        if bold:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)

        return item

    def create_trash(self, name, parent=None):
        item = QTreeWidgetItem(parent if parent else self.tree)
        item.setText(0, name)
        item.setIcon(0, self.trash_icon)
        return item

    def on_item_expanded(self, item):
        if item.childCount() > 0:  # 仅文件夹切换图标
            item.setIcon(0, self.folder_open)

    def on_item_collapsed(self, item):
        if item.childCount() > 0:  # 仅文件夹切换图标
            item.setIcon(0, self.folder_closed)

# 主程序入口
if __name__ == "__main__":
    window = TreeDemoWindow()
    window.show()
    sys.exit(app.exec())