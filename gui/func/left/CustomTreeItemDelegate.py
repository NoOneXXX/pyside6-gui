from PySide6.QtWidgets import QStyledItemDelegate, QLineEdit, QStyle
from PySide6.QtGui import (QColor, QFont, QPen, QPainter, QPainterPath, QBrush,
                            QLinearGradient, QRadialGradient)
from PySide6.QtCore import Qt, QRect, QRectF

'''
这个是控制左边的树的边框高度，并支持根节点路径灰色显示
以及搜索匹配度的气泡徽章绘制
'''
class CustomTreeItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setMinimumHeight(23)
        editor.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                padding: 0px;
                border: 1px solid #3A8EDB;
                border-radius: 6px;
                background-color: white;
            }
        """)
        return editor

    def paint(self, painter, option, index):
        tree = self.parent()
        if tree:
            item = tree.itemFromIndex(index)
            if item:
                # 检查是否有搜索匹配度数据
                score_percent = item.data(0, Qt.UserRole + 11)
                badge_color_hex = item.data(0, Qt.UserRole + 12)

                if score_percent is not None and badge_color_hex:
                    super().paint(painter, option, index)
                    self._paint_match_badge(painter, tree, item, score_percent, badge_color_hex)
                    return

                # 根节点路径灰色显示
                if item.parent() is None:
                    path_text = item.data(0, Qt.UserRole + 3)
                    if path_text:
                        super().paint(painter, option, index)
                        painter.save()
                        item_rect = tree.visualItemRect(item)
                        name_text = item.text(0)
                        font = item.font(0)
                        painter.setFont(font)
                        fm = painter.fontMetrics()
                        name_width = fm.horizontalAdvance(name_text)
                        path_color = QColor("#9CA3AF")
                        painter.setPen(QPen(path_color))
                        path_font = QFont(font)
                        path_font.setBold(False)
                        path_font.setPointSize(10)
                        painter.setFont(path_font)
                        path_x = item_rect.left() + name_width + 26
                        path_y = item_rect.top() + (item_rect.height() + painter.fontMetrics().ascent() - painter.fontMetrics().descent()) // 2
                        painter.drawText(path_x, path_y, path_text)
                        painter.restore()
                        return

        # 默认绘制
        super().paint(painter, option, index)

    def _paint_match_badge(self, painter, tree, item, score_percent, badge_color_hex):
        """
        绘制匹配度气泡徽章
        在文件名右侧显示一个精致的圆角胶囊气泡，内含百分比数字

        Args:
            painter: QPainter
            tree: QTreeWidget
            item: QTreeWidgetItem
            score_percent: 匹配度百分比（如 65.0）
            badge_color_hex: 徽章颜色十六进制（如 "#FF6B6B"）
        """
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        # ---- 1. 计算位置 ----
        item_rect = tree.visualItemRect(item)
        name_text = item.text(0)
        font = item.font(0)

        # 文件名宽度
        painter.setFont(font)
        name_width = painter.fontMetrics().horizontalAdvance(name_text)

        # ---- 2. 徽章文字与尺寸 ----
        badge_text = f"{int(score_percent)}%"
        badge_font = QFont(font.family(), max(font.pointSize() - 1, 9), QFont.Bold)
        painter.setFont(badge_font)
        badge_fm = painter.fontMetrics()

        # 用 boundingRect 精确测量文字宽高
        text_br = badge_fm.boundingRect(badge_text)
        text_w = text_br.width()
        text_h = badge_fm.ascent() + badge_fm.descent()

        # 气泡尺寸：确保数字和百分号都完整在内部
        h_pad = 8    # 水平内边距
        v_pad = 3    # 垂直内边距
        badge_w = max(text_w + h_pad * 2, 36)   # 最小宽度36，保证美观
        badge_h = text_h + v_pad * 2

        # 气泡位置：文件名右侧 + 间距
        gap = 8
        badge_x = item_rect.left() + name_width + 24 + gap  # 24 = 图标区
        badge_y = item_rect.top() + (item_rect.height() - badge_h) / 2

        badge_color = QColor(badge_color_hex)

        # ---- 3. 绘制阴影 ----
        shadow_rect = QRectF(badge_x + 0.5, badge_y + 1.5, badge_w, badge_h)
        shadow_path = QPainterPath()
        shadow_path.addRoundedRect(shadow_rect, badge_h / 2, badge_h / 2)
        painter.fillPath(shadow_path, QColor(0, 0, 0, 25))

        # ---- 4. 绘制气泡主体（渐变填充，从上到下稍深） ----
        badge_rect = QRectF(badge_x, badge_y, badge_w, badge_h)
        radius = badge_h / 2

        gradient = QLinearGradient(badge_rect.topLeft(), badge_rect.bottomLeft())
        # 顶部略亮
        lighter = badge_color.lighter(115)
        gradient.setColorAt(0.0, lighter)
        gradient.setColorAt(1.0, badge_color)

        bubble_path = QPainterPath()
        bubble_path.addRoundedRect(badge_rect, radius, radius)
        painter.fillPath(bubble_path, gradient)

        # ---- 5. 顶部高光弧线（玻璃质感） ----
        highlight_path = QPainterPath()
        hl_h = badge_h * 0.45
        highlight_rect = QRectF(badge_x + 2, badge_y + 1, badge_w - 4, hl_h)
        highlight_path.addRoundedRect(highlight_rect, hl_h / 2, hl_h / 2)
        painter.fillPath(highlight_path, QColor(255, 255, 255, 55))

        # ---- 6. 细微描边，增加精致感 ----
        painter.setPen(QPen(badge_color.darker(120), 0.5))
        painter.drawPath(bubble_path)

        # ---- 7. 绘制文字（白色，绝对居中） ----
        painter.setFont(badge_font)
        painter.setPen(QPen(QColor("#FFFFFF")))
        # 用 QRectF + AlignCenter 保证文字完全居中在气泡内
        painter.drawText(badge_rect, Qt.AlignCenter, badge_text)

        painter.restore()
