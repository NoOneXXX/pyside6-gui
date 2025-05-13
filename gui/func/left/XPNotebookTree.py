import re
import uuid
import time

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTreeWidget,
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
class XPNotebookTree(QWidget):
    def __init__(self, path, rich_text_edit=None, parent=None):
        super().__init__(parent)
        self.custom_path = os.path.expanduser(path)
        # 接收这个富文本框的参数属性
        self.rich_text_edit = rich_text_edit

        # 图标资源
        self.folder_closed_icon = QIcon(QPixmap(":images/folder-orange.png"))
        self.folder_open_icon = QIcon(QPixmap(":images/folder-orange-open.png"))
        self.file_icon = QIcon(QPixmap(":images/note-violet.png"))

        self.tree = None
        self.setup_ui()

    def populate_tree(self, parent_item, path):
        try:
            for name in os.listdir(path):
                full_path = os.path.join(path, name)
                # 判断这个文件夹是不是文件 读取它下面的json配置
                editor = JsonEditor()
                content_type = editor.read_notebook_if_dir(full_path)

                print(f"[populate_tree] {name} => content_type={content_type}")

                if 'dir' == content_type:
                    folder_item = QTreeWidgetItem(parent_item)
                    folder_item.setText(0, name)

                    if name.lower() == "python":
                        icon = QIcon(QPixmap(":images/folder-orange.png"))
                    elif name in ("我的垃圾桶", "trash"):
                        icon = QIcon(QPixmap(":images/trash.png"))
                    else:
                        icon = self.folder_closed_icon

                    folder_item.setIcon(0, icon)
                    folder_item.setFont(0, QFont("Microsoft YaHei", 12))

                    # 懒加载标记项
                    folder_item.addChild(QTreeWidgetItem())
                    folder_item.setData(0, Qt.UserRole, full_path)
                elif content_type == "file":
                    file_item = QTreeWidgetItem(parent_item)
                    file_item.setText(0, os.path.splitext(name)[0])
                    file_item.setIcon(0, self.file_icon)
                    file_item.setData(0, Qt.UserRole, full_path)
                    #  也允许子文件结构（懒加载子节点）
                    file_item.addChild(QTreeWidgetItem())  # 懒加载标记

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
        style = QStyleFactory.create("windows")
        if style:
            self.tree.setStyle(style)
        palette = self.tree.palette()
        palette.setColor(QPalette.Highlight, QColor("#E6F0FA"))
        palette.setColor(QPalette.HighlightedText, QColor("#000000"))
        self.tree.setPalette(palette)


        self.tree.itemExpanded.connect(self.handle_item_expanded)
        self.tree.itemCollapsed.connect(self.handle_item_collapsed)

        root = QTreeWidgetItem(self.tree)
        notebook_name = os.path.basename(self.custom_path)
        root.setText(0, notebook_name)
        root.setIcon(0, self.folder_closed_icon)
        font = QFont("Segoe UI", 12)
        font.setBold(True)
        root.setFont(0, font)
        root.setData(0, Qt.UserRole, self.custom_path)
        root.addChild(QTreeWidgetItem())  # 懒加载标记

        self.tree.setAnimated(True)
        self.tree.setExpandsOnDoubleClick(False)
        layout.addWidget(self.tree)

        ## 增加右键点击事件
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.on_context_menu)
        ## 右键点击事件增加结束

        # 左键点击事件 点击的时候就展开 不是只有点击前面的加号减号才展开
        self.tree.itemClicked.connect(self.on_item_clicked)
        self.tree.setItemDelegate(CustomTreeItemDelegate())
        self.tree.itemChanged.connect(self.on_item_renamed)

    def on_item_renamed(self, item, column):
        if not item or column != 0:
            return

        old_path = item.data(0, Qt.UserRole)
        if not old_path or not os.path.exists(old_path):
            return

        # 只处理刚创建的项
        is_new = item.data(0, Qt.UserRole + 1)
        if not is_new:
            return

        new_name = item.text(0).strip()
        if not new_name or new_name == os.path.basename(old_path):
            return

        parent_item = item.parent()
        parent_path = self.custom_path if parent_item is None else parent_item.data(0, Qt.UserRole)
        new_path = os.path.join(parent_path, new_name)

        if os.path.exists(new_path):
            QMessageBox.warning(self, "重命名失败", "已存在同名文件/文件夹")
            item.setText(0, os.path.basename(old_path))
            return

        try:
            os.rename(old_path, new_path)
            item.setData(0, Qt.UserRole, new_path)
            item.setData(0, Qt.UserRole + 1, None)  # ✅ 移除“刚创建”标记
            self._update_child_user_roles(item, old_path, new_path)
        except Exception as e:
            QMessageBox.critical(self, "重命名失败", str(e))
            item.setText(0, os.path.basename(old_path))

    '''
    左键点击的方法实现
    '''

    def on_item_clicked(self, item, column):
        if item.childCount() > 0:
            if item.isExpanded():
                item.setExpanded(False)
                self.handle_item_collapsed(item)
            else:
                item.setExpanded(True)
                self.handle_item_expanded(item)

        # 额外添加：如果是文件，读取 HTML 内容显示到富文本
        path = item.data(0, Qt.UserRole)
        editor = JsonEditor()
        content_type = editor.read_notebook_if_dir(path)
        if content_type == "file" and self.rich_text_edit:
            html_path = os.path.join(path, ".note.html")
            # 将这个路径发送到 main 用来给富文本保存文件内容使用
            sm.send_current_file_path_2_main_richtext_signal.emit(html_path)
            if os.path.exists(html_path):
                with open(html_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                    # Load HTML into rich text editor
                    self.rich_text_edit.setHtml(html_content)

                    # Set base URL for resolving relative paths
                    base_dir = os.path.dirname(html_path)
                    base_url = QUrl.fromLocalFile(base_dir + "/")  # Use forward slash for consistency
                    self.rich_text_edit.document().setBaseUrl(base_url)

                    # Extract and register image resources
                    pattern = re.compile(r'<img[^>]+src="([^"]+)"')
                    src_list = pattern.findall(html_content)
                    doc = self.rich_text_edit.document()
                    for src in src_list:
                        src = src.strip()
                        img_path = os.path.normpath(os.path.join(base_dir, src))
                        img_url = QUrl.fromLocalFile(img_path)
                        if os.path.exists(img_path):
                            image = QImage(img_path)
                            if not image.isNull():
                                doc.addResource(QTextDocument.ImageResource, img_url, image)
                                print(f"[Debug] Registered image resource: {img_url.toString()}")
                            else:
                                print(f"[Warning] Failed to load image: {img_path}")
                        else:
                            print(f"[Warning] Image file not found: {img_path}")


    '''
    右键点击事件的方法
    '''
    def on_context_menu(self, point):
        item = self.tree.itemAt(point)
        if item is None:
            return

        menu = QMenu(self.tree)

        open_action = QAction(QIcon(":images/open.png"), "打开", self)
        rename_action = QAction(QIcon(":images/open.png"), "重命名", self)
        create_file_action = QAction(QIcon(":images/open.png"), "创建子文件", self)
        create_dir_action = QAction(QIcon(":images/open.png"), "创建文件夹", self)
        delete_action = QAction(QIcon(":images/open.png"), "删除", self)
        # 方法绑定
        open_action.triggered.connect(lambda: self.open_item(item))
        rename_action.triggered.connect(lambda: self.rename_item(item))
        create_file_action.triggered.connect(lambda: self.create_file_item(item))
        create_dir_action.triggered.connect(lambda: self.create_dir_action(item))
        delete_action.triggered.connect(lambda: self.delete_item(item))
        # 方法绑定 结束
        menu.addAction(open_action)
        menu.addAction(rename_action)
        menu.addAction(create_file_action)
        menu.addAction(create_dir_action)


        menu.addAction(delete_action)
        # 右键点击的样式 封装到了文件的最底端
        menu.setStyleSheet(WINDOWS_MENU_STYLE)

        menu.exec(self.tree.viewport().mapToGlobal(point))


    def open_item(self, item):
        path = self.get_item_path(item)
        print(f"打开: {path}")

    def rename_item(self, item):
        old_path = item.data(0, Qt.UserRole)
        old_name = os.path.basename(old_path)
        new_name, ok = QInputDialog.getText(self, "重命名", "输入新名称：", text=os.path.splitext(old_name)[0])
        if not ok or not new_name :
            return
        if new_name == old_name:
            QMessageBox.information(self,"文件名已经存在","请更换别的名字，文件名已经存在")
        ext = os.path.splitext(old_path)[1]  # 获取旧后缀
        new_path = os.path.join(os.path.dirname(old_path), new_name + ext)
        try:
            os.rename(old_path, new_path)
        except Exception as e:
            QMessageBox.critical(self, "重命名失败", f"无法重命名")
            return

        item.setText(0, os.path.splitext(new_name)[0])
        item.setData(0, Qt.UserRole, new_path)
        self._update_child_user_roles(item, old_path, new_path)

    '''
        这个更新是防止懒加载的时候因为重命名导致加载失败
        因为他会找原来的路径名
        '''
    def _update_child_user_roles(self, item, old_base, new_base):
        for i in range(item.childCount()):
            child = item.child(i)
            old_child_path = child.data(0, Qt.UserRole)
            if old_child_path:
                new_child_path = old_child_path.replace(old_base, new_base, 1)
                child.setData(0, Qt.UserRole, new_child_path)
            self._update_child_user_roles(child, old_base, new_base)

    def delete_item(self, item):
        print(f"删除: {item.text(0)}")

    '''
    创建一个新的文件
    从ui下面的home.html 取出文件的模板
    '''

    def create_file_item(self, item, index=0):
        dir_path = item.data(0, Qt.UserRole)
        name = '新建文件' if index == 0 else f'新建文件-{index}'
        file_path = os.path.join(dir_path, name)

        if os.path.exists(file_path):
            self.create_file_item(item, index + 1)
            return

        try:
            os.makedirs(file_path, exist_ok=True)
            create_metadata_file_under_dir(file_path)
            note_path = os.path.join(file_path, ".note.html")
            with open(note_path, "w", encoding="utf-8") as f:
                f.write("<html></html>")

            new_item = QTreeWidgetItem()
            new_item.setText(0, name)
            new_item.setIcon(0, self.file_icon)
            new_item.setData(0, Qt.UserRole, file_path)
            new_item.setData(0, Qt.UserRole + 1, True)  #  标记“刚创建”
            new_item.setFlags(new_item.flags() | Qt.ItemIsEditable)
            # new_item.addChild(QTreeWidgetItem())

            item.addChild(new_item)
            item.setExpanded(True)

            self.tree.setCurrentItem(new_item)
            self.tree.editItem(new_item, 0)

        except Exception as e:
            QMessageBox.critical(self, "创建失败", f"无法创建文件:\n{e}")

    '''
    创建文件夹
    '''

    def create_dir_action(self, item, index_=0):
        dir_path = item.data(0, Qt.UserRole)
        name = '新建文件' if index_ == 0 else f'新建文件-{index_}'
        file_path = os.path.join(dir_path, name)

        if os.path.exists(file_path):
            self.create_dir_action(item, index_ + 1)
            return

        try:
            os.makedirs(file_path, exist_ok=True)
            create_metadata_dir_under_dir(file_path)

            # 不刷新，而是手动插入新节点
            new_item = QTreeWidgetItem()
            new_item.setText(0, name)
            new_item.setIcon(0, self.folder_closed_icon)
            new_item.setData(0, Qt.UserRole, file_path)
            new_item.setData(0, Qt.UserRole + 1, True)  # 标记刚创建
            new_item.setFlags(new_item.flags() | Qt.ItemIsEditable)
            # new_item.addChild(QTreeWidgetItem())  # 懒加载标记

            item.setExpanded(True)
            item.addChild(new_item)

            self.tree.setCurrentItem(new_item)
            self.tree.editItem(new_item, 0)

        except Exception as e:
            QMessageBox.critical(self, "创建失败", f"无法创建文件夹:\n{e}")

    def get_item_path(self, item):
        parts = []
        while item:
            parts.insert(0, item.text(0))
            item = item.parent()
        return os.path.join(self.custom_path, *parts)

    def handle_item_expanded(self, item):
        path = item.data(0, Qt.UserRole)

        editor = JsonEditor()
        content_type = editor.read_notebook_if_dir(path)
        self.set_item_icon(item, content_type)

        if item.childCount() == 1 and item.child(0).text(0) == "":
            item.takeChild(0)
            path = item.data(0, Qt.UserRole)
            if path:
                self.populate_tree(item, path)


    def handle_item_collapsed(self, item):
        # item.setIcon(0, self.folder_closed_icon)
        path = item.data(0, Qt.UserRole)
        editor = JsonEditor()
        content_type = editor.read_notebook_if_dir(path)
        self.set_item_icon(item, content_type)
    '''
    进行封装 如果是文件夹就用文件夹的图标 文件就用文件的图标
    '''
    def set_item_icon(self, item, content_type):
        if content_type == "dir":
            item.setIcon(0, self.folder_closed_icon)
        elif content_type == "file":
            item.setIcon(0, self.file_icon)
        else:
            item.setIcon(0, QIcon())  # 默认






# ========================
# Windows-style context menu QSS
# 右键点击的样式 放在这个主要是为了维护的时候简单
# ========================
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

def main():
    app = QApplication(sys.argv)
    widget = XPNotebookTree("C:/Users/Dell/Desktop/temp/log")  # 替换为你自己的路径
    widget.resize(300, 500)
    widget.setWindowTitle(f"目录树：{widget.custom_path}")
    widget.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
