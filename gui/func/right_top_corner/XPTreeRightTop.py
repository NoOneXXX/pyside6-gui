import re
import uuid
import time
import datetime
from gui.ui import resource_rc
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTreeWidget,
    QTreeWidgetItem, QStyleFactory, QMessageBox, QHeaderView, QMenu, QInputDialog
)
from PySide6.QtGui import QIcon, QPixmap, QFont, QPalette, QColor, QAction, QImage, QTextDocument
from PySide6.QtCore import Qt, Slot, QUrl
import sys
import os
from gui.func.singel_pkg.single_manager import sm
from gui.func.utils.json_utils import JsonEditor
from gui.func.utils.tools_utils import read_parent_id, create_metadata_file_under_dir, create_metadata_dir_under_dir
from gui.func.left.CustomTreeItemDelegate import CustomTreeItemDelegate


def format_time(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


class XPTreeRightTop(QWidget):
    def __init__(self, path, selected_path=None, rich_text_edit=None, parent=None):
        super().__init__(parent)
        self.custom_path = os.path.expanduser(path)
        self.selected_path = os.path.expanduser(selected_path) if selected_path else None
        self.rich_text_edit = rich_text_edit

        self.folder_closed_icon = QIcon(QPixmap(":images/folder-orange.png"))
        self.folder_open_icon = QIcon(QPixmap(":images/folder-orange-open.png"))
        self.file_icon = QIcon(QPixmap(":images/note-violet.png"))

        self.tree = None
        self.setup_ui()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.select_path_item(self.selected_path)) if self.selected_path else None

        # 确保 tree 已初始化和填充
        if self.selected_path:
            self.select_path_item(self.selected_path)

    def populate_tree(self, parent_item, path):
        try:
            for name in os.listdir(path):
                full_path = os.path.join(path, name)
                editor = JsonEditor()
                content_type = editor.read_notebook_if_dir(full_path)

                if 'dir' == content_type:
                    folder_item = QTreeWidgetItem(parent_item)
                    folder_item.setText(0, name)
                    stat = os.stat(full_path)
                    folder_item.setText(1, format_time(stat.st_ctime))
                    folder_item.setText(2, format_time(stat.st_mtime))

                    icon = (QIcon(QPixmap(":images/folder-orange.png"))
                            if name.lower() == "python" else
                            QIcon(QPixmap(":images/trash.png"))
                            if name in ("我的垃圾桶", "trash")
                            else self.folder_closed_icon)

                    folder_item.setIcon(0, icon)
                    folder_item.setFont(0, QFont("Microsoft YaHei", 12))
                    folder_item.addChild(QTreeWidgetItem())
                    folder_item.setData(0, Qt.UserRole, full_path)

                elif content_type == "file":
                    file_item = QTreeWidgetItem(parent_item)
                    file_item.setText(0, os.path.splitext(name)[0])
                    stat = os.stat(full_path)
                    file_item.setText(1, format_time(stat.st_ctime))
                    file_item.setText(2, format_time(stat.st_mtime))
                    file_item.setIcon(0, self.file_icon)
                    file_item.setData(0, Qt.UserRole, full_path)
                    file_item.addChild(QTreeWidgetItem())

        except PermissionError:
            pass

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Context", "Created Time", "Updated Time"])

        self.tree.header().setStretchLastSection(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.tree.setColumnWidth(0, 300)  # 设置第一列宽度
        self.tree.header().setSectionResizeMode(1, QHeaderView.Interactive)
        self.tree.setColumnWidth(1, 250)  # 设置第二列宽度
        self.tree.header().setSectionResizeMode(2, QHeaderView.Interactive)

        style = QStyleFactory.create("Fusion")
        if style:
            self.tree.setStyle(style)

        palette = self.tree.palette()
        palette.setColor(QPalette.Highlight, QColor("#E6F0FA"))
        palette.setColor(QPalette.HighlightedText, QColor("#000000"))
        self.tree.setPalette(palette)

        self.tree.itemExpanded.connect(self.handle_item_expanded)
        self.tree.itemCollapsed.connect(self.handle_item_collapsed)

        layout.addWidget(self.tree)

        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.setItemDelegate(CustomTreeItemDelegate())
        '''自定义前面的图标'''
        self.tree.setStyleSheet(QTREEW_WIDGET_STYLE)

        # 左键点击事件 点击的时候就展开 不是只有点击前面的加号减号才展开
        self.tree.itemClicked.connect(self.on_item_clicked)

        if os.path.exists(self.custom_path):
            root = QTreeWidgetItem(self.tree)
            notebook_name = os.path.basename(self.custom_path)
            root.setText(0, notebook_name)
            stat = os.stat(self.custom_path)
            root.setText(1, format_time(stat.st_ctime))
            root.setText(2, format_time(stat.st_mtime))
            root.setIcon(0, self.folder_closed_icon)
            font = QFont("Segoe UI", 12)
            font.setBold(True)
            root.setFont(0, font)
            root.setData(0, Qt.UserRole, self.custom_path)
            root.addChild(QTreeWidgetItem())
            root.setExpanded(True)

        self.tree.setAnimated(True)
        self.tree.setExpandsOnDoubleClick(False)

        if self.selected_path:
            self.select_item_by_path(self.selected_path)

    def select_item_by_path(self, target_path):
        def recurse(parent):
            for i in range(parent.childCount()):
                item = parent.child(i)
                item_path = item.data(0, Qt.UserRole)
                if item_path == target_path:
                    self.tree.setCurrentItem(item)
                    self.tree.scrollToItem(item)
                    return True
                if recurse(item):
                    item.setExpanded(True)
                    return True
            return False

        for i in range(self.tree.topLevelItemCount()):
            top_item = self.tree.topLevelItem(i)
            if recurse(top_item):
                break

    def handle_item_expanded(self, item):
        path = item.data(0, Qt.UserRole)
        editor = JsonEditor()
        content_type = editor.read_notebook_if_dir(path)
        self.set_item_icon(item, content_type)

        if item.childCount() == 1 and item.child(0).text(0) == "":
            item.takeChild(0)
            if path:
                self.populate_tree(item, path)

    def handle_item_collapsed(self, item):
        path = item.data(0, Qt.UserRole)
        editor = JsonEditor()
        content_type = editor.read_notebook_if_dir(path)
        self.set_item_icon(item, content_type)

    def set_item_icon(self, item, content_type):
        if content_type == "dir":
            item.setIcon(0, self.folder_closed_icon)
        elif content_type == "file":
            item.setIcon(0, self.file_icon)
        else:
            item.setIcon(0, QIcon())

    def select_path_item(self, path):
        def recursive_search(item):
            for i in range(item.childCount()):
                child = item.child(i)
                if child.data(0, Qt.UserRole) == path:
                    self.tree.setCurrentItem(child)
                    self.tree.scrollToItem(child)
                    return True
                if recursive_search(child):
                    return True
            return False

        root = self.tree.invisibleRootItem()
        recursive_search(root)

    '''
    左键点击的方法实现
    '''
    def on_item_clicked(self, item):
        # 这个是在点击的时候将树状图给展开和合并
        if item.childCount() > 0:
            if item.isExpanded():
                item.setExpanded(False)
                self.handle_item_collapsed(item)
            else:
                item.setExpanded(True)
                self.handle_item_expanded(item)

        file_path = item.data(0, Qt.UserRole)
        # 这个是发送地址给main那边 在那边自动保存的时候使用
        sm.send_current_file_path_2_main_richtext_signal.emit(file_path, 'right_top_cor')
        editor = JsonEditor()
        content_type = editor.read_notebook_if_dir(file_path)
        if content_type == "file" and self.rich_text_edit:
            file_path = os.path.join(file_path, ".note.html")
            with open(file_path, "r", encoding="utf-8") as f:
                html = f.read()
            # 必须先设置 baseUrl
            base_url = QUrl.fromLocalFile(os.path.dirname(file_path) + os.sep)
            self.rich_text_edit.document().setBaseUrl(base_url)

            # 设置内容
            self.rich_text_edit.setHtml(html)



WINDOWS_MENU_STYLE = """
QMenu {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    padding: 4px;
    border-radius: 8px;
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 10.5pt;
}
QMenu::item {
    padding: 6px 30px 6px 30px;
    margin: 2px 4px;
    background-color: transparent;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #e8f0fe;
    color: #000000;
}
QMenu::separator {
    height: 1px;
    background: #e0e0e0;
    margin: 4px 10px 4px 10px;
}
QMenu::icon {
    padding-left: 6px;
}
"""

'''树状图前面的图标'''
QTREEW_WIDGET_STYLE = """
        QTreeView::branch {
            background: transparent;
        }
        QTreeView::branch:has-children:!has-siblings:closed,
        QTreeView::branch:closed:has-children {
            image: url(:images/plus-square.svg);
        }
        QTreeView::branch:open:has-children:!has-siblings,
        QTreeView::branch:open:has-children {
            image: url(:images/minus-square.svg);
        }
        """

def main():
    app = QApplication(sys.argv)
    # 示例：选中某个文件  , selected_path="C:/Users/Dell/Desktop/temp/log/文件1.html
    widget = XPTreeRightTop("/Users/echo/Desktop/temp/test",
                            selected_path="/Users/echo/Desktop/temp/test/新建文件/新建文件/多余的名字")
    widget.resize(600, 500)
    widget.setWindowTitle(f"目录树：{widget.custom_path}")
    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


    # def select_path_item(self, path):
    #     def recursive_search(item):
    #         for i in range(item.childCount()):
    #             child = item.child(i)
    #             if child.data(0, Qt.UserRole) == path:
    #                 self.tree.setCurrentItem(child)
    #                 self.tree.scrollToItem(child)
    #                 return True
    #             if recursive_search(child):
    #                 return True
    #         return False
    #
    #     root = self.tree.invisibleRootItem()
    #     recursive_search(root)

    def select_path_item(self, target_path):
        def normalize(p):
            return os.path.normpath(os.path.abspath(p))

        target_path = normalize(target_path)

        def traverse_and_expand(parent):
            for i in range(parent.childCount()):
                child = parent.child(i)
                child_path = child.data(0, Qt.UserRole)
                if child_path and normalize(child_path) == target_path:
                    self.tree.setCurrentItem(child)
                    self.tree.scrollToItem(child)
                    self.tree.expandItem(child)
                    return True
                elif child.childCount() > 0:
                    self.tree.expandItem(child)
                    if traverse_and_expand(child):
                        return True
            return False

        root = self.tree.invisibleRootItem()
        traverse_and_expand(root)
