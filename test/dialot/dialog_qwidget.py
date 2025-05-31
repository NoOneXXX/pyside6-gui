from PySide6.QtWidgets import (
    QApplication, QDialog, QLabel, QVBoxLayout, QLineEdit, QFrame,
    QPushButton, QHBoxLayout, QWidget, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
import sys


class CreateNotebookDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setMinimumSize(460, 280)
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(255, 255, 255, 240);
                border-radius: 20px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 10)
        self.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        title = QLabel("📔 创建新的笔记本")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        main_layout.addWidget(title)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入笔记本名称…")
        self.name_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #CCC;
                border-radius: 12px;
                padding: 10px 16px;
                font-size: 11pt;
            }
        """)
        main_layout.addWidget(self.name_input)

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("笔记本描述（可选）")
        self.desc_input.setStyleSheet("""
            QLineEdit {
                background-color: #F7F9FB;
                border: 1px solid #EEE;
                border-radius: 12px;
                padding: 10px 16px;
                font-size: 10.5pt;
            }
        """)
        main_layout.addWidget(self.desc_input)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedHeight(36)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 10.5pt;
                padding: 6px 18px;
                color: #666;
            }
            QPushButton:hover {
                color: red;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        create_btn = QPushButton("创建")
        create_btn.setFixedHeight(36)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 8px;
                font-size: 10.5pt;
                padding: 6px 20px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
        """)
        create_btn.clicked.connect(self.accept)
        btn_layout.addWidget(create_btn)

        main_layout.addLayout(btn_layout)

    def get_notebook_data(self):
        return self.name_input.text().strip(), self.desc_input.text().strip()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    dialog = CreateNotebookDialog()
    if dialog.exec():
        name, desc = dialog.get_notebook_data()
        print("创建成功:", name, desc)

    sys.exit(0)
