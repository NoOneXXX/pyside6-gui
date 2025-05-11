import sys, os, re, uuid
from PySide6.QtWidgets import QApplication, QTextEdit, QMainWindow
from PySide6.QtGui import QImage, QTextDocument, QTextCursor, QTextImageFormat
from PySide6.QtCore import QUrl

class RichTextEditor(QTextEdit):
    def __init__(self, html_path, parent=None):
        super().__init__(parent)
        self.html_path = html_path
        self.image_prefix = "image_"  # 保存图片时的前缀
        self.load_html_with_images()
        self.textChanged.connect(self.auto_save_note)

    def load_html_with_images(self):
        """加载 HTML 并将图片 src 注册为资源 + 替换为图片格式"""
        if not os.path.exists(self.html_path):
            return

        with open(self.html_path, "r", encoding="utf-8") as f:
            html = f.read()
            self.setHtml(html)

        base_dir = os.path.dirname(self.html_path)
        pattern = re.compile(r'<img[^>]+src="([^"]+)"')
        srcs = pattern.findall(html)

        doc = self.document()
        for src in srcs:
            img_path = os.path.join(base_dir, src)
            if os.path.exists(img_path):
                image = QImage(img_path)
                if not image.isNull():
                    url = QUrl(src)
                    doc.addResource(QTextDocument.ImageResource, url, image)

        # ✅ 替换文档中的 image 标签为真实图像格式（否则无法显示）
        cursor = QTextCursor(doc)
        cursor.movePosition(QTextCursor.Start)
        while not cursor.atEnd():
            cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
            if cursor.charFormat().isImageFormat():
                fmt = cursor.charFormat().toImageFormat()
                img_name = fmt.name()
                new_fmt = QTextImageFormat()
                new_fmt.setName(img_name)
                cursor.insertImage(new_fmt)

    def auto_save_note(self):
        """保存 HTML，并确保图片写入本地"""
        doc = self.document()
        html = self.toHtml()
        base_dir = os.path.dirname(self.html_path)

        pattern = re.compile(r'<img[^>]+src="([^"]+)"')
        srcs = pattern.findall(html)

        for src in srcs:
            img_path = os.path.join(base_dir, src)
            if not os.path.exists(img_path):
                image = doc.resource(QTextDocument.ImageResource, QUrl(src))
                if isinstance(image, QImage) and not image.isNull():
                    image.save(img_path)
                    print(f"[保存图片] {img_path}")

        with open(self.html_path, "w", encoding="utf-8") as f:
            f.write(html)
            print(f"[保存HTML] {self.html_path}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        html_path = r"C:\Users\Dell\Desktop\temp\log\test11\新建文件\新建文件\.note.html"
        self.editor = RichTextEditor(html_path)
        self.setCentralWidget(self.editor)
        self.setWindowTitle("富文本编辑器测试")
        self.resize(800, 600)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
