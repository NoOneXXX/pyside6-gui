import re
import uuid
import time
from pathlib import Path

from gui.func.left.dropItemEvent import CustomTreeWidget
from gui.func.right_bottom_corner.RichTextEdit import RichTextEdit
from gui.ui import resource_rc
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTreeWidget,
    QTreeWidgetItem, QStyleFactory, QMessageBox, QHeaderView, QMenu, QInputDialog, QFileDialog
)
from PySide6.QtGui import QIcon, QPixmap, QFont, QPalette, QColor, QAction, QImage, QTextDocument
from PySide6.QtCore import Qt, Slot, QUrl
import sys
import os
from gui.func.singel_pkg.single_manager import sm
from gui.func.utils.json_utils import JsonEditor
from gui.func.utils.tools_utils import (read_parent_id, create_metadata_file_under_dir,
                                        create_metadata_dir_under_dir, scan_supported_files)
from gui.func.left.CustomTreeItemDelegate import CustomTreeItemDelegate
from gui.func.utils.file_loader import file_loader
from ..utils import copy_and_overwrite





class XPNotebookTree(QWidget):
    def __init__(self, path, rich_text_edit=None, parent=None):
        super().__init__(parent)
        self.custom_path = os.path.expanduser(path)
        # 接收这个富文本框的参数属性
        self.rich_text_edit = rich_text_edit
        # 需要加载的四种格式
        self.supported_exts = ['attachfile_pdf', 'attachfile_docx', 'attachfile_txt', 'attachfile_epub']
        # 图标资源
        self.folder_closed_icon = QIcon(QPixmap(":images/folder-orange.png"))

        self.file_icon = QIcon(QPixmap(":images/note-violet.png"))
        # 附件图片
        self.attach_file = QIcon(QPixmap(":images/attach-file.png"))
        sm.received_rich_text_2_left_click_signal.connect(self.rich_text_edit_received)

        self.tree = None
        self.setup_ui()

    def populate_tree(self, parent_item, path):
        try:
            items = []
            for name in os.listdir(path):
                full_path = os.path.join(path, name)
                # 判断这个文件夹是不是文件 读取它下面的json配置
                editor = JsonEditor()
                # 读取detail_info的信息
                detail_info = editor.read_file_metadata_infos(full_path)
                content_type = '0'
                order_dir = 0
                if detail_info:
                    content_type = detail_info.get('content_type', None)
                    # 获取到order的值
                    order_dir = detail_info.get('order', None)
                # 获取
                if 'dir' == content_type:
                    # 封装这个树
                    folder_item = QTreeWidgetItem()
                    self.set_item_icon(folder_item, content_type, 'collapsed', detail_info)
                    folder_item.setFont(0, QFont("Microsoft YaHei", 12))
                    folder_item.setData(0, Qt.UserRole, full_path)
                    folder_item.setData(0, Qt.UserRole + 2, order_dir)
                    folder_item.setText(0, name)
                    # 加入到集合
                    items.append((folder_item, order_dir))
                    # 懒加载标记项
                    if detail_info.get('has_children', False):
                        folder_item.addChild(QTreeWidgetItem())
                elif content_type == "file":
                    # 封装这个树
                    folder_item = QTreeWidgetItem()
                    folder_item.setData(0, Qt.UserRole, full_path)
                    folder_item.setData(0, Qt.UserRole + 2, order_dir)
                    folder_item.setText(0, os.path.splitext(name)[0])
                    folder_item.setIcon(0, self.file_icon)
                    # 加入到集合
                    items.append((folder_item, order_dir))
                    #  也允许子文件结构（懒加载子节点）
                    if detail_info.get('has_children', False):
                        folder_item.addChild(QTreeWidgetItem())  # 懒加载标记
                elif content_type.find('attachfile') != -1:
                    # 处理 epub 文件类型
                    # 封装这个树
                    folder_item = QTreeWidgetItem()
                    folder_item.setData(0, Qt.UserRole, full_path)
                    folder_item.setData(0, Qt.UserRole + 2, order_dir)
                    folder_item.setText(0, name)
                    folder_item.setIcon(0, self.attach_file)  # 用你自己的 epub 图标路径
                    # 加入到集合
                    items.append((folder_item, order_dir))
                    if detail_info.get('has_children', False):
                        folder_item.addChild(QTreeWidgetItem())  # 懒加载标记

            # 按 order 排序
            items.sort(key=lambda x: x[1])
            for item, _ in items:
                parent_item.addChild(item)

        except PermissionError:
            pass

    def setup_ui(self):
        if not os.path.exists(self.custom_path):
            QMessageBox.critical(self, "路径错误", f"目录不存在:\n{self.custom_path}")
            return

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # header = QLabel("")
        # header.setStyleSheet("background-color: #F0F0F0; padding: 2px; font-weight: bold;")
        # layout.addWidget(header)

        # self.tree = QTreeWidget()
        self.tree = CustomTreeWidget()  # 使用自定义树控件
        self.tree.notebook_tree = self  # 绑定 XPNotebookTree 实例
        self.tree.setColumnCount(1)
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setIndentation(16)

        # === 添加拖拽支持 ===
        self.tree.setDragEnabled(True)  # 允许节点被拖动
        self.tree.setAcceptDrops(True)  # 允许将其他节点拖到该树上
        self.tree.setDropIndicatorShown(True)  # 显示拖拽指示线
        self.tree.setDragDropMode(QTreeWidget.InternalMove)  # 设置为树内部的移动操作
        # === 拖拽支持结束 ===

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
        #展开树
        self.tree.expandAll()
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
            item.setData(0, Qt.UserRole + 1, None)  #移除“刚创建”标记
            self._update_child_user_roles(item, old_path, new_path)
        except Exception as e:
            QMessageBox.critical(self, "重命名失败", str(e))
            item.setText(0, os.path.basename(old_path))

    '''
    左键点击的方法实现
    '''
    def on_item_clicked(self, item):
        # 触发这个更新富文本框的信号
        sm.change_web_engine_2_richtext_signal.emit()
        # 这个是在点击的时候将树状图给展开和合并
        if item.childCount() > 0:
            if item.isExpanded():
                item.setExpanded(False)
                self.handle_item_collapsed(item)
            else:
                item.setExpanded(True)
                self.handle_item_expanded(item)

        file_path = item.data(0, Qt.UserRole)

        editor = JsonEditor()
        content_type =  editor.read_notebook_if_dir(file_path)
        # 这个是发送地址给main那边 在那边自动保存的时候使用
        sm.send_current_file_path_2_main_richtext_signal.emit(file_path, 'left')

        # 支持加载的类型：pdf、docx、txt、epub
        if  content_type in self.supported_exts:
            # 扫面这个目录下的文件然后找到符合文件名字的路径
            exts_file_path = scan_supported_files(file_path,self.supported_exts)
            # 加载支持的文件类型（PDF、Word、TXT、EPUB）
            loader_ = file_loader(exts_file_path, self.rich_text_edit)
            loader_.load_file()

        if content_type == "file" and self.rich_text_edit:
            file_path = os.path.join(file_path, ".note.html")
            with open(file_path, "r", encoding="utf-8") as f:
                html = f.read()
            # 必须先设置 baseUrl
            base_url = QUrl.fromLocalFile(os.path.dirname(file_path) + os.sep)
            self.rich_text_edit.document().setBaseUrl(base_url)

            # 设置内容
            self.rich_text_edit.setHtml(html)

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
        adds_on_action = QAction(QIcon(":images/open.png"), "添加附件", self)
        # 方法绑定
        open_action.triggered.connect(lambda: self.open_item(item))
        rename_action.triggered.connect(lambda: self.rename_item(item))
        create_file_action.triggered.connect(lambda: self.create_file_item(item))
        create_dir_action.triggered.connect(lambda: self.create_dir_action(item))
        delete_action.triggered.connect(lambda: self.delete_item(item))
        adds_on_action.triggered.connect(lambda: self.adds_on_item(item))
        # 方法绑定 结束
        menu.addAction(open_action)
        menu.addAction(rename_action)
        menu.addAction(create_file_action)
        menu.addAction(create_dir_action)
        menu.addAction(adds_on_action)

        menu.addAction(delete_action)
        # 右键点击的样式 封装到了文件的最底端
        menu.setStyleSheet(WINDOWS_MENU_STYLE)
        menu.exec(self.tree.viewport().mapToGlobal(point))

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
            # 将它的父类改成has_childer true 这个可以在创建的时候是否有子集
            editor = JsonEditor()
            editor_data = editor.read_node_infos(dir_path)
            editor_data['node']['detail_info']['has_children'] = True
            # 获取到子类最大的值 排序使用
            max_order_num_by_child_dir = editor_data['node']['detail_info']['max_order_num_by_child_dir']
            max_order_num_by_child_dir = max_order_num_by_child_dir + 1
            editor_data['node']['detail_info']['max_order_num_by_child_dir'] = max_order_num_by_child_dir
            meta_path = os.path.join(dir_path, ".metadata.json")
            editor.writeByData(meta_path,editor_data)

            os.makedirs(file_path, exist_ok=True)
            create_metadata_file_under_dir(file_path, content_type = 'file', order_file_num = max_order_num_by_child_dir)
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
            # 重新排序
            self.reorder_tree(item,max_order_num_by_child_dir)

            self.tree.setCurrentItem(new_item)
            self.tree.editItem(new_item, 0)

        except Exception as e:
            QMessageBox.critical(self, "创建失败", f"无法创建文件:\n{e}")

    def change_tag(data):
        data['node']['detail_info']['tag'] = 'new_tag'  # Add a new field
        return data

    def update_order(self, parent_item):
        editor = JsonEditor()
        non_trash_items = []
        trash_item = None

        # 收集子节点
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            path = child.data(0, Qt.UserRole)
            metadata = editor.read_node_infos(path)
            is_trash = metadata['node']['detail_info'].get('title', '')
            if 'trash' == is_trash:
                trash_item = child
            else:
                non_trash_items.append(child)

        # 更新 order 值
        for i, child in enumerate(non_trash_items):
            path = child.data(0, Qt.UserRole)
            metadata = editor.read_node_infos(path)
            metadata['node']['detail_info']['order'] = i
            editor.writeByData(os.path.join(path, ".metadata.json"), metadata)
            child.setData(0, Qt.UserRole + 2, i)

        # if trash_item:
        #     path = trash_item.data(0, Qt.UserRole)
        #     metadata = editor.read_node_infos(path)
        #     metadata['node']['detail_info']['order'] = 999999
        #     editor.writeByData(os.path.join(path, ".metadata.json"), metadata)
        #     trash_item.setData(0, Qt.UserRole + 2, 999999)

        # 重新排序
        self.reorder_tree(parent_item)

    '''重新排序'''
    def reorder_tree(self, parent_item, orders_by_file = 0):
        items = []
        for i in range(parent_item.childCount()):
            item = parent_item.child(i)
            order = item.data(0, Qt.UserRole + 2) or 0
            if order == 0:
                order = orders_by_file
            items.append((item, order))

        # 按 order 排序
        items.sort(key=lambda x: x[1])

        # 清空并重新添加
        parent_item.takeChildren()
        for item, _e in items:
            parent_item.addChild(item)
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
            # 将它的父类改成has_childer true 这个可以在创建的时候是否有子集
            editor = JsonEditor()
            editor_data = editor.read_node_infos(dir_path)
            editor_data['node']['detail_info']['has_children'] = True
            # 获取到子类最大的值 排序使用
            max_order_num_by_child_dir = editor_data['node']['detail_info']['max_order_num_by_child_dir']
            max_order_num_by_child_dir = max_order_num_by_child_dir + 1
            editor_data['node']['detail_info']['max_order_num_by_child_dir'] = max_order_num_by_child_dir
            meta_path = os.path.join(dir_path, ".metadata.json")
            editor.writeByData(meta_path, editor_data)

            os.makedirs(file_path, exist_ok=True)
            create_metadata_dir_under_dir(file_path,content_type = 'dir', order_file_num = max_order_num_by_child_dir)

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
            # 重新排序
            self.reorder_tree(item, max_order_num_by_child_dir)

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

    '''
    打开文件夹
    '''
    def handle_item_expanded(self, item):
        path = item.data(0, Qt.UserRole)

        editor = JsonEditor()
        content_type = editor.read_notebook_if_dir(path)
        # 读取detail_info的信息
        detail_info = editor.read_file_metadata_infos(path)
        self.set_item_icon(item, content_type, 'expanded' , detail_info)

        if item.childCount() == 1 and item.child(0).text(0) == "":
            item.takeChild(0)
            path = item.data(0, Qt.UserRole)
            if path:
                self.populate_tree(item, path)
    '''
    关闭文件夹
    '''
    def handle_item_collapsed(self, item):
        path = item.data(0, Qt.UserRole)
        editor = JsonEditor()
        content_type = editor.read_notebook_if_dir(path)
        # 读取detail_info的信息
        detail_info = editor.read_file_metadata_infos(path)
        self.set_item_icon(item, content_type, 'collapsed', detail_info)
    '''
    进行封装 如果是文件夹就用文件夹的图标 文件就用文件的图标
    exps 是展开还是关闭
    detail_info 就是元数据的详细信息
    '''
    def set_item_icon(self, item, content_type, exps, detail_infos):
        # 关闭
        if 'collapsed' == exps:
            if content_type == "dir" or content_type == "file":
                colla_icon = detail_infos['close_dir_icon']
                item.setIcon(0,  QIcon(QPixmap(colla_icon)))
            else:
                colla_icon = detail_infos['adds_on_icon']
                item.setIcon(0, QIcon(QPixmap(colla_icon)))
        else:
            if content_type == "dir" or content_type == "file":
                colla_icon = detail_infos['open_dir_icon']
                item.setIcon(0,  QIcon(QPixmap(colla_icon)))
            else:
                colla_icon = detail_infos['adds_on_icon']
                item.setIcon(0, QIcon(QPixmap(colla_icon)))



    '''
    接收这个富文本框 重新渲染
    '''
    @Slot(RichTextEdit)
    def rich_text_edit_received(self, rich_text):
        self.rich_text_edit = rich_text

    '''
    右键点击
    添加附件
    '''
    def adds_on_item(self, item):
        # 弹出文件选择框（默认打开当前目录）
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "请选择文件",
            ".",  # 默认打开目录
            "所有文件 (*);;PDF 文件 (*.pdf);;文本文件 (*.txt)"
        )
        # 选择了文件
        if file_path:
            # 获取路径
            base_dir_path = item.data(0, Qt.UserRole)
            try:
                # 将它的父类改成has_childer true 这个可以在创建的时候是否有子集
                editor = JsonEditor()
                editor_data = editor.read_node_infos(base_dir_path)
                editor_data['node']['detail_info']['has_children'] = True
                # 获取到子类最大的值 排序使用
                max_order_num_by_child_dir = editor_data['node']['detail_info']['max_order_num_by_child_dir']
                max_order_num_by_child_dir = max_order_num_by_child_dir + 1
                editor_data['node']['detail_info']['max_order_num_by_child_dir'] = max_order_num_by_child_dir

                meta_path = os.path.join(base_dir_path, ".metadata.json")
                editor.writeByData(meta_path, editor_data)


                # 获取文件名 并且创建这个文件夹
                file_name = os.path.basename(file_path)
                target_file_path = os.path.join(base_dir_path, file_name)
                os.makedirs(target_file_path, exist_ok=True)
                # # 扩展名（不含点） pdf
                ext_types = Path(file_path).suffix.lstrip('.')
                # file_path.suffix 含有标点 .pdf
                create_metadata_file_under_dir(target_file_path, 'attachfile_' + ext_types, max_order_num_by_child_dir)
                # 复制这个文件到新的文件夹下面
                copy_and_overwrite(file_path, target_file_path)

                new_item = QTreeWidgetItem()
                new_item.setText(0, file_name)
                new_item.setIcon(0, self.attach_file)
                # 这里修改文件路径为新的文件路径这样第一次读取的时候才不会报错
                new_item.setData(0, Qt.UserRole, target_file_path)
                new_item.setData(0, Qt.UserRole + 1, True)  # 标记“刚创建”

                item.addChild(new_item)
                item.setExpanded(True)
                # 重新排序
                self.reorder_tree(item, max_order_num_by_child_dir)
                self.tree.setCurrentItem(new_item)
                self.tree.editItem(new_item, 0)

            except Exception as e:
                QMessageBox.critical(self, "创建失败", f"无法创建文件:\n{e}")

        else:
            # 取消选择
            pass

    '''拖拽的重写函数'''
    def handle_drop(self, dragged_item, parent_item, target_item, drop_pos):
        try:
            # 获取父节点路径
            parent_path = self.custom_path if parent_item is None or parent_item == self.tree.invisibleRootItem() else parent_item.data(0, Qt.UserRole)
            dragged_path = dragged_item.data(0, Qt.UserRole)
            dragged_name = os.path.basename(dragged_path)
            new_path = os.path.join(parent_path, dragged_name)

            # 防止重名
            if os.path.exists(new_path):
                QMessageBox.warning(self, "拖拽失败", "目标路径已存在同名文件/文件夹")
                return

            # 移动文件/文件夹
            os.rename(dragged_path, new_path)

            # 更新拖拽节点的路径和元数据
            dragged_item.setData(0, Qt.UserRole, new_path)
            self._update_child_user_roles(dragged_item, dragged_path, new_path)

            editor = JsonEditor()
            # 更新拖拽节点的 parent_id 和 order
            dragged_metadata = editor.read_node_infos(new_path)
            dragged_metadata['node']['detail_info']['parent_id'] = read_parent_id(parent_path)
            # 分配新的 order 值（使用 max_order_num_by_child_dir + 1）
            parent_metadata = editor.read_node_infos(parent_path)
            max_order_num = parent_metadata['node']['detail_info'].get('max_order_num_by_child_dir', 0)
            dragged_metadata['node']['detail_info']['order'] = max_order_num + 1
            dragged_item.setData(0, Qt.UserRole + 1, True)  # 标记为新节点
            dragged_item.setData(0, Qt.UserRole + 2, max_order_num + 1)
            editor.writeByData(os.path.join(new_path, ".metadata.json"), dragged_metadata)

            # 更新父节点的 has_children 和 max_order_num_by_child_dir
            parent_metadata['node']['detail_info']['has_children'] = True
            parent_metadata['node']['detail_info']['max_order_num_by_child_dir'] = max_order_num + 1
            editor.writeByData(os.path.join(parent_path, ".metadata.json"), parent_metadata)

            # 将拖拽节点添加到新父节点
            if dragged_item.parent():
                dragged_item.parent().takeChild(dragged_item.parent().indexOfChild(dragged_item))
            parent_item.addChild(dragged_item)

            # 更新 order 值并重新排序
            self.update_order(parent_item)
            self.reorder_tree(parent_item)

            # 强制刷新树控件
            self.tree.viewport().update()

            # 如果父节点已展开，重新加载子节点
            # if parent_item.isExpanded():
            parent_item.takeChildren()
            self.populate_tree(parent_item, parent_path)

            # 高亮拖拽后的节点
            self.tree.setCurrentItem(dragged_item)
            self.tree.scrollToItem(dragged_item)

        except Exception as e:
            QMessageBox.critical(self, "拖拽失败", f"无法完成拖拽操作:\n{e}")












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
    import PySide6.QtCore as QtCore

    print(QtCore.QFile.exists(":images/grandidier.jpg"))

    main()
