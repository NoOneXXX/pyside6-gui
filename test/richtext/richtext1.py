import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QToolBar,
    QFileDialog, QColorDialog
)
from PySide6.QtGui import QTextCharFormat, QFont, QTextCursor, QColor
from PySide6.QtCore import Qt
from datetime import datetime

class RichTextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("富文本编辑器 Demo")
        self.resize(800, 600)

        # 编辑器核心
        self.editor = QTextEdit()
        self.setCentralWidget(self.editor)

        # 工具栏
        toolbar = QToolBar("格式")
        self.addToolBar(toolbar)

        toolbar.addAction("加粗", self.toggle_bold)
        toolbar.addAction("斜体", self.toggle_italic)
        toolbar.addAction("下划线", self.toggle_underline)
        toolbar.addAction("字体颜色", self.set_text_color)
        toolbar.addAction("插入图片", self.insert_image)
        toolbar.addAction("插入表格", self.insert_table)
        toolbar.addAction("插入时间", self.insert_datetime)
        toolbar.addAction("清除格式", self.clear_formatting)

    def toggle_bold(self):
        fmt = QTextCharFormat()
        weight = QFont.Bold if not self.editor.fontWeight() == QFont.Bold else QFont.Normal
        fmt.setFontWeight(weight)
        self.merge_format(fmt)

    def toggle_italic(self):
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self.editor.fontItalic())
        self.merge_format(fmt)

    def toggle_underline(self):
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not self.editor.fontUnderline())
        self.merge_format(fmt)

    def set_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            self.merge_format(fmt)

    def insert_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Images (*.png *.jpg *.bmp)")
        if file_path:
            cursor = self.editor.textCursor()
            cursor.insertImage(file_path)

    def insert_table(self):
        self.editor.textCursor().insertTable(2, 3)

    def insert_datetime(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.editor.insertPlainText(now)

    def clear_formatting(self):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            fmt = QTextCharFormat()
            cursor.mergeCharFormat(fmt)

    def merge_format(self, fmt: QTextCharFormat):
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
        cursor.mergeCharFormat(fmt)
        self.editor.setTextCursor(cursor)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RichTextEditor()
    window.show()
    sys.exit(app.exec())
