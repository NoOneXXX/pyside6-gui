from PySide6.QtWidgets import (
    QApplication, QWidget, QTextEdit, QPushButton, QVBoxLayout, QColorDialog
)
from PySide6.QtGui import QTextCharFormat, QTextCursor, QColor, QAction, QIcon, QKeySequence
import sys
from gui.ui import resource_rc
class RichTextColor(QWidget):
    def __init__(self, text_edit=None):
        super().__init__()
        self.text_edit = text_edit

    def change_text_color(self):
        print("点击颜色按钮")
        if not self.text_edit:
            print("text_edit 未绑定")
            return

        color: QColor = QColorDialog.getColor()
        if not color.isValid():
            return  # 用户点击取消

        cursor: QTextCursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            return  # 没有选中文本，不做处理

        fmt = QTextCharFormat()
        fmt.setForeground(color)
        cursor.mergeCharFormat(fmt)

        self.text_edit.mergeCurrentCharFormat(fmt)  # 确保后续输入的字符也使用该颜色

    '''
    颜色选择
    '''
    def color_picker_action(self, parent=None):
        print("[DEBUG] 正在创建 color_picker_action")
        print("[DEBUG] 当前绑定的 text_edit：", self.text_edit)
        self.edit_color_action = QAction(
            QIcon(":/images/edit-color.png"),
            "editColor",
            parent,
        )
        self.edit_color_action.setStatusTip("editColor")
        self.edit_color_action.setCheckable(False)
        self.edit_color_action.triggered.connect(self.change_text_color)
        return self.edit_color_action



if __name__ == "__main__":
    app = QApplication(sys.argv)

    test_icon = QIcon(":/images/edit-color.png")
    print("icon is null:", test_icon.isNull())

    # 不显示窗口，也可以
    sys.exit(0)
