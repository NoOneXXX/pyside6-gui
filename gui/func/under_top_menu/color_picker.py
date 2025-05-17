from PySide6.QtWidgets import (
    QWidget, QMenu, QPushButton, QGridLayout, QWidgetAction,
    QColorDialog, QToolButton
)
from PySide6.QtGui import QTextCharFormat, QTextCursor, QColor, QIcon, QAction
from PySide6.QtCore import QSize, Qt

'''
富文本框的颜色选择
'''
class ColorPickerTool(QWidget):
    def __init__(self, text_edit, parent=None):
        super().__init__(parent)
        self.text_edit = text_edit
        self.color_menu = QMenu(parent)
        self._build_color_menu()

        self.action = QAction(QIcon(":/images/edit-color.png"), "Text Color", self)
        self.action.setStatusTip("Choose text color")
        self.action.triggered.connect(self.show_menu)

        # 工具栏按钮
        self.tool_button = QToolButton(parent)
        self.tool_button.setIcon(self.action.icon())
        self.tool_button.setToolTip(self.action.text())
        self.tool_button.setPopupMode(QToolButton.InstantPopup)
        self.tool_button.setMenu(self.color_menu)
        self.tool_button.setAutoRaise(True)
        self.tool_button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.tool_button.setDefaultAction(self.action)
        # 删掉这个按钮自带的向下角标
        self.tool_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")

    def _build_color_menu(self):
        # 默认颜色
        default_action = self.color_menu.addAction("Default Color")
        default_action.triggered.connect(lambda: self.set_text_color("#000000"))

        # 自定义颜色
        custom_action = self.color_menu.addAction("New Color...")
        custom_action.triggered.connect(self.pick_custom_color)

        self.color_menu.addSeparator()

        # 网格颜色块
        color_grid_widget = QWidget()
        grid_layout = QGridLayout(color_grid_widget)
        grid_layout.setSpacing(4)
        grid_layout.setContentsMargins(5, 5, 5, 5)

        colors = [
            "#F4CCCC", "#FFF2CC", "#D9EAD3", "#CFE2F3", "#D9D2E9", "#EAD1DC",
            "#EA9999", "#F9CB9C", "#B6D7A8", "#A2C4C9", "#B4A7D6", "#D5A6BD",
            "#E06666", "#F6B26B", "#93C47D", "#76A5AF", "#8E7CC3", "#C27BA0",
            "#CC0000", "#E69138", "#6AA84F", "#45818E", "#674EA7", "#A64D79",
            "#990000", "#B45F06", "#38761D", "#134F5C", "#351C75", "#741B47",
            "#000000", "#434343", "#666666", "#999999", "#CCCCCC", "#FFFFFF"
        ]

        for i, color in enumerate(colors):
            btn = QPushButton()
            btn.setFixedSize(QSize(24, 24))
            btn.setStyleSheet(f"background-color: {color}; border: 1px solid #aaa;")
            btn.clicked.connect(lambda _, c=color: self.set_text_color(c))
            grid_layout.addWidget(btn, i // 6, i % 6)

        grid_action = QWidgetAction(self.color_menu)
        grid_action.setDefaultWidget(color_grid_widget)
        self.color_menu.addAction(grid_action)

    def set_text_color(self, color_code):
        if not self.text_edit:
            return
        color = QColor(color_code)
        cursor: QTextCursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            return
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        cursor.mergeCharFormat(fmt)
        self.text_edit.mergeCurrentCharFormat(fmt)

    def pick_custom_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.set_text_color(color.name())

    def show_menu(self):
        if self.tool_button and self.color_menu:
            pos = self.tool_button.mapToGlobal(self.tool_button.rect().bottomLeft())
            self.color_menu.popup(pos)
