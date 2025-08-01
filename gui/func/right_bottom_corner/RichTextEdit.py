import os
import re
import base64
from PySide6.QtWidgets import QTextEdit, QMenu, QMessageBox
from PySide6.QtGui import QImage, QClipboard, QContextMenuEvent, QAction, QTextCharFormat, QFont, QCursor, QIcon, \
    QKeySequence
from PySide6.QtCore import QMimeData, QBuffer, QByteArray

''''
富文本类设置
'''
class RichTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.html_file_path = None  # 必须外部设置
        self._cleaning_base64 = False

    def insertFromMimeData(self, source: QMimeData):
        # 情况 1：如果剪贴板中包含图片数据（例如截图）
        if source.hasImage():
            image = source.imageData()
            if isinstance(image, QImage):
                if not self.html_file_path:
                    print("请先设置 html_file_path")
                    return

                # 获取 HTML 文件所在目录，用于保存粘贴的图片
                html_dir = os.path.dirname(self.html_file_path)

                # 生成一个唯一的图片文件名
                img_name = f"pasted_img_{len(os.listdir(html_dir))}.png"
                img_path = os.path.join(html_dir, img_name)

                # 保存图片到文件
                image.save(img_path)

                # 使用相对路径将图片插入到富文本框中
                self.textCursor().insertHtml(f'<img src="{img_name}">')

        # 情况 2：如果是拖拽或复制的文件（URL），例如拖拽一个本地图片进来
        elif source.hasUrls():
            for url in source.urls():
                local_path = url.toLocalFile()

                # 仅处理常见图片格式
                if local_path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
                    if not self.html_file_path:
                        print("请先设置 html_file_path")
                        continue

                    html_dir = os.path.dirname(self.html_file_path)

                    # 生成新的文件名，并拷贝图片到 HTML 文件目录中
                    img_name = f"dragged_img_{len(os.listdir(html_dir))}.png"
                    img_path = os.path.join(html_dir, img_name)

                    from shutil import copyfile
                    copyfile(local_path, img_path)

                    # 插入到 HTML 中使用相对路径
                    self.textCursor().insertHtml(f'<img src="{img_name}">')
                else:
                    # 如果不是图片，默认插入路径字符串
                    self.textCursor().insertText(local_path)

        # 情况 3：默认处理，比如复制粘贴文本
        else:
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

    '''右键点击事件'''
    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = QMenu()

        #  设置更美观的样式
        menu.setStyleSheet("""
                    QMenu {
                        background-color: #ffffff;
                        border: 1px solid #dcdcdc;
                        border-radius: 8px;
                        padding: 4px;
                        font-size: 14px;
                        font-family: 'Microsoft YaHei', 'Arial', sans-serif;
                    }
                    QMenu::item {
                        padding: 6px 24px 6px 8px;
                        border-radius: 4px;
                        color: #333333;
                    }
                    QMenu::item:selected {
                        background-color: #e6f7ff;
                        color: #1890ff;
                    }
                    QMenu::icon {
                        padding-left: 0px;
                        margin-left: 0px;
                    }
                    QMenu::separator {
                        height: 1px;
                        background: #f0f0f0;
                        margin: 4px 0px;
                    }
                """)

        new_file = QAction(QIcon(":images/scissors.png"), "新建文件", self)
        new_folder = QAction(QIcon(":images/question.png"), "新建文件夹", self)

        rename = QAction(QIcon(":images/question.png"), "重命名", self)
        rename.setShortcut(QKeySequence("F2"))

        delete = QAction(QIcon(":images/question.png"), "删除", self)
        delete.setShortcut(QKeySequence.Delete)

        open_folder = QAction(QIcon(":images/question.png"), "打开所在目录", self)
        refresh = QAction(QIcon(":images/question.png"), "刷新", self)

        sub_menu = QMenu("导出为", self)
        sub_menu.setStyleSheet(menu.styleSheet())  # 子菜单也继承样式
        sub_menu.addAction(QAction(QIcon(":images/question.png"), "PDF", self))
        sub_menu.addAction(QAction(QIcon(":images/question.png"), "Word", self))
        sub_menu.addAction(QAction(QIcon(":images/question.png"), "Markdown", self))

        menu.addAction(new_file)
        menu.addAction(new_folder)
        menu.addSeparator()
        menu.addAction(rename)
        menu.addAction(delete)
        menu.addSeparator()
        menu.addAction(open_folder)
        menu.addAction(refresh)
        menu.addSeparator()
        menu.addMenu(sub_menu)

        action = menu.exec(QCursor.pos())

        if action == new_file:
            QMessageBox.information(self, "提示", "新建文件")
        elif action == rename:
            QMessageBox.information(self, "提示", "重命名")
        elif action == delete:
            QMessageBox.warning(self, "提示", "删除")

    '''给字体加粗'''
    def toggle_bold(self):
        """Toggle bold formatting for selected text."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return

        fmt = QTextCharFormat()
        weight = QFont.Bold if not cursor.charFormat().font().bold() else QFont.Normal
        fmt.setFontWeight(weight)
        cursor.mergeCharFormat(fmt)
        self.setTextCursor(cursor)