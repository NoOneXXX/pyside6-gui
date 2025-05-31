import os
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QPushButton, QVBoxLayout, QWidget, QTextEdit, QMessageBox
)
import random


class FileShredder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔥 超级安全文件粉碎工具")
        self.setFixedSize(500, 300)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("待粉碎的文件路径将显示在这里...")

        self.select_btn = QPushButton("选择文件")
        self.select_btn.clicked.connect(self.select_file)

        self.shred_btn = QPushButton("⚠️ 粉碎文件（彻底删除）")
        self.shred_btn.clicked.connect(self.shred_file)

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addWidget(self.select_btn)
        layout.addWidget(self.shred_btn)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.selected_file = None

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择要粉碎的文件")
        if file_path:
            self.selected_file = file_path
            self.text_edit.setPlainText(file_path)

    def shred_file(self):
        path = self.selected_file
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "错误", "未选择有效文件或文件不存在！")
            return

        try:
            length = os.path.getsize(path)
            with open(path, "ba+", buffering=0) as f:
                # 第1次写全0
                f.seek(0)
                f.write(b'\x00' * length)
                # 第2次写全1
                f.seek(0)
                f.write(b'\xFF' * length)
                # 第3次写随机数据
                f.seek(0)
                f.write(os.urandom(length))
                f.flush()
                os.fsync(f.fileno())

            # 重命名防止文件名被恢复
            wiped_path = path + ".deleted"
            os.rename(path, wiped_path)
            os.remove(wiped_path)

            QMessageBox.information(self, "完成", "文件已彻底粉碎，无法恢复！")
            self.text_edit.clear()
            self.selected_file = None

        except Exception as e:
            QMessageBox.critical(self, "错误", f"粉碎失败：{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileShredder()
    window.show()
    sys.exit(app.exec())
