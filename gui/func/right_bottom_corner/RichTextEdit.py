import os
import re
import base64
from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import QImage, QClipboard
from PySide6.QtCore import QMimeData, QBuffer, QByteArray

class RichTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.html_file_path = None  # 必须外部设置
        self._cleaning_base64 = False

    def insertFromMimeData(self, source: QMimeData):
        if source.hasImage():
            image = source.imageData()
            if isinstance(image, QImage):
                # 保存图片
                if not self.html_file_path:
                    print("请先设置 html_file_path")
                    return

                html_dir = os.path.dirname(self.html_file_path)
                img_name = f"pasted_img_{len(os.listdir(html_dir))}.png"
                img_path = os.path.join(html_dir, img_name)
                image.save(img_path)

                # 插入图片使用相对路径
                self.textCursor().insertHtml(f'<img src="{img_name}">')
        else:
            # 默认行为处理文本或其他
            super().insertFromMimeData(source)

    def clean_base64_images(self):
        if self._cleaning_base64:
            return
        self._cleaning_base64 = True

        try:
            if not self.html_file_path:
                return

            html = self.toHtml()
            html_dir = os.path.dirname(self.html_file_path)

            pattern = re.compile(
                r'<img[^>]+src="data:image/(?P<ext>png|jpg|jpeg);base64,(?P<data>[A-Za-z0-9+/=]{100,})"'
            )

            counter = 0

            def repl(match):
                nonlocal counter
                ext = match.group("ext")
                data = match.group("data")

                filename = f"pasted_img_{counter}.{ext}"
                file_path = os.path.join(html_dir, filename)

                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(data))

                counter += 1
                return f'<img src="{filename}"'

            new_html = pattern.sub(repl, html)

            #  关键：避免 setHtml 再次触发 clean_base64_images
            if new_html != html:
                self.blockSignals(True)
                self.setHtml(new_html)
                self.blockSignals(False)

        finally:
            self._cleaning_base64 = False

