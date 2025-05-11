from PySide6.QtWidgets import QApplication, QTextEdit
from PySide6.QtCore import QUrl
import os, sys

app = QApplication(sys.argv)
editor = QTextEdit()

html_path = r"C:\Users\Dell\Desktop\temp\log\test11\新建文件\新建文件\.note.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

editor.setHtml(html)

# ✅ 加斜杠，确保是“目录”
base_dir = os.path.dirname(html_path)
base_url = QUrl.fromLocalFile(base_dir + os.sep)
print("baseUrl:", base_url.toString())

editor.document().setBaseUrl(base_url)

editor.resize(800, 600)
editor.show()
app.exec()
