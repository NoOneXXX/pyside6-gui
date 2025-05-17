from PySide6.QtCore import QObject, QSize, Qt, QPoint
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor, QIcon
from PySide6.QtWidgets import (
    QToolButton, QDialog, QVBoxLayout, QPushButton,
    QGridLayout, QFrame, QColorDialog
)

'''
颜色的选择
'''
class ColorPickerTool(QObject):
    def __init__(self, text_edit, parent=None):
        super().__init__(parent)
        self.text_edit = text_edit

        self.tool_button = QToolButton(parent)
        self.tool_button.setIcon(QIcon(":/images/edit-color.png"))
        self.tool_button.setToolTip("Text Color")
        self.tool_button.setAutoRaise(True)
        self.tool_button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.tool_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")
        self.tool_button.clicked.connect(self.show_color_popup)

    def show_color_popup(self):
        popup = QDialog(self.tool_button)
        popup.setWindowFlags(Qt.Popup)
        popup.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(popup)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(2)

        # Default Color
        btn_default = QPushButton("Default Color")
        btn_default.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                padding: 4px 6px;
                color: #444;
                font-size: 12px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
                border-radius: 4px;
            }
        """)
        btn_default.clicked.connect(lambda: self.set_text_color_and_close("#000000", popup))
        layout.addWidget(btn_default)

        # New Color...
        btn_new_color = QPushButton("New Color…")
        btn_new_color.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                padding: 4px 6px;
                color: #444;
                font-size: 12px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
                border-radius: 4px;
            }
        """)
        btn_new_color.clicked.connect(lambda: self.open_color_dialog_and_close(popup))
        layout.addWidget(btn_new_color)

        # Color grid
        color_grid = QFrame()
        grid_layout = QGridLayout(color_grid)
        grid_layout.setSpacing(4)
        grid_layout.setContentsMargins(0, 0, 0, 0)

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
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 1px solid #aaa;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    border: 1px solid #333;
                }}
            """)
            btn.clicked.connect(lambda _, c=color: self.set_text_color_and_close(c, popup))
            grid_layout.addWidget(btn, i // 6, i % 6)

        layout.addWidget(color_grid)
        popup.adjustSize()
        popup.move(self.tool_button.mapToGlobal(QPoint(0, self.tool_button.height())))
        popup.exec()

    def set_text_color_and_close(self, color_code, dialog):
        self.set_text_color(color_code)
        dialog.accept()

    def open_color_dialog_and_close(self, dialog):
        color = QColorDialog.getColor()
        if color.isValid():
            self.set_text_color(color.name())
        dialog.accept()

    def set_text_color(self, color_code):
        if not self.text_edit:
            return
        cursor: QTextCursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            return
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color_code))
        cursor.mergeCharFormat(fmt)
        self.text_edit.mergeCurrentCharFormat(fmt)
