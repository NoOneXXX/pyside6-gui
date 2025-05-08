import sys
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QPainter, QFont, QPen, QColor
from PySide6.QtCore import QRect, Qt


class TreeNode:
    def __init__(self, text, children=None, expanded=True):
        self.text = text
        self.children = children or []
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
        self.setMinimumWidth(400)
        self.setMinimumHeight(600)
        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(self.font)
        self._draw_node(painter, self.root, 0, 10)

    def _draw_node(self, painter, node, depth, y):
        x = depth * self.indent
        node.rect = QRect(x, y, 300, self.node_height)

        mid_y = y + self.node_height // 2
        mid_x = x - self.indent // 2

        # 🎯 XP 风格虚线画笔
        pen = QPen(QColor(160, 160, 160), 1, Qt.DotLine)
        painter.setPen(pen)

        # ✅ 横线连接文字
        if node.parent:
            painter.drawLine(mid_x, mid_y, x, mid_y)

        # ✅ 父级竖线延伸
        ancestor = node.parent
        ancestor_depth = depth - 1
        while ancestor:
            if not self._is_last_sibling(ancestor):
                ax = ancestor_depth * self.indent + self.indent // 2
                painter.drawLine(ax, y, ax, y + self.node_height)
            ancestor = ancestor.parent
            ancestor_depth -= 1

        # ✅ 当前节点竖线
        if node.parent and not self._is_last_sibling(node):
            painter.drawLine(mid_x, mid_y, mid_x, y + self.node_height)

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

        # ✅ 节点文字
        painter.setPen(Qt.black)
        painter.drawText(x + 16, y + 15, node.text)

        y += self.node_height
        if node.expanded:
            for child in node.children:
                y = self._draw_node(painter, child, depth + 1, y)
        return y

    def _is_last_sibling(self, node):
        if not node.parent:
            return True
        return node == node.parent.children[-1]

    def mousePressEvent(self, event):
        if self._toggle_node(self.root, event.pos()):
            self.update()

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
