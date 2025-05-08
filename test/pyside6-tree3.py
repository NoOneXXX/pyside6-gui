import sys
from PySide6.QtWidgets import QApplication, QWidget, QStyle
from PySide6.QtGui import QPainter, QFont, QPen, QColor, QIcon
from PySide6.QtCore import QRect, Qt, QSize


class TreeNode:
    def __init__(self, text, children=None, icon_type="folder", expanded=True):
        self.text = text
        self.children = children or []
        self.icon_type = icon_type  # "folder", "file", "dot"
        self.expanded = expanded
        self.parent = None
        for child in self.children:
            child.parent = self
        self.rect = QRect()


class TreeWidget(QWidget):
    def __init__(self, root):
        super().__init__()
        self.root = root
        self.node_height = 20
        self.indent = 20
        self.font = QFont("Arial", 10)
        self.setMinimumWidth(500)
        self.setMinimumHeight(800)
        self.setMouseTracking(True)

        style = self.style()
        self.icon_folder_closed = style.standardIcon(QStyle.SP_DirClosedIcon)
        self.icon_folder_open = style.standardIcon(QStyle.SP_DirOpenIcon)
        self.icon_file = style.standardIcon(QStyle.SP_FileIcon)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(self.font)
        self._draw_node(painter, self.root, 0, 10, is_first_root=True)

    def _draw_node(self, painter, node, depth, y, is_first_root=False):
        x = depth * self.indent
        node.rect = QRect(x, y, 300, self.node_height)
        mid_y = y + self.node_height // 2
        mid_x = x - self.indent // 2

        # 🎯 灰色点状线条
        painter.setPen(QPen(QColor(160, 160, 160), 1, Qt.DotLine))

        # ✅ 为所有“非最后兄弟”的祖先绘制贯穿列线
        # ✅ 绘制每一列是否要垂直延伸（XP风格核心）
        current = node
        for d in range(depth):
            ancestor = self._get_ancestor_at_depth(current, depth - d - 1)
            if ancestor and not self._is_last_sibling(ancestor):
                ax = d * self.indent + self.indent // 2
                painter.drawLine(ax, y, ax, y + self.node_height)

        # ✅ 当前节点竖线（非最左根节点 & 非最后兄弟）
        if node.parent and not is_first_root:
            painter.drawLine(mid_x, mid_y, mid_x, y + self.node_height)

        # ✅ 横线（从父竖线连到图标左）
        if node.parent and not is_first_root:
            painter.drawLine(mid_x, mid_y, x, mid_y)

        # ✅ 加减框
        if node.children:
            box_size = 9
            box_x = mid_x - box_size // 2
            box_y = mid_y - box_size // 2
            painter.setPen(QColor(102, 102, 102))
            painter.setBrush(QColor(255, 255, 255))
            painter.drawRect(box_x, box_y, box_size, box_size)
            painter.drawLine(box_x + 2, mid_y, box_x + box_size - 2, mid_y)
            if not node.expanded:
                painter.drawLine(mid_x, box_y + 2, mid_x, box_y + box_size - 2)

        # ✅ 图标（文件夹 / 文件 / 圆点）
        icon = None
        icon_x = x
        if node.icon_type == "folder":
            icon = self.icon_folder_open if node.expanded else self.icon_folder_closed
        elif node.icon_type == "file":
            icon = self.icon_file

        if icon:
            icon.paint(painter, icon_x, y + 2, 16, 16)
        elif node.icon_type == "dot":
            painter.setBrush(QColor(0, 120, 215))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(icon_x + 4, y + 6, 8, 8)

        # ✅ 文本（图标右侧 4px）
        painter.setPen(Qt.black)
        painter.drawText(icon_x + 20, y + 15, node.text)

        # ✅ 递归子节点
        y += self.node_height
        if node.expanded:
            for idx, child in enumerate(node.children):
                y = self._draw_node(painter, child, depth + 1, y)
        return y

    def _is_last_sibling(self, node):
        if not node.parent:
            return True
        return node == node.parent.children[-1]

    def mousePressEvent(self, event):
        if self._toggle_node(self.root, event.pos()):
            self.update()

    def _get_ancestor_at_depth(self, node, target_depth):
        current = node
        while current and self._get_depth(current) > target_depth:
            current = current.parent
        return current

    def _get_depth(self, node):
        d = 0
        while node.parent:
            d += 1
            node = node.parent
        return d

    def _toggle_node(self, node, pos):
        x = node.rect.left()
        mid_y = node.rect.center().y()
        box_size = 9
        box_x = x - self.indent // 2 - box_size // 2
        box_rect = QRect(box_x, mid_y - box_size // 2, box_size, box_size)

        if node.children and box_rect.contains(pos):
            node.expanded = not node.expanded
            return True

        if node.expanded:
            for child in node.children:
                if self._toggle_node(child, pos):
                    return True
        return False



if __name__ == "__main__":
    app = QApplication(sys.argv)

    tree = TreeNode("Page", [
        TreeNode("Top"),
        TreeNode("Statics", [
            TreeNode("Pre", [
                TreeNode("Top"),
                TreeNode("Text-style"),
                TreeNode("Group (header)", [
                    TreeNode("Top"),
                    TreeNode("Box"),
                    TreeNode("Line"),
                    TreeNode("Line"),
                    TreeNode("If (PAGE=1)"),
                    TreeNode("If (PAGE<>1)", [
                        TreeNode("Top"),
                        TreeNode("Offset-style"),
                        TreeNode("Include"),
                        TreeNode("Offset-style"),
                        TreeNode("Include"),
                    ]),
                ]),
            ]),
        ]),
        TreeNode("Post")
    ])

    widget = TreeWidget(tree)
    widget.setWindowTitle("🖋️ 手绘 XP 风格树结构")
    widget.show()

    sys.exit(app.exec())
