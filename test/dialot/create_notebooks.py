from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox,
    QDialogButtonBox, QFormLayout
)

class CreateNoteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建笔记")
        self.setFixedSize(300, 200)

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.title_edit = QLineEdit()
        self.category_combo = QComboBox()
        self.category_combo.addItems(["默认分类", "工作", "学习", "生活"])

        form_layout.addRow("标题：", self.title_edit)
        form_layout.addRow("分类：", self.category_combo)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return self.title_edit.text(), self.category_combo.currentText()
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox,
    QDialogButtonBox, QFormLayout
)

class CreateNoteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建笔记")
        self.setFixedSize(300, 200)

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.title_edit = QLineEdit()
        self.category_combo = QComboBox()
        self.category_combo.addItems(["默认分类", "工作", "学习", "生活"])

        form_layout.addRow("标题：", self.title_edit)
        form_layout.addRow("分类：", self.category_combo)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return self.title_edit.text(), self.category_combo.currentText()

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QMessageBox
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("主窗口")
        self.setFixedSize(400, 300)

        btn = QPushButton("新建笔记", self)
        btn.clicked.connect(self.create_note)
        self.setCentralWidget(btn)

    def create_note(self):
        dialog = CreateNoteDialog(self)
        if dialog.exec():
            title, category = dialog.get_data()
            QMessageBox.information(self, "笔记信息", f"标题：{title}\n分类：{category}")
            # ➤ 你可以在这里创建文件夹、笔记文件等

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
