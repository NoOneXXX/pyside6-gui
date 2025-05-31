# FileActions.py
import os
import sqlite3

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QFileDialog, QMessageBox, QMenu
import uuid
import time

from gui.func.utils.json_utils import JsonEditor
from gui.data.NoteDB import NoteDB
from gui.func.singel_pkg.single_manager import sm
# 这个文件的引用不能删除 否则下面的图片就会找不到文件
from gui.ui import resource_rc


'''
file文件的事件操作和处理
'''
class FileActions:
    def __init__(self, parent=None):
        self.parent = parent  # 通常是 QMainWindow，用来绑定对话框等
        self.note_db = None
        # 默认打开最近一次笔记本
        note_db = NoteDB("recent_notebooks.db")
        if note_db:
            list_path = note_db.get_recent_notebooks(1)
            if list_path:
                sm.left_tree_structure_rander_after_create_new_notebook_signal.emit(list_path[0])

    '''
    创建笔记本的action
    '''
    def create_file_action(self):
        action = QAction(
            QIcon(":/images/blue-folder-open-document.png"),
            "创建笔记",
            self.parent
        )
        action.setStatusTip("创建一个新笔记")
        action.triggered.connect(self.create_file)
        return action

    '''
    打开笔记
    '''
    def open_notebook_action(self):
        action = QAction(
            QIcon(":/images/blue-folder-open-document.png"),
            "打开笔记",
            self.parent
        )
        action.setStatusTip("打开笔记")
        action.triggered.connect(self.open_folder)
        return action

    '''打开最近的笔记本'''

    def open_recent_notebook_action(self):
        """
        返回一个 QAction，但能弹出最近文件的 QMenu
        """
        # 创建“打开最近笔记”的 QAction
        action = QAction(
            QIcon(":/images/blue-folder-open-document.png"),
            "打开最近笔记",
            self.parent
        )

        # 设置状态提示
        action.setStatusTip("打开最近笔记")

        # 创建子菜单（即最近文件路径列表）
        recent_menu = QMenu(self.parent)
        note_db = NoteDB("recent_notebooks.db")

        # 加载最近的笔记本
        recent_paths = note_db.get_recent_notebooks(15)
        recent_menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
                border-radius: 8px;  /* 设置圆角半径 */
                padding: 4px;
            }

            QMenu::item {
                padding: 6px 24px;
                background-color: transparent;
                border-radius: 4px;  /* 给 item 也加圆角，避免选中时遮住菜单圆角 */
            }

            QMenu::item:selected {
                background-color: #cce8ff;  /* 浅蓝色，模拟 Win10 的悬浮 */
                border-radius: 4px;
            }
        """)

        for idx, path in enumerate(recent_paths, start=1):
            sub_action = QAction(f"{idx}. {path}", self.parent)
            sub_action.setData(path)
            sub_action.triggered.connect(lambda checked=False, p=path: self.open_recent_notebook_path(p))
            recent_menu.addAction(sub_action)


        # 关键：将 menu 设置给这个 QAction，点击后就能弹出子菜单
        action.setMenu(recent_menu)
        return action

    def open_recent_notebook_path(self, path):
        if path and os.path.exists(path):
            metadata_path = os.path.join(path, ".metadata.json")
            if not os.path.exists(metadata_path):
                QMessageBox.warning(self.parent, "打开失败", "该目录不是有效的笔记本")
                return

            sm.left_tree_structure_rander_after_create_new_notebook_signal.emit(path)
        else:
            QMessageBox.warning(self.parent, "打开失败", "路径不存在")

    '''打开最近笔记本的函数'''
    def open_notebook(self):
        pass


    def open_folder(self):
        # 保存这个笔记本的路径
        # 统一的 recent_notebooks.db 数据库文件路径
        note_db = NoteDB("recent_notebooks.db")
        # 弹出对话框选择要创建新文件夹的位置（用户选择一个父目录）
        folder_path = QFileDialog.getExistingDirectory(
            self.parent, "选择要打开的笔记本"
        )
        if folder_path:
            metadata_path = os.path.join(folder_path, ".metadata.json")
            if not os.path.exists(metadata_path):
                QMessageBox.warning(self.parent, "打开失败", "该目录不是有效的笔记本")
                return
        # 赋值给path_
        self.path_ = folder_path
        if folder_path and os.path.exists(folder_path):
            # 这个路径存在就更新时间 不存在就保存
            note_db.save_recent_notebook(folder_path, int(time.time()))
        # 笔记被成功创建后 发射信号通知主窗口要进行渲染左边的树
        sm.left_tree_structure_rander_after_create_new_notebook_signal.emit(folder_path)

    '''
    创建笔记
    '''
    def create_file(self):
        # 示例：弹出对话框创建文件（你可以自定义逻辑）
        file_path, _ = QFileDialog.getSaveFileName(self.parent, "创建新笔记", "", "All Files (*)")
        if file_path:
            try:
                # 判断是否已存在
                exists_flag =  os.path.exists(file_path)
                if exists_flag:
                    QMessageBox.information(self.parent, "创建笔记本", "当前文件名字已经存在！！！")
                    return
                # 创建一个空文件夹
                os.makedirs(file_path, exist_ok=False)
                # 创建  .metadata.json
                self.create_metadata_file(file_path)

                # 创建的这个文件夹下面创建三个文件 一个trash 一个.metadata.json 一个.rte.html（富文本编辑）
                # 2. 在文件夹内创建子目录 trash/
                trash_path = os.path.join(file_path, "trash")
                os.makedirs(trash_path, exist_ok=True)
                # 创建  .metadata.json
                self.create_metadata_file(trash_path)

                APP_ROOT = os.path.dirname(os.path.abspath(__file__))
                # 统一的 recent_notebooks.db 数据库文件路径
                RECENT_DB_PATH = os.path.join(APP_ROOT, "recent_notebooks.db")
                note_db = NoteDB(RECENT_DB_PATH)
                # 这个路径存在就更新时间 不存在就保存
                if file_path:
                    note_db.save_recent_notebook(file_path, int(time.time()))

                # 笔记被成功创建后 发射信号通知主窗口要进行渲染左边的树
                sm.left_tree_structure_rander_after_create_new_notebook_signal.emit(file_path)


            except Exception as e:
                QMessageBox.critical(self.parent, "错误", str(e))


    '''
    给文件夹下面创建.metadata.json
    这里创建得是文件夹 就不用修改文件夹属性
    '''
    def create_metadata_file(self, file_path):
        # 3. 创建空文件 .metadata.json
        # 创建编辑器并加载
        editor = JsonEditor().load()
        # 直接修改字段
        data = editor.get_data()
        # 加上id
        id = str(uuid.uuid4())
        data['node']['id'] = id
        timestamp = int(time.time())  # 创建时间
        data['node']['detail_info']['created_time'] = timestamp
        folder_name = os.path.basename(file_path)  # 创建名字
        data['node']['detail_info']['title'] = folder_name

        # 写入到原文件或新文件
        metadata_path = os.path.join(file_path, ".metadata.json")
        editor.write(metadata_path)

        # 插入数据 将这个文件的创建给记录到数据库表格中
        # 在 create_metadata_file 的最后
        # 3 创建当前笔记本得数据库
        # 创建数据库文件夹
        if 'trash' != folder_name:
            data_db_path = os.path.join(file_path, "data")
            if not os.path.exists(data_db_path):
                os.makedirs(data_db_path)
            # 创建数据库表 如果不存在数据库就创建表格
            db_path = os.path.join(data_db_path, "notebook.db")
            if not os.path.exists(db_path):
                self.note_db = NoteDB(db_path)
            if 'data' != folder_name and 'trash' != folder_name:
                self.note_db.insert_note(
                    id_=id,
                    path=folder_name,
                    title=folder_name,
                    parent_id="0",  # 如果你有上级逻辑就填实际 UUID
                    created_time=timestamp,
                    updated_time=timestamp
                )










