
import json
import shutil
from pathlib import Path
from gui.func.left.dropItemEvent import CustomTreeWidget
from gui.func.left.file_encryption.encryption_data import FolderEncryptor
from gui.func.left.file_encryption.EncryptPasswordDialog import EncryptPasswordDialog, EncryptSuccessDialog
from gui.func.right_bottom_corner.RichTextEdit import RichTextEdit
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget,
    QTreeWidgetItem, QStyleFactory, QMessageBox, QHeaderView, QInputDialog, QFileDialog,
    QGraphicsOpacityEffect, QGraphicsDropShadowEffect, QDialog, QPushButton, QLineEdit
)
from PySide6.QtGui import QIcon, QPixmap, QFont, QPalette, QColor, QCursor
from PySide6.QtCore import Qt, Slot, QUrl, QMimeData, QTimer, QPropertyAnimation, QEasingCurve, Signal
import sys
import os
from gui.func.singel_pkg.single_manager import sm
from gui.func.utils.json_utils import JsonEditor
from gui.func.utils.tools_utils import (read_parent_id, create_metadata_file_under_dir,
                                        create_metadata_dir_under_dir, scan_supported_files)
from gui.func.left.CustomTreeItemDelegate import CustomTreeItemDelegate
from gui.func.utils.file_loader import file_loader
from ..utils import copy_and_overwrite,get_parent_path





class XPNotebookTree(QWidget):
    # 信号定义
    open_markdown_editor = Signal(str)  # 打开 Markdown 编辑器，参数为文件路径
    update_markdown_obj = Signal(str)  # 更新 Markdown 编辑器对象
    open_mindmap_editor = Signal(str)   # 打开思维导图编辑器，参数为文件路径
    file_renamed = Signal(str, str)     # 文件重命名信号，参数为(旧路径, 新路径)
    unlock_dir_with_password = Signal(str)  # 通过密码来解压出来这个文件内容
    clear_richtext_editor = Signal()  # 清空富文本编辑器
    
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
        self.tree.setAnimated(True)

        # Apply this stylesheet to your QTreeWidget
        self.tree.setStyleSheet("""
                    QTreeView::branch:has-siblings:!adjoins-item {
                        image: url(:images/branch/vline.png);
                    }
                    QTreeView::branch:has-siblings:adjoins-item {
                        image: url(:images/branch/branch-more.png);
                    }
                    QTreeView::branch:!has-children:!has-siblings:adjoins-item {
                        image: url(:images/branch/branch-end.png);
                    }
                    QTreeView::branch:has-children:has-siblings:closed,
                    QTreeView::branch:closed:has-children:has-siblings {
                        image: url(:images/branch/branch-closed.png);
                    }
                    QTreeView::branch:open:has-children:has-siblings,
                    QTreeView::branch:open:has-children:!has-siblings {
                        image: url(:images/branch/branch-open.png);
                    }

                    /* 修复：没有兄弟节点（最后一个节点）且是折叠状态 */
                    QTreeView::branch:!has-siblings:adjoins-item:has-children:closed {
                        image: url(:images/branch/branch-closed.png);
                    }

                    /* 修复：没有兄弟节点（最后一个节点）且是展开状态 */
                    QTreeView::branch:!has-siblings:adjoins-item:has-children:open {
                        image: url(:images/branch/branch-open.png);
                    }
                """)

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
        # 将路径存储到 UserRole+3 用于委托绘制灰色显示
        root.setData(0, Qt.UserRole + 3, f"  {self.custom_path}(🙋如果你看到了这句话，那就说明这里有一句话！！！🤪🤪🤪)")
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
        self.tree.setItemDelegate(CustomTreeItemDelegate(self.tree))
        self.tree.itemChanged.connect(self.on_item_renamed)

    def _set_item_font_color(self, item, detail_info):
        """设置树节点字体颜色，从 detail_info 的 font_color 字段读取十六进制颜色"""
        if detail_info:
            font_color = detail_info.get('font_color', '')
            if font_color and font_color.strip():
                # 设置字体颜色（十六进制颜色）
                item.setForeground(0, QColor(font_color))
            else:
                # 默认黑色
                item.setForeground(0, QColor("#000000"))
        else:
            # 默认黑色
            item.setForeground(0, QColor("#000000"))

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
                    # 设置字体颜色
                    self._set_item_font_color(folder_item, detail_info)
                    # 加入到集合
                    items.append((folder_item, order_dir))
                    # 懒加载标记项
                    if detail_info and detail_info.get('has_children', False):
                        folder_item.addChild(QTreeWidgetItem())
                elif content_type == "file":
                    # 封装这个树
                    folder_item = QTreeWidgetItem()
                    folder_item.setData(0, Qt.UserRole, full_path)
                    folder_item.setData(0, Qt.UserRole + 2, order_dir)
                    folder_item.setText(0, os.path.splitext(name)[0])
                    folder_item.setIcon(0, self.file_icon)
                    # 设置字体颜色
                    self._set_item_font_color(folder_item, detail_info)
                    # 加入到集合
                    items.append((folder_item, order_dir))
                    #  也允许子文件结构（懒加载子节点）
                    if detail_info and detail_info.get('has_children', False):
                        folder_item.addChild(QTreeWidgetItem())  # 懒加载标记
                elif content_type == "markdown":
                    # 处理 Markdown 文件类型
                    folder_item = QTreeWidgetItem()
                    folder_item.setData(0, Qt.UserRole, full_path)
                    folder_item.setData(0, Qt.UserRole + 2, order_dir)
                    folder_item.setText(0, name)
                    # 使用 Markdown 图标
                    markdown_icon = QIcon(QPixmap(":images/markdown.png"))
                    folder_item.setIcon(0, markdown_icon)
                    # 设置字体颜色
                    self._set_item_font_color(folder_item, detail_info)
                    # 加入到集合
                    items.append((folder_item, order_dir))
                    if detail_info and detail_info.get('has_children', False):
                        folder_item.addChild(QTreeWidgetItem())  # 懒加载标记
                elif content_type == "mindmap":
                    # 处理思维导图文件类型
                    folder_item = QTreeWidgetItem()
                    folder_item.setData(0, Qt.UserRole, full_path)
                    folder_item.setData(0, Qt.UserRole + 2, order_dir)
                    folder_item.setText(0, name)
                    # 使用思维导图图标
                    mindmap_icon = QIcon(QPixmap(":images/markdown.png"))
                    folder_item.setIcon(0, mindmap_icon)
                    # 设置字体颜色
                    self._set_item_font_color(folder_item, detail_info)
                    # 加入到集合
                    items.append((folder_item, order_dir))
                    if detail_info and detail_info.get('has_children', False):
                        folder_item.addChild(QTreeWidgetItem())  # 懒加载标记
                elif "lock" in content_type:
                    # 加密的文件
                    folder_item = QTreeWidgetItem()
                    folder_item.setData(0, Qt.UserRole, full_path)
                    folder_item.setData(0, Qt.UserRole + 2, order_dir)
                    # 移除名称中已存在的🔐，避免重复添加
                    display_name = name.replace("🔐", "").strip()
                    folder_item.setText(0, f"{display_name}  🔐")
                    # 使用文件夹图标（加密文件夹仍然显示文件夹样式）
                    if detail_info:
                        close_icon = detail_info.get('close_dir_icon', ':images/folder-orange.png')
                        folder_item.setIcon(0, QIcon(QPixmap(close_icon)))
                    else:
                        folder_item.setIcon(0, self.folder_closed_icon)
                    # 设置字体颜色
                    self._set_item_font_color(folder_item, detail_info)
                    # 加入到集合
                    items.append((folder_item, order_dir))
                    if detail_info and detail_info.get('has_children', False):
                        folder_item.addChild(QTreeWidgetItem())  # 懒加载标记
                elif content_type and content_type.find('attachfile') != -1:
                    # 处理 epub 文件类型
                    # 封装这个树
                    folder_item = QTreeWidgetItem()
                    folder_item.setData(0, Qt.UserRole, full_path)
                    folder_item.setData(0, Qt.UserRole + 2, order_dir)
                    folder_item.setText(0, name)
                    folder_item.setIcon(0, self.attach_file)  # 用你自己的 epub 图标路径
                    # 设置字体颜色
                    self._set_item_font_color(folder_item, detail_info)
                    # 加入到集合
                    items.append((folder_item, order_dir))
                    if detail_info and detail_info.get('has_children', False):
                        folder_item.addChild(QTreeWidgetItem())  # 懒加载标记

            # 按 order 排序
            items.sort(key=lambda x: x[1])
            for item, _ in items:
                parent_item.addChild(item)

        except PermissionError:
            pass

    def on_item_renamed(self, item, column):
        if not item or column != 0:
            return

        old_path = item.data(0, Qt.UserRole)
        if not old_path or not os.path.exists(old_path):
            return

        new_name = item.text(0).strip()
        # 移除🔐，确保实际文件夹名称不包含emoji
        actual_name = new_name.replace("🔐", "").strip()
        
        if not actual_name or actual_name == os.path.basename(old_path):
            # 恢复显示名称
            editor = JsonEditor()
            content_type = editor.read_notebook_if_dir(old_path)
            if content_type and "lock" in content_type:
                item.setText(0, f"{os.path.basename(old_path)}  🔐")
            else:
                item.setText(0, os.path.basename(old_path))
            return

        parent_item = item.parent()
        parent_path = self.custom_path if parent_item is None else parent_item.data(0, Qt.UserRole)
        new_path = os.path.join(parent_path, actual_name)

        if os.path.exists(new_path):
            QMessageBox.warning(self, "重命名失败", "已存在同名文件/文件夹")
            # 恢复显示名称
            editor = JsonEditor()
            content_type = editor.read_notebook_if_dir(old_path)
            if content_type and "lock" in content_type:
                item.setText(0, f"{os.path.basename(old_path)}  🔐")
            else:
                item.setText(0, os.path.basename(old_path))
            return

        try:
            os.rename(old_path, new_path)
            item.setData(0, Qt.UserRole, new_path)
            item.setData(0, Qt.UserRole + 1, None)  #移除"刚创建"标记
            self._update_child_user_roles(item, old_path, new_path)
            
            # 如果是加密文件夹，保持显示名称带🔐
            editor = JsonEditor()
            content_type = editor.read_notebook_if_dir(new_path)
            if content_type and "lock" in content_type:
                item.setText(0, f"{actual_name}  🔐")
                    
            # 发射文件重命名信号，通知主窗口更新编辑器路径
            self.file_renamed.emit(old_path, new_path)
        except Exception as e:
            QMessageBox.critical(self, "重命名失败", str(e))
            # 恢复显示名称
            editor = JsonEditor()
            content_type = editor.read_notebook_if_dir(old_path)
            if content_type and "lock" in content_type:
                item.setText(0, f"{os.path.basename(old_path)}  🔐")
            else:
                item.setText(0, os.path.basename(old_path))

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

        editor = JsonEditor()
        content_type =  editor.read_notebook_if_dir(file_path)
        
        # 处理 Markdown 文件类型 - 提前返回，不触发富文本框信号
        if content_type == "markdown":
            self.open_markdown_editor.emit(file_path)
            return
        
        # 处理思维导图文件类型 - 提前返回，不触发富文本框信号
        if content_type == "mindmap":
            self.open_mindmap_editor.emit(file_path)
            return

        # 如果是加密的就直接的弹框让输入密码
        if "lock" in content_type:
            self.unlock_dir_with_password.emit(file_path)
            return
        
        # 触发这个更新富文本框的信号（Markdown 和思维导图类型不触发）
        sm.change_web_engine_2_richtext_signal.emit()
        
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

        # 获取节点信息
        item_path = item.data(0, Qt.UserRole)
        content_type = ""
        detail_info = None

        if item_path:
            editor = JsonEditor()
            content_type = editor.read_notebook_if_dir(item_path)
            detail_info = editor.read_file_metadata_infos(item_path)

        # 状态判断
        is_attachment = content_type and 'attachfile' in content_type
        is_trash_folder = detail_info and detail_info.get('title') == 'trash'
        is_in_trash = self._is_item_in_trash(item)

        if "lock" not in content_type:
            # 初始化自定义菜单
            menu = ModernContextMenu(self)

            # ====================== 公共方法：添加通用菜单 ======================
            def add_common_actions():
                """添加所有节点通用的右键菜单（打开、重命名、删除等）"""
                menu.add_action("📂", "打开", lambda: self.open_item(item), "#3B82F6")
                menu.add_action("✏", "重命名", lambda: self.rename_item(item), "#F59E0B")
                menu.add_separator()
                menu.add_action("📝", "创建 Markdown", lambda: self.create_markdown_file(item), "#6366F1")
                menu.add_action("🧠", "创建思维导图", lambda: self.create_mindmap_file(item), "#9B59B6")
                menu.add_action("📄", "创建子文件", lambda: self.create_file_item(item), "#10B981")
                menu.add_action("📁", "创建文件夹", lambda: self.create_dir_action(item), "#8B5CF6")
                menu.add_action("📎", "添加附件", lambda: self.adds_on_item(item), "#06B6D4")
                menu.add_separator()
                menu.add_action("🔐", "加密", lambda: self.encrypt_item(item), "#06B6D4")
                menu.add_action("🗑", "删除", lambda: self.delete_item(item), "#EF4444")

            # ====================== 根据类型显示菜单 ======================
            if is_trash_folder:
                # 回收站根目录：仅清空
                menu.add_action("🗑", "清空回收站", lambda: self.empty_trash(item), "#EF4444")

            elif is_in_trash:
                # 回收站内部：永久删除 + 恢复
                menu.add_action("☠", "永久删除", lambda: self.permanent_delete_item(item), "#DC2626")
                menu.add_action("↩", "恢复文件", lambda: self.restore_item(item), "#10B981")

            elif is_attachment:
                # 附件：额外加“复制附件”，其他通用
                menu.add_action("📋", "复制附件", lambda: self.copy_attachment(item), "#8B5CF6")
                add_common_actions()

            else:
                # 普通文件/文件夹：全量通用菜单
                add_common_actions()

            # 显示
            menu.show_menu(self.tree.viewport().mapToGlobal(point))

    '''
    创建彩色图标
    '''
    def _create_colored_icon(self, emoji, color_hex):
        """创建带颜色的图标"""
        from PySide6.QtGui import QPainter, QFont
        
        # 创建一个透明背景的图标
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 设置字体
        font = QFont("Segoe UI Emoji", 14)
        painter.setFont(font)
        
        # 设置颜色
        color = QColor(color_hex)
        painter.setPen(color)
        
        # 绘制 emoji
        painter.drawText(pixmap.rect(), Qt.AlignCenter, emoji)
        painter.end()
        
        return QIcon(pixmap)

    '''
    判断节点是否在 trash 文件夹内
    '''
    def _is_item_in_trash(self, item):
        parent = item.parent()
        while parent:
            parent_path = parent.data(0, Qt.UserRole)
            if parent_path:
                editor = JsonEditor()
                detail_info = editor.read_file_metadata_infos(parent_path)
                if detail_info and detail_info.get('title', '') == 'trash':
                    return True
            parent = parent.parent()
        return False

    '''
    获取 trash 文件夹路径
    '''
    def _get_trash_path(self):
        # trash 文件夹在根目录下
        trash_path = os.path.join(self.custom_path, "trash")
        if os.path.exists(trash_path):
            return trash_path
        return None

    '''
    获取文件原始位置（用于恢复）
    '''
    def _get_original_path(self, item):
        item_path = item.data(0, Qt.UserRole)
        if not item_path:
            return None
        
        # 从 metadata 中获取原始位置信息
        editor = JsonEditor()
        metadata = editor.read_node_infos(item_path)
        if metadata and 'node' in metadata:
            original_path = metadata['node']['detail_info'].get('original_path', '')
            if original_path:
                return original_path
        
        # 如果没有存储原始路径，尝试从父级推断
        # 获取 trash 的父目录（即根目录）
        trash_path = self._get_trash_path()
        if trash_path:
            # 原始位置应该是根目录
            return self.custom_path
        return None

    '''
    复制附件到剪贴板
    '''
    def copy_attachment(self, item):
        item_path = item.data(0, Qt.UserRole)
        if not item_path or not os.path.exists(item_path):
            show_toast(self, "附件路径不存在", ToastWidget.ERROR)
            return

        try:
            # 获取附件文件夹中的实际文件
            # 附件存储在文件夹中，需要找到实际的文件
            files = [f for f in os.listdir(item_path) if not f.startswith('.')]
            if not files:
                show_toast(self, "附件文件夹为空", ToastWidget.WARNING)
                return

            # 通常附件文件夹中只有一个文件（即附件本身）
            attachment_file = os.path.join(item_path, files[0])

            # 复制文件到剪贴板
            clipboard = QApplication.clipboard()
            mime_data = QMimeData()
            mime_data.setUrls([QUrl.fromLocalFile(attachment_file)])
            clipboard.setMimeData(mime_data)

            show_toast(self, f"附件已复制到剪贴板\n{files[0]}", ToastWidget.SUCCESS)
        except Exception as e:
            show_toast(self, f"复制失败: {str(e)}", ToastWidget.ERROR)

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
        
        # 检查是否为加密文件夹
        editor = JsonEditor()
        content_type = editor.read_notebook_if_dir(old_path)
        is_locked = content_type and "lock" in content_type
        
        # 显示名称（不带🔐）
        display_name = old_name.replace("🔐", "").strip()
        new_name, ok = QInputDialog.getText(self, "重命名", "输入新名称：", text=display_name)
        if not ok or not new_name:
            return
        # 移除用户输入中可能包含的🔐
        actual_name = new_name.replace("🔐", "").strip()
        if actual_name == old_name:
            QMessageBox.information(self, "文件名已经存在", "请更换别的名字，文件名已经存在")
            return
        ext = os.path.splitext(old_path)[1]  # 获取旧后缀
        new_path = os.path.join(os.path.dirname(old_path), actual_name + ext)
        try:
            os.rename(old_path, new_path)
        except Exception as e:
            QMessageBox.critical(self, "重命名失败", f"无法重命名")
            return

        # 如果是加密文件夹，显示名称带🔐
        if is_locked:
            item.setText(0, f"{actual_name}  🔐")
        else:
            item.setText(0, actual_name)
        item.setData(0, Qt.UserRole, new_path)
        # 更新markdown对象 防止更换名字后重新创建多个文件
        self.update_markdown_obj.emit(new_path)
        self._update_child_user_roles(item, old_path, new_path)



    def delete_item(self, item):
        """删除文件/文件夹，移动到回收站"""
        item_path = item.data(0, Qt.UserRole)
        if not item_path or not os.path.exists(item_path):
            show_toast(self, "文件路径不存在", ToastWidget.ERROR)
            return

        # 获取 trash 路径
        trash_path = self._get_trash_path()
        if not trash_path:
            show_toast(self, "回收站不存在", ToastWidget.ERROR)
            return

        # 二次确认对话框 - 使用自定义样式
        item_name = os.path.basename(item_path)
        reply = self._show_delete_confirm_dialog(item_name, "删除到回收站")

        if not reply:
            return

        try:
            import shutil
            
            # 获取文件名
            item_name = os.path.basename(item_path)
            target_path = os.path.join(trash_path, item_name)
            
            # 如果回收站中已存在同名文件，先删除它
            if os.path.exists(target_path):
                if os.path.isdir(target_path):
                    shutil.rmtree(target_path)
                else:
                    os.remove(target_path)

            # 保存原始路径到 metadata
            editor = JsonEditor()
            metadata = editor.read_node_infos(item_path)
            if metadata and 'node' in metadata:
                metadata['node']['detail_info']['original_path'] = os.path.dirname(item_path)
                editor.writeByData(os.path.join(item_path, ".metadata.json"), metadata)

            # 移动文件到回收站
            shutil.move(item_path, target_path)
            
            # 验证移动是否成功（源文件应该不存在了）
            if os.path.exists(item_path):
                # 如果源文件还存在，强制删除
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)

            # 更新父节点的 has_children 状态
            parent_item = item.parent()
            if parent_item:
                parent_path = parent_item.data(0, Qt.UserRole)
                if parent_path and os.path.exists(parent_path):
                    # 检查父目录下是否还有子文件夹（排除隐藏文件和.metadata.json）
                    has_children = False
                    try:
                        for f in os.listdir(parent_path):
                            # 跳过隐藏文件和.metadata.json，images也要排除
                            if f.startswith('.') or f == '.metadata.json' or f.lower() == 'images':
                                continue
                            full_path = os.path.join(parent_path, f)
                            if os.path.isdir(full_path):
                                has_children = True
                                break
                    except (PermissionError, OSError):
                        pass
                    
                    parent_metadata = editor.read_node_infos(parent_path)
                    if parent_metadata and 'node' in parent_metadata:
                        parent_metadata['node']['detail_info']['has_children'] = has_children
                        editor.writeByData(os.path.join(parent_path, ".metadata.json"), parent_metadata)

                # 从树中移除节点
                parent_item.removeChild(item)

            # 更新回收站的 has_children 状态
            trash_metadata = editor.read_node_infos(trash_path)
            if trash_metadata and 'node' in trash_metadata:
                trash_metadata['node']['detail_info']['has_children'] = True
                editor.writeByData(os.path.join(trash_path, ".metadata.json"), trash_metadata)

            # 刷新 trash 文件夹显示
            self._refresh_trash_folder()

            show_toast(self, f"已移动到回收站\n{item_name}", ToastWidget.SUCCESS)

        except Exception as e:
            show_toast(self, f"删除失败: {str(e)}", ToastWidget.ERROR)

    '''
    刷新 trash 文件夹
    '''
    def _refresh_trash_folder(self):
        """刷新回收站文件夹以显示新删除的文件"""
        root = self.tree.topLevelItem(0)
        if not root:
            return
        
        # 查找 trash 节点
        for i in range(root.childCount()):
            child = root.child(i)
            child_path = child.data(0, Qt.UserRole)
            if child_path:
                editor = JsonEditor()
                detail_info = editor.read_file_metadata_infos(child_path)
                if detail_info and detail_info.get('title', '') == 'trash':
                    # 找到 trash 节点，刷新其子节点
                    child.takeChildren()
                    self.populate_tree(child, child_path)
                    child.setExpanded(True)
                    break

    '''
    清空回收站
    '''
    def empty_trash(self, trash_item):
        """清空回收站，需要二次确认"""
        # 二次确认对话框 - 使用自定义美观对话框
        reply = self._show_delete_confirm_dialog("回收站", "清空回收站")
        
        if not reply:
            return

        trash_path = trash_item.data(0, Qt.UserRole)
        if not trash_path or not os.path.exists(trash_path):
            show_toast(self, "回收站路径不存在", ToastWidget.ERROR)
            return

        try:
            import shutil
            deleted_count = 0
            # 记录需要更新 has_children 的原始父目录
            original_parents_to_update = set()
            
            # 遍历删除所有内容（包括文件和文件夹）
            for item_name in os.listdir(trash_path):
                # 跳过以 . 开头的隐藏文件/文件夹（如 .metadata.json）
                if item_name.startswith('.'):
                    continue
                    
                item_full_path = os.path.join(trash_path, item_name)
                
                # 获取 original_path 并记录需要更新的父目录
                editor = JsonEditor()
                metadata = editor.read_node_infos(item_full_path)
                if metadata and 'node' in metadata:
                    original_path = metadata['node']['detail_info'].get('original_path')
                    if original_path:
                        original_parents_to_update.add(original_path)
                
                # 检查并删除可能存在的源文件（original_path）
                self._delete_original_path_if_exists(item_full_path)
                
                if os.path.isdir(item_full_path):
                    shutil.rmtree(item_full_path)
                    deleted_count += 1
                elif os.path.isfile(item_full_path):
                    os.remove(item_full_path)
                    deleted_count += 1

            # 清空树节点
            trash_item.takeChildren()

            # 更新回收站的 has_children 状态
            editor = JsonEditor()
            trash_metadata = editor.read_node_infos(trash_path)
            if trash_metadata and 'node' in trash_metadata:
                trash_metadata['node']['detail_info']['has_children'] = False
                editor.writeByData(os.path.join(trash_path, ".metadata.json"), trash_metadata)
            
            # 更新所有原始父目录的 has_children 状态
            for original_parent_path in original_parents_to_update:
                if os.path.exists(original_parent_path):
                    # 检查父目录下是否还有子文件夹（排除隐藏文件和.metadata.json）
                    has_children = False
                    try:
                        for f in os.listdir(original_parent_path):
                            # 跳过隐藏文件和.metadata.json
                            if f.startswith('.') or f == '.metadata.json' or f.lower() == 'images':
                                continue
                            full_path = os.path.join(original_parent_path, f)
                            if os.path.isdir(full_path):
                                has_children = True
                                break
                    except (PermissionError, OSError):
                        pass
                    
                    parent_metadata = editor.read_node_infos(original_parent_path)
                    if parent_metadata and 'node' in parent_metadata:
                        parent_metadata['node']['detail_info']['has_children'] = has_children
                        editor.writeByData(os.path.join(original_parent_path, ".metadata.json"), parent_metadata)

            show_toast(self, f"回收站已清空\n共删除 {deleted_count} 个项目", ToastWidget.SUCCESS)

        except Exception as e:
            show_toast(self, f"清空失败: {str(e)}", ToastWidget.ERROR)
    
    def _delete_original_path_if_exists(self, item_path):
        """检查并删除 item 对应的 original_path 源文件（如果存在）"""
        try:
            editor = JsonEditor()
            metadata = editor.read_node_infos(item_path)
            if metadata and 'node' in metadata:
                original_path = metadata['node']['detail_info'].get('original_path')
                if original_path:
                    # 构建完整的源文件路径
                    item_name = os.path.basename(item_path)
                    full_original_path = os.path.join(original_path, item_name)
                    # 如果源文件存在，删除它
                    if os.path.exists(full_original_path):
                        if os.path.isdir(full_original_path):
                            import shutil
                            shutil.rmtree(full_original_path)
                        elif os.path.isfile(full_original_path):
                            os.remove(full_original_path)
        except Exception:
            # 忽略错误，继续执行主删除操作
            pass

    '''
    永久删除文件
    '''
    def permanent_delete_item(self, item):
        """永久删除文件，不可恢复"""
        item_path = item.data(0, Qt.UserRole)
        if not item_path or not os.path.exists(item_path):
            show_toast(self, "文件路径不存在", ToastWidget.ERROR)
            return

        # 二次确认 - 使用自定义美观对话框
        item_name = os.path.basename(item_path)
        reply = self._show_delete_confirm_dialog(item_name, "永久删除")
        
        if not reply:
            return

        try:
            import shutil
            
            # 检查并删除可能存在的源文件（original_path）
            self._delete_original_path_if_exists(item_path)
            
            shutil.rmtree(item_path)

            # 从树中移除节点
            parent_item = item.parent()
            if parent_item:
                parent_item.removeChild(item)

                # 更新父节点的 has_children 状态
                parent_path = parent_item.data(0, Qt.UserRole)
                if parent_path and os.path.exists(parent_path):
                    # 检查父目录下是否还有子文件夹（排除隐藏文件和.metadata.json）
                    has_children = False
                    try:
                        for f in os.listdir(parent_path):
                            # 跳过隐藏文件和.metadata.json
                            if f.startswith('.') or f == '.metadata.json' or f.lower() == 'images':
                                continue
                            full_path = os.path.join(parent_path, f)
                            if os.path.isdir(full_path):
                                has_children = True
                                break
                    except (PermissionError, OSError):
                        pass
                    
                    editor = JsonEditor()
                    parent_metadata = editor.read_node_infos(parent_path)
                    if parent_metadata and 'node' in parent_metadata:
                        parent_metadata['node']['detail_info']['has_children'] = has_children
                        editor.writeByData(os.path.join(parent_path, ".metadata.json"), parent_metadata)

            show_toast(self, f"已永久删除\n{item_name}", ToastWidget.SUCCESS)

        except Exception as e:
            show_toast(self, f"删除失败: {str(e)}", ToastWidget.ERROR)

    '''
    恢复文件
    '''
    def restore_item(self, item):
        """从回收站恢复文件"""
        item_path = item.data(0, Qt.UserRole)
        if not item_path or not os.path.exists(item_path):
            show_toast(self, "文件路径不存在", ToastWidget.ERROR)
            return

        try:
            # 获取原始路径
            original_parent_path = self._get_original_path(item)
            if not original_parent_path:
                # 如果没有原始路径，恢复到根目录
                original_parent_path = self.custom_path

            # 检查原始路径是否存在，不存在则恢复到根目录
            if not os.path.exists(original_parent_path):
                original_parent_path = self.custom_path

            item_name = os.path.basename(item_path)
            target_path = os.path.join(original_parent_path, item_name)

            # 如果目标已存在，先删除它再恢复
            if os.path.exists(target_path):
                import shutil
                if os.path.isdir(target_path):
                    shutil.rmtree(target_path)
                else:
                    os.remove(target_path)

            # 移动文件
            import shutil
            shutil.move(item_path, target_path)

            # 清除 original_path 信息
            editor = JsonEditor()
            metadata = editor.read_node_infos(target_path)
            if metadata and 'node' in metadata:
                if 'original_path' in metadata['node']['detail_info']:
                    del metadata['node']['detail_info']['original_path']
                editor.writeByData(os.path.join(target_path, ".metadata.json"), metadata)

            # 从树中移除节点
            parent_item = item.parent()
            if parent_item:
                parent_item.removeChild(item)

                # 更新回收站的 has_children 状态
                trash_path = parent_item.data(0, Qt.UserRole)
                if trash_path and os.path.exists(trash_path):
                    # 检查回收站下是否还有子文件夹（排除隐藏文件和.metadata.json）
                    has_children = False
                    try:
                        for f in os.listdir(trash_path):
                            # 跳过隐藏文件和.metadata.json
                            if f.startswith('.') or f == '.metadata.json' or f.lower() == 'images':
                                continue
                            full_path = os.path.join(trash_path, f)
                            if os.path.isdir(full_path):
                                has_children = True
                                break
                    except (PermissionError, OSError):
                        pass
                    
                    trash_metadata = editor.read_node_infos(trash_path)
                    if trash_metadata and 'node' in trash_metadata:
                        trash_metadata['node']['detail_info']['has_children'] = has_children
                        editor.writeByData(os.path.join(trash_path, ".metadata.json"), trash_metadata)

            # 更新目标父目录的 has_children 状态
            target_parent_metadata = editor.read_node_infos(original_parent_path)
            if target_parent_metadata and 'node' in target_parent_metadata:
                target_parent_metadata['node']['detail_info']['has_children'] = True
                editor.writeByData(os.path.join(original_parent_path, ".metadata.json"), target_parent_metadata)

            # 刷新树结构
            self._refresh_tree_for_restore(original_parent_path, target_path)

            # 显示美观的恢复成功弹框
            self._show_restore_success_dialog(item_name, target_path)

        except Exception as e:
            show_toast(self, f"恢复失败: {str(e)}", ToastWidget.ERROR)

    '''
    刷新树结构以显示恢复的文件
    '''
    def _refresh_tree_for_restore(self, parent_path, restored_path):
        """刷新树结构以显示恢复的文件"""
        # 找到父节点并刷新
        root = self.tree.topLevelItem(0)
        if root:
            self._refresh_tree_node(root, parent_path, restored_path)

    def _refresh_tree_node(self, item, target_parent_path, restored_path):
        """递归查找并刷新目标节点"""
        item_path = item.data(0, Qt.UserRole)
        
        # 找到目标父节点
        if item_path == target_parent_path:
            # 刷新该节点的子节点
            item.takeChildren()
            self.populate_tree(item, item_path)
            item.setExpanded(True)
            return True
        
        # 递归查找
        for i in range(item.childCount()):
            child = item.child(i)
            if self._refresh_tree_node(child, target_parent_path, restored_path):
                return True
        return False

    '''
    显示美观的恢复成功弹框
    '''
    def _show_restore_success_dialog(self, file_name, target_path):
        """显示美观的恢复成功弹框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("恢复成功")
        dialog.setFixedSize(400, 180)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # 设置整体样式
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
                border-radius: 12px;
            }
            QLabel {
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            }
            QPushButton {
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            }
        """)
        
        # 主布局
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        
        # 顶部：图标和标题
        header_layout = QHBoxLayout()
        
        # 成功图标
        icon_label = QLabel()
        icon_label.setFixedSize(44, 44)
        icon_label.setText("✓")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #10B981;
                color: white;
                border-radius: 22px;
                font-size: 22px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(icon_label)
        
        # 标题区域
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        title_label = QLabel("恢复成功")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #1F2937;
            }
        """)
        title_layout.addWidget(title_label)
        
        subtitle_label = QLabel(f"{file_name} 已恢复到原位置")
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #6B7280;
            }
        """)
        title_layout.addWidget(subtitle_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 路径信息
        path_container = QLabel(f"📁 {target_path}")
        path_container.setStyleSheet("""
            QLabel {
                background-color: #F3F4F6;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 11px;
                color: #4B5563;
            }
        """)
        path_container.setWordWrap(True)
        layout.addWidget(path_container)
        
        # 确定按钮
        ok_btn = QPushButton("确定")
        ok_btn.setFixedSize(100, 34)
        ok_btn.setCursor(QCursor(Qt.PointingHandCursor))
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
        """)
        ok_btn.clicked.connect(dialog.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)
        
        # 居中显示
        main_window = QApplication.activeWindow()
        if main_window:
            x = main_window.x() + (main_window.width() - dialog.width()) // 2
            y = main_window.y() + (main_window.height() - dialog.height()) // 2
            dialog.move(x, y)
        
        dialog.exec()

    def _show_delete_confirm_dialog(self, item_name, delete_type="删除"):
        """
        显示美观的删除确认对话框
        
        Args:
            item_name: 要删除的项目名称
            delete_type: 删除类型，如"删除到回收站"、"永久删除"、"清空回收站"
        
        Returns:
            bool: 用户是否确认删除
        """
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(420, 280)
        
        # 主布局
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 主容器
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #FDF8F3;
                border-radius: 24px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(32, 28, 32, 24)
        container_layout.setSpacing(20)
        
        # 图标区域
        icon_widget = QWidget()
        icon_widget.setFixedSize(72, 72)
        icon_widget.setStyleSheet("""
            QWidget {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                    stop:0 #F5E6D3, stop:0.7 #EBD5C5, stop:1 #E0C4B0);
                border-radius: 24px;
            }
        """)
        icon_layout = QHBoxLayout(icon_widget)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel("🗑")
        icon_label.setStyleSheet("background: transparent; font-size: 32px;")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(icon_label)
        
        icon_container = QHBoxLayout()
        icon_container.addStretch()
        icon_container.addWidget(icon_widget)
        icon_container.addStretch()
        container_layout.addLayout(icon_container)
        
        # 标题
        title_label = QLabel(delete_type)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #4A4540;
                font-size: 20px;
                font-weight: 700;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
        """)
        container_layout.addWidget(title_label)
        
        # 内容文本
        content_text = f'确定要删除 "{item_name}" 吗？'
        if delete_type == "清空回收站":
            content_text = "确定要清空回收站吗？"
        
        content_label = QLabel(content_text)
        content_label.setAlignment(Qt.AlignCenter)
        content_label.setWordWrap(True)
        content_label.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #6B6560;
                font-size: 14px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
                line-height: 1.5;
            }
        """)
        container_layout.addWidget(content_label)
        
        # 提示信息
        if delete_type == "删除到回收站":
            tip_text = "删除的文件将被移动到回收站，可以在回收站中恢复。"
        elif delete_type == "永久删除":
            tip_text = "⚠️ 此操作不可撤销，文件将被永久删除！"
        elif delete_type == "清空回收站":
            tip_text = "⚠️ 回收站中的所有文件将被永久删除，不可恢复！"
        else:
            tip_text = ""
        
        if tip_text:
            tip_label = QLabel(tip_text)
            tip_label.setAlignment(Qt.AlignCenter)
            tip_label.setWordWrap(True)
            tip_label.setStyleSheet("""
                QLabel {
                    background: transparent;
                    color: #9A9590;
                    font-size: 12px;
                    font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
                }
            """)
            container_layout.addWidget(tip_label)
        
        # 按钮区域 - 居中布局
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)
        btn_layout.addStretch()
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(100, 40)
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #EDE8E3;
                color: #5C5855;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 500;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: #E0D9D2;
            }
            QPushButton:pressed {
                background-color: #D3CCC4;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        # 确认删除按钮
        confirm_btn = QPushButton("确定删除")
        confirm_btn.setFixedSize(100, 40)
        confirm_btn.setCursor(QCursor(Qt.PointingHandCursor))
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #E07A5F;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 600;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: #D4694F;
            }
            QPushButton:pressed {
                background-color: #C55A40;
            }
        """)
        confirm_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(confirm_btn)
        
        btn_layout.addStretch()
        container_layout.addLayout(btn_layout)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 8)
        container.setGraphicsEffect(shadow)
        
        layout.addWidget(container)
        
        # 居中显示
        main_window = QApplication.activeWindow()
        if main_window:
            x = main_window.x() + (main_window.width() - dialog.width()) // 2
            y = main_window.y() + (main_window.height() - dialog.height()) // 2
            dialog.move(x, y)
        
        result = dialog.exec()
        return result == QDialog.Accepted

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
        
        created_folder = False
        
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

            os.makedirs(file_path, exist_ok=False)
            created_folder = True
            
            create_metadata_file_under_dir(file_path, content_type = 'file', order_file_num = max_order_num_by_child_dir)
            note_path = os.path.join(file_path, ".note.html")
            with open(note_path, "w", encoding="utf-8") as f:
                f.write("<html></html>")

            new_item = QTreeWidgetItem()
            new_item.setText(0, name)
            new_item.setIcon(0, self.file_icon)
            new_item.setData(0, Qt.UserRole, file_path)
            new_item.setData(0, Qt.UserRole + 1, True)  #  标记“刚创建”
            new_item.setData(0, Qt.UserRole + 2, max_order_num_by_child_dir)  # 设置排序值
            new_item.setFlags(new_item.flags() | Qt.ItemIsEditable)
            # new_item.addChild(QTreeWidgetItem())

            item.addChild(new_item)
            item.setExpanded(True)
            # 重新排序
            self.reorder_tree(item)

            self.tree.setCurrentItem(new_item)
            self.tree.editItem(new_item, 0)

        except Exception as e:
            # 清理：如果创建过程中失败，删除已创建的文件/文件夹
            import shutil
            if created_folder and os.path.exists(file_path):
                try:
                    shutil.rmtree(file_path)
                except:
                    pass
            QMessageBox.critical(self, "创建失败", f"无法创建文件:\n{e}")

    '''
    创建 Markdown 文件
    '''
    def create_markdown_file(self, item, index=0):
        dir_path = item.data(0, Qt.UserRole)
        name = '新建文档' if index == 0 else f'新建文档-{index}'
        file_path = os.path.join(dir_path, name)

        if os.path.exists(file_path):
            self.create_markdown_file(item, index + 1)
            return
        
        # 先创建临时文件夹名，避免创建失败后留下残留
        temp_file_path = file_path
        created_folder = False
        try:
            # 将它的父类改成 has_children true
            editor = JsonEditor()
            editor_data = editor.read_node_infos(dir_path)
            editor_data['node']['detail_info']['has_children'] = True
            # 获取到子类最大的值 排序使用
            max_order_num_by_child_dir = editor_data['node']['detail_info']['max_order_num_by_child_dir']
            max_order_num_by_child_dir = max_order_num_by_child_dir + 1
            editor_data['node']['detail_info']['max_order_num_by_child_dir'] = max_order_num_by_child_dir
            meta_path = os.path.join(dir_path, ".metadata.json")
            editor.writeByData(meta_path, editor_data)

            os.makedirs(file_path, exist_ok=False)
            created_folder = True
            
            # 创建 Markdown 类型的 metadata
            create_metadata_file_under_dir(file_path, content_type='markdown', order_file_num=max_order_num_by_child_dir)

            # 创建空的 Markdown 文件
            md_path = os.path.join(file_path, "document.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(f"# {name}\n\n")


            new_item = QTreeWidgetItem()
            new_item.setText(0, name)
            # 使用 Markdown 图标
            markdown_icon = QIcon(QPixmap(":images/markdown.png"))
            new_item.setIcon(0, markdown_icon)
            new_item.setData(0, Qt.UserRole, file_path)
            new_item.setData(0, Qt.UserRole + 1, True)  # 标记"刚创建"
            new_item.setData(0, Qt.UserRole + 2, max_order_num_by_child_dir)  # 设置排序值
            new_item.setFlags(new_item.flags() | Qt.ItemIsEditable)

            item.addChild(new_item)
            item.setExpanded(True)
            # 重新排序
            self.reorder_tree(item)

            self.tree.setCurrentItem(new_item)
            self.tree.editItem(new_item, 0)
            
            # 发送信号通知主窗口打开 Markdown 编辑器
            self.open_markdown_editor.emit(file_path)

        except Exception as e:
            # 清理：如果创建过程中失败，删除已创建的文件/文件夹
            import shutil
            if created_folder and os.path.exists(temp_file_path):
                try:
                    shutil.rmtree(temp_file_path)
                except:
                    pass
            QMessageBox.critical(self, "创建失败", f"无法创建 Markdown 文件:\n{e}")

    '''
    创建思维导图文件
    '''
    def create_mindmap_file(self, item, index=0):
        dir_path = item.data(0, Qt.UserRole)
        name = '新建思维导图' if index == 0 else f'新建思维导图-{index}'
        file_path = os.path.join(dir_path, name)

        if os.path.exists(file_path):
            self.create_mindmap_file(item, index + 1)
            return
        
        created_folder = False
        created_metadata = False
        created_mindmap = False
        
        try:
            # 将它的父类改成 has_children true
            editor = JsonEditor()
            editor_data = editor.read_node_infos(dir_path)
            editor_data['node']['detail_info']['has_children'] = True
            # 获取到子类最大的值 排序使用
            max_order_num_by_child_dir = editor_data['node']['detail_info']['max_order_num_by_child_dir']
            max_order_num_by_child_dir = max_order_num_by_child_dir + 1
            editor_data['node']['detail_info']['max_order_num_by_child_dir'] = max_order_num_by_child_dir
            meta_path = os.path.join(dir_path, ".metadata.json")
            editor.writeByData(meta_path, editor_data)

            os.makedirs(file_path, exist_ok=False)
            created_folder = True
            
            # 创建思维导图类型的 metadata
            create_metadata_file_under_dir(file_path, content_type='mindmap', order_file_num=max_order_num_by_child_dir)
            created_metadata = True
            
            # 创建空的思维导图文件
            mindmap_path = os.path.join(file_path, "mindmap.json")
            initial_data = {
                "id": "root",
                "text": name,
                "x": 0,
                "y": 0,
                "level": 0,
                "collapsed": False,
                "children": []
            }
            with open(mindmap_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
            created_mindmap = True

            new_item = QTreeWidgetItem()
            new_item.setText(0, name)
            # 使用思维导图图标
            mindmap_icon = QIcon(QPixmap(":images/markdown.png"))
            new_item.setIcon(0, mindmap_icon)
            new_item.setData(0, Qt.UserRole, file_path)
            new_item.setData(0, Qt.UserRole + 1, True)  # 标记"刚创建"
            new_item.setData(0, Qt.UserRole + 2, max_order_num_by_child_dir)  # 设置排序值
            new_item.setFlags(new_item.flags() | Qt.ItemIsEditable)

            item.addChild(new_item)
            item.setExpanded(True)
            # 重新排序
            self.reorder_tree(item)

            self.tree.setCurrentItem(new_item)
            
            # 发送信号通知主窗口打开思维导图编辑器
            self.open_mindmap_editor.emit(file_path)
            
            # 进入编辑模式（延迟执行，确保信号处理完成）
            QTimer.singleShot(100, lambda: self.tree.editItem(new_item, 0))

        except Exception as e:
            # 清理：如果创建过程中失败，删除已创建的文件/文件夹
            import shutil
            if created_folder and os.path.exists(file_path):
                try:
                    shutil.rmtree(file_path)
                except:
                    pass
            QMessageBox.critical(self, "创建失败", f"无法创建思维导图文件:\n{e}")

    def change_tag(data):
        data['node']['detail_info']['tag'] = 'new_tag'  # Add a new field
        return data

    def update_order(self, parent_item):
        editor = JsonEditor()
        non_trash_items = []
        # 收集子节点
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            path = child.data(0, Qt.UserRole)
            if path:
                metadata = editor.read_node_infos(path)
                is_trash = metadata['node']['detail_info'].get('title', '')
                if 'trash' == is_trash:
                    pass
                else:
                    non_trash_items.append(child)

        # 更新 order 值
        for i, child in enumerate(non_trash_items):
            path = child.data(0, Qt.UserRole)
            metadata = editor.read_node_infos(path)
            metadata['node']['detail_info']['order'] = i
            editor.writeByData(os.path.join(path, ".metadata.json"), metadata)
            child.setData(0, Qt.UserRole + 2, i)

        # 重新排序
        self.reorder_tree(parent_item)

    '''重新排序'''
    def reorder_tree(self, parent_item):
        items = []
        editor = JsonEditor()
        for i in range(parent_item.childCount()):
            item = parent_item.child(i)
            path = item.data(0, Qt.UserRole)
            metadata = editor.read_node_infos(path)
            order = metadata['node']['detail_info']['order']
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

        created_folder = False
        
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

            os.makedirs(file_path, exist_ok=False)
            created_folder = True
            
            create_metadata_dir_under_dir(file_path,content_type = 'dir', order_file_num = max_order_num_by_child_dir)

            # 不刷新，而是手动插入新节点
            new_item = QTreeWidgetItem()
            new_item.setText(0, name)
            new_item.setIcon(0, self.folder_closed_icon)
            new_item.setData(0, Qt.UserRole, file_path)
            new_item.setData(0, Qt.UserRole + 1, True)  # 标记刚创建
            new_item.setData(0, Qt.UserRole + 2, max_order_num_by_child_dir)  # 设置排序值
            new_item.setFlags(new_item.flags() | Qt.ItemIsEditable)
            # new_item.addChild(QTreeWidgetItem())  # 懒加载标记

            item.setExpanded(True)
            item.addChild(new_item)
            # 重新排序
            self.reorder_tree(item)

            self.tree.setCurrentItem(new_item)
            self.tree.editItem(new_item, 0)

        except Exception as e:
            # 清理：如果创建过程中失败，删除已创建的文件/文件夹
            import shutil
            if created_folder and os.path.exists(file_path):
                try:
                    shutil.rmtree(file_path)
                except:
                    pass
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
        # Markdown 类型保持自己的图标
        if content_type == "markdown":
            markdown_icon = QIcon(QPixmap(":images/markdown.png"))
            item.setIcon(0, markdown_icon)
            return
        
        # 思维导图类型
        if content_type == "mindmap":
            # 暂时使用 markdown 图标，可以后续添加专门的思维导图图标
            mindmap_icon = QIcon(QPixmap(":images/markdown.png"))
            item.setIcon(0, mindmap_icon)
            return
        
        # 默认文件夹图标
        default_folder_icon = ":images/folder-orange.png"
        
        # 关闭
        if 'collapsed' == exps:
            if content_type == "dir" or content_type == "file" or "lock" in content_type:
                # 安全获取图标，使用 get 方法提供默认值
                colla_icon = detail_infos.get('close_dir_icon', default_folder_icon) if detail_infos else default_folder_icon
                item.setIcon(0, QIcon(QPixmap(colla_icon)))
            else:
                colla_icon = detail_infos.get('adds_on_icon', default_folder_icon) if detail_infos else default_folder_icon
                item.setIcon(0, QIcon(QPixmap(colla_icon)))
        else:
            if content_type == "dir" or content_type == "file" or "lock" in content_type:
                colla_icon = detail_infos.get('open_dir_icon', default_folder_icon) if detail_infos else default_folder_icon
                item.setIcon(0, QIcon(QPixmap(colla_icon)))
            else:
                colla_icon = detail_infos.get('adds_on_icon', default_folder_icon) if detail_infos else default_folder_icon
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
            created_folder = False
            
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
                
                # 检查是否已存在同名文件夹
                if os.path.exists(target_file_path):
                    QMessageBox.warning(self, "创建失败", f"已存在同名文件:\n{file_name}")
                    return
                    
                os.makedirs(target_file_path, exist_ok=False)
                created_folder = True
                
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
                new_item.setData(0, Qt.UserRole + 2, max_order_num_by_child_dir)  # 设置排序值

                item.addChild(new_item)
                item.setExpanded(True)
                # 重新排序
                self.reorder_tree(item)
                self.tree.setCurrentItem(new_item)
                self.tree.editItem(new_item, 0)

            except Exception as e:
                # 清理：如果创建过程中失败，删除已创建的文件/文件夹
                import shutil
                if created_folder and os.path.exists(target_file_path):
                    try:
                        shutil.rmtree(target_file_path)
                    except:
                        pass
                QMessageBox.critical(self, "创建失败", f"无法创建文件:\n{e}")

        else:
            # 取消选择
            pass

    '''拖拽的重写函数'''
    def handle_drop(self, dragged_item, parent_item, target_item, drop_pos):
        # try:
        # 获取父节点路径
        parent_path = self.custom_path if parent_item is None or parent_item == self.tree.invisibleRootItem() else parent_item.data(0, Qt.UserRole)
        # 拖拽的文件路径
        dragged_path = dragged_item.data(0, Qt.UserRole)
        dragged_name = os.path.basename(dragged_path)
        new_path = os.path.join(parent_path, dragged_name)

        # 防止重名
        if os.path.exists(new_path):
            raise ValueError("目标路径已存在同名文件/文件夹")

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

        # 检查源文件夹内容是否为空
        dragget_parent_ = get_parent_path(dragged_path)
        if dragget_parent_:
            flag_ = False
            for item in os.listdir(dragget_parent_):
                # 检查每个项是否为文件夹
                if os.path.isdir(os.path.join(dragget_parent_, item)):
                    flag_ = True
                    break
            # 如果存在不存在文件夹 那么就将这个父类设置为没有子类
            if not flag_:
                dragged_parent_metadata = editor.read_node_infos(dragget_parent_)
                dragged_parent_metadata['node']['detail_info']['has_children'] = False
                editor.writeByData(os.path.join(dragget_parent_, ".metadata.json"), dragged_parent_metadata)

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

        # except Exception as e:
        #     QMessageBox.critical(self, "拖拽失败", f"无法完成拖拽操作:\n{e}")

    # 对当前文件夹进行加密
    def encrypt_item(self, item):
        content_type = ''
        # 获取路径
        base_dir_path = item.data(0, Qt.UserRole)
        
        # 显示密码输入弹框
        password, tip = self._show_encrypt_password_dialog()
        if password is None:
            return  # 用户取消
        
        # 加密
        success, message = FolderEncryptor.encrypt_folder_content(base_dir_path, password)
        
        if not success:
            QMessageBox.critical(self, "加密失败", message)
            return
        
        
        # 保存密码提示到 .metadata.json
        editor = JsonEditor()
        detail_info = editor.read_node_infos(base_dir_path)
        content_type = detail_info['node']['detail_info'].get('content_type', '')
        detail_info['node']['detail_info']['tip'] = tip
        editor.writeByData(os.path.join(base_dir_path, ".metadata.json"), detail_info)

        EXCLUDES = [".metadata.json", "encrypted_data.7z"]


        # 刷新当前文件夹的树状结构
        parent_item = item.parent()
        if parent_item:
            parent_path = parent_item.data(0, Qt.UserRole)
            # 强制刷新树控件
            self.tree.viewport().update()
            # 重新加载子节点
            parent_item.takeChildren()
            self.populate_tree(parent_item, parent_path)
            # 高亮当前节点
            self.tree.setCurrentItem(item)
            self.tree.scrollToItem(item)

        # 3. 清理逻辑
        if base_dir_path:
            for item in os.listdir(base_dir_path):
                if item in EXCLUDES:
                    continue

                full_item_path = os.path.join(base_dir_path, item)
                if os.path.isdir(full_item_path):
                    shutil.rmtree(full_item_path)
                else:
                    os.remove(full_item_path)
        # 发送信号通知主窗口打开 Markdown 编辑器 跟新为空将文件隐藏
        self.open_markdown_editor.emit("")
        self.clear_richtext_editor.emit()

        # 显示加密成功弹框
        EncryptSuccessDialog(self).exec()

    def _show_encrypt_password_dialog(self):
        """显示加密密码输入弹框"""
        dialog = EncryptPasswordDialog(self)
        if dialog.exec():
            return dialog.get_password_data()
        return None, None

    def _show_encrypt_success_dialog(self):
        """显示加密成功弹框"""
        EncryptSuccessDialog(self).exec()

    def refresh_tree_by_path(self, file_path):
        """根据文件路径刷新对应的树节点"""
        # 查找对应路径的树节点
        item = self.find_item_by_path(file_path)
        if item:
            parent_item = item.parent()
            if parent_item:
                parent_path = parent_item.data(0, Qt.UserRole)
                # 记住当前节点名称，用于刷新后重新选中
                item_name = os.path.basename(file_path)
                # 强制刷新树控件
                self.tree.viewport().update()
                # 重新加载子节点
                parent_item.takeChildren()
                self.populate_tree(parent_item, parent_path)
                # 重新查找并高亮当前节点
                new_item = self._find_item_by_name(parent_item, item_name)
                if new_item:
                    self.tree.setCurrentItem(new_item)
                    self.tree.scrollToItem(new_item)

    def _find_item_by_name(self, parent_item, name):
        """根据名称在父节点下查找子节点"""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            child_path = child.data(0, Qt.UserRole)
            if child_path:
                child_name = os.path.basename(child_path)
                # 移除🔐后比较名称
                child_name = child_name.replace("🔐", "").strip()
                name = name.replace("🔐", "").strip()
                if child_name == name:
                    return child
        return None

    def find_item_by_path(self, file_path):
        """根据文件路径查找树节点"""
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            result = self._find_item_recursive(item, file_path)
            if result:
                return result
        return None

    def _find_item_recursive(self, item, file_path):
        """递归查找树节点"""
        item_path = item.data(0, Qt.UserRole)
        if item_path == file_path:
            return item
        for i in range(item.childCount()):
            child = item.child(i)
            result = self._find_item_recursive(child, file_path)
            if result:
                return result
        return None


# ========================
# 自定义右键菜单组件
# 美观的现代风格菜单
# ========================
class ModernContextMenu(QWidget):
    """现代化的右键菜单组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        self.actions = []
        self.hovered_index = -1
        self.item_height = 44
        self.min_width = 220
        
        # 设置鼠标追踪
        self.setMouseTracking(True)

    def add_action(self, icon_text, text, callback, color="#4B5563"):
        """添加菜单项"""
        self.actions.append({
            'icon': icon_text,
            'text': text,
            'callback': callback,
            'color': color,
            'type': 'action'
        })
        
    def add_separator(self):
        """添加分隔线"""
        self.actions.append({'type': 'separator'})
        
    def show_menu(self, pos):
        """显示菜单"""
        # 计算菜单大小
        total_height = 20  # 上下边距
        for action in self.actions:
            if action['type'] == 'separator':
                total_height += 14
            else:
                total_height += self.item_height
        
        self.setFixedSize(self.min_width, total_height)
        self.move(pos)
        self.show()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QFont, QPen, QBrush, QPainterPath, QLinearGradient
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 绘制阴影背景
        shadow_path = QPainterPath()
        shadow_path.addRoundedRect(4, 4, self.width() - 8, self.height() - 8, 16, 16)
        painter.fillPath(shadow_path, QColor(0, 0, 0, 30))
        
        # 绘制渐变背景 - 优雅的浅灰蓝色调
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor("#FAFBFC"))
        gradient.setColorAt(0.5, QColor("#F5F7FA"))
        gradient.setColorAt(1, QColor("#EEF2F7"))
        
        bg_path = QPainterPath()
        bg_path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        painter.fillPath(bg_path, gradient)
        
        # 绘制边框 - 柔和的蓝灰色
        border_pen = QPen(QColor("#D1D5DB"), 1)
        painter.setPen(border_pen)
        painter.drawPath(bg_path)
        
        # 绘制内发光效果
        inner_path = QPainterPath()
        inner_path.addRoundedRect(1, 1, self.width() - 2, self.height() - 2, 15, 15)
        inner_pen = QPen(QColor(255, 255, 255, 180), 1)
        painter.setPen(inner_pen)
        painter.drawPath(inner_path)
        
        # 绘制菜单项
        y = 10
        for i, action in enumerate(self.actions):
            if action['type'] == 'separator':
                # 绘制渐变分隔线
                gradient_line = QLinearGradient(24, 0, self.width() - 24, 0)
                gradient_line.setColorAt(0, QColor("#E5E7EB"))
                gradient_line.setColorAt(0.5, QColor("#D1D5DB"))
                gradient_line.setColorAt(1, QColor("#E5E7EB"))
                pen = QPen(gradient_line, 1)
                painter.setPen(pen)
                painter.drawLine(24, y + 6, self.width() - 24, y + 6)
                y += 14
            else:
                # 绘制悬停背景 - 柔和的蓝紫色渐变
                if i == self.hovered_index:
                    hover_gradient = QLinearGradient(8, y, 8, y + self.item_height - 2)
                    hover_gradient.setColorAt(0, QColor("#EEF2FF"))
                    hover_gradient.setColorAt(1, QColor("#E0E7FF"))
                    hover_path = QPainterPath()
                    hover_path.addRoundedRect(8, y, self.width() - 16, self.item_height - 2, 10, 10)
                    painter.fillPath(hover_path, hover_gradient)
                    
                    # 悬停边框
                    hover_border = QPen(QColor("#C7D2FE"), 1)
                    painter.setPen(hover_border)
                    painter.drawPath(hover_path)
                
                # 绘制图标背景圆圈
                icon_bg_path = QPainterPath()
                icon_bg_path.addRoundedRect(16, y + 8, 26, 26, 6, 6)
                icon_bg_color = QColor(action['color'])
                icon_bg_color.setAlpha(15)
                painter.fillPath(icon_bg_path, icon_bg_color)
                
                # 绘制图标
                icon_font = QFont("Segoe UI Emoji", 13)
                painter.setFont(icon_font)
                painter.setPen(QColor(action['color']))
                painter.drawText(20, y + self.item_height - 14, action['icon'])
                
                # 绘制文字
                text_font = QFont("Microsoft YaHei UI", 10)
                text_font.setWeight(QFont.Medium)
                painter.setFont(text_font)
                if i == self.hovered_index:
                    painter.setPen(QColor("#4F46E5"))
                else:
                    painter.setPen(QColor("#374151"))
                painter.drawText(52, y + self.item_height - 13, action['text'])
                
                y += self.item_height
        
        painter.end()
        
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        y = 8
        for i, action in enumerate(self.actions):
            if action['type'] == 'separator':
                y += 12
            else:
                if y <= event.pos().y() <= y + self.item_height:
                    if self.hovered_index != i:
                        self.hovered_index = i
                        self.update()
                    return
                y += self.item_height
        
        if self.hovered_index != -1:
            self.hovered_index = -1
            self.update()
            
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        y = 8
        for i, action in enumerate(self.actions):
            if action['type'] == 'separator':
                y += 12
            else:
                if y <= event.pos().y() <= y + self.item_height:
                    self.hide()
                    if action['callback']:
                        action['callback']()
                    return
                y += self.item_height
        self.hide()
        
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.hovered_index = -1
        self.update()


# ========================
# Windows-style context menu QSS
# 右键点击的样式 放在这个主要是为了维护的时候简单
# ========================
WINDOWS_MENU_STYLE = """
QMenu {
    background-color: #ffffff;
    border: none;
    padding: 10px 8px;
    border-radius: 16px;
    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
    font-size: 14px;
    font-weight: 400;
}
QMenu::item {
    padding: 10px 20px 10px 16px;
    margin: 3px 4px;
    background-color: transparent;
    border-radius: 10px;
    color: #1F2937;
    letter-spacing: 0.5px;
}
QMenu::item:selected {
    background-color: #EEF2FF;
    color: #4F46E5;
}
QMenu::item:disabled {
    color: #9CA3AF;
}
QMenu::separator {
    height: 1px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(229, 231, 235, 0), 
        stop:0.2 rgba(229, 231, 235, 1), 
        stop:0.8 rgba(229, 231, 235, 1), 
        stop:1 rgba(229, 231, 235, 0));
    margin: 8px 16px 8px 16px;
}
QMenu::icon {
    padding-left: 4px;
    padding-right: 10px;
}
QMenu::indicator {
    width: 18px;
    height: 18px;
    margin-left: 6px;
}
"""


# ========================
# Toast 通知组件
# 美观的消息提示弹框
# ========================
class ToastWidget(QWidget):
    """美观的 Toast 通知组件"""
    
    # 定义类型常量
    SUCCESS = "success"
    WARNING = "warning"  
    ERROR = "error"
    INFO = "info"
    
    def __init__(self, message, toast_type="success", parent=None, duration=2000):
        super().__init__(parent)
        self.duration = duration
        self.toast_type = toast_type
        
        # 设置窗口属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # 设置固定宽度
        self.setFixedWidth(320)
        self.setMinimumHeight(60)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # 创建内容容器
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)
        
        # 图标标签
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.icon_label)
        
        # 消息标签
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        content_layout.addWidget(self.message_label, 1)
        
        layout.addWidget(content_widget)
        
        # 设置样式和图标
        self._setup_style()
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        # 透明度动画
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)
        
        # 动画
        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(200)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(200)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_out_animation.finished.connect(self.close)
        
        # 自动关闭定时器
        self.close_timer = QTimer()
        self.close_timer.setSingleShot(True)
        self.close_timer.timeout.connect(self._start_fade_out)
    
    def _setup_style(self):
        """设置样式"""
        styles = {
            "success": {
                "bg": "#10B981",
                "text": "#FFFFFF",
                "icon": "✓"
            },
            "warning": {
                "bg": "#F59E0B", 
                "text": "#FFFFFF",
                "icon": "⚠"
            },
            "error": {
                "bg": "#EF4444",
                "text": "#FFFFFF", 
                "icon": "✕"
            },
            "info": {
                "bg": "#3B82F6",
                "text": "#FFFFFF",
                "icon": "ℹ"
            }
        }
        
        style = styles.get(self.toast_type, styles["success"])
        
        # 设置背景样式
        self.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
            }}
            QLabel {{
                background-color: transparent;
            }}
        """)
        
        # 设置内容容器样式
        content_widget = self.findChild(QWidget)
        if content_widget:
            content_widget.setStyleSheet(f"""
                QWidget {{
                    background-color: {style['bg']};
                    border-radius: 12px;
                }}
            """)
        
        # 设置图标
        self.icon_label.setText(style['icon'])
        self.icon_label.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                color: {style['text']};
                font-size: 14px;
                font-weight: bold;
            }}
        """)
        
        # 设置消息文本
        self.message_label.setStyleSheet(f"""
            QLabel {{
                color: {style['text']};
                font-size: 13px;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                background-color: transparent;
            }}
        """)
    
    def show_toast(self):
        """显示 Toast"""
        # 调整大小
        self.adjustSize()
        
        # 获取主窗口
        main_window = QApplication.activeWindow()
        if main_window:
            # 在主窗口右下角显示
            main_window_rect = main_window.geometry()
            x = main_window_rect.x() + main_window_rect.width() - self.width() - 20
            y = main_window_rect.y() + main_window_rect.height() - self.height() - 50
        else:
            # 备用：屏幕右下角
            screen = QApplication.primaryScreen()
            if screen:
                screen_rect = screen.availableGeometry()
                x = screen_rect.width() - self.width() - 20
                y = screen_rect.height() - self.height() - 80
            else:
                x = 100
                y = 100
        
        self.move(x, y)
        self.show()
        
        # 开始淡入动画
        self.fade_in_animation.start()
        
        # 启动自动关闭定时器
        self.close_timer.start(self.duration)
    
    def _start_fade_out(self):
        """开始淡出动画"""
        self.fade_out_animation.start()


def show_toast(parent, message, toast_type="success", duration=2000):
    """显示 Toast 通知的便捷函数"""
    toast = ToastWidget(message, toast_type, parent, duration)
    toast.show_toast()
    return toast

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
