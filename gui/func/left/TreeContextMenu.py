"""
树控件右键菜单功能封装
提供右键菜单的创建和管理，包含字体颜色设置功能
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt


class TreeContextMenuManager:
    """树控件右键菜单管理器"""
    
    def __init__(self, tree_widget):
        """
        初始化菜单管理器
        
        Args:
            tree_widget: XPNotebookTree 实例
        """
        self.tree_widget = tree_widget
        
    def create_context_menu(self, item, content_type, detail_info, is_trash_folder=False, 
                           is_in_trash=False, is_attachment=False):
        """
        创建右键菜单
        
        Args:
            item: 树节点项
            content_type: 内容类型
            detail_info: 详细信息
            is_trash_folder: 是否是回收站文件夹
            is_in_trash: 是否在回收站内
            is_attachment: 是否是附件
            
        Returns:
            ModernContextMenu: 创建的菜单实例
        """
        from gui.func.left.XPNotebookTree import ModernContextMenu
        
        menu = ModernContextMenu(self.tree_widget)
        
        # 添加公共菜单项
        def add_common_actions():
            """添加所有节点通用的右键菜单"""
            menu.add_action("📂", "打开", lambda: self.tree_widget.open_item(item), "#3B82F6")
            menu.add_action("✏", "重命名", lambda: self.tree_widget.rename_item(item), "#F59E0B")
            menu.add_separator()
            # 添加设置字体颜色选项
            menu.add_action("🎨", "设置字体颜色", 
                          lambda: self.tree_widget.set_item_font_color(item), "#EC4899")
            menu.add_separator()
            menu.add_action("📝", "创建 Markdown", 
                          lambda: self.tree_widget.create_markdown_file(item), "#6366F1")
            menu.add_action("🧠", "创建思维导图", 
                          lambda: self.tree_widget.create_mindmap_file(item), "#9B59B6")
            menu.add_action("📄", "创建子文件", 
                          lambda: self.tree_widget.create_file_item(item), "#10B981")
            menu.add_action("📁", "创建文件夹", 
                          lambda: self.tree_widget.create_dir_action(item), "#8B5CF6")
            menu.add_action("📎", "添加附件", 
                          lambda: self.tree_widget.adds_on_item(item), "#06B6D4")
            menu.add_separator()
            menu.add_action("🔐", "加密", 
                          lambda: self.tree_widget.encrypt_item(item), "#06B6D4")
            menu.add_action("🗑", "删除", 
                          lambda: self.tree_widget.delete_item(item), "#EF4444")
        
        # 根据类型显示菜单
        if is_trash_folder:
            # 回收站根目录：仅清空
            menu.add_action("🗑", "清空回收站", 
                          lambda: self.tree_widget.empty_trash(item), "#EF4444")
            
        elif is_in_trash:
            # 回收站内部：永久删除 + 恢复
            menu.add_action("☠", "永久删除", 
                          lambda: self.tree_widget.permanent_delete_item(item), "#DC2626")
            menu.add_action("↩", "恢复文件", 
                          lambda: self.tree_widget.restore_item(item), "#10B981")
            
        elif is_attachment:
            # 附件：额外加"复制附件"，其他通用
            menu.add_action("📋", "复制附件", 
                          lambda: self.tree_widget.copy_attachment(item), "#8B5CF6")
            add_common_actions()
            
        else:
            # 普通文件/文件夹：全量通用菜单
            add_common_actions()
            
        return menu


class FontColorManager:
    """字体颜色管理器"""
    
    # 默认15种颜色
    DEFAULT_COLORS = [
        "#000000",  # 黑色
        "#FF0000",  # 红色
        "#00FF00",  # 绿色
        "#0000FF",  # 蓝色
        "#FFFF00",  # 黄色
        "#FF00FF",  # 紫色
        "#00FFFF",  # 青色
        "#FFA500",  # 橙色
        "#5500FF",  # 深紫
        "#FFC0CB",  # 粉色
        "#A52A2A",  # 棕色
        "#808080",  # 灰色
        "#008000",  # 深绿
        "#800000",  # 深红
        "#000080",  # 深蓝
    ]
    
    def __init__(self, tree_widget):
        """
        初始化字体颜色管理器
        
        Args:
            tree_widget: XPNotebookTree 实例
        """
        self.tree_widget = tree_widget
        self.custom_colors = self.DEFAULT_COLORS.copy()
        
    def show_color_picker(self, item, current_color=""):
        """
        显示颜色选择器并处理颜色设置
        
        Args:
            item: 树节点项
            current_color: 当前颜色（十六进制）
            
        Returns:
            bool: 是否成功设置颜色
        """
        from gui.func.left.ColorPickerDialog import show_color_picker
        from gui.func.utils.json_utils import JsonEditor
        from gui.func.left.XPNotebookTree import show_toast, ToastWidget
        import os
        
        # 获取当前颜色
        if not current_color:
            item_path = item.data(0, Qt.UserRole)
            if item_path:
                editor = JsonEditor()
                detail_info = editor.read_file_metadata_infos(item_path)
                if detail_info:
                    current_color = detail_info.get('font_color', '')
                    
        if not current_color:
            current_color = "#000000"
            
        # 显示颜色选择器
        confirmed, selected_color, new_custom_colors = show_color_picker(
            parent=self.tree_widget,
            current_color=current_color,
            custom_colors=self.custom_colors
        )
        
        if confirmed:
            # 更新自定义颜色列表
            self.custom_colors = new_custom_colors
            
            # 保存颜色到 metadata.json
            success = self._save_font_color(item, selected_color)
            
            if success:
                # 更新树节点显示
                from PySide6.QtGui import QColor
                item.setForeground(0, QColor(selected_color))
                show_toast(self.tree_widget, f"字体颜色已更新", ToastWidget.SUCCESS)
                return True
            else:
                show_toast(self.tree_widget, "保存颜色失败", ToastWidget.ERROR)
                return False
                
        return False
        
    def _save_font_color(self, item, color_hex):
        """
        保存字体颜色到 metadata.json
        
        Args:
            item: 树节点项
            color_hex: 十六进制颜色值
            
        Returns:
            bool: 是否保存成功
        """
        from gui.func.utils.json_utils import JsonEditor
        import os
        
        try:
            item_path = item.data(0, Qt.UserRole)
            if not item_path:
                return False
                
            editor = JsonEditor()
            metadata = editor.read_node_infos(item_path)
            
            if metadata and 'node' in metadata:
                # 确保 detail_info 存在
                if 'detail_info' not in metadata['node']:
                    metadata['node']['detail_info'] = {}
                    
                # 设置字体颜色
                metadata['node']['detail_info']['font_color'] = color_hex
                
                # 写入文件
                meta_path = os.path.join(item_path, ".metadata.json")
                editor.writeByData(meta_path, metadata)
                return True
                
        except Exception as e:
            print(f"保存字体颜色失败: {e}")
            
        return False
        
    def get_font_color(self, item_path):
        """
        获取节点的字体颜色
        
        Args:
            item_path: 节点路径
            
        Returns:
            str: 十六进制颜色值，如果不存在返回默认黑色
        """
        from gui.func.utils.json_utils import JsonEditor
        
        try:
            editor = JsonEditor()
            detail_info = editor.read_file_metadata_infos(item_path)
            if detail_info:
                font_color = detail_info.get('font_color', '')
                if font_color and font_color.strip():
                    return font_color
        except Exception as e:
            print(f"获取字体颜色失败: {e}")
            
        return "#000000"
        
    def reset_to_default(self, item):
        """
        重置字体颜色为默认（黑色）
        
        Args:
            item: 树节点项
            
        Returns:
            bool: 是否重置成功
        """
        return self._save_font_color(item, "#000000")


# 便捷函数
def create_tree_context_menu(tree_widget, item, content_type, detail_info, 
                             is_trash_folder=False, is_in_trash=False, is_attachment=False):
    """
    创建树控件右键菜单的便捷函数
    
    Args:
        tree_widget: XPNotebookTree 实例
        item: 树节点项
        content_type: 内容类型
        detail_info: 详细信息
        is_trash_folder: 是否是回收站文件夹
        is_in_trash: 是否在回收站内
        is_attachment: 是否是附件
        
    Returns:
        ModernContextMenu: 创建的菜单实例
    """
    manager = TreeContextMenuManager(tree_widget)
    return manager.create_context_menu(item, content_type, detail_info, 
                                       is_trash_folder, is_in_trash, is_attachment)


def show_font_color_picker(tree_widget, item, current_color=""):
    """
    显示字体颜色选择器的便捷函数
    
    Args:
        tree_widget: XPNotebookTree 实例
        item: 树节点项
        current_color: 当前颜色（十六进制）
        
    Returns:
        bool: 是否成功设置颜色
    """
    manager = FontColorManager(tree_widget)
    return manager.show_color_picker(item, current_color)
