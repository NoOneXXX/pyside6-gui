import os

from PySide6.QtCore import QUrl
from PySide6.QtGui import QFont, QTextDocument, QImage
from PySide6.QtWidgets import QTextEdit

# 富文本框
class RichTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFormatting(QTextEdit.AutoFormattingFlag.AutoAll)
        font = QFont("Times", 20)
        self.setFont(font)
        self.setFontPointSize(20)

    def insertFromMimeData(self, source):
        """Handle paste events to support images from clipboard."""
        cursor = self.textCursor()
        document = self.document()

        if source.hasImage():
            image = source.imageData()
            if image.isNull():
                super().insertFromMimeData(source)
                return

            image_name = f"image_{id(image)}.png"
            document.addResource(QTextDocument.ImageResource, QUrl(image_name), image)
            cursor.insertImage(image_name)
            self.setTextCursor(cursor)
        elif source.hasUrls():
            for u in source.urls():
                file_ext = os.path.splitext(str(u.toLocalFile()))[1].lower()
                if u.isLocalFile() and file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                    image = QImage(u.toLocalFile())
                    document.addResource(QTextDocument.ImageResource, u, image)
                    cursor.insertImage(u.toLocalFile())
                else:
                    break
            else:
                return
        else:
            super().insertFromMimeData(source)

    def canInsertFromMimeData(self, source):
        if source.hasImage() or source.hasUrls():
            return True
        return super().canInsertFromMimeData(source)
 # 右键鼠标点击事件
    def contextMenuEvent(self, event):
        """Customize the context menu to fix text shadow issue."""
        menu = self.createStandardContextMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                color: black;
                border: 1px solid #CCCCCC;
            }
            QMenu::item {
                background-color: transparent;
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #E0E0E0;
            }
        """)
        menu.exec(event.globalPos())