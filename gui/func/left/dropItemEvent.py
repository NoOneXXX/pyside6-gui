
'''
树的拖拽事件重写
将拖拽后的文件进行持久化
'''

from PySide6.QtWidgets import QTreeWidget

class CustomTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.notebook_tree = None  # 存储 XPNotebookTree 实例

    def dropEvent(self, event):
        # 获取拖拽的节点
        dragged_item = self.currentItem()
        if not dragged_item:
            event.ignore()
            return

        # 获取目标父节点和放置位置
        drop_pos = self.dropIndicatorPosition()
        target_item = self.itemAt(event.pos())
        parent_item = target_item.parent() if target_item and drop_pos in (QTreeWidget.AboveItem, QTreeWidget.BelowItem) else target_item
        if parent_item is None:
            parent_item = self.invisibleRootItem()

        # 调用 XPNotebookTree 的 handle_drop 方法
        if self.notebook_tree:
            self.notebook_tree.handle_drop(dragged_item, parent_item, target_item, drop_pos)

        event.accept()